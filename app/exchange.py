from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import login_required, current_user
from datetime import datetime, timezone

from .domain import (
    create_credit_transaction,
    get_credit_balance,
    get_session_by_id,
    list_user_sessions,
    session_has_credit_transactions,
)
from .supabase_client import supabase

exchange_bp = Blueprint("exchange", __name__, url_prefix="/exchange")


def _utc_now():
    return datetime.now(timezone.utc).isoformat()


@exchange_bp.route("/request/<int:provider_id>", methods=["POST"])
@login_required
def create_exchange(provider_id):
    exchange_type = request.form.get("exchange_type", "time_credit")
    provider_skill_id = request.form.get("provider_skill_id", type=int)
    requester_skill_id = request.form.get("requester_skill_id", type=int)
    requester_notes = (request.form.get("requester_notes") or "").strip() or None

    if provider_id == int(current_user.id):
        flash("You cannot request a session with yourself.", "danger")
        return redirect(url_for("skills.matches"))

    if not provider_skill_id:
        flash("Choose the skill you want help with before sending the request.", "danger")
        return redirect(url_for("skills.matches"))

    if exchange_type == "direct_swap" and not requester_skill_id:
        flash("Direct swaps need one of your offered skills selected.", "danger")
        return redirect(url_for("skills.matches"))

    if exchange_type == "time_credit" and get_credit_balance(current_user.id) < 1:
        flash("You need at least 1 credit to request a time-credit session.", "danger")
        return redirect(url_for("skills.matches"))

    duplicate_response = (
        supabase.table("exchange_sessions")
        .select("id")
        .eq("requester_id", current_user.id)
        .eq("provider_id", provider_id)
        .eq("provider_skill_id", provider_skill_id)
        .in_("status", ["pending", "accepted"])
        .limit(1)
        .execute()
    )
    if duplicate_response.data:
        flash("You already have an active request for this skill with this provider.", "warning")
        return redirect(url_for("skills.matches"))

    session_data = {
        "requester_id": current_user.id,
        "provider_id": provider_id,
        "requester_skill_id": requester_skill_id,
        "provider_skill_id": provider_skill_id,
        "exchange_type": exchange_type,
        "requester_notes": requester_notes,
        "duration_minutes": request.form.get("duration_minutes", type=int) or 60,
        "status": "pending",
        "created_at": _utc_now(),
        "updated_at": _utc_now(),
    }

    response = supabase.table("exchange_sessions").insert(session_data).execute()

    if not response.data:
        flash("Failed to send exchange request.", "danger")
        return redirect(url_for("skills.matches"))

    flash("Exchange request sent.", "success")
    return redirect(url_for("skills.matches"))


@exchange_bp.route("/sessions")
@login_required
def sessions():
    return render_template("exchange/sessions.html", sessions=list_user_sessions(current_user.id))


@exchange_bp.route("/session/<int:session_id>/status", methods=["POST"])
@login_required
def update_session_status(session_id):
    session = get_session_by_id(session_id)
    if not session:
        flash("Session not found.", "danger")
        return redirect(url_for("exchange.sessions"))

    new_status = request.form.get("status")
    is_requester = str(session["requester_id"]) == str(current_user.id)
    is_provider = str(session["provider_id"]) == str(current_user.id)

    if not (is_requester or is_provider):
        flash("You do not have access to update this session.", "danger")
        return redirect(url_for("exchange.sessions"))

    allowed = False
    if new_status in {"accepted", "rejected"} and is_provider and session["status"] == "pending":
        allowed = True
    elif new_status == "cancelled" and session["status"] in {"pending", "accepted"}:
        allowed = True

    if not allowed:
        flash("That session update is not allowed right now.", "warning")
        return redirect(url_for("exchange.sessions"))

    payload = {"status": new_status, "updated_at": _utc_now()}
    if new_status in {"rejected", "cancelled"}:
        payload["requester_confirmed"] = False
        payload["provider_confirmed"] = False

    supabase.table("exchange_sessions").update(payload).eq("id", session_id).execute()

    flash(f"Session marked as {new_status}.", "success")
    return redirect(url_for("exchange.sessions"))


@exchange_bp.route("/session/<int:session_id>/confirm", methods=["POST"])
@login_required
def confirm_session(session_id):
    session = get_session_by_id(session_id)
    if not session:
        flash("Session not found.", "danger")
        return redirect(url_for("exchange.sessions"))

    if session["status"] != "accepted":
        flash("Only accepted sessions can be confirmed.", "warning")
        return redirect(url_for("exchange.sessions"))

    is_requester = str(session["requester_id"]) == str(current_user.id)
    is_provider = str(session["provider_id"]) == str(current_user.id)
    if not (is_requester or is_provider):
        flash("You do not have access to confirm this session.", "danger")
        return redirect(url_for("exchange.sessions"))

    payload = {"updated_at": _utc_now()}
    if is_requester:
        payload["requester_confirmed"] = True
    if is_provider:
        payload["provider_confirmed"] = True

    updated = supabase.table("exchange_sessions").update(payload).eq("id", session_id).execute()
    session = updated.data[0] if updated.data else get_session_by_id(session_id)

    if session.get("requester_confirmed") and session.get("provider_confirmed"):
        completion_payload = {"status": "completed", "updated_at": _utc_now()}
        supabase.table("exchange_sessions").update(completion_payload).eq("id", session_id).execute()

        if session["exchange_type"] == "time_credit" and not session_has_credit_transactions(session_id):
            create_credit_transaction(
                session["requester_id"],
                session_id,
                -1,
                "spent",
                "Time-credit exchange completed",
            )
            create_credit_transaction(
                session["provider_id"],
                session_id,
                1,
                "earned",
                "Time-credit exchange completed",
            )

        flash("Both confirmations are in. Session completed successfully.", "success")
    else:
        flash("Your completion confirmation has been recorded.", "success")

    return redirect(url_for("exchange.sessions"))


@exchange_bp.route("/credits/history")
@login_required
def credit_history():
    transactions = (
        supabase.table("credit_transactions")
        .select("*")
        .eq("user_id", current_user.id)
        .order("created_at", desc=True)
        .execute()
    )
    return render_template("exchange/credit_history.html", transactions=transactions.data or [])
