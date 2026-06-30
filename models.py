"""SQLAlchemy data models for users and tasks."""

from datetime import datetime

from db import db


VALID_TASK_STATUSES = {"pending", "in_progress", "completed"}
VALID_TASK_PRIORITIES = {"low", "medium", "high"}


class User(db.Model):
    """Registered API user."""

    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    tasks = db.relationship("Task", back_populates="user", cascade="all, delete-orphan")

    def to_dict(self):
        """Return a public representation of the user."""
        return {"id": self.id, "email": self.email, "created_at": self.created_at.isoformat()}


class Task(db.Model):
    """Task owned by a user."""

    __tablename__ = "tasks"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, index=True)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(32), nullable=False, default="pending")
    priority = db.Column(db.String(32), nullable=False, default="medium")
    due_date = db.Column(db.Date, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = db.relationship("User", back_populates="tasks")

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
