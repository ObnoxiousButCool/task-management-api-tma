"""Database extension setup for the Task Management API."""

from flask_sqlalchemy import SQLAlchemy


db = SQLAlchemy()


def init_db(app):
    """Initialize SQLAlchemy for the Flask application."""
    # Defect #5: initialize the real Flask-SQLAlchemy extension instead of in-memory stores.
    db.init_app(app)


def reset_db(app):
    """Drop and recreate all database tables for tests and local maintenance."""
    with app.app_context():
        db.drop_all()
        db.create_all()
