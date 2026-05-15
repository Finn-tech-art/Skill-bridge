from flask import Blueprint, flash, redirect, render_template, request, session, url_for
from flask_login import current_user, login_required, login_user, logout_user, UserMixin

from .domain import create_credit_transaction, get_credit_balance, get_reputation_map, update_user_profile
from .supabase_client import create_supabase_client, supabase

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")


class AuthUser(UserMixin):
    def __init__(self, user_id, full_name, email, username=None, auth_user_id=None):
        self.id = str(user_id)
        self.full_name = full_name
        self.email = email
        self.username = username
        self.auth_user_id = auth_user_id

def get_user_by_username(username: str):
    response = supabase.table("users").select("*").eq("username", username).execute()
    data = response.data
    return data[0] if data else None

def get_user_by_email(email: str):
    response = supabase.table("users").select("*").eq("email", email).execute()
    data = response.data
    return data[0] if data else None


def get_user_by_id(user_id: str):
    response = supabase.table("users").select("*").eq("id", user_id).execute()
    data = response.data
    return data[0] if data else None


def get_user_by_auth_user_id(auth_user_id: str):
    response = supabase.table("users").select("*").eq("auth_user_id", auth_user_id).execute()
    data = response.data
    return data[0] if data else None


def sync_profile_from_auth(auth_user, profile_seed):
    existing_profile = get_user_by_auth_user_id(auth_user.id)
    if existing_profile:
        return existing_profile

    email = getattr(auth_user, "email", None)
    legacy_profile = get_user_by_email(email) if email else None

    if legacy_profile:
        response = (
            supabase.table("users")
            .update({"auth_user_id": auth_user.id})
            .eq("id", legacy_profile["id"])
            .execute()
        )
        return (response.data or [legacy_profile])[0]

    insert_payload = {
        "auth_user_id": auth_user.id,
        "full_name": profile_seed["full_name"],
        "email": profile_seed["email"],
        "username": profile_seed["username"],
        "year_of_study": profile_seed.get("year_of_study"),
        "department": profile_seed.get("department"),
        "bio": profile_seed.get("bio"),
        "is_active": True,
    }
    response = supabase.table("users").insert(insert_payload).execute()
    return (response.data or [None])[0]


