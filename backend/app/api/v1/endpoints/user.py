from fastapi import APIRouter, Depends, Query, status

from app.core.permission import require_permissions_db
from app.models import User as UserModel
from app.schemas import UserRead, UserSearch, UserUpdate
from app.service import UserService, get_user_service

router = APIRouter()


@router.get("/me", response_model=UserRead, status_code=status.HTTP_200_OK)
async def get_my_profile(
    current_user: UserModel = Depends(require_permissions_db("user:view:own")),
    svc: UserService = Depends(get_user_service),
) -> UserRead:
    """Get current user profile."""
    return await svc.get_my_profile(current_user=current_user)


@router.get("", response_model=list[UserRead], status_code=status.HTTP_200_OK)
async def search_users(
    search: UserSearch = Depends(),
    sort: UserSearch = Depends(),
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: UserModel = Depends(require_permissions_db("user:view:any")),
    svc: UserService = Depends(get_user_service),
) -> list[UserRead]:
    """Search users (autocomplete, lists)."""
    return await svc.search_users(search=search, sort=sort, limit=limit, offset=offset)


@router.get(
    "/groups/{group_id}/members",
    response_model=list[UserRead],
    status_code=status.HTTP_200_OK,
)
async def search_users_in_group(
    group_id: int,
    search: UserSearch = Depends(),
    sort: UserSearch = Depends(),
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: UserModel = Depends(require_permissions_db("group:view:group")),
    svc: UserService = Depends(get_user_service),
) -> list[UserRead]:
    """Get group members."""
    return await svc.search_users_in_group(
        group_id=group_id, search=search, sort=sort, limit=limit, offset=offset
    )


@router.get(
    "/tasks/{task_id}/members",
    response_model=list[UserRead],
    status_code=status.HTTP_200_OK,
)
async def search_users_in_task(
    task_id: int,
    search: UserSearch = Depends(),
    sort: UserSearch = Depends(),
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: UserModel = Depends(require_permissions_db("task:view:group")),
    svc: UserService = Depends(get_user_service),
) -> list[UserRead]:
    """Get task assignees."""
    return await svc.search_users_in_tasks(
        task_id=task_id, search=search, sort=sort, limit=limit, offset=offset
    )


@router.patch("/me", response_model=UserRead, status_code=status.HTTP_200_OK)
async def update_my_profile(
    user_in: UserUpdate,
    current_user: UserModel = Depends(require_permissions_db("user:update:own")),
    svc: UserService = Depends(get_user_service),
) -> UserRead:
    """Update own profile."""
    return await svc.update_my_profile(current_user, user_in)


@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
async def delete_my_profile(
    current_user: UserModel = Depends(require_permissions_db("user:delete:own")),
    svc: UserService = Depends(get_user_service),
) -> None:
    """Soft-delete own profile."""
    return await svc.delete_my_profile(current_user=current_user)


@router.get(
    "/groups/{group_id}/admin", response_model=UserRead, status_code=status.HTTP_200_OK
)
async def get_group_admin(
    group_id: int,
    current_user: UserModel = Depends(require_permissions_db("group:view:group")),
    svc: UserService = Depends(get_user_service),
) -> UserRead:
    """Get group administrator profile."""
    return await svc.get_group_admin(group_id=group_id)


@router.get(
    "/tasks/{task_id}/owner", response_model=UserRead, status_code=status.HTTP_200_OK
)
async def get_owner_task(
    task_id: int,
    current_user: UserModel = Depends(require_permissions_db("task:view:group")),
    svc: UserService = Depends(get_user_service),
) -> UserRead:
    """Get task owner profile."""
    return await svc.get_owner_task(task_id=task_id)
