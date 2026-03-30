from typing import Any

from fastapi import APIRouter, Depends, Query, status

from app.core.permission import require_permissions_db
from app.models import User as UserModel
from app.schemas import UserRead, UserSearch
from app.service.admin import AdminService, get_admin_service

router = APIRouter()


@router.get("/users", response_model=list[UserRead], status_code=status.HTTP_200_OK)
async def get_all_users(
    search: UserSearch = Depends(),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: UserModel = Depends(require_permissions_db("admin:users:view")),
    svc: AdminService = Depends(get_admin_service),
) -> list[UserRead]:
    """Get all users (admin only)."""
    return await svc.get_all_users(search=search, limit=limit, offset=offset)


@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: int,
    current_user: UserModel = Depends(require_permissions_db("admin:users:delete")),
    svc: AdminService = Depends(get_admin_service),
) -> None:
    """Delete user (soft delete, admin only)."""
    return await svc.delete_user(user_id=user_id, admin_id=current_user.id)


@router.get("/stats")
async def get_stats(
    current_user: UserModel = Depends(require_permissions_db("admin:stats:view")),
    svc: AdminService = Depends(get_admin_service),
) -> dict[str, Any]:
    """Get statistics (admin only)."""
    return await svc.get_stats()
