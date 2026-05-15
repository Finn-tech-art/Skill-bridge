from pathlib import Path

from flask import Blueprint, current_app, redirect, render_template, send_from_directory, url_for
from flask_login import current_user

test_bp = Blueprint("test", __name__)

@test_bp.route("/")
def home():
    if current_user.is_authenticated:
        return redirect(url_for("skills.dashboard"))

    return render_template("home.html")


@test_bp.route("/googlefdab6438de2f962c.html")
def google_site_verification():
    project_root = Path(current_app.root_path).parent
    return send_from_directory(project_root, "googlefdab6438de2f962c.html", mimetype="text/html")
