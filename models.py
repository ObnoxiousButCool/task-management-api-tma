"""Data models for users and tasks."""

from dataclasses import dataclass, field
from datetime import date, datetime


VALID_TASK_STATUSES = {"pending", "in_progress", "completed"}
VALID_TASK_PRIORITIES = {"low", "medium", "high"}


@dataclass
class User:
    """Registered API user."""

    id: int
    email: str
    password_hash: str
    created_at: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self):
        """Return a public representation of the user."""
        return {"id": self.id, "email": self.email, "created_at": self.created_at.isoformat()}


@dataclass
class Task:
    """Task owned by a user."""

    id: int
    user_id: int
    title: str
    description: str | None = None
    status: str = "pending"
    priority: str = "medium"
    due_date: date | None = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)

    def validate(self):
        """Validate task status and priority values."""
        if self.status not in VALID_TASK_STATUSES:
            raise ValueError(f"Invalid status: {self.status}")
        if self.priority not in VALID_TASK_PRIORITIES:
            raise ValueError(f"Invalid priority: {self.priority}")

    def to_dict(self):
        """Return a JSON-serializable representation of the task."""
        return {
            "id": self.id,
            "user_id": self.user_id,
            "title": self.title,
            "description": self.description,
            "status": self.status,
            "priority": self.priority,
            "due_date": self.due_date.isoformat() if self.due_date else None,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }
