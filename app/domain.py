from collections import defaultdict
from datetime import datetime, timezone
import re
from statistics import mean

from .supabase_client import supabase


PROFICIENCY_SCORES = {
    "beginner": 1,
    "intermediate": 2,
    "advanced": 3,
    "expert": 4,
}


def utc_now_iso():
    return datetime.now(timezone.utc).isoformat()


def slugify(value):
    normalized = re.sub(r"[^a-z0-9]+", "-", value.strip().lower())
    normalized = re.sub(r"-{2,}", "-", normalized).strip("-")
    return normalized or "skill"


def fetch_users_by_ids(user_ids):
    ids = [user_id for user_id in set(user_ids) if user_id is not None]
    if not ids:
        return {}

    response = supabase.table("users").select("*").in_("id", ids).execute()
    return {user["id"]: user for user in (response.data or [])}


def get_user_by_id(user_id):
    response = supabase.table("users").select("*").eq("id", user_id).single().execute()
    return response.data


def fetch_skills_by_ids(skill_ids):
    ids = [skill_id for skill_id in set(skill_ids) if skill_id is not None]
    if not ids:
        return {}

    response = supabase.table("skills").select("*").in_("id", ids).execute()
    return {skill["id"]: skill for skill in (response.data or [])}


def find_skill_by_name(skill_name):
    response = supabase.table("skills").select("*").ilike("name", skill_name).limit(1).execute()
    data = response.data or []
    return data[0] if data else None


def get_or_create_skill(skill_name, description=None):
    existing = find_skill_by_name(skill_name)
    if existing:
        return existing

    base_slug = slugify(skill_name)
    candidate_slug = base_slug
    suffix = 1
    while True:
        slug_check = supabase.table("skills").select("id").eq("slug", candidate_slug).limit(1).execute()
        if not slug_check.data:
            break
        suffix += 1
        candidate_slug = f"{base_slug}-{suffix}"

    payload = {
        "name": skill_name,
        "slug": candidate_slug,
        "description": description or None,
        "created_at": utc_now_iso(),
    }
    response = supabase.table("skills").insert(payload).execute()
    data = response.data or []
    return data[0] if data else None


def list_reviews_for_users(user_ids):
    ids = [user_id for user_id in set(user_ids) if user_id is not None]
    if not ids:
        return []

    response = supabase.table("reviews").select("*").in_("reviewee_id", ids).execute()
    return response.data or []


def get_reputation_map(user_ids):
    ratings_by_user = defaultdict(list)
    for review in list_reviews_for_users(user_ids):
        ratings_by_user[review["reviewee_id"]].append(review["rating"])

    reputation = {}
    for user_id in user_ids:
        ratings = ratings_by_user.get(user_id, [])
        reputation[user_id] = round(mean(ratings), 1) if ratings else None

    return reputation


def list_credit_transactions(user_id):
    response = (
        supabase.table("credit_transactions")
        .select("*")
        .eq("user_id", user_id)
        .order("created_at", desc=True)
        .execute()
    )
    return response.data or []


def get_credit_balance(user_id):
    transactions = list_credit_transactions(user_id)
    if not transactions:
        return 0
    return transactions[0]["balance_after"]


def get_credit_balances(user_ids):
    return {user_id: get_credit_balance(user_id) for user_id in set(user_ids)}


def get_user_skill_offers(user_id):
    response = supabase.table("user_skill_offers").select("*").eq("user_id", user_id).execute()
    return response.data or []


def get_user_skill_wants(user_id):
    response = supabase.table("user_skill_wants").select("*").eq("user_id", user_id).execute()
    return response.data or []


def enrich_skill_records(records, record_type):
    skill_map = fetch_skills_by_ids([record["skill_id"] for record in records])
    enriched = []

    for record in records:
        skill = skill_map.get(record["skill_id"], {})
        merged = dict(record)
        merged["skill_name"] = skill.get("name", f"Skill #{record['skill_id']}")
        merged["skill_slug"] = skill.get("slug")
        merged["skill_description"] = skill.get("description")
        merged["card_description"] = (
            record.get("description")
            if record_type == "offer"
            else record.get("notes") or skill.get("description")
        )
        enriched.append(merged)

    return enriched


def summarize_dashboard(user_id):
    offered = enrich_skill_records(get_user_skill_offers(user_id), "offer")
    wanted = enrich_skill_records(get_user_skill_wants(user_id), "want")

    sessions_response = (
        supabase.table("exchange_sessions")
        .select("*")
        .or_(f"requester_id.eq.{user_id},provider_id.eq.{user_id}")
        .execute()
    )
    sessions = sessions_response.data or []

    status_counts = defaultdict(int)
    for session in sessions:
        status_counts[session["status"]] += 1

    return {
        "offered": offered,
        "wanted": wanted,
        "profile": get_user_by_id(user_id),
        "metrics": {
            "credit_balance": get_credit_balance(user_id),
            "reputation": get_reputation_map([user_id]).get(user_id),
            "offers_count": len(offered),
            "wants_count": len(wanted),
            "active_sessions": sum(
                1 for session in sessions if session["status"] in {"pending", "accepted"}
            ),
            "completed_sessions": status_counts["completed"],
        },
    }


