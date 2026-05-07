"""Group endpoint examples for Swagger documentation."""

from typing import Any, ClassVar


class GroupExamples:
    """Examples for group endpoints."""

    CREATE_SUCCESS: ClassVar[dict[str, Any]] = {
        "id": 1,
        "name": "Backend Team",
        "description": "Team for backend development",
        "visibility": "PUBLIC",
        "join_policy": "OPEN",
        "created_by": 1,
        "created_at": "2024-01-15T10:30:00Z",
        "updated_at": "2024-01-15T10:30:00Z",
    }

    CREATE_REQUEST: ClassVar[dict[str, Any]] = {
        "name": "Backend Team",
        "description": "Team for backend development",
        "visibility": "PUBLIC",
        "join_policy": "OPEN",
    }

    GET_BY_ID: ClassVar[dict[str, Any]] = {
        "id": 1,
        "name": "Backend Team",
        "description": "Team for backend development",
        "visibility": "PUBLIC",
        "join_policy": "OPEN",
        "created_by": 1,
        "role": "OWNER",
        "created_at": "2024-01-15T10:30:00Z",
        "updated_at": "2024-01-15T10:30:00Z",
    }

    UPDATE_SUCCESS: ClassVar[dict[str, Any]] = {
        "id": 1,
        "name": "Updated Backend Team",
        "description": "Updated description",
        "visibility": "PRIVATE",
        "join_policy": "REQUEST",
    }

    DELETE_SUCCESS: ClassVar[None] = None

    JOIN_SUCCESS: ClassVar[dict[str, Any]] = {
        "message": "Successfully joined the group"
    }

    ALREADY_MEMBER: ClassVar[dict[str, Any]] = {
        "detail": "User is already a member of this group"
    }

    JOIN_REQUEST_SENT: ClassVar[dict[str, Any]] = {"message": "Join request sent"}


class GroupMemberExamples:
    """Examples for group membership endpoints."""

    GROUP_MEMBERS: ClassVar[dict[str, Any]] = {
        "members": [
            {
                "id": 1,
                "username": "owner",
                "email": "owner@example.com",
                "first_name": "Owner",
                "last_name": "User",
                "role": "OWNER",
            },
            {
                "id": 2,
                "username": "admin",
                "email": "admin@example.com",
                "first_name": "Admin",
                "last_name": "User",
                "role": "ADMIN",
            },
        ],
        "total": 2,
    }

    ADD_MEMBER_SUCCESS: ClassVar[None] = None

    REMOVE_MEMBER_SUCCESS: ClassVar[None] = None


class GroupRequestExamples:
    """Examples for group join requests."""

    JOIN_REQUESTS: ClassVar[dict[str, Any]] = {
        "requests": [
            {
                "id": 1,
                "user_id": 2,
                "username": "new_user",
                "status": "PENDING",
                "created_at": "2024-01-20T10:30:00Z",
            }
        ],
        "total": 1,
    }

    APPROVE_SUCCESS: ClassVar[dict[str, Any]] = {
        "id": 1,
        "user_id": 2,
        "status": "APPROVED",
    }

    REJECT_SUCCESS: ClassVar[dict[str, Any]] = {
        "id": 1,
        "user_id": 2,
        "status": "REJECTED",
    }


class GroupTaskExamples:
    """Examples for group tasks."""

    GROUP_TASKS: ClassVar[dict[str, Any]] = {
        "tasks": [
            {
                "id": 1,
                "title": "Implement API",
                "description": "Create new API endpoint",
                "status": "IN_PROGRESS",
                "priority": "HIGH",
                "group_id": 1,
                "created_by": 1,
                "created_at": "2024-01-15T10:30:00Z",
                "updated_at": "2024-01-15T10:30:00Z",
            }
        ],
        "total": 1,
    }

    SUBGROUPS: ClassVar[dict[str, Any]] = {
        "groups": [
            {
                "id": 2,
                "name": "Backend API Team",
                "description": "Subteam for API development",
                "visibility": "INTERNAL",
                "join_policy": "OPEN",
                "role": "OWNER",
            }
        ],
        "total": 1,
    }


class GroupSearchExamples:
    """Examples for group search."""

    SEARCH_SUCCESS: ClassVar[dict[str, Any]] = {
        "groups": [
            {
                "id": 1,
                "name": "Backend Team",
                "description": "Team for backend development",
                "visibility": "PUBLIC",
                "join_policy": "OPEN",
                "members_count": 5,
            },
        ],
        "total": 1,
    }

    NOT_FOUND: ClassVar[dict[str, Any]] = {"detail": "Group not found"}

    FORBIDDEN: ClassVar[dict[str, Any]] = {"detail": "Permission denied"}
