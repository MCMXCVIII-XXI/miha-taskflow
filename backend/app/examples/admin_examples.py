"""Admin endpoint examples for Swagger documentation."""

from typing import Any, ClassVar


class AdminExamples:
    """Examples for admin endpoints."""

    GET_USERS: ClassVar[dict[str, Any]] = {
        "users": [
            {
                "id": 1,
                "username": "john",
                "email": "john@example.com",
                "role": "USER",
                "is_active": True,
            }
        ],
        "total": 1,
    }

    GET_USERS_PAGINATED: ClassVar[dict[str, Any]] = {
        "users": [],
        "total": 100,
        "limit": 10,
        "offset": 10,
    }

    DELETE_SUCCESS: ClassVar[None] = None

    STATS: ClassVar[dict[str, Any]] = {
        "total_users": 150,
        "active_users": 120,
        "total_tasks": 500,
        "pending_tasks": 50,
        "completed_tasks": 450,
        "total_groups": 20,
        "total_xp_distributed": 50000,
    }

    CREATE_ADMIN_SUCCESS: ClassVar[dict[str, Any]] = {
        "id": 2,
        "username": "new_admin",
        "email": "new_admin@example.com",
        "role": "ADMIN",
    }

    NOT_FOUND: ClassVar[dict[str, Any]] = {"detail": "User not found"}

    ALREADY_EXISTS: ClassVar[dict[str, Any]] = {"detail": "Admin user already exists"}
