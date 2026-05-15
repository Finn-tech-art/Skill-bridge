from flask import Flask, session
from flask_login import LoginManager, UserMixin
from dotenv import load_dotenv
import os
from werkzeug.middleware.proxy_fix import ProxyFix

from .supabase_client import create_supabase_client, supabase

load_dotenv()

login_manager = LoginManager()


# ============================================================
# USER LOADER (CRITICAL FOR FLASK-LOGIN)
# ============================================================
@login_manager.user_loader
def load_user(user_id):
    response = supabase.table("users").select("*").eq("id", user_id).execute()
    data = response.data

    if not data:
        return None

    user = data[0]

    return _build_auth_user(user)


def _build_auth_user(user):
    class AuthUser(UserMixin):
        def __init__(self, user):
            self.id = str(user["id"])
            self.full_name = user.get("full_name")
            self.username = user.get("username")
            self.email = user.get("email")
            self.auth_user_id = user.get("auth_user_id")

    return AuthUser(user)


def create_app():
    app = Flask(__name__)
    app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

    # =========================
    # CONFIGURATION
    # =========================
    environment = os.getenv("FLASK_ENV", "production").lower()
    secret_key = os.getenv("SECRET_KEY")

    if environment == "production" and not secret_key:
        raise RuntimeError("SECRET_KEY must be set in production.")

    app.config["SECRET_KEY"] = secret_key or "dev-secret-key"
    app.config["SESSION_COOKIE_HTTPONLY"] = True
    app.config["REMEMBER_COOKIE_HTTPONLY"] = True
    app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
    app.config["REMEMBER_COOKIE_SAMESITE"] = "Lax"
    app.config["SESSION_COOKIE_SECURE"] = environment == "production"
    app.config["REMEMBER_COOKIE_SECURE"] = environment == "production"

    # =========================
    # INIT EXTENSIONS
    # =========================
    login_manager.init_app(app)
    login_manager.login_view = "auth.login"

    # =========================
    # REGISTER BLUEPRINTS
    # =========================
    from .auth import auth_bp
    from .skills import skills_bp
    from .exchange import exchange_bp
    from .feedback import feedback_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(skills_bp)
    app.register_blueprint(exchange_bp)
    app.register_blueprint(feedback_bp)

    # Optional test route
    from .test import test_bp
    app.register_blueprint(test_bp)

    @app.get("/healthz")
    def healthcheck():
        return {"status": "ok"}, 200

    @app.before_request
    def restore_supabase_session():
        from flask_login import current_user, login_user, logout_user

        access_token = session.get("sb_access_token")
        refresh_token = session.get("sb_refresh_token")

        if not access_token or not refresh_token:
            return

        auth_client = create_supabase_client()
        try:
            session_response = auth_client.auth.set_session(access_token, refresh_token)
            current_session = session_response.session or auth_client.auth.get_session()
            verified_response = auth_client.auth.get_user()
            verified_user = verified_response.user if verified_response else None
            if not verified_user:
                raise ValueError("Supabase user could not be verified.")

            session["sb_access_token"] = current_session.access_token
            session["sb_refresh_token"] = current_session.refresh_token
            session["sb_auth_user_id"] = verified_user.id

            response = supabase.table("users").select("*").eq("auth_user_id", verified_user.id).limit(1).execute()
            data = response.data or []
            if not data:
                logout_user()
                session.pop("sb_access_token", None)
                session.pop("sb_refresh_token", None)
                session.pop("sb_auth_user_id", None)
                return

            profile_user = data[0]
            if not current_user.is_authenticated or str(current_user.id) != str(profile_user["id"]):
                login_user(_build_auth_user(profile_user))
        except Exception:
            logout_user()
            session.pop("sb_access_token", None)
            session.pop("sb_refresh_token", None)
            session.pop("sb_auth_user_id", None)

    return app
