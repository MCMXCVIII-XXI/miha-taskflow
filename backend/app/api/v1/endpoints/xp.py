from typing import Any

from fastapi import APIRouter, Depends, Query, status

from app.core.permission import require_permissions_db
from app.examples.xp_rating_examples import RatingExamples, XPExamples
from app.models import User as UserModel
from app.schemas import UserSkillWithTitle
from app.service import XPService, get_xp_service

router = APIRouter(tags=["xp"])


@router.get(
    "/users/{user_id}/skills",
    response_model=list[UserSkillWithTitle],
    status_code=status.HTTP_200_OK,
    summary="Get user skills",
    description="""
    Get all skills for a user with XP and level per sphere.

    **Permissions required:** AUTHENTICATED_USER

    **Returns:** List of skills sorted by XP (descending).
    """,
    responses={
        200: {
            "description": "Skills retrieved",
            "content": {"application/json": {"example": XPExamples.GET_XP}},
        },
    },
)
async def get_user_skills(
    user_id: int,
    current_user: UserModel = Depends(require_permissions_db("user:view:any")),
    xp_service: XPService = Depends(get_xp_service),
) -> list[UserSkillWithTitle]:
    """Get all skills for a user."""
    return await xp_service.get_user_skills(user_id)


@router.get(
    "/users/{user_id}/skills/top",
    response_model=list[UserSkillWithTitle],
    status_code=status.HTTP_200_OK,
    summary="Get top skills",
    description="""
    Get top N skills for a user.

    **Permissions required:** AUTHENTICATED_USER

    **Query parameters:**
    - `limit` (default: 3, max: 1000): Number of skills to return
    """,
    responses={
        200: {
            "description": "Top skills retrieved",
        },
    },
)
async def get_top_user_skills(
    user_id: int,
    limit: int = Query(3, ge=0, le=1000, description="Number of top skills"),
    current_user: UserModel = Depends(require_permissions_db("user:view:any")),
    xp_service: XPService = Depends(get_xp_service),
) -> list[UserSkillWithTitle]:
    """Get top N skills for a user."""
    return await xp_service.get_top_skills(user_id, limit)


@router.get(
    "/leaderboard",
    response_model=list[dict[str, Any]],
    status_code=status.HTTP_200_OK,
    summary="Get leaderboard",
    description="""
    Get global or sphere-specific leaderboard.

    **Permissions required:** AUTHENTICATED_USER

    **Query parameters:**
    - `sphere` (optional): Filter by sphere (e.g., BACKEND, FRONTEND)
    - `limit` (default: 10, max: 1000): Number of users to return

    **Returns:** List of users sorted by XP (descending).
    """,
    responses={
        200: {
            "description": "Leaderboard retrieved",
            "content": {"application/json": {"example": RatingExamples.LEADERBOARD}},
        },
    },
)
async def get_leaderboard(
    sphere: str | None = Query(None, description="Filter by sphere"),
    limit: int = Query(10, ge=0, le=1000, description="Max users to return"),
    current_user: UserModel = Depends(require_permissions_db("user:view:any")),
    xp_service: XPService = Depends(get_xp_service),
) -> list[dict[str, Any]]:
    """Leaderboard users by XP."""
    return await xp_service.get_leaderboard(sphere, limit)
