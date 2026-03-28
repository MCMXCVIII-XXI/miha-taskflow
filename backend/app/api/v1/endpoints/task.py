from fastapi import APIRouter, Depends, Query, status

from app.core.permission import require_permissions_db
from app.models import User as UserModel
from app.schemas import TaskCreate, TaskRead, TaskSearch, TaskStatus, TaskUpdate
from app.service import TaskService, get_task_service

router = APIRouter()


@router.post(
    "/groups/{group_id}",
    response_model=TaskRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_task_for_group(
    group_id: int,
    task_in: TaskCreate,
    current_user: UserModel = Depends(
        require_permissions_db("task:create", "group:manage:own")
    ),
    svc: TaskService = Depends(get_task_service),
) -> TaskRead:
    """Create task in group (GROUP_ADMIN only)."""
    return await svc.create_task_for_group(
        group_id=group_id, task_in=task_in, current_user=current_user
    )


@router.get("", response_model=list[TaskRead], status_code=status.HTTP_200_OK)
async def search_tasks(
    search: TaskSearch = Depends(),
    sort: TaskSearch = Depends(),
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: UserModel = Depends(require_permissions_db("task:view")),
    svc: TaskService = Depends(get_task_service),
) -> list[TaskRead]:
    """Search all tasks."""
    return await svc.search_tasks(search=search, sort=sort, limit=limit, offset=offset)


@router.get("/me", response_model=list[TaskRead], status_code=status.HTTP_200_OK)
async def search_my_tasks(
    search: TaskSearch = Depends(),
    sort: TaskSearch = Depends(),
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: UserModel = Depends(require_permissions_db("task:view:own")),
    svc: TaskService = Depends(get_task_service),
) -> list[TaskRead]:
    """Get own tasks (GROUP_ADMIN)."""
    return await svc.search_my_tasks(
        current_user, search=search, sort=sort, limit=limit, offset=offset
    )


@router.get(
    "/groups/{group_id}", response_model=list[TaskRead], status_code=status.HTTP_200_OK
)
async def search_group_tasks(
    group_id: int,
    search: TaskSearch = Depends(),
    sort: TaskSearch = Depends(),
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: UserModel = Depends(require_permissions_db("task:view:group")),
    svc: TaskService = Depends(get_task_service),
) -> list[TaskRead]:
    """Get tasks in group (GROUP_ADMIN/MEMBER)."""
    return await svc.search_group_tasks(
        group_id=group_id,
        current_user=current_user,
        search=search,
        sort=sort,
        limit=limit,
        offset=offset,
    )


@router.get("/assigned", response_model=list[TaskRead], status_code=status.HTTP_200_OK)
async def search_assigned_tasks(
    search: TaskSearch = Depends(),
    sort: TaskSearch = Depends(),
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: UserModel = Depends(require_permissions_db("task:view")),
    svc: TaskService = Depends(get_task_service),
) -> list[TaskRead]:
    """Get assigned tasks (TASK_LEADER/MEMBER)."""
    return await svc.search_assigned_tasks(
        current_user, search=search, sort=sort, limit=limit, offset=offset
    )


@router.patch("/{task_id}", response_model=TaskRead, status_code=status.HTTP_200_OK)
async def update_my_task(
    task_id: int,
    task_in: TaskUpdate,
    current_user: UserModel = Depends(require_permissions_db("task:update:own")),
    svc: TaskService = Depends(get_task_service),
) -> TaskRead:
    """Update own task (GROUP_ADMIN)."""
    return await svc.update_my_task(
        task_id=task_id, task_in=task_in, current_user=current_user
    )


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_my_task(
    group_id: int,
    task_id: int,
    current_user: UserModel = Depends(require_permissions_db("task:delete:own")),
    svc: TaskService = Depends(get_task_service),
) -> None:
    """Soft-delete own task (GROUP_ADMIN)."""
    return await svc.delete_my_task(
        group_id=group_id, task_id=task_id, current_user=current_user
    )


@router.patch(
    "/{task_id}/status", response_model=TaskRead, status_code=status.HTTP_200_OK
)
async def update_status_task(
    task_id: int,
    status: TaskStatus,
    current_user: UserModel = Depends(require_permissions_db("task:update:status")),
    svc: TaskService = Depends(get_task_service),
) -> TaskRead:
    """Update task status (GROUP_ADMIN/TASK_LEADER)."""
    return await svc.update_status_task(
        task_id=task_id, status=status, current_user=current_user
    )


@router.post("/{task_id}/members/{user_id}", status_code=status.HTTP_201_CREATED)
async def add_user_to_task(
    task_id: int,
    user_id: int,
    current_user: UserModel = Depends(require_permissions_db("task:manage:group")),
    svc: TaskService = Depends(get_task_service),
) -> None:
    """Add user to task assignees (GROUP_ADMIN)."""
    return await svc.add_user_to_task(
        task_id=task_id, user_id=user_id, current_user=current_user
    )


@router.delete("/{task_id}/members/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_user_from_task(
    task_id: int,
    user_id: int,
    current_user: UserModel = Depends(require_permissions_db("task:manage:group")),
    svc: TaskService = Depends(get_task_service),
) -> None:
    """Remove user from task (GROUP_ADMIN)."""
    return await svc.remove_user_from_task(
        task_id=task_id, user_id=user_id, current_user=current_user
    )


@router.delete("/me/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def exit_task(
    task_id: int,
    current_user: UserModel = Depends(require_permissions_db("task:view")),
    svc: TaskService = Depends(get_task_service),
) -> None:
    """Exit task (self-remove, TASK_LEADER/MEMBER)."""
    return await svc.exit_task(task_id=task_id, current_user=current_user)
