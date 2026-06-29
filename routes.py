"""Request routing helpers for authentication, tasks, and analytics."""

from urllib.parse import parse_qs, urlparse

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


def response(body, status_code=200):
    """Create a response tuple used by the local app layer."""
    return body, status_code


def error_response(message, status_code):
    """Create a consistent JSON error response."""
    return response({"error": message}, status_code)


def _query_params(path):
    """Return single-value query parameters from a request path."""
    parsed = urlparse(path)
    return {key: values[-1] for key, values in parse_qs(parsed.query).items()}


def _task_id(path):
    """Extract a task id from a task detail path."""
    try:
        return int(urlparse(path).path.rsplit("/", 1)[1])
    except ValueError as exc:
        raise ValueError("invalid task id") from exc


def _auth_user(headers):
    """Return the authenticated user from request headers."""
    auth_header = (headers or {}).get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        raise PermissionError("missing bearer token")
    return current_user_from_token(auth_header.split(" ", 1)[1].strip())


def route_request(method, path, payload=None, headers=None):
    """Route a test-client request to the correct API handler."""
    payload = payload or {}
    parsed_path = urlparse(path).path

    try:
        if method == "POST" and parsed_path == "/api/auth/register":
            user = register_user(payload.get("email"), payload.get("password"))
            return response({"user": user.to_dict()}, 201)
        if method == "POST" and parsed_path == "/api/auth/login":
            return response({"token": authenticate_user(payload.get("email"), payload.get("password"))})

        user = _auth_user(headers)
        if method == "POST" and parsed_path == "/api/tasks":
            task = create_task(user.id, payload)
            return response({"task": task.to_dict()}, 201)
        if method == "GET" and parsed_path == "/api/tasks":
            tasks = list_tasks(user.id, _query_params(path))
            return response({"tasks": [task.to_dict() for task in tasks]})
        if method == "GET" and parsed_path == "/api/tasks/analytics/completion":
            return response({"analytics": completion_analytics(user.id)})
        if parsed_path.startswith("/api/tasks/"):
            task_id = _task_id(path)
            if method == "GET":
                task = get_task_for_user(user.id, task_id)
                return response({"task": task.to_dict()} if task else {"error": "task not found"}, 200 if task else 404)
            if method == "PUT":
                task = update_task(user.id, task_id, payload)
                return response({"task": task.to_dict()} if task else {"error": "task not found"}, 200 if task else 404)
            if method == "DELETE":
                return response(None, 204) if delete_task(user.id, task_id) else error_response("task not found", 404)
    except PermissionError as exc:
        return error_response(str(exc), 401)
    except ValueError as exc:
        status = 401 if str(exc) in {"invalid token", "expired token", "invalid email or password"} else 400
        return error_response(str(exc), status)

    return error_response("not found", 404)
