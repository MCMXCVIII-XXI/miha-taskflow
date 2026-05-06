from fastapi import APIRouter, Depends, status

from app.core.permission import require_permissions_db
from app.models import User as UserModel
from app.schemas import (
    JoinRequestRead,
    NotificationRead,
    UserGroupCreate,
    UserGroupRead,
    UserGroupUpdate,
)
from app.service import GroupService, get_group_service

router = APIRouter()


@router.post("", response_model=UserGroupRead, status_code=status.HTTP_201_CREATED)
async def create_my_group(
    group_in: UserGroupCreate,
    current_user: UserModel = Depends(require_permissions_db("group:create:own")),
    svc: GroupService = Depends(get_group_service),
) -> UserGroupRead:
    """Create new group."""
    return await svc.create_my_group(group_in=group_in, current_user=current_user)


@router.get("/{group_id}", response_model=UserGroupRead, status_code=status.HTTP_200_OK)
async def get_my_group(
    group_id: int,
    current_user: UserModel = Depends(require_permissions_db("group:view:own")),
    svc: GroupService = Depends(get_group_service),
) -> UserGroupRead:
    """Get owned group profile (GROUP_ADMIN)."""
    return await svc.get_my_group(group_id=group_id, current_user=current_user)


@router.post(
    "/{group_id}/members/{user_id}",
    status_code=status.HTTP_201_CREATED,
)
async def add_member_to_group(
    group_id: int,
    user_id: int,
    current_user: UserModel = Depends(require_permissions_db("group:add:own")),
    svc: GroupService = Depends(get_group_service),
) -> None:
    """Add user to group (GROUP_ADMIN)."""
    return await svc.add_member_to_group(
        group_id=group_id, user_id=user_id, current_user=current_user
    )


@router.delete("/{group_id}/members/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_member_from_group(
    group_id: int,
    user_id: int,
    current_user: UserModel = Depends(require_permissions_db("group:remove:own")),
    svc: GroupService = Depends(get_group_service),
) -> None:
    """Remove user from group (GROUP_ADMIN)."""
    return await svc.remove_member_from_group(
        group_id=group_id, user_id=user_id, current_user=current_user
    )


@router.patch(
    "/{group_id}", response_model=UserGroupRead, status_code=status.HTTP_200_OK
)
async def update_my_group(
    group_id: int,
    group_in: UserGroupUpdate,
    current_user: UserModel = Depends(require_permissions_db("group:update:own")),
    svc: GroupService = Depends(get_group_service),
) -> UserGroupRead:
    """Update owned group (GROUP_ADMIN)."""
    return await svc.update_my_group(
        group_id=group_id, current_user=current_user, group_in=group_in
    )


@router.delete("/{group_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_my_group(
    group_id: int,
    current_user: UserModel = Depends(require_permissions_db("group:delete:own")),
    svc: GroupService = Depends(get_group_service),
) -> None:
    """Soft-delete owned group (GROUP_ADMIN)."""
    return await svc.delete_my_group(group_id=group_id, current_user=current_user)


@router.get(
    "/{group_id}/join-requests",
    response_model=list[JoinRequestRead],
    status_code=status.HTTP_200_OK,
)
async def get_join_requests(
    group_id: int,
    current_user: UserModel = Depends(require_permissions_db("group:view:own")),
    svc: GroupService = Depends(get_group_service),
) -> list[JoinRequestRead]:
    return await svc.get_join_requests(group_id, current_user)


@router.post(
    "/{group_id}/join-requests/{request_id}/approve",
    response_model=NotificationRead,
    status_code=status.HTTP_200_OK,
)
async def approve_join_request(
    group_id: int,
    request_id: int,
    current_user: UserModel = Depends(require_permissions_db("group:update:own")),
    svc: GroupService = Depends(get_group_service),
) -> NotificationRead:
    return await svc.approve_join_request(group_id, request_id, current_user)


@router.post(
    "/{group_id}/join-requests/{request_id}/reject",
    status_code=status.HTTP_200_OK,
)
async def reject_join_request(
    group_id: int,
    request_id: int,
    current_user: UserModel = Depends(require_permissions_db("group:update:own")),
    svc: GroupService = Depends(get_group_service),
) -> NotificationRead | None:
    return await svc.reject_join_request(request_id, current_user)


@router.post("/{group_id}/join", status_code=status.HTTP_201_CREATED)
async def join_group(
    group_id: int,
    current_user: UserModel = Depends(require_permissions_db("group:join:any")),
    svc: GroupService = Depends(get_group_service),
) -> None:
    """Join group (MEMBER+)."""
    return await svc.join_group(group_id=group_id, current_user=current_user)


@router.delete("/{group_id}/exit", status_code=status.HTTP_204_NO_CONTENT)
async def exit_group(
    group_id: int,
    current_user: UserModel = Depends(require_permissions_db("group:exit:member")),
    svc: GroupService = Depends(get_group_service),
) -> None:
    """Leave group (MEMBER+)."""
    return await svc.exit_group(group_id=group_id, current_user=current_user)
