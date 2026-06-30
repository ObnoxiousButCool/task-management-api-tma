"""Authentication services for the Task Management API."""

from datetime import datetime, timedelta
import base64
import binascii
import hashlib
import hmac
import json

import bcrypt
from flask import current_app
from sqlalchemy.exc import IntegrityError

from db import db
from models import User


def hash_password(password):
    """Hash a password with bcrypt."""
    # Defect #10: use bcrypt instead of a custom salted SHA-256 format.
    rounds = current_app.config["BCRYPT_ROUNDS"]
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt(rounds=rounds)).decode("utf-8")


def check_password(password, password_hash):
    """Return whether a plain password matches the stored bcrypt hash."""
    # Defect #11: verify passwords with bcrypt's constant-time checker.
    return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))


def _b64encode(payload):
    """Encode JSON-compatible data as URL-safe base64."""
    raw = json.dumps(payload, separators=(",", ":")).encode("utf-8")
    return base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=")


def _b64decode(value):
    """Decode URL-safe base64 JSON data."""
    padded = value + "=" * (-len(value) % 4)
    return json.loads(base64.urlsafe_b64decode(padded.encode("ascii")).decode("utf-8"))


def _jwt_secret():
    """Return the active Flask application's JWT secret."""
    # Defect #12: token signing reads active app configuration, not the Config class.
    return current_app.config["JWT_SECRET_KEY"].encode("utf-8")


def create_token(user):
    """Create a signed token for a user."""
    payload = {
        "sub": str(user.id),
        "email": user.email,
        "exp": (datetime.utcnow() + timedelta(hours=24)).timestamp(),
    }
    body = _b64encode(payload)
    signature = hmac.new(_jwt_secret(), body.encode("ascii"), hashlib.sha256)
    return f"{body}.{signature.hexdigest()}"


def decode_token(token):
    """Decode and validate a signed token."""
    try:
        body, signature = token.split(".", 1)
    except ValueError as exc:
        raise ValueError("invalid token") from exc
    expected = hmac.new(_jwt_secret(), body.encode("ascii"), hashlib.sha256)
    if not hmac.compare_digest(signature, expected.hexdigest()):
        raise ValueError("invalid token")
    try:
        # Defect #13: normalize malformed base64 and non-JSON payload errors.
        payload = _b64decode(body)
    except (ValueError, json.JSONDecodeError, binascii.Error, UnicodeDecodeError) as exc:
        raise ValueError("invalid token") from exc
    # Defect #1: reject non-object JSON payloads before accessing claims.
    if not isinstance(payload, dict):
        raise ValueError("invalid token")
    if payload.get("exp", 0) < datetime.utcnow().timestamp():
        raise ValueError("expired token")
    return payload


def register_user(email, password):
    """Register a new user and return the user record."""
    normalized_email = (email or "").strip().lower()
    if not normalized_email or not password:
        raise ValueError("email and password are required")
    if User.query.filter_by(email=normalized_email).first():
        raise ValueError("email is already registered")

    user = User(email=normalized_email, password_hash=hash_password(password))
    db.session.add(user)
    try:
        db.session.commit()
    except IntegrityError as exc:
        # Defect #2: handle duplicate-email races from the database constraint.
        db.session.rollback()
        raise ValueError("email is already registered") from exc
    return user


def authenticate_user(email, password):
    """Authenticate a user and return a token."""
    normalized_email = (email or "").strip().lower()
    user = User.query.filter_by(email=normalized_email).first()
    if not user or not password or not check_password(password, user.password_hash):
        raise ValueError("invalid email or password")
    return create_token(user)


def current_user_from_token(token):
    """Return the user represented by a token."""
    payload = decode_token(token)
    try:
        # Defect #3: normalize invalid token subjects instead of leaking int() errors.
        user_id = int(payload.get("sub", 0))
    except (TypeError, ValueError) as exc:
        raise ValueError("invalid token") from exc
    user = User.query.get(user_id)
    if not user:
        raise ValueError("invalid token")
    return user
