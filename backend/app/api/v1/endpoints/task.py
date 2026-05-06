from fastapi import APIRouter, Depends, status

from app.core.permission import require_permissions_db
from app.models import User as UserModel
from app.schemas import (
    JoinRequestRead,
    NotificationRead,
    TaskCreate,
    TaskRead,
    TaskUpdate,
)
from app.schemas.enum import (
    TaskStatus,
)
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
    current_user: UserModel = Depends(require_permissions_db("task:create:own")),
    svc: TaskService = Depends(get_task_service),
) -> TaskRead:
    """Create a new task within a specific group."""
    return await svc.create_task_for_group(
        group_id=group_id, task_in=task_in, current_user=current_user
    )


@router.get(
    "/{task_id}/join-requests",
    response_model=list[JoinRequestRead],
    status_code=status.HTTP_200_OK,
)
async def get_task_join_requests(
    task_id: int,
    current_user: UserModel = Depends(require_permissions_db("task:view:group")),
    svc: TaskService = Depends(get_task_service),
) -> list[JoinRequestRead]:
    """Get join requests for a specific task."""
    return await svc.get_task_join_requests(task_id, current_user)


@router.post(
    "/{task_id}/join-requests/{request_id}/approve",
    response_model=NotificationRead,
    status_code=status.HTTP_200_OK,
)
async def approve_task_join_request(
    request_id: int,
    current_user: UserModel = Depends(require_permissions_db("task:update:own")),
    svc: TaskService = Depends(get_task_service),
) -> NotificationRead:
    """Approve a join request for a task."""
    return await svc.approve_task_join_request(request_id, current_user)


@router.post(
    "/{task_id}/join-requests/{request_id}/reject",
    response_model=NotificationRead,
    status_code=status.HTTP_200_OK,
)
async def reject_task_join_request(
    task_id: int,
    request_id: int,
    current_user: UserModel = Depends(require_permissions_db("task:update:own")),
    svc: TaskService = Depends(get_task_service),
) -> NotificationRead:
    """Reject a join request for a task."""
    return await svc.reject_task_join_request(task_id, request_id, current_user)


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
    task_id: int,
    current_user: UserModel = Depends(require_permissions_db("task:exit:own")),
    svc: TaskService = Depends(get_task_service),
) -> None:
    """Remove self from a task assignment."""
    return await svc.delete_my_task(task_id=task_id, current_user=current_user)


@router.patch(
    "/{task_id}/status", response_model=TaskRead, status_code=status.HTTP_200_OK
)
async def update_status_task(
    task_id: int,
    new_status: TaskStatus,
    current_user: UserModel = Depends(require_permissions_db("task:update:status")),
    svc: TaskService = Depends(get_task_service),
) -> TaskRead:
    """Update task status (GROUP_ADMIN/TASK_LEADER)."""
    return await svc.update_status_task(
        task_id=task_id, status=new_status, current_user=current_user
    )


@router.post("/{task_id}/members/{user_id}", status_code=status.HTTP_201_CREATED)
async def add_user_to_task(
    task_id: int,
    user_id: int,
    current_user: UserModel = Depends(require_permissions_db("task:add:own")),
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
    current_user: UserModel = Depends(require_permissions_db("task:remove:own")),
    svc: TaskService = Depends(get_task_service),
) -> None:
    """Remove user from task (GROUP_ADMIN)."""
    return await svc.remove_user_from_task(
        task_id=task_id, user_id=user_id, current_user=current_user
    )


@router.post("/{task_id}/join", status_code=status.HTTP_201_CREATED)
async def join_task(
    task_id: int,
    current_user: UserModel = Depends(require_permissions_db("task:join:any")),
    svc: TaskService = Depends(get_task_service),
) -> None:
    """Join task (self-add, TASK_LEADER/MEMBER)."""
    return await svc.join_task(task_id=task_id, current_user=current_user)


@router.delete("/{task_id}/exit", status_code=status.HTTP_204_NO_CONTENT)
async def exit_task(
    task_id: int,
    current_user: UserModel = Depends(require_permissions_db("task:exit:assignee")),
    svc: TaskService = Depends(get_task_service),
) -> None:
    """Exit task (self-remove, TASK_LEADER/MEMBER)."""
    return await svc.exit_task(task_id=task_id, current_user=current_user)
