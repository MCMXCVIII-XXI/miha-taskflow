"""Task service for task management and assignment operations.

This module provides the TaskService class for managing tasks,
including creation, updates, assignments, and join requests.

**Key Components:**
* `TaskService`: Main service class for task operations;
* `get_task_service`: FastAPI dependency injection factory.

**Dependencies:**
* `TaskRepository`: Task data access layer;
* `TaskAssigneeRepository`: Task assignee data access layer;
* `GroupRepository`: Group data access layer;
* `JoinRequestRepository`: Join request data access layer;
* `NotificationService`: Notification service;
* `XPService`: XP calculation service;
* `ElasticsearchIndexer`: Search index management.

**Usage Example:**
    ```python
    from app.service.task import get_task_service

    @router.post("/tasks")
    async def create_task(
        task_data: TaskCreate,
        task_svc: TaskService = Depends(get_task_service),
        current_user: User = Depends(get_current_user)
    ):
        return await task_svc.create_task_for_group(current_user, task_data)
    ```

**Notes:**
- Tasks belong to groups and can be assigned to users;
- Support for open join (auto-assign) or request-based join;
- XP awarded on task completion based on difficulty;
- Soft delete pattern (is_active=False).
"""

from datetime import UTC, datetime
from typing import Any

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.log import logging
from app.core.metrics import (
    METRICS,
)
from app.db import db_helper
from app.es import ElasticsearchIndexer, get_es_indexer
from app.models import JoinRequest as JoinRequestModel
from app.models import Task as TaskModel
from app.models import TaskAssignee
from app.models import User as UserModel
from app.models import UserGroup as UserGroupModel
from app.schemas import (
    JoinRequestRead,
    NotificationRead,
    TaskCreate,
    TaskRead,
    TaskUpdate,
)
from app.schemas.enum import (
    JoinRequestStatus,
    TaskSphere,
    TaskStatus,
)

from .base import GroupTaskBaseService
from .exceptions import group_exc, task_exc
from .notification import NotificationService, get_notification_service
from .transactions.task import TaskTransaction, get_task_transaction
from .utils import Indexer
from .xp import XPService, get_xp_service

logger = logging.get_logger(__name__)


