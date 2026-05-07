from fastapi import APIRouter, Depends, Query, status

from app.core.permission import require_permissions_db
from app.examples.task_examples import (
    TaskExamples,
)
from app.models import User as UserModel
from app.schemas import (
    JoinRequestRead,
    NotificationRead,
    TaskCreate,
    TaskRead,
    TaskUpdate,
)
from app.schemas.enum import TaskStatus
from app.service import TaskService, get_task_service

router = APIRouter(tags=["tasks"])


@router.post(
    "/groups/{group_id}",
    response_model=TaskRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create task",
    description="""
    Create a new task within a specific group.

    **Permissions required:** GROUP_ADMIN or OWNER

    **Request body:**
    - `title` (required, 1-200 chars): Task title
    - `description` (optional, max 1000 chars): Task description
    - `priority` (optional): HIGH, MEDIUM, LOW (default: MEDIUM)
    - `difficulty` (optional): EXPERT, HARD, MEDIUM, EASY
    - `deadline` (optional): ISO 8601 datetime
    - `spheres` (optional): List of task spheres

    **Returns:** Created task with ID and all fields.

    **Side effects:** Creates outbox event for ES indexing.
    """,
    responses={
        201: {
            "description": "Task created successfully",
            "content": {"application/json": {"example": TaskExamples.CREATE_SUCCESS}},
        },
        403: {"description": "Permission denied"},
        404: {"description": "Group not found"},
    },
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
    summary="Get task join requests",
    response_model=list[JoinRequestRead],
    description="""
    Get join requests for a specific task.

    **Permissions required:** GROUP_ADMIN or TASK_LEADER
    """,
    responses={
        200: {
            "description": "Join requests retrieved",
            "content": {"application/json": {"example": []}},
        },
    },
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
    summary="Approve join request",
    description="""
    Approve a join request for a task.

    **Permissions required:** TASK_LEADER or GROUP_ADMIN

    **Side effects:** User is added as assignee.
    """,
    responses={
        200: {"description": "Request approved"},
    },
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
    summary="Reject join request",
    description="""
    Reject a join request for a task.

    **Permissions required:** TASK_LEADER or GROUP_ADMIN
    """,
    responses={
        200: {"description": "Request rejected"},
    },
)
async def reject_task_join_request(
    task_id: int,
    request_id: int,
    current_user: UserModel = Depends(require_permissions_db("task:update:own")),
    svc: TaskService = Depends(get_task_service),
) -> NotificationRead:
    """Reject a join request for a task."""
    return await svc.reject_task_join_request(task_id, request_id, current_user)


@router.patch(
    "/{task_id}",
    response_model=TaskRead,
    summary="Update task",
    description="""
    Update task details.

    **Permissions required:** TASK_LEADER or GROUP_ADMIN

    **Request body (all optional):**
    - `title`: Task title
    - `description`: Task description
    - `priority`: HIGH, MEDIUM, LOW
    - `difficulty`: EXPERT, HARD, MEDIUM, EASY
    - `visibility`: PUBLIC, PRIVATE
    """,
    responses={
        200: {
            "description": "Task updated",
            "content": {"application/json": {"example": TaskExamples.UPDATE_SUCCESS}},
        },
    },
)
async def update_my_task(
    task_id: int,
    task_in: TaskUpdate,
    current_user: UserModel = Depends(require_permissions_db("task:update:own")),
    svc: TaskService = Depends(get_task_service),
) -> TaskRead:
    """Update task details."""
    return await svc.update_my_task(
        task_id=task_id, task_in=task_in, current_user=current_user
    )


@router.delete(
    "/{task_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete task",
    description="""
    Soft-delete a task.

    **Permissions required:** GROUP_ADMIN or TASK_CREATOR

    **Side effects:** Task is marked as inactive.
    """,
    responses={
        204: {"description": "Task deleted"},
    },
)
async def delete_my_task(
    task_id: int,
    current_user: UserModel = Depends(require_permissions_db("task:exit:own")),
    svc: TaskService = Depends(get_task_service),
) -> None:
    """Soft-delete a task."""
    return await svc.delete_my_task(task_id=task_id, current_user=current_user)


