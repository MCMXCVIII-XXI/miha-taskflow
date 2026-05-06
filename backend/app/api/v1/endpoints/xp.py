from typing import Any

from fastapi import APIRouter, Depends, status

from app.core.permission import require_permissions_db
from app.models import User as UserModel
from app.schemas import UserSkillWithTitle
from app.service import XPService, get_xp_service

router = APIRouter()


@router.get(
    "/users/{user_id}/skills",
    response_model=list[UserSkillWithTitle],
    status_code=status.HTTP_200_OK,
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
)
async def get_top_user_skills(
    user_id: int,
    limit: int = 3,
    current_user: UserModel = Depends(require_permissions_db("user:view:any")),
    xp_service: XPService = Depends(get_xp_service),
) -> list[UserSkillWithTitle]:
    """Get top N skills for a user."""
    return await xp_service.get_top_skills(user_id, limit)


@router.get(
    "/leaderboard", response_model=list[dict[str, Any]], status_code=status.HTTP_200_OK
)
async def get_leaderboard(
    sphere: str | None = None,
    limit: int = 10,
    current_user: UserModel = Depends(require_permissions_db("user:view:any")),
    xp_service: XPService = Depends(get_xp_service),
) -> list[dict[str, Any]]:
    """Leaderboard users by XP."""
    return await xp_service.get_leaderboard(sphere, limit)
