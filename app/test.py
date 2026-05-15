from flask import Blueprint, redirect, render_template, url_for
from flask_login import current_user

test_bp = Blueprint("test", __name__)

@test_bp.route("/")
def home():
    if current_user.is_authenticated:
        return redirect(url_for("skills.dashboard"))

    return render_template("home.html")
