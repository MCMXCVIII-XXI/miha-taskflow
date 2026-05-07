from typing import Any

from fastapi import APIRouter, Depends, Query, status

from app.core.permission import require_permissions_db
from app.examples.admin_examples import AdminExamples
from app.models import User as UserModel
from app.schemas import UserRead, UserSearch
from app.service.admin import AdminService, get_admin_service

router = APIRouter(tags=["admin"])


@router.get(
    "/users",
    response_model=list[UserRead],
    status_code=status.HTTP_200_OK,
    summary="Get all users (admin)",
    description="""
    Get all users with pagination and search filters.

    **Permissions required:** ADMIN role only

    **Query parameters:**
    - `search` (optional): Search filter object (username, email, role, is_active)
    - `limit` (default: 50, max: 100)
    - `offset` (default: 0)

    **Returns:** List of users with their profiles.
    """,
    responses={
        200: {
            "description": "Users retrieved",
            "content": {"application/json": {"example": AdminExamples.GET_USERS}},
        },
        403: {"description": "Admin access required"},
    },
)
async def get_all_users(
    search: UserSearch = Depends(),
    limit: int = Query(50, ge=1, le=100, description="Max users to return"),
    offset: int = Query(0, ge=0, description="User offset"),
    current_user: UserModel = Depends(require_permissions_db("admin:users:view")),
    svc: AdminService = Depends(get_admin_service),
) -> list[UserRead]:
    """Get all users (admin only)."""
    return await svc.get_all_users(search=search, limit=limit, offset=offset)


@router.delete(
    "/users/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete user (admin)",
    description="""
    Soft-delete a user account.

    **Permissions required:** ADMIN role only

    **Side effects:**
    - User is marked as deleted
    - All group memberships removed
    - All tasks deactivated
    - Notifications cleared
    """,
    responses={
        204: {"description": "User deleted"},
        404: {"description": "User not found"},
    },
)
async def delete_user(
    user_id: int,
    current_user: UserModel = Depends(require_permissions_db("admin:users:delete")),
    svc: AdminService = Depends(get_admin_service),
) -> None:
    """Delete user (soft delete, admin only)."""
    return await svc.delete_user(user_id=user_id, admin_id=current_user.id)


@router.get(
    "/stats",
    response_model=dict[str, Any],
    status_code=status.HTTP_200_OK,
    summary="Get platform stats",
    description="""
    Get platform-wide statistics.

    **Permissions required:** ADMIN role only

    **Returns:**
    - Total users (active/inactive)
    - Total groups
    - Total tasks
    - Platform activity metrics
    """,
    responses={
        200: {
            "description": "Stats retrieved",
            "content": {"application/json": {"example": AdminExamples.STATS}},
        },
    },
)
async def get_stats(
    current_user: UserModel = Depends(require_permissions_db("admin:stats:view")),
    svc: AdminService = Depends(get_admin_service),
) -> dict[str, Any]:
    """Get statistics (admin only)."""
    return await svc.get_stats()
