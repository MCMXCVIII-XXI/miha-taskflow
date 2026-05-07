from fastapi import APIRouter, Depends, status

from app.core.permission import require_permissions_db
from app.examples.group_examples import (
    GroupExamples,
    GroupRequestExamples,
    GroupSearchExamples,
)
from app.models import User as UserModel
from app.schemas import (
    JoinRequestRead,
    NotificationRead,
    UserGroupCreate,
    UserGroupRead,
    UserGroupUpdate,
)
from app.service import GroupService, get_group_service

router = APIRouter(tags=["groups"])


@router.post(
    "",
    response_model=UserGroupRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create group",
    description="""
    Create a new group.

    **Permissions required:** AUTHENTICATED_USER

    **Request body:**
    - `name` (required, 3-100 chars): Group name
    - `description` (optional, max 500 chars): Group description
    - `visibility` (optional): PUBLIC, INTERNAL, PRIVATE (default: PUBLIC)
    - `join_policy` (optional): OPEN, REQUEST, INVITE (default: OPEN)

    **Returns:** Created group with ID and timestamps.

    **Side effects:** Creator becomes group OWNER automatically.
    """,
    responses={
        201: {
            "description": "Group created successfully",
            "content": {"application/json": {"example": GroupExamples.CREATE_SUCCESS}},
        },
        422: {"description": "Validation error"},
    },
)
async def create_my_group(
    group_in: UserGroupCreate,
    current_user: UserModel = Depends(require_permissions_db("group:create:own")),
    svc: GroupService = Depends(get_group_service),
) -> UserGroupRead:
    """Create new group."""
    return await svc.create_my_group(group_in=group_in, current_user=current_user)


@router.get(
    "/{group_id}",
    response_model=UserGroupRead,
    status_code=status.HTTP_200_OK,
    summary="Get group",
    description="""
    Get group by ID.

    **Permissions required:** GROUP_MEMBER or PUBLIC visibility

    **Returns:** Group details with member role.
    """,
    responses={
        200: {
            "description": "Group retrieved successfully",
            "content": {"application/json": {"example": GroupExamples.GET_BY_ID}},
        },
        404: {
            "description": "Group not found",
            "content": {"application/json": {"example": GroupSearchExamples.NOT_FOUND}},
        },
    },
)
async def get_my_group(
    group_id: int,
    current_user: UserModel = Depends(require_permissions_db("group:view:own")),
    svc: GroupService = Depends(get_group_service),
) -> UserGroupRead:
    """Get group by ID."""
    return await svc.get_my_group(group_id=group_id, current_user=current_user)


@router.patch(
    "/{group_id}",
    response_model=UserGroupRead,
    status_code=status.HTTP_200_OK,
    summary="Update group",
    description="""
    Update group details.

    **Permissions required:** GROUP_OWNER

    **Request body (all optional):**
    - `name`: Group name
    - `description`: Group description
    - `visibility`: PUBLIC, INTERNAL, PRIVATE
    - `join_policy`: OPEN, REQUEST, INVITE
    """,
    responses={
        200: {
            "description": "Group updated successfully",
            "content": {"application/json": {"example": GroupExamples.UPDATE_SUCCESS}},
        },
        403: {
            "description": "Permission denied",
            "content": {"application/json": {"example": GroupSearchExamples.FORBIDDEN}},
        },
    },
)
async def update_my_group(
    group_id: int,
    group_in: UserGroupUpdate,
    current_user: UserModel = Depends(require_permissions_db("group:update:own")),
    svc: GroupService = Depends(get_group_service),
) -> UserGroupRead:
    """Update group details."""
    return await svc.update_my_group(
        group_id=group_id, current_user=current_user, group_in=group_in
    )


@router.delete(
    "/{group_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete group",
    description="""
    Soft-delete group (deactivate).

    **Permissions required:** GROUP_OWNER

    **Side effects:**
    - All members are removed
    - All tasks are deactivated
    - Group is marked as inactive
    """,
    responses={
        204: {"description": "Group deleted successfully"},
        403: {
            "description": "Permission denied",
            "content": {"application/json": {"example": GroupSearchExamples.FORBIDDEN}},
        },
    },
)
async def delete_my_group(
    group_id: int,
    current_user: UserModel = Depends(require_permissions_db("group:delete:own")),
    svc: GroupService = Depends(get_group_service),
) -> None:
    """Soft-delete group."""
    return await svc.delete_my_group(group_id=group_id, current_user=current_user)


