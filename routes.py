"""Flask blueprints for authentication, tasks, and analytics."""

from flask import Blueprint, jsonify, request

from services import (
    authenticate_user,
    completion_analytics,
    create_task,
    current_user_from_token,
    delete_task,
    get_task_for_user,
    list_tasks,
    register_user,
    update_task,
)


auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")
tasks_bp = Blueprint("tasks", __name__, url_prefix="/api/tasks")


def error_response(message, status_code):
    """Create a consistent JSON error response."""
    return jsonify({"error": message}), status_code


def _auth_user():
    """Return the authenticated user from the Authorization header."""
    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        raise PermissionError("missing bearer token")
    return current_user_from_token(auth_header.split(" ", 1)[1].strip())


def _handle_error(exc):
    """Translate service exceptions to HTTP responses."""
    status = 401 if str(exc) in {"invalid token", "expired token", "invalid email or password"} else 400
    return error_response(str(exc), status)


@auth_bp.post("/register")
def register():
    """Register a user account."""
    payload = request.get_json(silent=True) or {}
    try:
        user = register_user(payload.get("email"), payload.get("password"))
        return jsonify({"user": user.to_dict()}), 201
    except ValueError as exc:
        return _handle_error(exc)


@auth_bp.post("/login")
def login():
    """Authenticate a user and return a bearer token."""
    payload = request.get_json(silent=True) or {}
    try:
        return jsonify({"token": authenticate_user(payload.get("email"), payload.get("password"))})
    except ValueError as exc:
        return _handle_error(exc)


@tasks_bp.post("")
def create_task_route():
    """Create a task for the authenticated user."""
    try:
        user = _auth_user()
        task = create_task(user.id, request.get_json(silent=True) or {})
        return jsonify({"task": task.to_dict()}), 201
    except PermissionError as exc:
        return error_response(str(exc), 401)
    except ValueError as exc:
        return _handle_error(exc)


@tasks_bp.get("")
def list_tasks_route():
    """List tasks for the authenticated user."""
    try:
        user = _auth_user()
        tasks = list_tasks(user.id, request.args.to_dict())
        return jsonify({"tasks": [task.to_dict() for task in tasks]})
    except PermissionError as exc:
        return error_response(str(exc), 401)
    except ValueError as exc:
        return _handle_error(exc)


@tasks_bp.get("/analytics/completion")
def completion_analytics_route():
    """Return task completion analytics for the authenticated user."""
    try:
        user = _auth_user()
        return jsonify({"analytics": completion_analytics(user.id)})
    except PermissionError as exc:
        return error_response(str(exc), 401)
    except ValueError as exc:
        return _handle_error(exc)


@tasks_bp.get("/<int:task_id>")
def get_task_route(task_id):
    """Return a single task belonging to the authenticated user."""
    try:
        user = _auth_user()
        task = get_task_for_user(user.id, task_id)
        if not task:
            return error_response("task not found", 404)
        return jsonify({"task": task.to_dict()})
    except PermissionError as exc:
        return error_response(str(exc), 401)
    except ValueError as exc:
        return _handle_error(exc)


@tasks_bp.put("/<int:task_id>")
def update_task_route(task_id):
    """Update a task belonging to the authenticated user."""
    try:
        user = _auth_user()
        task = update_task(user.id, task_id, request.get_json(silent=True) or {})
        if not task:
            return error_response("task not found", 404)
        return jsonify({"task": task.to_dict()})
    except PermissionError as exc:
        return error_response(str(exc), 401)
    except ValueError as exc:
        return _handle_error(exc)


@tasks_bp.delete("/<int:task_id>")
def delete_task_route(task_id):
    """Delete a task belonging to the authenticated user."""
    try:
        user = _auth_user()
        if not delete_task(user.id, task_id):
            return error_response("task not found", 404)
        return "", 204
    except PermissionError as exc:
        return error_response(str(exc), 401)
    except ValueError as exc:
        return _handle_error(exc)


def register_blueprints(app):
    """Register all API blueprints on the Flask application."""
    # Defect #8: use Flask blueprints instead of a custom router.
    app.register_blueprint(auth_bp)
    app.register_blueprint(tasks_bp)
