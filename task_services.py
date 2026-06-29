"""Task services for the Task Management API."""

from datetime import date, datetime

from db import db
from models import Task, VALID_TASK_PRIORITIES, VALID_TASK_STATUSES


def parse_date(value, field_name="date"):
    """Parse an ISO date string into a date object."""
    if value in (None, ""):
        return None
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"{field_name} must be in YYYY-MM-DD format") from exc


def create_task(user_id, payload):
    """Create a task for a user."""
    title = (payload.get("title") or "").strip()
    if not title:
        raise ValueError("title is required")
    task = Task(
        user_id=user_id,
        title=title,
        description=payload.get("description"),
        status=payload.get("status", "pending"),
        priority=payload.get("priority", "medium"),
        due_date=parse_date(payload.get("due_date"), "due_date"),
    )
    task.validate()
    # Defect #14: persist tasks through SQLAlchemy and commit the transaction.
    db.session.add(task)
    db.session.commit()
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

    query = Task.query.filter_by(user_id=user_id)
    if status:
        query = query.filter_by(status=status)
    if priority:
        query = query.filter_by(priority=priority)
    if due_from:
        query = query.filter(Task.due_date >= due_from)
    if due_to:
        query = query.filter(Task.due_date <= due_to)
    return query.order_by(Task.created_at.desc()).all()


def get_task_for_user(user_id, task_id):
    """Return a single task belonging to a user, or None."""
    return Task.query.filter_by(id=task_id, user_id=user_id).first()


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
    db.session.commit()
    return task


def delete_task(user_id, task_id):
    """Delete a task owned by a user and return whether it existed."""
    task = get_task_for_user(user_id, task_id)
    if not task:
        return False
    db.session.delete(task)
    db.session.commit()
    return True


def completion_analytics(user_id):
    """Return task completion counts and rates overall and by priority."""
    tasks = Task.query.filter_by(user_id=user_id).all()
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
