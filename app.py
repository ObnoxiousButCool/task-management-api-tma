"""Application entry point for the Task Management API."""

from flask import Flask

from config import Config
from db import db, init_db
from routes import register_blueprints


def _validate_config(app):
    """Validate runtime configuration before serving requests."""
    # Defect #4: non-test startup must fail when JWT_SECRET_KEY is not supplied.
    if not app.config.get("TESTING") and not app.config.get("JWT_SECRET_KEY"):
        raise RuntimeError("JWT_SECRET_KEY environment variable is required")


def _register_cli_commands(app):
    """Register explicit local setup commands for the Flask application."""

    @app.cli.command("init-db")
    def init_db_command():
        """Create database tables for local or test initialization."""
        # Defect #4: schema creation is explicit and never runs during app startup.
        db.create_all()
        print("Initialized database tables.")


def create_app(config_object=Config):
    """Create and configure a Flask application instance."""
    # Defects #1 and #7: use a real Flask app so HTTP routes are handled by Flask.
    app = Flask(__name__)
    app.config.from_object(config_object)
    _validate_config(app)
    init_db(app)
    register_blueprints(app)
    _register_cli_commands(app)
    # Defect #4: schema creation is explicit; startup must not mutate databases.
    return app


if __name__ == "__main__":
    # Defect #2: running this module starts the HTTP API.
    create_app().run(host="0.0.0.0", port=5000)
