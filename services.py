"""Compatibility exports for authentication and task services."""

# Defect: services.py file-size violation fixed by splitting implementation modules.
from auth_services import (
    authenticate_user,
    check_password,
    create_token,
    current_user_from_token,
    decode_token,
    hash_password,
    register_user,
)
from task_services import (
    completion_analytics,
    create_task,
    delete_task,
    get_task_for_user,
    list_tasks,
    parse_date,
    update_task,
)

__all__ = [
    "authenticate_user",
    "check_password",
    "completion_analytics",
    "create_task",
    "create_token",
    "current_user_from_token",
    "decode_token",
    "delete_task",
    "get_task_for_user",
    "hash_password",
    "list_tasks",
    "parse_date",
    "register_user",
    "update_task",
]