class TaskService(GroupTaskBaseService):
    """Task management service for handling task lifecycle,
        assignments, and related operations.

    This service provides comprehensive task management functionality including:
    - Task creation, update, and deletion within groups
    - Task assignment and unassignment of users
    - Status management and workflow transitions
    - Search functionality with caching
    - Integration with XP/leveling system for completed tasks
    - Elasticsearch indexing for search functionality

    Attributes:
        _db (AsyncSession): SQLAlchemy async database session
        _task_repo (TaskRepository): Task repository for database operations
        _notification (NotificationService): Service for sending notifications
        _xp_service (XPService): XP calculation and management service
        _indexer (Indexer): Elasticsearch indexer wrapper

    Raises:
        task_exc.ForbiddenTaskAccess: When user doesn't have access to a task
        task_exc.TaskNotFound: When task is not found or inactive
        task_exc.TaskTitleConflict: When task title already exists in group
        task_exc.TaskStatusAlreadySet: When trying to set the same status
        task_exc.UserNotInTask: When user is not assigned to a task
        task_exc.UserAlreadyInTask: When user is already assigned to a task
        group_exc.GroupNotFound: When group is not found or inactive
    """

    def __init__(
        self,
        db: AsyncSession,
        indexer: ElasticsearchIndexer,
        notification_service: NotificationService,
        xp_service: XPService,
        task_transaction: TaskTransaction,
    ) -> None:
        super().__init__(db)
        self._notification = notification_service
        self._xp_service = xp_service
        self._indexer = Indexer(indexer)
        self._task_transaction = task_transaction

    async def _get_task_assignees(self, task_id: int) -> list[TaskAssignee]:
        """Get all assignees for a task.

        Args:
            task_id: ID of the task to get assignees for
                Type: int

        Returns:
            list[TaskAssignee]: List of assignees for the task

        Example:
            ```python
            assignees = await self._get_task_assignees(123)
            ```
        """
        result = await self._task_assignee_repo.by_task(
            task_id=task_id,
        )
        return list(result)

    async def _get_id_admin_groups(self, current_user: UserModel) -> list[int]:
        """
        Extract admin group IDs from current user.

        Details:
            Fast list comprehension from user.admin_groups relationship.
            Used for task/group access validation.

        Arguments:
            current_user (UserModel): Authenticated user

        Returns:
            list[int]: Group IDs where user is admin
        """
        group_ids = await self._group_repo.get_admin_group_ids(
            user_id=current_user.id,
            is_active=True,
        )
        return list(group_ids)

    async def _cleanup_assignee_role_if_no_tasks(self, user_id: int) -> None:
        """
        Clean up ASSIGNEE role if user has no active task assignees.

        Scans for any active task assignees for the user.
        If none found, deletes the ASSIGNEE role from the user.

        Arguments:
            user_id (int): Target user ID

        Raises:
            NotFoundError: If ASSIGNEE role cannot be found

        Example Usage:
            await self._cleanup_assignee_role_if_no_tasks()
        """
        remaining = await self._task_assignee_repo.find_many(user_id=user_id, limit=1)

        if not remaining:
            role_id = await self._get_role_id(self._role.ASSIGNEE.value)
            if role_id:
                user_role = await self._user_role_repo.get(
                    user_id=user_id, role_id=role_id
                )
                if user_role:
                    await self._db.delete(user_role)

    async def _get_active_task_assignee(
        self, task_id: int, user_id: int
    ) -> TaskAssignee:
        """
        Get active TaskAssignee with joined loads.
        Details:
            Validates task/user active status.
            joinedload(task, user) for relationship prefetch.
        Arguments:
            task_id (int): Target task ID
            user_id (int): Target user ID
        Returns:
            TaskAssignee: Active assignee record
        Raises:
            task_exc.UserNotInTask: No assignee or inactive
        Example Usage:
            assignee = await self._get_active_task_assignee(123, 456)
        """
        assignee = await self._task_assignee_repo.get(
            user_id=user_id, task_id=task_id, with_relations=True
        )
        if not assignee:
            raise task_exc.UserNotInTask(message="User is not in the task")
        if not assignee.task.is_active or not assignee.user.is_active:
            raise task_exc.UserNotInTask(message="Inactive task/user")
        return assignee

    async def _check_task_access(self, task_id: int, current_user: UserModel) -> None:
        """
        Validate user owns task's group.

        Details:
            Single IN query checks all user's admin groups at once.
            No N+1, no redundant checks.

        Args:
            task_id: Target task ID
            current_user: Authenticated user

        Raises:
            task_exc.ForbiddenTaskAccess: Task not in user's groups

        Example:
            await self._check_task_access(123, current_user)
        """
        group_ids = await self._get_id_admin_groups(current_user)

        task = await self._task_repo.get_by_group_ids(
            task_id=task_id, group_ids=group_ids, is_active=True
        )

        if not task:
            raise task_exc.ForbiddenTaskAccess(
                message="Task does not belong to your group"
            )

    async def _check_group_access(self, group_id: int, current_user: UserModel) -> None:
        """
        Validate user owns target group.

        Details:
            Fast list membership check on admin_groups.

        Arguments:
            group_id (int): Target group ID
            current_user (UserModel): Authenticated user

        Raises:
            group_exc.GroupNotFound: User not group admin

        Example Usage:
            await self._check_group_access(123, current_user)
        """
        if group_id not in await self._get_id_admin_groups(current_user):
            raise group_exc.GroupNotFound("Group not found or inactive")

    async def create_task_for_group(
        self, group_id: int, task_in: TaskCreate, current_user: UserModel
    ) -> TaskRead:
        """
        Create new task in user's group.

        Args:
            group_id: Target group ID
            task_in: Task creation payload
            current_user: Authenticated group admin

        Returns:
            Created task

        Raises:
            group_exc.GroupNotFound: Group inactive/not owned
            task_exc.TaskTitleConflict: Duplicate title in group
        """
        task = await self._task_transaction.create_task_for_group(
            group_id=group_id, task_in=task_in, current_user=current_user
        )

        METRICS.TASKS_TOTAL.labels(
            action="create",
            status="success",
            sphere=(
                task.spheres[0]["sphere"].value
                if hasattr(task, "spheres") and task.spheres
                else "general"
            ),
        ).inc()
        await self._indexer.index(task)
        await self._invalidate("tasks")
        await self._invalidate("rbac")

        logger.info(
            "Task created: id={task_id}, title={title}, \
                group_id={group_id}, owner_id={user_id}",
            task_id=task.id,
            title=task.title,
            group_id=group_id,
            user_id=current_user.id,
        )

        return TaskRead.model_validate(task)

    async def _get_active_group(self, group_id: int) -> UserGroupModel:
        """Get active group by ID.

        Args:
            group_id: ID of the group to retrieve
                Type: int

        Returns:
            UserGroupModel: Active group instance

        Raises:
            group_exc.GroupNotFound: When group not found or inactive

        Example:
            ```python
            group = await self._get_active_group(123)
            ```
        """
        group = await self._group_repo.get(
            id=group_id,
            is_active=True,
        )
        if not group:
            raise group_exc.GroupNotFound(message="Group not found or inactive")
        return group

    async def _process_task_completion_xp(
        self, task: TaskModel, current_user: UserModel
    ) -> None:
        """
        Process XP rewards for task completion.
        Args:
            task: Completed task
            current_user: User who completed the task
        """
        assignees = await self._get_task_assignees(task.id)
        story_points = task.difficulty.value if task.difficulty else 1
        actual_days = max(1, (datetime.now(UTC) - task.created_at).days)
        deadline_days = (task.deadline - task.created_at).days if task.deadline else 7
        for assignee in assignees:
            await self._process_assignee_xp(
                assignee, task, story_points, actual_days, deadline_days
            )

    async def _process_assignee_xp(
        self,
        assignee: TaskAssignee,
        task: TaskModel,
        story_points: int,
        actual_days: int,
        deadline_days: int,
    ) -> None:
        """
        Process XP for a single assignee on a completed task.
        Args:
            assignee: Task assignee
            task: Completed task
            story_points: Story points for the task
            actual_days: Days taken to complete
            deadline_days: Days until deadline
        """
        spheres: list[dict[str, Any]] = task.spheres if task.spheres is not None else []
        for sphere_data in spheres:
            sphere = TaskSphere[sphere_data["sphere"].upper()]
            skill = await self._xp_service.get_or_create_skill(assignee.user_id, sphere)
            streak = skill.streak
            xp_distribution = self._xp_service.calculate_task_xp(
                spheres=spheres,
                story_points=story_points,
                deadline_days=deadline_days,
                actual_days=actual_days,
                streak=streak,
            )
            xp = xp_distribution.get(sphere.value, 0)
            leveled_up, new_level = await self._xp_service.add_sphere_xp(
                assignee.user_id, sphere, xp
            )
            if leveled_up and self._notification:
                title = self._xp_service.get_title(sphere, new_level)
                await self._notification.notify_level_up(
                    user_id=assignee.user_id,
                    sphere=sphere.value,
                    new_level=new_level,
                    title=title,
                )

    async def _validate_task_status_update(
        self, task_id: int, status: TaskStatus
    ) -> TaskModel:
        """
        Validate that task exists and status is changing.

        Args:
            task_id: Target task ID
            status: New status to set
        Returns:
            Validated task model

        Raises:
            task_exc.TaskNotFound: Task not found or inactive
            task_exc.TaskStatusAlreadySet: Status is already set to this value
        """
        task = await self._task_repo.get(id=task_id, is_active=True)
        if not task:
            raise task_exc.TaskNotFound(message="Task not found or inactive")
        if task.status == status:
            raise task_exc.TaskStatusAlreadySet(
                message="Task status is already set to this value"
            )
        return task

    async def add_user_to_task(
        self,
        task_id: int,
        user_id: int,
        current_user: UserModel,
    ) -> None:
        """
        Add user as assignee to task (group admin only).

        Details:
            Duplicate assignee check + ownership validation.

        Arguments:
            task_id (int): Target task ID
            user_id (int): User to assign
            current_user (UserModel): Group admin

        Raises:
            task_exc.ForbiddenTaskAccess: Not owner
            task_exc.UserAlreadyInTask: Duplicate assignee

        Example Usage:
            await task_svc.add_user_to_task(123, 456, current_user)
        """
        await self._task_transaction.add_user_to_task(
            task_id=task_id, user_id=user_id, current_user=current_user
        )

        await self._invalidate("tasks")
        logger.info(
            "User added to task: user_id={user_id}, \
                task_id={task_id}, by_user_id={by_user_id}",
            user_id=user_id,
            task_id=task_id,
            by_user_id=current_user.id,
        )

    async def update_my_task(
        self,
        task_id: int,
        task_in: TaskUpdate,
        current_user: UserModel,
    ) -> TaskRead:
        """
        Update task owned by current user.

        Details:
            Partial updates via model_dump(exclude_unset=True).
            Task ownership validation + cache invalidation.

        Arguments:
            task_id (int): Target task ID
            task_in (TaskUpdate): Update payload
            current_user (UserModel): Task owner

        Returns:
            TaskRead: Updated task

        Raises:
            task_exc.ForbiddenTaskAccess: Not task owner
            task_exc.TaskNotFound: Task inactive/not found

        Example Usage:
            updated = await task_svc.update_my_task(123, task_update, current_user)
        """
        task = await self._task_transaction.update_my_task(
            task_id=task_id, task_in=task_in, current_user=current_user
        )

        METRICS.TASKS_TOTAL.labels(
            action="update",
            status="success",
            sphere=(
                task.spheres[0]["sphere"].value
                if hasattr(task, "spheres") and task.spheres
                else "general"
            ),
        ).inc()
        await self._indexer.index(task)
        await self._invalidate("tasks")
        logger.info(
            "Task updated: task_id={task_id}, fields={fields}, user_id={user_id}",
            task_id=task.id,
            fields=list(task_in.model_dump(exclude_unset=True).keys()),
            user_id=current_user.id,
        )
        return TaskRead.model_validate(task)

    async def delete_my_task(
        self,
        task_id: int,
        current_user: UserModel,
    ) -> None:
        """
        Soft-delete task owned by current user.
        Details:
            Sets task.is_active = False.
            Ownership validation + cache invalidation.
        Arguments:
            task_id (int): Target task ID
            current_user (UserModel): Task owner
        Raises:
            task_exc.ForbiddenTaskAccess: Not task owner
            task_exc.TaskNotFound: Task not found
        Example Usage:
            await task_svc.delete_my_task(123, current_user)
        """
        await self._task_transaction.delete_my_task(
            task_id=task_id, current_user=current_user
        )
        task = await self._task_repo.get(id=task_id)
        sphere = task.spheres[0]["sphere"].value if task and task.spheres else "general"
        METRICS.TASKS_TOTAL.labels(
            action="delete", status="deleted", sphere=sphere
        ).inc()
        await self._indexer.delete({"type": "task", "id": task_id})
        await self._invalidate("tasks")

    async def update_status_task(
        self,
        task_id: int,
        status: TaskStatus,
        current_user: UserModel,
    ) -> TaskRead:
        """
        Update task status (group admin only).
        Validates status change (no duplicate) and handles XP calculation
        when task is marked as DONE.
        Args:
            task_id: Target task ID
            status: New status enum
            current_user: Group admin
        Returns:
            Updated task
        Raises:
            task_exc.TaskNotFound: Task inactive
            task_exc.TaskStatusAlreadySet: No change
        """
        task = await self._task_transaction.update_status_task(
            task_id=task_id, status=status, current_user=current_user
        )
        old_status = task.status
        METRICS.TASKS_TOTAL.labels(
            action="update",
            status="success",
            sphere=(
                task.spheres[0]["sphere"].value
                if hasattr(task, "spheres") and task.spheres
                else "general"
            ),
        ).inc()
        await self._invalidate("tasks")

        if status == TaskStatus.DONE and task.spheres:
            await self._process_task_completion_xp(task, current_user)
        logger.info(
            "Task status updated: task_id={task_id}, \
                {old_status} -> {new_status}, user_id={user_id}",
            task_id=task.id,
            old_status=old_status.value,
            new_status=status.value,
            user_id=current_user.id,
        )
        return TaskRead.model_validate(task)

    async def remove_user_from_task(
        self,
        task_id: int,
        user_id: int,
        current_user: UserModel,
    ) -> None:
        """
        Remove user assignee from task (group admin only).

        Details:
            Uses _get_active_task_assignee for validation.

        Arguments:
            task_id (int): Target task ID
            user_id (int): User to remove
            current_user (UserModel): Group admin

        Raises:
            task_exc.ForbiddenTaskAccess: Not owner
            task_exc.UserNotInTask: No active assignee

        Example Usage:
            await task_svc.remove_user_from_task(123, 456, current_user)
        """
        await self._task_transaction.remove_user_from_task(
            task_id=task_id, user_id=user_id, current_user=current_user
        )
        task = await self._task_repo.get(id=task_id)
        sphere = task.spheres[0]["sphere"].value if task and task.spheres else "general"

        METRICS.TASKS_TOTAL.labels(
            action="remove_assignee", status="success", sphere=sphere
        ).inc()
        await self._invalidate("tasks")

        logger.info(
            "User removed from task: user_id={user_id}, \
                task_id={task_id}, by_user_id={by_user_id}",
            user_id=user_id,
            task_id=task_id,
            by_user_id=current_user.id,
        )

    async def get_task_join_requests(
        self, task_id: int, current_user: UserModel
    ) -> list[JoinRequestRead]:
        task = await self._task_repo.get(
            id=task_id,
            is_active=True,
        )
        if not task:
            raise task_exc.TaskNotFound(message="Task not found")

        group = await self._group_repo.get(
            id=task.group_id,
            is_active=True,
        )
        if group and group.admin_id != current_user.id:
            raise task_exc.TaskAccessDenied(
                message="Only group admin can view join requests"
            )

        requests = await self._join_repo.find_many(
            task_id=task_id,
            status=JoinRequestStatus.PENDING,
        )
        return [JoinRequestRead.model_validate(request) for request in requests]

    async def approve_task_join_request(
        self, request_id: int, current_user: UserModel
    ) -> NotificationRead:
        """
        Approve a join request for a task.

        Args:
            request_id: ID of the join request to approve
            current_user: Group admin approving the request

        Returns:
            Notification for the approval
        """
        notification = await self._task_transaction.approve_task_join_request(
            request_id=request_id, current_user=current_user
        )
        task = await self._task_repo.get(id=request_id)
        sphere = task.spheres[0]["sphere"].value if task and task.spheres else "general"
        METRICS.TASKS_TOTAL.labels(
            action="approve_join", status="success", sphere=sphere
        ).inc()
        return NotificationRead.model_validate(notification)

    async def _get_join_request(self, request_id: int) -> JoinRequestModel:
        """Get join request by ID with validation.

        Args:
            request_id: ID of the join request
                Type: int

        Returns:
            JoinRequestModel: Join request instance

        Raises:
            task_exc.JoinRequestNotFound: When request not found

        Example:
            ```python
            request = await self._get_join_request(123)
            ```
        """
        request = await self._join_repo.get(id=request_id)
        if not request:
            raise task_exc.JoinRequestNotFound(message="Join request not found")
        return request

    async def _get_task_for_request(self, request: JoinRequestModel) -> TaskModel:
        """Get task associated with join request.

        Args:
            request: Join request to get task for
                Type: JoinRequestModel

        Returns:
            TaskModel: Associated task instance

        Raises:
            task_exc.TaskNotFound: When task not found
        """
        task = await self._task_repo.get(
            id=request.task_id,
            is_active=True,
        )
        if not task or not task.group_id:
            raise task_exc.TaskNotFound(message=f"Task {request.task_id} not found")
        return task

    async def _get_group_for_task(self, task: TaskModel) -> UserGroupModel:
        """Get group associated with task.

        Args:
            task: Task to get group for
                Type: TaskModel

        Returns:
            UserGroupModel: Associated group instance
        """
        group = await self._group_repo.get(
            id=task.group_id,
            is_active=True,
        )
        if not group:
            raise group_exc.GroupNotFound(message=f"Group {task.group_id} not found")
        return group

    async def _validate_join_request_approval(
        self, request: JoinRequestModel, task: TaskModel, current_user: UserModel
    ) -> None:
        """Validate that user can approve this join request.

        Checks that:
        - Request is pending
        - User is group admin

        Args:
            request: Join request to validate
                Type: JoinRequestModel
            task: Associated task
                Type: TaskModel
            current_user: User attempting to approve
                Type: UserModel

        Returns:
            None

        Raises:
            task_exc.TaskAccessDenied: When user cannot approve
        """
        if request.status != JoinRequestStatus.PENDING:
            raise task_exc.JoinRequestAlreadyHandled(
                message="Join request already processed"
            )

    async def reject_task_join_request(
        self, task_id: int, request_id: int, current_user: UserModel
    ) -> NotificationRead:
        """
        Reject a join request for a task.

        Args:
            task_id: ID of the task (from path parameter)
            request_id: ID of the join request to reject
            current_user: Group admin rejecting the request

        Returns:
            Notification for the rejection
        """
        notification = await self._task_transaction.reject_task_join_request(
            task_id=task_id,
            request_id=request_id,
            current_user=current_user,
        )
        task = await self._task_repo.get(id=task_id)
        sphere = task.spheres[0]["sphere"].value if task and task.spheres else "general"
        METRICS.TASKS_TOTAL.labels(
            action="reject_join", status="rejected", sphere=sphere
        ).inc()
        return NotificationRead.model_validate(notification)

    async def join_task(self, task_id: int, current_user: UserModel) -> None:
        """
        Join a task by either direct assignment or creating a join request.

        Args:
            task_id: ID of the task to join
            current_user: User joining the task
        """
        await self._task_transaction.join_task(
            task_id=task_id, current_user=current_user
        )
        task = await self._task_repo.get(id=task_id)
        sphere = task.spheres[0]["sphere"].value if task and task.spheres else "general"
        METRICS.TASKS_TOTAL.labels(
            action="join_task", status="success", sphere=sphere
        ).inc()

    async def exit_task(self, task_id: int, current_user: UserModel) -> None:
        """
        Remove self from task assignees.

        User-initiated task exit (no admin rights needed).

        Args:
            task_id: Target task ID
            current_user: User exiting task

        Raises:
            task_exc.UserNotInTask: User not assigned
        """
        await self._task_transaction.exit_task(
            task_id=task_id, current_user=current_user
        )
        task = await self._task_repo.get(id=task_id)
        sphere = task.spheres[0]["sphere"].value if task and task.spheres else "general"
        METRICS.TASKS_TOTAL.labels(
            action="exit_task", status="success", sphere=sphere
        ).inc()
        await self._invalidate("tasks")

    async def bulk_index_tasks(self, tasks: list[TaskModel]) -> dict[str, Any]:
        """Bulk index multiple tasks to Elasticsearch.

        Args:
            tasks: List of tasks to index
                Type: list[TaskModel]

        Returns:
            dict[str, Any]: Result of bulk indexing

        Example:
            ```python
            result = await task_svc.bulk_index_tasks(tasks)
            ```
        """
        return await self._indexer.bulk_index_tasks(tasks)


def get_task_service(
    db: AsyncSession = Depends(db_helper.get_session),
    indexer: ElasticsearchIndexer = Depends(get_es_indexer),
    notification_service: NotificationService = Depends(get_notification_service),
    xp_service: XPService = Depends(get_xp_service),
    task_transaction: TaskTransaction = Depends(get_task_transaction),
) -> TaskService:
    """
    FastAPI dependency factory for TaskService injection.

    Automatically creates TaskService with database session.
    Follows FastAPI service layer isolation pattern.

    Args:
        db: Database session from db_helper.get_session
        indexer: Elasticsearch indexer from get_es_indexer
        notification_service: Notification service instance
            from get_notification_service
        xp_service: XP service instance from get_xp_service
        outbox_service: Outbox service instance from get_outbox_service

    Returns:
        Fresh TaskService instance with injected dependencies
    """
    return TaskService(
        db=db,
        indexer=indexer,
        notification_service=notification_service,
        xp_service=xp_service,
        task_transaction=task_transaction,
    )