@router.post(
    "/{group_id}/join",
    status_code=status.HTTP_201_CREATED,
    summary="Join group",
    description="""
    Join a group.

    **Permissions required:** AUTHENTICATED_USER

    **Behavior depends on join_policy:**
    - OPEN: User joins immediately
    - REQUEST: Join request is created (pending)
    - INVITE: User must be invited by group admin

    **Returns:** Success message or join request status.
    """,
    responses={
        201: {
            "description": "Joined successfully or request sent",
            "content": {"application/json": {"example": GroupExamples.JOIN_SUCCESS}},
        },
        400: {
            "description": "Already member or request pending",
            "content": {"application/json": {"example": GroupExamples.ALREADY_MEMBER}},
        },
    },
)
async def join_group(
    group_id: int,
    current_user: UserModel = Depends(require_permissions_db("group:join:any")),
    svc: GroupService = Depends(get_group_service),
) -> None:
    """Join group."""
    return await svc.join_group(group_id=group_id, current_user=current_user)


@router.delete(
    "/{group_id}/exit",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Leave group",
    description="""
    Leave a group.

    **Permissions required:** GROUP_MEMBER (not owner)

    **Side effects:**
    - User is removed from group
    - User's task assignments are removed
    """,
    responses={
        204: {"description": "Left group successfully"},
    },
)
async def exit_group(
    group_id: int,
    current_user: UserModel = Depends(require_permissions_db("group:exit:member")),
    svc: GroupService = Depends(get_group_service),
) -> None:
    """Leave group."""
    return await svc.exit_group(group_id=group_id, current_user=current_user)


@router.post(
    "/{group_id}/members/{user_id}",
    status_code=status.HTTP_201_CREATED,
    summary="Add member",
    description="""
    Add user to group manually.

    **Permissions required:** GROUP_ADMIN

    **Side effects:** User receives notification.
    """,
    responses={
        201: {"description": "Member added successfully"},
        404: {"description": "User or group not found"},
    },
)
async def add_member_to_group(
    group_id: int,
    user_id: int,
    current_user: UserModel = Depends(require_permissions_db("group:add:own")),
    svc: GroupService = Depends(get_group_service),
) -> None:
    """Add member to group."""
    return await svc.add_member_to_group(
        group_id=group_id, user_id=user_id, current_user=current_user
    )


@router.delete(
    "/{group_id}/members/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remove member",
    description="""
    Remove user from group.

    **Permissions required:** GROUP_ADMIN

    **Side effects:**
    - User is removed from group
    - User's tasks are reassigned
    """,
    responses={
        204: {"description": "Member removed successfully"},
    },
)
async def remove_member_from_group(
    group_id: int,
    user_id: int,
    current_user: UserModel = Depends(require_permissions_db("group:remove:own")),
    svc: GroupService = Depends(get_group_service),
) -> None:
    """Remove member from group."""
    return await svc.remove_member_from_group(
        group_id=group_id, user_id=user_id, current_user=current_user
    )


@router.get(
    "/{group_id}/join-requests",
    summary="Get join requests",
    response_model=list[JoinRequestRead],
    description="""
    Get pending join requests for group.

    **Permissions required:** GROUP_ADMIN
    """,
    responses={
        200: {
            "description": "Requests retrieved",
            "content": {
                "application/json": {"example": GroupRequestExamples.JOIN_REQUESTS}
            },
        },
    },
)
async def get_join_requests(
    group_id: int,
    current_user: UserModel = Depends(require_permissions_db("group:view:own")),
    svc: GroupService = Depends(get_group_service),
) -> list[JoinRequestRead]:
    """Get join requests."""
    return await svc.get_join_requests(group_id, current_user)


@router.post(
    "/{group_id}/join-requests/{request_id}/approve",
    response_model=NotificationRead,
    summary="Approve join request",
    description="""
    Approve user's join request.

    **Permissions required:** GROUP_ADMIN

    **Side effects:**
    - User is added to group
    - Notification is sent to user
    """,
    responses={
        200: {
            "description": "Request approved",
            "content": {
                "application/json": {"example": GroupRequestExamples.APPROVE_SUCCESS}
            },
        },
    },
)
async def approve_join_request(
    group_id: int,
    request_id: int,
    current_user: UserModel = Depends(require_permissions_db("group:update:own")),
    svc: GroupService = Depends(get_group_service),
) -> NotificationRead:
    """Approve join request."""
    return await svc.approve_join_request(group_id, request_id, current_user)


@router.post(
    "/{group_id}/join-requests/{request_id}/reject",
    summary="Reject join request",
    description="""
    Reject user's join request.

    **Permissions required:** GROUP_ADMIN

    **Side effects:** Notification is sent to user.
    """,
    responses={
        200: {
            "description": "Request rejected",
            "content": {
                "application/json": {"example": GroupRequestExamples.REJECT_SUCCESS}
            },
        },
    },
)
async def reject_join_request(
    group_id: int,
    request_id: int,
    current_user: UserModel = Depends(require_permissions_db("group:update:own")),
    svc: GroupService = Depends(get_group_service),
) -> NotificationRead | None:
    """Reject join request."""
    return await svc.reject_join_request(request_id, current_user)
