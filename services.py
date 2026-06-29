"""Business logic for authentication and task management."""

from datetime import date, datetime, timedelta
import base64
import hashlib
import hmac
import json

from config import Config
from db import db
from models import Task, User, VALID_TASK_PRIORITIES, VALID_TASK_STATUSES


def parse_date(value, field_name="date"):
    """Parse an ISO date string into a date object."""
    if value in (None, ""):
        return None
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"{field_name} must be in YYYY-MM-DD format") from exc


def hash_password(password):
    """Hash a password with a salted SHA-256 digest for offline CI execution."""
    salt = hashlib.sha256(f"{datetime.utcnow().timestamp()}".encode("utf-8")).hexdigest()[:16]
    digest = hashlib.sha256(f"{salt}:{password}".encode("utf-8")).hexdigest()
    return f"{salt}${digest}"


def check_password(password, password_hash):
    """Return whether a plain password matches the stored password hash."""
    salt, digest = password_hash.split("$", 1)
    candidate = hashlib.sha256(f"{salt}:{password}".encode("utf-8")).hexdigest()
    return hmac.compare_digest(candidate, digest)


def _b64encode(payload):
    """Encode JSON-compatible data as URL-safe base64."""
    raw = json.dumps(payload, separators=(",", ":")).encode("utf-8")
    return base64.urlsafe_b64encode(raw).decode("ascii").rstrip("=")


def _b64decode(value):
    """Decode URL-safe base64 JSON data."""
    padded = value + "=" * (-len(value) % 4)
    return json.loads(base64.urlsafe_b64decode(padded.encode("ascii")).decode("utf-8"))


def create_token(user):
    """Create a signed token for a user."""
    payload = {
        "sub": str(user.id),
        "email": user.email,
        "exp": (datetime.utcnow() + timedelta(hours=24)).timestamp(),
    }
    body = _b64encode(payload)
    signature = hmac.new(Config.JWT_SECRET_KEY.encode("utf-8"), body.encode("ascii"), hashlib.sha256)
    return f"{body}.{signature.hexdigest()}"


def decode_token(token):
    """Decode and validate a signed token."""
    try:
        body, signature = token.split(".", 1)
    except ValueError as exc:
        raise ValueError("invalid token") from exc
    expected = hmac.new(Config.JWT_SECRET_KEY.encode("utf-8"), body.encode("ascii"), hashlib.sha256)
    if not hmac.compare_digest(signature, expected.hexdigest()):
        raise ValueError("invalid token")
    payload = _b64decode(body)
    if payload.get("exp", 0) < datetime.utcnow().timestamp():
        raise ValueError("expired token")
    return payload


def register_user(email, password):
    """Register a new user and return the user record."""
    normalized_email = (email or "").strip().lower()
    if not normalized_email or not password:
        raise ValueError("email and password are required")
    if normalized_email in db.users_by_email:
        raise ValueError("email is already registered")

    user = User(id=db.next_user_id, email=normalized_email, password_hash=hash_password(password))
    db.users[user.id] = user
    db.users_by_email[user.email] = user.id
    db.next_user_id += 1
    return user


def authenticate_user(email, password):
    """Authenticate a user and return a token."""
    normalized_email = (email or "").strip().lower()
    user_id = db.users_by_email.get(normalized_email)
    user = db.users.get(user_id)
    if not user or not password or not check_password(password, user.password_hash):
        raise ValueError("invalid email or password")
    return create_token(user)


def current_user_from_token(token):
    """Return the user represented by a token."""
    payload = decode_token(token)
    user = db.users.get(int(payload.get("sub", 0)))
    if not user:
        raise ValueError("invalid token")
    return user


def create_task(user_id, payload):
    """Create a task for a user."""
    title = (payload.get("title") or "").strip()
    if not title:
        raise ValueError("title is required")
    task = Task(
        id=db.next_task_id,
        user_id=user_id,
        title=title,
        description=payload.get("description"),
        status=payload.get("status", "pending"),
        priority=payload.get("priority", "medium"),
        due_date=parse_date(payload.get("due_date"), "due_date"),
    )
    task.validate()
    db.tasks[task.id] = task
    db.next_task_id += 1
    return task


def list_tasks(user_id, filters):
    """List tasks for a user, optionally filtered by status, priority, and due dates."""
    status = filters.get("status")
    priority = filters.get("priority")
    due_from = parse_date(filters.get("due_from"), "due_from")
    due_to = parse_date(filters.get("due_to"), "due_to")
    if status and status not in VALID_TASK_STATUSES:
        raise ValueError(f"Invalid status: {status}")
    if priority and priority not in VALID_TASK_PRIORITIES:
        raise ValueError(f"Invalid priority: {priority}")

    tasks = [task for task in db.tasks.values() if task.user_id == user_id]
    if status:
        tasks = [task for task in tasks if task.status == status]
    if priority:
        tasks = [task for task in tasks if task.priority == priority]
    if due_from:
        tasks = [task for task in tasks if task.due_date and task.due_date >= due_from]
    if due_to:
        tasks = [task for task in tasks if task.due_date and task.due_date <= due_to]
    return sorted(tasks, key=lambda task: task.created_at, reverse=True)


def get_task_for_user(user_id, task_id):
    """Return a single task belonging to a user, or None."""
    task = db.tasks.get(task_id)
    if not task or task.user_id != user_id:
        return None
    return task


def update_task(user_id, task_id, payload):
    """Update an existing task owned by a user."""
    task = get_task_for_user(user_id, task_id)
    if not task:
        return None
    for field in ("title", "description", "status", "priority"):
        if field in payload:
            value = payload[field]
            if field == "title":
                value = (value or "").strip()
                if not value:
                    raise ValueError("title cannot be empty")
            setattr(task, field, value)
    if "due_date" in payload:
        task.due_date = parse_date(payload.get("due_date"), "due_date")
    task.validate()
    task.updated_at = datetime.utcnow()
    return task


def delete_task(user_id, task_id):
    """Delete a task owned by a user and return whether it existed."""
    task = get_task_for_user(user_id, task_id)
    if not task:
        return False
    del db.tasks[task.id]
    return True


def completion_analytics(user_id):
    """Return task completion counts and rates overall and by priority."""
    tasks = [task for task in db.tasks.values() if task.user_id == user_id]
    by_priority = {}
    for priority in sorted(VALID_TASK_PRIORITIES):
        priority_tasks = [task for task in tasks if task.priority == priority]
        if not priority_tasks:
            continue
        completed = len([task for task in priority_tasks if task.status == "completed"])
        total = len(priority_tasks)
        by_priority[priority] = {
            "total": total,
            "completed": completed,
            "completion_rate": completed / total if total else 0,
        }
    completed_total = len([task for task in tasks if task.status == "completed"])
    total = len(tasks)
    return {
        "total": total,
        "completed": completed_total,
        "completion_rate": completed_total / total if total else 0,
        "by_priority": by_priority,
    }
