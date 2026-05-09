"""
Feedback module for SkillBridge
Handles reviews and reputation scoring
"""
from flask import Blueprint, render_template, request, redirect, session, flash
from app.auth import login_required, get_db_connection

feedback_bp = Blueprint('feedback', __name__, url_prefix='/feedback')

# Placeholder routes - will be implemented in Sprint 4
@feedback_bp.route('/reviews', methods=['GET'])
@login_required
def my_reviews():
    """View all reviews received by current user."""
    return render_template('feedback/reviews.html')