@router.patch(
    "/{task_id}/status",
    response_model=TaskRead,
    summary="Update task status",
    description="""
    Update task status.

    **Permissions required:** TASK_LEADER, TASK_ASSIGNEE, or GROUP_ADMIN

    **Status values:**
    - PENDING: Task created, not started
    - IN_PROGRESS: Task is being worked on
    - DONE: Task completed
    - CANCELLED: Task cancelled

    **Side effects:**
    - Completing task (→ DONE) awards XP to assignee
    - Creates outbox event for ES indexing
    """,
    responses={
        200: {
            "description": "Status updated",
            "content": {"application/json": {"example": TaskExamples.STATUS_UPDATE}},
        },
    },
)
async def update_status_task(
    task_id: int,
    new_status: TaskStatus = Query(..., description="New task status"),
    current_user: UserModel = Depends(require_permissions_db("task:update:status")),
    svc: TaskService = Depends(get_task_service),
) -> TaskRead:
    """Update task status."""
    return await svc.update_status_task(
        task_id=task_id, status=new_status, current_user=current_user
    )


@router.post(
    "/{task_id}/join",
    status_code=status.HTTP_201_CREATED,
    summary="Join task",
    description="""
    Request to join a task as assignee.

    **Permissions required:** GROUP_MEMBER

    **Note:** Requires task to have join_policy allowing requests.
    """,
    responses={
        201: {"description": "Join request created"},
    },
)
async def join_task(
    task_id: int,
    current_user: UserModel = Depends(require_permissions_db("task:join:any")),
    svc: TaskService = Depends(get_task_service),
) -> None:
    """Request to join a task."""
    return await svc.join_task(task_id=task_id, current_user=current_user)


@router.delete(
    "/{task_id}/exit",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Exit task",
    description="""
    Exit from a task (remove self as assignee).

    **Permissions required:** TASK_ASSIGNEE

    **Note:** Task creator cannot exit until task is deleted.
    """,
    responses={
        204: {"description": "Exited task successfully"},
    },
)
async def exit_task(
    task_id: int,
    current_user: UserModel = Depends(require_permissions_db("task:exit:assignee")),
    svc: TaskService = Depends(get_task_service),
) -> None:
    """Exit from a task."""
    return await svc.exit_task(task_id=task_id, current_user=current_user)


@router.post(
    "/{task_id}/members/{user_id}",
    status_code=status.HTTP_201_CREATED,
    summary="Assign user to task",
    description="""
    Manually assign a user to a task.

    **Permissions required:** TASK_LEADER or GROUP_ADMIN

    **Side effects:** User receives notification.
    """,
    responses={
        201: {"description": "User assigned"},
        400: {"description": "User already assigned"},
    },
)
async def add_user_to_task(
    task_id: int,
    user_id: int,
    current_user: UserModel = Depends(require_permissions_db("task:add:own")),
    svc: TaskService = Depends(get_task_service),
) -> None:
    """Assign user to task."""
    return await svc.add_user_to_task(
        task_id=task_id, user_id=user_id, current_user=current_user
    )


@router.delete(
    "/{task_id}/members/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Unassign user from task",
    description="""
    Remove a user from task assignees.

    **Permissions required:** TASK_LEADER or GROUP_ADMIN
    """,
    responses={
        204: {"description": "User unassigned"},
    },
)
async def remove_user_from_task(
    task_id: int,
    user_id: int,
    current_user: UserModel = Depends(require_permissions_db("task:remove:own")),
    svc: TaskService = Depends(get_task_service),
) -> None:
    """Remove user from task."""
    return await svc.remove_user_from_task(
        task_id=task_id, user_id=user_id, current_user=current_user
    )
