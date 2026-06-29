"""Tests for the Task Management API."""

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
