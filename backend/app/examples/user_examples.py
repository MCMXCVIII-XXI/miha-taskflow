"""User endpoint examples for Swagger documentation."""

from typing import Any, ClassVar


class UserExamples:
    """Examples for user endpoints."""

    GET_ME: ClassVar[dict[str, Any]] = {
        "id": 1,
        "username": "john_doe",
        "email": "john@example.com",
        "first_name": "John",
        "last_name": "Doe",
        "role": "USER",
        "xp": 1500,
        "level": 3,
        "created_at": "2024-01-15T10:30:00Z",
        "updated_at": "2024-01-20T14:45:00Z",
    }

    GET_BY_ID: ClassVar[dict[str, Any]] = {
        "id": 1,
        "username": "john_doe",
        "email": "john@example.com",
        "first_name": "John",
        "last_name": "Doe",
        "role": "USER",
        "xp": 1500,
        "level": 3,
    }

    UPDATE_SUCCESS: ClassVar[dict[str, Any]] = {
        "id": 1,
        "username": "john_doe",
        "email": "john_updated@example.com",
        "first_name": "John",
        "last_name": "Smith",
        "role": "USER",
        "xp": 1500,
        "level": 3,
        "created_at": "2024-01-15T10:30:00Z",
        "updated_at": "2024-01-20T14:45:00Z",
    }

    UPDATE_REQUEST: ClassVar[dict[str, Any]] = {
        "first_name": "John",
        "last_name": "Smith",
        "email": "john_new@example.com",
    }

    NOT_FOUND: ClassVar[dict[str, Any]] = {"detail": "User not found"}

    FORBIDDEN: ClassVar[dict[str, Any]] = {
        "detail": "Permission denied: You can only update your own profile"
    }

    UNAUTHORIZED: ClassVar[dict[str, Any]] = {"detail": "Not authenticated"}

    VALIDATION_ERROR: ClassVar[dict[str, Any]] = {"detail": "Invalid email format"}

    GROUP_ADMIN: ClassVar[dict[str, Any]] = {
        "id": 2,
        "username": "admin_user",
        "email": "admin@group.com",
        "first_name": "Admin",
        "last_name": "User",
        "role": "USER",
        "xp": 5000,
        "level": 10,
        "created_at": "2024-01-01T00:00:00Z",
        "updated_at": "2024-01-15T00:00:00Z",
    }

    TASK_OWNER: ClassVar[dict[str, Any]] = {
        "id": 3,
        "username": "owner_user",
        "email": "owner@task.com",
        "first_name": "Task",
        "last_name": "Owner",
        "role": "USER",
        "xp": 3000,
        "level": 5,
        "created_at": "2024-01-05T00:00:00Z",
        "updated_at": "2024-01-10T00:00:00Z",
    }

    DELETE_SUCCESS: ClassVar[None] = None


class UserSearchExamples:
    """Examples for user search endpoints."""

    SEARCH_SUCCESS: ClassVar[dict[str, Any]] = {
        "users": [
            {
                "id": 1,
                "username": "john_doe",
                "email": "john@example.com",
                "first_name": "John",
                "last_name": "Doe",
                "role": "USER",
                "xp": 1500,
                "level": 3,
            },
            {
                "id": 2,
                "username": "jane_doe",
                "email": "jane@example.com",
                "first_name": "Jane",
                "last_name": "Doe",
                "role": "USER",
                "xp": 2000,
                "level": 4,
            },
        ],
        "total": 2,
        "limit": 10,
        "offset": 0,
    }

    SEARCH_EMPTY: ClassVar[dict[str, Any]] = {
        "users": [],
        "total": 0,
        "limit": 10,
        "offset": 0,
    }


class UserGroupExamples:
    """Examples for user group endpoints."""

    USER_GROUPS: ClassVar[dict[str, Any]] = {
        "groups": [
            {
                "id": 1,
                "name": "Backend Team",
                "description": "Team for backend development",
                "visibility": "PUBLIC",
                "join_policy": "OPEN",
                "role": "OWNER",
                "created_at": "2024-01-01T00:00:00Z",
            },
        ],
        "total": 1,
    }

    USER_TASKS: ClassVar[dict[str, Any]] = {
        "tasks": [
            {
                "id": 1,
                "title": "Implement API",
                "description": "Create new API endpoint",
                "status": "IN_PROGRESS",
                "priority": "HIGH",
            },
        ],
        "total": 1,
    }
