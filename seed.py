"""Seed the Task Management API database with a default user."""

import os

from app import create_app
from config import Config
from db import db
from services import register_user


def seed_default_user():
    """Create the default user if it does not already exist."""
    app = create_app(Config)
    with app.app_context():
        try:
            # Defect #9: require the local seed password from the environment.
            password = os.environ["TMA_SEED_ADMIN_PASSWORD"]
            # Defect #9: create and commit the seed user in the SQLAlchemy database.
            user = register_user("admin@example.com", password)
            db.session.commit()
            return user
        except ValueError:
            db.session.rollback()
            return None


if __name__ == "__main__":
    user = seed_default_user()
    if user:
        print(f"Seeded default user: {user.email}")
    else:
        print("Default user already exists")
