from flask import Flask
from flask_session import Session
from config import Config
from backend.database.db_manager import DatabaseManager

db = None

def create_app(config_class=Config):
    app = Flask(__name__,
                static_folder="../../frontend/static",
                template_folder="../../frontend/templates")
    app.config.from_object(config_class)

    # Initialize database
    global db
    db = DatabaseManager(app.config['DATABASE_URL'])

    # Register blueprints
    from app.auth.routes import auth_bp
    from app.admin.routes import admin_bp
    from app.api.routes import api_bp
    from app.projects.routes import projects_bp
    from app.search.routes import search_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(api_bp)
    app.register_blueprint(projects_bp)
    app.register_blueprint(search_bp)

    return app