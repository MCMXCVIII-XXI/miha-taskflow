"""Comment endpoint examples for Swagger documentation."""

from typing import Any, ClassVar


class CommentExamples:
    """Examples for comment endpoints."""

    CREATE_SUCCESS: ClassVar[dict[str, Any]] = {
        "id": 1,
        "content": "This is a great task description",
        "task_id": 1,
        "user_id": 1,
        "created_at": "2024-01-15T10:30:00Z",
    }

    CREATE_REQUEST: ClassVar[dict[str, Any]] = {
        "content": "This is a great task description",
        "parent_id": None,
    }

    GET_ALL: ClassVar[dict[str, Any]] = {
        "comments": [
            {
                "id": 1,
                "content": "This is a comment",
                "task_id": 1,
                "user_id": 1,
                "created_at": "2024-01-15T10:30:00Z",
            }
        ],
        "total": 1,
    }

    GET_BY_ID: ClassVar[dict[str, Any]] = {
        "id": 1,
        "content": "This is a comment",
        "task_id": 1,
        "user_id": 1,
        "parent_id": None,
        "created_at": "2024-01-15T10:30:00Z",
    }

    UPDATE_SUCCESS: ClassVar[dict[str, Any]] = {
        "id": 1,
        "content": "Updated comment",
        "updated_at": "2024-01-15T12:00:00Z",
    }

    DELETE_SUCCESS: ClassVar[None] = None

    NOT_FOUND: ClassVar[dict[str, Any]] = {"detail": "Comment not found"}
