from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import login_required, current_user
from datetime import datetime, timezone

from .domain import get_session_by_id
from .supabase_client import supabase

feedback_bp = Blueprint("feedback", __name__, url_prefix="/feedback")


# ============================================================
# SUBMIT REVIEW
# ============================================================
@feedback_bp.route("/submit/<int:session_id>", methods=["GET", "POST"])
@login_required
def submit_review(session_id):

    # ----------------------------------------
    # GET SESSION DETAILS
    # ----------------------------------------
    session = get_session_by_id(session_id)

    if not session:
        flash("Session not found.", "danger")
        return redirect(url_for("exchange.sessions"))

    if str(current_user.id) not in {str(session["requester_id"]), str(session["provider_id"])}:
        flash("You cannot review a session you were not part of.", "danger")
        return redirect(url_for("exchange.sessions"))

    if session["status"] != "completed":
        flash("Reviews are available after a session is completed.", "warning")
        return redirect(url_for("exchange.sessions"))

    # ============================================================
    # HANDLE FORM SUBMISSION
    # ============================================================
    if request.method == "POST":

        rating = request.form.get("rating", type=int)
        comment = (request.form.get("comment") or "").strip()

        if not rating or rating < 1 or rating > 5:
            flash("Please provide a rating between 1 and 5.", "danger")
            return redirect(url_for("feedback.submit_review", session_id=session_id))

        # --------------------------------------------------------
        # DETERMINE WHO IS BEING REVIEWED
        # --------------------------------------------------------
        if session["requester_id"] == current_user.id:
            reviewee_id = session["provider_id"]
        else:
            reviewee_id = session["requester_id"]

        # --------------------------------------------------------
        # BUILD REVIEW OBJECT
        # --------------------------------------------------------
        review_data = {
            "session_id": session_id,
            "reviewer_id": current_user.id,
            "reviewee_id": reviewee_id,
            "rating": rating,
            "comment": comment,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }

        response = supabase.table("reviews").insert(review_data).execute()

        if not response.data:
            flash("Review could not be submitted. You may already have reviewed this session.", "danger")
            return redirect(url_for("exchange.sessions"))

        flash("Review submitted successfully.", "success")
        return redirect(url_for("exchange.sessions"))

    # ============================================================
    # RENDER PAGE
    # ============================================================
    return render_template(
        "feedback/review.html",
        session=session,
    )
