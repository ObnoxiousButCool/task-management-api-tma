"""In-memory persistence used by the local CI-safe API implementation."""


class Database:
    """Small repository abstraction for users and tasks."""

    def __init__(self):
        """Initialize empty storage."""
        self.create_all()

    def init_app(self, app):
        """Match the Flask-SQLAlchemy extension hook used by the app factory."""
        return None

    def create_all(self):
        """Create empty stores and reset primary-key counters."""
        self.users = {}
        self.users_by_email = {}
        self.tasks = {}
        self.next_user_id = 1
        self.next_task_id = 1

    def drop_all(self):
        """Drop all stored records."""
        self.create_all()

    def session_commit(self):
        """Compatibility no-op for persistence commits."""
        return None


db = Database()


def init_db(app):
    """Initialize application persistence."""
    db.init_app(app)


def reset_db(app):
    """Reset application persistence."""
    db.drop_all()
