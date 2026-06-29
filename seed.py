"""Seed the Task Management API database with a default user."""

from app import create_app
from config import Config
from services import register_user


def seed_default_user():
    """Create the default user if it does not already exist."""
    create_app(Config)
    try:
        return register_user("admin@example.com", "admin123")
    except ValueError:
        return None


if __name__ == "__main__":
    user = seed_default_user()
    if user:
        print(f"Seeded default user: {user.email}")
    else:
        print("Default user already exists")
