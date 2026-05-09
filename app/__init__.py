"""
SkillBridge Flask Application Factory
"""
from flask import Flask
from flask_session import Session
from config import config

def create_app():
    """Create and configure the Flask application."""
    app = Flask(__name__)
    app.config.from_object(config)
    
    # Initialize Flask-Session
    Session(app)
    
    # Register blueprints
    from app.auth import auth_bp
    from app.skills import skills_bp
    from app.exchange import exchange_bp
    from app.feedback import feedback_bp
    
    app.register_blueprint(auth_bp)
    app.register_blueprint(skills_bp)
    app.register_blueprint(exchange_bp)
    app.register_blueprint(feedback_bp)
    
    # Register main routes
    @app.route('/')
    def index():
        return 'SkillBridge API'
    
    return app
