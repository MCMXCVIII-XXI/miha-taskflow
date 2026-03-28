from fastapi import APIRouter, Depends, Query, status

from app.core.permission import require_permissions_db
from app.models import User as UserModel
from app.schemas import UserGroupCreate, UserGroupRead, UserGroupSearch, UserGroupUpdate
from app.service import GroupService, get_group_service

router = APIRouter()


@router.get("/{group_id}", response_model=UserGroupRead, status_code=status.HTTP_200_OK)
async def get_my_group(
    group_id: int,
    current_user: UserModel = Depends(require_permissions_db("group:manage:own")),
    svc: GroupService = Depends(get_group_service),
) -> UserGroupRead:
    """Get owned group profile (GROUP_ADMIN)."""
    return await svc.get_my_group(group_id=group_id, current_user=current_user)


@router.get("", response_model=list[UserGroupRead], status_code=status.HTTP_200_OK)
async def search_groups(
    search: UserGroupSearch = Depends(),
    sort: UserGroupSearch = Depends(),
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: UserModel = Depends(require_permissions_db("group:view")),
    svc: GroupService = Depends(get_group_service),
) -> list[UserGroupRead]:
    """Search all groups."""
    return await svc.search_groups(search=search, sort=sort, limit=limit, offset=offset)


@router.get("/me", response_model=list[UserGroupRead], status_code=status.HTTP_200_OK)
async def search_my_groups(
    search: UserGroupSearch = Depends(),
    sort: UserGroupSearch = Depends(),
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: UserModel = Depends(require_permissions_db("group:manage:own")),
    svc: GroupService = Depends(get_group_service),
) -> list[UserGroupRead]:
    """Get owned groups (GROUP_ADMIN)."""
    return await svc.search_my_groups(
        current_user, search=search, sort=sort, limit=limit, offset=offset
    )


@router.get(
    "/membership", response_model=list[UserGroupRead], status_code=status.HTTP_200_OK
)
async def search_member_groups(
    search: UserGroupSearch = Depends(),
    sort: UserGroupSearch = Depends(),
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: UserModel = Depends(require_permissions_db("group:view")),
    svc: GroupService = Depends(get_group_service),
) -> list[UserGroupRead]:
    """Get groups where user is member (MEMBER+)."""
    return await svc.search_member_groups(
        current_user, search=search, sort=sort, limit=limit, offset=offset
    )


@router.post("", response_model=UserGroupRead, status_code=status.HTTP_201_CREATED)
async def create_my_group(
    group_in: UserGroupCreate,
    current_user: UserModel = Depends(require_permissions_db("group:create")),
    svc: GroupService = Depends(get_group_service),
) -> UserGroupRead:
    """Create new group."""
    return await svc.create_my_group(group_in=group_in, current_user=current_user)


@router.post(
    "/{group_id}/members/{user_id}",
    response_model=UserGroupRead,
    status_code=status.HTTP_201_CREATED,
)
async def add_member_to_group(
    group_id: int,
    user_id: int,
    current_user: UserModel = Depends(require_permissions_db("group:manage:group")),
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
    current_user: UserModel = Depends(require_permissions_db("group:manage:group")),
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
    current_user: UserModel = Depends(require_permissions_db("group:manage:own")),
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


@router.delete("/{group_id}/exit", status_code=status.HTTP_204_NO_CONTENT)
async def exit_group(
    group_id: int,
    current_user: UserModel = Depends(require_permissions_db("group:view")),
    svc: GroupService = Depends(get_group_service),
) -> None:
    """Leave group (MEMBER+)."""
    return await svc.exit_group(group_id=group_id, current_user=current_user)
