from flask import Flask
from config import settings


def create_app() -> Flask:
    """Application factory."""
    app = Flask(__name__, template_folder="../templates", static_folder="../static")
    app.secret_key = settings.flask_secret_key
    
    # Validate configuration
    missing = settings.validate()
    if missing:
        print(f"Warning: Missing environment variables: {', '.join(missing)}")
    
    # Register blueprints
    from app.routes.chat import chat_bp
    app.register_blueprint(chat_bp)
    
    return app
