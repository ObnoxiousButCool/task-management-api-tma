"""Tests for the Task Management API."""

from datetime import datetime, timedelta
import base64
import hashlib
import hmac
import json

import pytest

from app import create_app
from config import TestConfig
from db import db


def make_client():
    """Create a Flask test client with a clean in-memory database."""
    app = create_app(TestConfig)
    # Defect #15: reset the real Flask-SQLAlchemy database under an app context.
    with app.app_context():
        db.drop_all()
        db.create_all()
    return app.test_client()


def auth_header(client, email="user@example.com"):
    """Register and log in a test user, returning an Authorization header."""
    client.post("/api/auth/register", json={"email": email, "password": "secret"})
    response = client.post("/api/auth/login", json={"email": email, "password": "secret"})
    token = response.get_json()["token"]
    return {"Authorization": f"Bearer {token}"}


def signed_token(payload):
    """Return a signed test token for arbitrary JSON-compatible payload data."""
    raw = json.dumps(payload, separators=(",", ":")).encode("utf-8")
    body = base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=")
    signature = hmac.new(TestConfig.JWT_SECRET_KEY.encode("utf-8"), body.encode("ascii"), hashlib.sha256)
    return f"{body}.{signature.hexdigest()}"


def test_register_login_and_create_task():
    """Users can register, log in, and create a task."""
    client = make_client()
    headers = auth_header(client)

    response = client.post(
        "/api/tasks",
        json={"title": "Write tests", "priority": "high", "due_date": "2026-07-01"},
        headers=headers,
    )

    assert response.status_code == 201
    body = response.get_json()
    assert body["task"]["title"] == "Write tests"
    assert body["task"]["priority"] == "high"


def test_task_filtering_and_ownership():
    """Task listing applies filters and keeps users isolated."""
    client = make_client()
    first_headers = auth_header(client, "first@example.com")
    second_headers = auth_header(client, "second@example.com")
    client.post("/api/tasks", json={"title": "A", "priority": "high"}, headers=first_headers)
    client.post("/api/tasks", json={"title": "B", "priority": "low"}, headers=first_headers)
    client.post("/api/tasks", json={"title": "C", "priority": "high"}, headers=second_headers)

    response = client.get("/api/tasks?priority=high", headers=first_headers)

    assert response.status_code == 200
    tasks = response.get_json()["tasks"]
    assert len(tasks) == 1
    assert tasks[0]["title"] == "A"


def test_update_delete_and_analytics():
    """Tasks can be updated, deleted, and counted in completion analytics."""
    client = make_client()
    headers = auth_header(client)
    created = client.post("/api/tasks", json={"title": "Done", "priority": "medium"}, headers=headers)
    task_id = created.get_json()["task"]["id"]

    update = client.put(f"/api/tasks/{task_id}", json={"status": "completed"}, headers=headers)
    analytics = client.get("/api/tasks/analytics/completion", headers=headers)
    delete = client.delete(f"/api/tasks/{task_id}", headers=headers)

    assert update.status_code == 200
    assert analytics.status_code == 200
    assert analytics.get_json()["analytics"]["completion_rate"] == 1
    assert delete.status_code == 204


# Defect #7: negative API coverage for auth, validation, ownership, and unauthenticated flows.
def test_duplicate_registration_returns_validation_error():
    """Duplicate email registration returns a controlled client error."""
    client = make_client()

    first = client.post("/api/auth/register", json={"email": "dupe@example.com", "password": "secret"})
    second = client.post("/api/auth/register", json={"email": "DUPE@example.com", "password": "secret"})

    assert first.status_code == 201
    assert second.status_code == 400
    assert second.get_json()["error"] == "email is already registered"


@pytest.mark.parametrize(
    "token",
    [
        "not-a-token",
        signed_token(["not", "a", "dict"]),
        signed_token({"sub": "not-an-int", "exp": (datetime.utcnow() + timedelta(hours=1)).timestamp()}),
        signed_token({"sub": "1", "exp": (datetime.utcnow() - timedelta(seconds=1)).timestamp()}),
    ],
)
def test_invalid_and_expired_tokens_are_rejected(token):
    """Malformed, non-object, invalid-subject, and expired tokens are rejected."""
    client = make_client()

    response = client.get("/api/tasks", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 401
    assert response.get_json()["error"] in {"invalid token", "expired token"}


@pytest.mark.parametrize(
    ("payload", "expected_error"),
    [
        ({}, "title is required"),
        ({"title": "Bad status", "status": "blocked"}, "Invalid status: blocked"),
        ({"title": "Bad priority", "priority": "urgent"}, "Invalid priority: urgent"),
        ({"title": "Bad date", "due_date": "07/01/2026"}, "due_date must be in YYYY-MM-DD format"),
    ],
)
def test_task_create_validation_errors(payload, expected_error):
    """Task creation reports validation errors for invalid input."""
    client = make_client()
    headers = auth_header(client)

    response = client.post("/api/tasks", json=payload, headers=headers)

    assert response.status_code == 400
    assert response.get_json()["error"] == expected_error


@pytest.mark.parametrize(
    ("method", "path"),
    [
        ("get", "/api/tasks"),
        ("post", "/api/tasks"),
        ("get", "/api/tasks/1"),
        ("put", "/api/tasks/1"),
        ("delete", "/api/tasks/1"),
    ],
)
def test_task_routes_require_authentication(method, path):
    """Task CRUD endpoints reject unauthenticated requests."""
    client = make_client()

    response = getattr(client, method)(path, json={"title": "No auth"} if method in {"post", "put"} else None)

    assert response.status_code == 401
    assert response.get_json()["error"] == "missing bearer token"


@pytest.mark.parametrize("method", ["get", "put", "delete"])
def test_task_ownership_checks_return_404(method):
    """Task CRUD routes hide tasks owned by another user."""
    client = make_client()
    owner_headers = auth_header(client, "owner@example.com")
    other_headers = auth_header(client, "other@example.com")
    created = client.post("/api/tasks", json={"title": "Private"}, headers=owner_headers)
    task_id = created.get_json()["task"]["id"]

    if method == "put":
        response = client.put(f"/api/tasks/{task_id}", json={"title": "Changed"}, headers=other_headers)
    else:
        response = getattr(client, method)(f"/api/tasks/{task_id}", headers=other_headers)

    assert response.status_code == 404
    assert response.get_json()["error"] == "task not found"
