"""XP and Rating endpoint examples for Swagger documentation."""

from typing import Any, ClassVar


class XPExamples:
    """Examples for XP endpoints."""

    GET_XP: ClassVar[dict[str, Any]] = {
        "xp_total": 1500,
        "spheres": {
            "BACKEND": {"xp": 800, "level": 4},
            "FRONTEND": {"xp": 500, "level": 2},
            "DEVOPS": {"xp": 200, "level": 1},
        },
    }

    GET_LEVEL: ClassVar[dict[str, Any]] = {"level": 3, "xp_to_next_level": 500}

    GET_TITLE: ClassVar[dict[str, Any]] = {
        "sphere": "BACKEND",
        "title": "Senior Backend Developer",
    }

    GET_PROGRESS: ClassVar[dict[str, Any]] = {
        "current_level": 3,
        "next_level": 4,
        "current_xp": 1500,
        "next_level_xp": 2000,
        "progress_percent": 50,
    }

    ADD_XP_SUCCESS: ClassVar[dict[str, Any]] = {"xp_added": 100, "new_total": 1600}

    DAILY_CAP_REACHED: ClassVar[dict[str, Any]] = {
        "detail": "Daily XP cap reached. Try again tomorrow."
    }


class RatingExamples:
    """Examples for rating endpoints."""

    LEADERBOARD: ClassVar[dict[str, Any]] = {
        "leaderboard": [
            {
                "rank": 1,
                "user_id": 1,
                "username": "top_user",
                "xp": 5000,
                "level": 10,
                "title": "CTO",
            },
            {
                "rank": 2,
                "user_id": 2,
                "username": "second_user",
                "xp": 3000,
                "level": 7,
                "title": "Tech Lead",
            },
        ],
        "total": 10,
    }