def build_match_recommendations(user_id):
    wanted = enrich_skill_records(get_user_skill_wants(user_id), "want")
    offered = enrich_skill_records(get_user_skill_offers(user_id), "offer")
    wanted_by_skill_id = {item["skill_id"]: item for item in wanted}
    offered_by_skill_id = {item["skill_id"]: item for item in offered}

    wanted_ids = list(wanted_by_skill_id.keys())
    if not wanted_ids:
        return []

    offers_response = (
        supabase.table("user_skill_offers")
        .select("*")
        .in_("skill_id", wanted_ids)
        .neq("user_id", user_id)
        .execute()
    )
    matching_offers = offers_response.data or []

    provider_ids = [offer["user_id"] for offer in matching_offers]
    if not provider_ids:
        return []

    provider_wants_response = (
        supabase.table("user_skill_wants")
        .select("*")
        .in_("user_id", provider_ids)
        .execute()
    )
    provider_wants = provider_wants_response.data or []

    provider_wants_map = defaultdict(list)
    for want in provider_wants:
        provider_wants_map[want["user_id"]].append(want)

    skill_map = fetch_skills_by_ids(
        wanted_ids
        + [offer["skill_id"] for offer in matching_offers]
        + [want["skill_id"] for want in provider_wants]
        + list(offered_by_skill_id.keys())
    )
    users = fetch_users_by_ids(provider_ids)
    reputations = get_reputation_map(provider_ids)

    grouped_matches = defaultdict(lambda: {
        "provider": None,
        "score": 0.0,
        "matched_skills": [],
        "reciprocal_skills": [],
        "recommended_exchange_type": "time_credit",
    })

    for offer in matching_offers:
        provider_id = offer["user_id"]
        wanted_item = wanted_by_skill_id.get(offer["skill_id"])
        if not wanted_item:
            continue

        group = grouped_matches[provider_id]
        group["provider"] = users.get(provider_id)

        base_priority = wanted_item.get("priority") or 1
        proficiency_bonus = PROFICIENCY_SCORES.get(offer.get("proficiency_level"), 2) * 0.5
        verification_bonus = 0.75 if offer.get("is_verified") else 0
        reputation_bonus = (reputations.get(provider_id) or 0) * 0.35
        score = base_priority * 2 + proficiency_bonus + verification_bonus + reputation_bonus
        group["score"] += score
        group["matched_skills"].append({
            "skill_id": offer["skill_id"],
            "skill_name": skill_map.get(offer["skill_id"], {}).get("name", f"Skill #{offer['skill_id']}"),
            "priority": base_priority,
            "proficiency_level": offer.get("proficiency_level"),
            "is_verified": offer.get("is_verified", False),
            "offer_id": offer["id"],
        })

    for provider_id, wants in provider_wants_map.items():
        reciprocal = []
        for want in wants:
            offered_item = offered_by_skill_id.get(want["skill_id"])
            if offered_item:
                reciprocal.append({
                    "skill_id": want["skill_id"],
                    "skill_name": skill_map.get(want["skill_id"], {}).get("name", f"Skill #{want['skill_id']}"),
                    "priority": want.get("priority") or 1,
                })

        if reciprocal and provider_id in grouped_matches:
            grouped_matches[provider_id]["reciprocal_skills"] = reciprocal
            grouped_matches[provider_id]["recommended_exchange_type"] = "direct_swap"
            grouped_matches[provider_id]["score"] += len(reciprocal) * 3

    results = []
    for provider_id, data in grouped_matches.items():
        provider = data["provider"]
        if not provider:
            continue

        results.append({
            "provider": provider,
            "score": round(data["score"], 1),
            "matched_skills": sorted(
                data["matched_skills"],
                key=lambda item: (item["priority"], item["skill_name"]),
                reverse=True,
            ),
            "reciprocal_skills": sorted(
                data["reciprocal_skills"],
                key=lambda item: (item["priority"], item["skill_name"]),
                reverse=True,
            ),
            "recommended_exchange_type": data["recommended_exchange_type"],
            "provider_credit_balance": get_credit_balance(provider_id),
            "provider_reputation": reputations.get(provider_id),
        })

    results.sort(
        key=lambda item: (
            item["recommended_exchange_type"] != "direct_swap",
            -item["score"],
            item["provider"]["full_name"].lower(),
        )
    )
    return results


def _review_lookup_for_user(user_id, session_ids):
    if not session_ids:
        return set()

    response = (
        supabase.table("reviews")
        .select("session_id")
        .eq("reviewer_id", user_id)
        .in_("session_id", session_ids)
        .execute()
    )
    return {item["session_id"] for item in (response.data or [])}