def store_supabase_session_tokens(auth_session, auth_user_id):
    session["sb_access_token"] = auth_session.access_token
    session["sb_refresh_token"] = auth_session.refresh_token
    session["sb_auth_user_id"] = auth_user_id


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        full_name = (request.form.get("full_name") or "").strip()
        email = (request.form.get("email") or "").strip().lower()
        username = (request.form.get("username") or "").strip().lower()
        password = request.form.get("password")
        year_of_study = request.form.get("year_of_study")
        department = (request.form.get("department") or "").strip() or None
        bio = (request.form.get("bio") or "").strip() or None

        if not all([full_name, email, username, password]):
            flash("Complete the required fields before registering.", "danger")
            return redirect(url_for("auth.register"))

        existing_username = get_user_by_username(username)
        if existing_username:
            flash("Username already taken.", "danger")
            return redirect(url_for("auth.register"))

        auth_client = create_supabase_client()
        try:
            sign_up_response = auth_client.auth.sign_up(
                {
                    "email": email,
                    "password": password,
                    "options": {
                        "data": {
                            "full_name": full_name,
                            "username": username,
                        }
                    },
                }
            )
        except Exception as exc:
            flash(str(exc), "danger")
            return redirect(url_for("auth.register"))

        auth_user = getattr(sign_up_response, "user", None)
        if not auth_user:
            flash("Registration failed in Supabase Auth.", "danger")
            return redirect(url_for("auth.register"))

        profile_user = sync_profile_from_auth(
            auth_user,
            {
                "full_name": full_name,
                "email": email,
                "username": username,
                "year_of_study": int(year_of_study) if year_of_study else None,
                "department": department,
                "bio": bio,
            },
        )
        if not profile_user:
            flash("Profile creation failed after account signup.", "danger")
            return redirect(url_for("auth.register"))

        existing_credits = supabase.table("credit_transactions").select("id").eq("user_id", profile_user["id"]).limit(1).execute()
        if not existing_credits.data:
            create_credit_transaction(
                profile_user["id"],
                None,
                100,
                "adjustment",
                "Welcome credits for new account",
            )

        if getattr(sign_up_response, "session", None):
            store_supabase_session_tokens(sign_up_response.session, auth_user.id)
            login_user(
                AuthUser(
                    user_id=profile_user["id"],
                    full_name=profile_user["full_name"],
                    email=profile_user["email"],
                    username=profile_user.get("username"),
                    auth_user_id=profile_user.get("auth_user_id"),
                )
            )
            flash("Registration successful. Your account is ready to use.", "success")
            return redirect(url_for("skills.dashboard"))

        flash("Registration successful. Check your email to confirm your account before logging in.", "success")
        return redirect(url_for("auth.login"))

    return render_template("auth/register.html")


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("skills.dashboard"))

    if request.method == "POST":
        email = (request.form.get("email") or "").strip().lower()
        password = request.form.get("password")

        auth_client = create_supabase_client()
        try:
            auth_response = auth_client.auth.sign_in_with_password(
                {
                    "email": email,
                    "password": password,
                }
            )
        except Exception as exc:
            flash(str(exc), "danger")
            return render_template("auth/login.html")

        auth_user = getattr(auth_response, "user", None)
        auth_session = getattr(auth_response, "session", None)
        if auth_user and auth_session:
            metadata = auth_user.user_metadata or {}
            profile_user = sync_profile_from_auth(
                auth_user,
                {
                    "full_name": metadata.get("full_name") or email.split("@")[0],
                    "email": email,
                    "username": metadata.get("username") or email.split("@")[0],
                    "year_of_study": None,
                    "department": None,
                    "bio": None,
                },
            )
            if not profile_user:
                flash("Profile loading failed after login.", "danger")
                return render_template("auth/login.html")

            store_supabase_session_tokens(auth_session, auth_user.id)
            auth_user = AuthUser(
                user_id=profile_user["id"],
                full_name=profile_user["full_name"],
                email=profile_user["email"],
                username=profile_user.get("username"),
                auth_user_id=profile_user.get("auth_user_id"),
            )
            login_user(auth_user)
            flash("Login successful.", "success")
            return redirect(url_for("skills.dashboard"))

        flash("Invalid email or password.", "danger")

    return render_template("auth/login.html")


@auth_bp.route("/logout")
@login_required
def logout():
    access_token = session.get("sb_access_token")
    refresh_token = session.get("sb_refresh_token")
    if access_token and refresh_token:
        try:
            auth_client = create_supabase_client()
            auth_client.auth.set_session(access_token, refresh_token)
            auth_client.auth.sign_out()
        except Exception:
            pass

    logout_user()
    session.pop("sb_access_token", None)
    session.pop("sb_refresh_token", None)
    session.pop("sb_auth_user_id", None)
    flash("You have been logged out.", "info")
    return redirect(url_for("auth.login"))


@auth_bp.route("/profile")
@login_required
def profile():
    user = get_user_by_id(current_user.id)
    if not user:
        flash("Profile could not be loaded.", "danger")
        return redirect(url_for("skills.dashboard"))

    user["credit_balance"] = get_credit_balance(current_user.id)
    user["reputation_score"] = get_reputation_map([current_user.id]).get(current_user.id)
    return render_template("auth/profile.html", user=user)


@auth_bp.route("/profile/edit", methods=["POST"])
@login_required
def edit_profile():
    full_name = (request.form.get("full_name") or "").strip()
    department = (request.form.get("department") or "").strip() or None
    bio = (request.form.get("bio") or "").strip() or None
    year_of_study = request.form.get("year_of_study", type=int)

    if not full_name:
        flash("Full name is required.", "danger")
        return redirect(url_for("auth.profile"))

    response = update_user_profile(
        current_user.id,
        {
            "full_name": full_name,
            "department": department,
            "bio": bio,
            "year_of_study": year_of_study,
        },
    )
    if not response.data:
        flash("Profile update failed.", "danger")
        return redirect(url_for("auth.profile"))

    flash("Profile updated successfully.", "success")
    return redirect(url_for("auth.profile"))
