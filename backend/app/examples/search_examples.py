"""Search endpoint examples for Swagger documentation."""

from typing import Any, ClassVar


class SearchExamples:
    """Examples for search endpoints."""

    SEARCH_USERS: ClassVar[dict[str, Any]] = {
        "users": [
            {
                "id": 1,
                "username": "john",
                "email": "john@example.com",
                "first_name": "John",
                "level": 3,
            }
        ],
        "total": 1,
    }

    SEARCH_TASKS: ClassVar[dict[str, Any]] = {
        "tasks": [
            {
                "id": 1,
                "title": "Implement API",
                "status": "PENDING",
                "priority": "HIGH",
                "group_name": "Backend Team",
            }
        ],
        "total": 1,
    }

    SEARCH_GROUPS: ClassVar[dict[str, Any]] = {
        "groups": [
            {
                "id": 1,
                "name": "Backend Team",
                "description": "Team for backend development",
                "members_count": 5,
            }
        ],
        "total": 1,
    }

    EMPTY_RESULTS: ClassVar[dict[str, Any]] = {"results": [], "total": 0}
