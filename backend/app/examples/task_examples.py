"""Task endpoint examples for Swagger documentation."""

from typing import Any, ClassVar


class TaskExamples:
    """Examples for task endpoints."""

    CREATE_SUCCESS: ClassVar[dict[str, Any]] = {
        "id": 1,
        "title": "Implement user authentication",
        "description": "Create JWT authentication system",
        "status": "PENDING",
        "priority": "HIGH",
        "difficulty": "MEDIUM",
        "visibility": "PRIVATE",
        "group_id": 1,
        "created_by": 1,
        "created_at": "2024-01-15T10:30:00Z",
        "updated_at": "2024-01-15T10:30:00Z",
    }

    GET_ALL: ClassVar[dict[str, Any]] = {
        "tasks": [
            {
                "id": 1,
                "title": "Implement user authentication",
                "status": "PENDING",
                "priority": "HIGH",
                "group_id": 1,
            }
        ],
        "total": 1,
    }

    GET_BY_ID: ClassVar[dict[str, Any]] = {
        "id": 1,
        "title": "Implement user authentication",
        "description": "Create JWT authentication system",
        "status": "IN_PROGRESS",
        "priority": "HIGH",
        "difficulty": "MEDIUM",
        "visibility": "PRIVATE",
        "group_id": 1,
        "created_by": 1,
        "created_at": "2024-01-15T10:30:00Z",
        "updated_at": "2024-01-15T10:30:00Z",
    }

    UPDATE_SUCCESS: ClassVar[dict[str, Any]] = {
        "id": 1,
        "title": "Update authentication",
        "status": "DONE",
    }

    STATUS_UPDATE: ClassVar[dict[str, Any]] = {
        "id": 1,
        "status": "DONE",
    }

    JOIN_REQUEST: ClassVar[dict[str, Any]] = {"message": "Join request sent"}

    ASSIGNEES: ClassVar[dict[str, Any]] = {
        "assignees": [
            {
                "id": 2,
                "username": "assignee",
                "assigned_at": "2024-01-15T10:30:00Z",
            }
        ]
    }


class TaskAssignExamples:
    """Examples for task assignment endpoints."""

    ASSIGN_SUCCESS: ClassVar[dict[str, Any]] = {"message": "User assigned to task"}

    UNASSIGN_SUCCESS: ClassVar[dict[str, Any]] = {
        "message": "User unassigned from task"
    }

    ALREADY_ASSIGNED: ClassVar[dict[str, Any]] = {
        "detail": "User is already assigned to this task"
    }


class TaskSearchExamples:
    """Examples for task search."""

    SEARCH_SUCCESS: ClassVar[dict[str, Any]] = {
        "tasks": [
            {
                "id": 1,
                "title": "Implement authentication",
                "status": "PENDING",
                "priority": "HIGH",
            }
        ],
        "total": 1,
    }
