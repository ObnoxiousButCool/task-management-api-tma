"""Application configuration for the Task Management API."""

import os


class Config:
    """Base configuration loaded from environment variables."""

    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL",
        "sqlite:///tma.db",
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
    JWT_ALGORITHM = "HS256"
    BCRYPT_ROUNDS = int(os.getenv("BCRYPT_ROUNDS", "12"))


class TestConfig(Config):
    """Configuration used by the unit test suite."""

    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    JWT_SECRET_KEY = "test-secret"
    BCRYPT_ROUNDS = 4
