from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from .domain import (
    build_match_recommendations,
    create_user_skill_offer,
    create_user_skill_want,
    delete_user_skill_offer,
    delete_user_skill_want,
    get_public_provider_profile,
    get_or_create_skill,
    list_browseable_skill_offers,
    summarize_dashboard,
)

skills_bp = Blueprint("skills", __name__, url_prefix="/skills")

@skills_bp.route("/dashboard")
@login_required
def dashboard():
    summary = summarize_dashboard(current_user.id)

    return render_template(
        "skills/dashboard.html",
        offered_skills=summary["offered"],
        wanted_skills=summary["wanted"],
        metrics=summary["metrics"],
    )


@skills_bp.route("/matches")
@login_required
def matches():
    return render_template("skills/matches.html", matches=build_match_recommendations(current_user.id))


@skills_bp.route("/browse")
@login_required
def browse():
    query = request.args.get("q", "")
    return render_template(
        "skills/browse.html",
        skills=list_browseable_skill_offers(query=query),
        query=query,
    )


@skills_bp.route("/provider/<int:user_id>")
@login_required
def provider_profile(user_id):
    profile = get_public_provider_profile(user_id)
    if not profile:
        flash("That teacher profile could not be found.", "danger")
        return redirect(url_for("skills.browse"))

    return render_template("skills/provider_profile.html", profile=profile)


@skills_bp.route("/add", methods=["POST"])
@login_required
def add_skill():
    skill_name = (request.form.get("skill_name") or "").strip()
    skill_type = request.form.get("skill_type")
    description = (request.form.get("description") or "").strip() or None

    if not skill_name or skill_type not in {"offer", "want"}:
        flash("Choose a valid skill name and type.", "danger")
        return redirect(url_for("skills.dashboard"))

    skill = get_or_create_skill(skill_name, description=description)
    if not skill:
        flash("That skill could not be created right now.", "danger")
        return redirect(url_for("skills.dashboard"))

    if skill_type == "offer":
        proficiency_level = request.form.get("proficiency_level") or "intermediate"
        response = create_user_skill_offer(current_user.id, skill["id"], proficiency_level, description)
    else:
        priority = request.form.get("priority", type=int) or 1
        response = create_user_skill_want(current_user.id, skill["id"], priority, description)

    if not response.data:
        flash("That skill may already exist on your profile.", "warning")
        return redirect(url_for("skills.dashboard"))

    flash("Skill added successfully.", "success")
    return redirect(url_for("skills.dashboard"))


@skills_bp.route("/delete/<skill_type>/<int:record_id>", methods=["POST"])
@login_required
def delete_skill(skill_type, record_id):
    if skill_type == "offer":
        response = delete_user_skill_offer(record_id, current_user.id)
    elif skill_type == "want":
        response = delete_user_skill_want(record_id, current_user.id)
    else:
        flash("Invalid skill type.", "danger")
        return redirect(url_for("skills.dashboard"))

    if not response.data:
        flash("That skill could not be removed.", "danger")
        return redirect(url_for("skills.dashboard"))

    flash("Skill removed from your profile.", "success")
    return redirect(url_for("skills.dashboard"))
