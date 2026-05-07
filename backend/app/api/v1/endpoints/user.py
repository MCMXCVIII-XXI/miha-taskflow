from typing import Any

from fastapi import APIRouter, Depends, status
from fastapi_cache.decorator import cache

from app.cache import kb
from app.core.permission import require_permissions_db
from app.examples.user_examples import (
    UserExamples,
)
from app.models import User as UserModel
from app.schemas import UserRead, UserUpdate
from app.service import UserService, get_user_service

router = APIRouter(tags=["users"])


@router.get(
    "/me",
    response_model=UserRead,
    status_code=status.HTTP_200_OK,
    summary="Get my profile",
    description="""
    Get current authenticated user's profile information.

    **Permissions required:** OWNER (self)

    **Returns:** User profile including:
    - Basic info (id, username, email, first_name, last_name)
    - Role (USER, ADMIN, MODERATOR)
    - XP and level (RPG system)
    - Timestamps (created_at, updated_at)

    **Caching:** Cached for 30 minutes (1800s).
    """,
    responses={
        200: {
            "description": "User profile retrieved successfully",
            "content": {"application/json": {"example": UserExamples.GET_ME}},
        },
        401: {
            "description": "Not authenticated",
            "content": {"application/json": {"example": UserExamples.UNAUTHORIZED}},
        },
    },
)
@cache(expire=1800, key_builder=kb.search_key_builder)
async def get_my_profile(
    current_user: UserModel = Depends(require_permissions_db("user:view:own")),
    svc: UserService = Depends(get_user_service),
) -> UserRead:
    """Get current authenticated user's profile information."""
    return await svc.get_my_profile(current_user=current_user)


@router.get(
    "/{user_id}",
    response_model=dict[str, Any],
    status_code=status.HTTP_200_OK,
    summary="Get user by ID",
    description="""
    Get specific user's public profile information with top skills.

    **Permissions required:** USER role (any user can view)

    **Returns:** User profile with public fields.
                 Sensitive data (email) visible to authenticated users.

    **Caching:** Cached for 30 minutes (1800s).
    """,
    responses={
        200: {
            "description": "User profile retrieved successfully",
            "content": {"application/json": {"example": UserExamples.GET_BY_ID}},
        },
        401: {
            "description": "Not authenticated",
            "content": {"application/json": {"example": UserExamples.UNAUTHORIZED}},
        },
        404: {
            "description": "User not found",
            "content": {"application/json": {"example": UserExamples.NOT_FOUND}},
        },
    },
)
@cache(expire=1800, key_builder=kb.id_key_builder("user_id"))
async def get_user(
    user_id: int,
    current_user: UserModel = Depends(require_permissions_db("user:view:any")),
    svc: UserService = Depends(get_user_service),
) -> dict[str, Any]:
    """Get specific user's public profile information with top skills."""
    return await svc.get_user(user_id)


@router.patch(
    "/me",
    response_model=UserRead,
    status_code=status.HTTP_200_OK,
    summary="Update my profile",
    description="""
    Update current authenticated user's profile information.

    **Permissions required:** OWNER (self)

    **Request body:** (all fields optional)
    - `first_name` (max 50 chars): User's first name
    - `last_name` (max 50 chars): User's last name
    - `email` (valid email format): Email address

    **Returns:** Updated user profile.

    **Side effects:**
    - Clears user cache after successful update
    - Invalidates auth tokens if email changed
    """,
    responses={
        200: {
            "description": "Profile updated successfully",
            "content": {"application/json": {"example": UserExamples.UPDATE_SUCCESS}},
        },
        400: {
            "description": "Invalid email format",
            "content": {"application/json": {"example": UserExamples.VALIDATION_ERROR}},
        },
        401: {
            "description": "Not authenticated",
            "content": {"application/json": {"example": UserExamples.UNAUTHORIZED}},
        },
        403: {
            "description": "Permission denied - can only update own profile",
            "content": {"application/json": {"example": UserExamples.FORBIDDEN}},
        },
        422: {
            "description": "Validation error",
            "content": {"application/json": {"example": UserExamples.VALIDATION_ERROR}},
        },
    },
)
async def update_my_profile(
    user_in: UserUpdate,
    current_user: UserModel = Depends(require_permissions_db("user:update:own")),
    svc: UserService = Depends(get_user_service),
) -> UserRead:
    """Update current user's profile information."""
    return await svc.update_my_profile(current_user, user_in)


@router.delete(
    "/me",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete my profile",
    description="""
    Soft-delete current user's profile (deactivate account).

    **Permissions required:** OWNER (self)

    **Returns:** No content (204)

    **Side effects:**
        - User profile is soft-deleted (is_active = false)
        - All tokens are invalidated
        - User is removed from all groups
        - User's tasks are reassigned

    **Note:** This is a soft delete. Data can be restored by admin.
    """,
    responses={
        204: {"description": "Profile deleted successfully"},
        401: {
            "description": "Not authenticated",
            "content": {"application/json": {"example": UserExamples.UNAUTHORIZED}},
        },
    },
)
async def delete_my_profile(
    current_user: UserModel = Depends(require_permissions_db("user:delete:own")),
    svc: UserService = Depends(get_user_service),
) -> None:
    """Soft-delete current user's profile."""
    return await svc.delete_my_profile(current_user=current_user)


@router.get(
    "/groups/{group_id}/admin",
    response_model=UserRead,
    status_code=status.HTTP_200_OK,
    summary="Get group admin",
    description="""
    Get group administrator profile.

    **Permissions required:** GROUP_MEMBER (any member can view)

    **Returns:** User profile of the group owner/admin.
    """,
    responses={
        200: {
            "description": "Group admin profile retrieved",
            "content": {"application/json": {"example": UserExamples.GROUP_ADMIN}},
        },
        404: {"description": "Group not found"},
    },
)
async def get_group_admin(
    group_id: int,
    current_user: UserModel = Depends(require_permissions_db("group:view:group")),
    svc: UserService = Depends(get_user_service),
) -> UserRead:
    """Get group administrator profile."""
    return await svc.get_group_admin(group_id=group_id)


@router.get(
    "/tasks/{task_id}/owner",
    response_model=UserRead,
    status_code=status.HTTP_200_OK,
    summary="Get task owner",
    description="""
    Get task owner profile.

    **Permissions required:** TASK_VIEW (group member)

    **Returns:** User profile of the task owner.
    """,
    responses={
        200: {
            "description": "Task owner profile retrieved",
            "content": {"application/json": {"example": UserExamples.TASK_OWNER}},
        },
        404: {"description": "Task not found"},
    },
)
async def get_owner_task(
    task_id: int,
    current_user: UserModel = Depends(require_permissions_db("task:view:group")),
    svc: UserService = Depends(get_user_service),
) -> UserRead:
    """Get task owner profile."""
    return await svc.get_owner_task(task_id=task_id)