def list_user_sessions(user_id):
    response = (
        supabase.table("exchange_sessions")
        .select("*")
        .or_(f"requester_id.eq.{user_id},provider_id.eq.{user_id}")
        .order("created_at", desc=True)
        .execute()
    )
    sessions = response.data or []

    if not sessions:
        return []

    user_map = fetch_users_by_ids(
        [session["requester_id"] for session in sessions]
        + [session["provider_id"] for session in sessions]
    )
    skill_map = fetch_skills_by_ids(
        [session.get("requester_skill_id") for session in sessions]
        + [session.get("provider_skill_id") for session in sessions]
    )
    reviewed_sessions = _review_lookup_for_user(user_id, [session["id"] for session in sessions])

    enriched_sessions = []
    for session in sessions:
        is_requester = str(session["requester_id"]) == str(user_id)
        counterpart_id = session["provider_id"] if is_requester else session["requester_id"]
        counterpart = user_map.get(counterpart_id, {})

        enriched = dict(session)
        enriched["is_requester"] = is_requester
        enriched["counterpart"] = counterpart
        enriched["requester_name"] = user_map.get(session["requester_id"], {}).get("full_name", "Unknown requester")
        enriched["provider_name"] = user_map.get(session["provider_id"], {}).get("full_name", "Unknown provider")
        enriched["provider_skill_name"] = skill_map.get(session.get("provider_skill_id"), {}).get(
            "name", "Not specified"
        )
        enriched["requester_skill_name"] = skill_map.get(session.get("requester_skill_id"), {}).get(
            "name", "Not specified"
        )
        enriched["user_has_reviewed"] = session["id"] in reviewed_sessions
        enriched["can_review"] = session["status"] == "completed" and session["id"] not in reviewed_sessions
        enriched["awaiting_user_confirmation"] = (
            session["status"] == "accepted"
            and (
                (is_requester and not session.get("requester_confirmed"))
                or (not is_requester and not session.get("provider_confirmed"))
            )
        )
        enriched_sessions.append(enriched)

    return enriched_sessions


def get_session_by_id(session_id):
    response = supabase.table("exchange_sessions").select("*").eq("id", session_id).single().execute()
    return response.data


def update_user_profile(user_id, payload):
    payload = dict(payload)
    payload["updated_at"] = utc_now_iso()
    return supabase.table("users").update(payload).eq("id", user_id).execute()


def create_user_skill_offer(user_id, skill_id, proficiency_level, description):
    payload = {
        "user_id": user_id,
        "skill_id": skill_id,
        "proficiency_level": proficiency_level,
        "description": description or None,
        "updated_at": utc_now_iso(),
        "created_at": utc_now_iso(),
    }
    return supabase.table("user_skill_offers").insert(payload).execute()


def create_user_skill_want(user_id, skill_id, priority, notes):
    payload = {
        "user_id": user_id,
        "skill_id": skill_id,
        "priority": priority,
        "notes": notes or None,
        "updated_at": utc_now_iso(),
        "created_at": utc_now_iso(),
    }
    return supabase.table("user_skill_wants").insert(payload).execute()


def delete_user_skill_offer(record_id, user_id):
    return supabase.table("user_skill_offers").delete().eq("id", record_id).eq("user_id", user_id).execute()


def delete_user_skill_want(record_id, user_id):
    return supabase.table("user_skill_wants").delete().eq("id", record_id).eq("user_id", user_id).execute()


def list_browseable_skill_offers(query=None):
    response = supabase.table("user_skill_offers").select("*").execute()
    offers = response.data or []
    if not offers:
        return []

    users = fetch_users_by_ids([offer["user_id"] for offer in offers])
    skills = fetch_skills_by_ids([offer["skill_id"] for offer in offers])
    reputations = get_reputation_map(users.keys())

    results = []
    needle = (query or "").strip().lower()
    for offer in offers:
        user = users.get(offer["user_id"], {})
        skill = skills.get(offer["skill_id"], {})
        haystack = " ".join(
            str(value or "")
            for value in [
                skill.get("name"),
                skill.get("description"),
                offer.get("description"),
                user.get("full_name"),
                user.get("department"),
            ]
        ).lower()
        if needle and needle not in haystack:
            continue

        results.append({
            "offer_id": offer["id"],
            "provider": user,
            "skill_id": offer["skill_id"],
            "skill_name": skill.get("name", f"Skill #{offer['skill_id']}"),
            "skill_description": skill.get("description"),
            "offer_description": offer.get("description"),
            "proficiency_level": offer.get("proficiency_level"),
            "is_verified": offer.get("is_verified", False),
            "reputation": reputations.get(offer["user_id"]),
        })

    results.sort(
        key=lambda item: (
            item["skill_name"].lower(),
            -(PROFICIENCY_SCORES.get(item["proficiency_level"], 0)),
            item["provider"].get("full_name", "").lower(),
        )
    )
    return results


def create_credit_transaction(user_id, session_id, amount, transaction_type, reference_note):
    current_balance = get_credit_balance(user_id)
    new_balance = current_balance + amount

    payload = {
        "user_id": user_id,
        "session_id": session_id,
        "amount": amount,
        "balance_after": new_balance,
        "transaction_type": transaction_type,
        "reference_note": reference_note,
    }
    return supabase.table("credit_transactions").insert(payload).execute()


def session_has_credit_transactions(session_id):
    response = (
        supabase.table("credit_transactions")
        .select("id")
        .eq("session_id", session_id)
        .limit(1)
        .execute()
    )
    return bool(response.data)
