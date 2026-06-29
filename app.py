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


def create_app(config_object=Config):
    """Create and configure a Flask application instance."""
    # Defects #1 and #7: use a real Flask app so HTTP routes are handled by Flask.
    app = Flask(__name__)
    app.config.from_object(config_object)
    _validate_config(app)
    init_db(app)
    register_blueprints(app)
    with app.app_context():
        db.create_all()
    return app


if __name__ == "__main__":
    # Defect #2: running this module starts the HTTP API.
    create_app().run(host="0.0.0.0", port=5000)
