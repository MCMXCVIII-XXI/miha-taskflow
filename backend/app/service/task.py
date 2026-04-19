from datetime import UTC, datetime
from typing import Any

from fastapi import Depends
from sqlalchemy import Select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.log import logging
from app.core.metrics import (
    SEARCH_QUERIES_TOTAL,
    TASKS_TOTAL,
)
from app.db import db_helper
from app.es import ElasticsearchIndexer, get_es_indexer
from app.models import JoinRequest as JoinRequestModel
from app.models import Task as TaskModel
from app.models import TaskAssignee
from app.models import User as UserModel
from app.models import UserGroup as UserGroupModel
from app.models import UserRole as UserRoleModel
from app.models.group import UserGroupMembership as UserGroupMembershipModel
from app.schemas import (
    JoinRequestRead,
    NotificationRead,
    TaskCreate,
    TaskRead,
    TaskSearch,
    TaskUpdate,
)
from app.schemas.enum import (
    JoinPolicy,
    JoinRequestStatus,
    OutboxEventType,
    TaskSphere,
    TaskStatus,
)

from .base import GroupTaskBaseService
from .exceptions import group_exc, task_exc
from .notification import NotificationService, get_notification_service
from .outbox import OutboxService
from .search import task_search
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
        _task_queries (TaskQueries): Task-specific optimized query builders
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
    ) -> None:
        super().__init__(db)
        self._notification = notification_service
        self._xp_service = xp_service
        self._indexer = Indexer(indexer)

    async def _get_task_assignees(self, task_id: int) -> list[TaskAssignee]:
        result = await self._db.scalars(
            self._task_assignee_queries.get_task_assignee(task_id=task_id)
        )
        return list(result.all())

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
        group_ids = await self._db.scalars(
            self._group_queries.by_admin_groups_get_id(
                user_id=current_user.id, is_active=True
            )
        )
        return list(group_ids.all())

    async def _check_task_access(self, task_id: int, current_user: UserModel) -> None:
        """
        Validate user owns task's group.

        Details:
            Checks task.group_id in user's admin_groups.
            Single scalar query via TaskQueries.by_id.

        Arguments:
            task_id (int): Target task ID
            current_user (UserModel): Authenticated user

        Raises:
            task_exc.ForbiddenTaskAccess: Task not in user's groups

        Example Usage:
            await self._check_task_access(123, current_user)
        """
        group_ids = await self._get_id_admin_groups(current_user)

        task_in_user_group = await self._db.scalar(
            self._task_queries.get_task(id=task_id, is_active=True).where(
                TaskModel.group_id.in_(group_ids)
            )
        )
        if not task_in_user_group:
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
        await self._check_group_access(group_id, current_user)
        await self._validate_task_title_unique(group_id, task_in.title, current_user)
        group = await self._get_active_group(group_id)

        task = await self._create_task_model(task_in, group)
        user_role = await self._create_user_role(task, current_user, group_id)

        self._db.add(task)
        self._db.add(user_role)
        await self._db.flush()
        task_id = task.id

        assignee = TaskAssignee(user_id=current_user.id, task_id=task.id)
        self._db.add(assignee)

        outbox_service = OutboxService(self._db)
        await outbox_service.publish(
            event_type=OutboxEventType.CREATED,
            entity_type="task",
            entity_id=task_id,
        )

        await self._db.commit()
        TASKS_TOTAL.labels(
            action="create",
            status="success",
            sphere=task.sphere.value
            if hasattr(task, "sphere") and task.sphere
            else "general",
        ).inc()
        await self._db.refresh(task)

        await self._index_task_and_invalidate_cache(task)

        logger.info(
            "Task created: id={task_id}, title={title}, \
                group_id={group_id}, owner_id={user_id}",
            task_id=task.id,
            title=task.title,
            group_id=group_id,
            user_id=current_user.id,
        )

        return TaskRead.model_validate(task)

    async def _validate_task_title_unique(
        self, group_id: int, title: str, current_user: UserModel
    ) -> None:
        """Validate that task title is unique within the group."""
        result = await self._db.scalars(
            self._task_queries.get_task(group_id=group_id, title=title, is_active=True)
        )
        if result.first():
            logger.warning(
                "Task creation failed: duplicate title {title} \
                    in group {group_id} by user {user_id}",
                title=title,
                group_id=group_id,
                user_id=current_user.id,
            )
            raise task_exc.TaskTitleConflict(
                message="Task with this title already exists"
            )

    async def _get_active_group(self, group_id: int) -> UserGroupModel:
        """Get active group by ID."""
        group = await self._db.scalar(
            self._group_queries.get_group(id=group_id, is_active=True)
        )
        if not group:
            raise group_exc.GroupNotFound(message="Group not found or inactive")
        return group

    async def _create_task_model(
        self, task_in: TaskCreate, group: UserGroupModel
    ) -> TaskModel:
        """Create task model from input data."""
        return TaskModel(
            title=task_in.title,
            description=task_in.description,
            priority=task_in.priority,
            group_id=group.id,
        )

    async def _create_user_role(
        self, task: TaskModel, current_user: UserModel, group_id: int
    ) -> UserRoleModel:
        """Create user role for task owner."""
        role_id = await self._get_role_id(self._role.GROUP_ADMIN.value)
        return UserRoleModel(
            task_id=task.id,
            user_id=current_user.id,
            role_id=role_id,
            group_id=group_id,
        )

    async def _index_task_and_invalidate_cache(self, task: TaskModel) -> None:
        """Index task in Elasticsearch and invalidate caches."""
        await self._indexer.index(task)
        await self._invalidate("tasks")
        await self._invalidate("rbac")

    @task_search
    async def search_tasks(
        self,
        search: TaskSearch,
        sort: TaskSearch,
        limit: int,
        offset: int,
        **kwargs: Any,
    ) -> Select[tuple[TaskModel]]:
        """
        Base query for all active tasks search/filter/sort.

        Details:
            @task_search decorator applies TaskSearch filters/sorting.
            Only active tasks (is_active=True).

        Returns:
            Select[tuple[TaskModel]]: Base query for search decorator.

        Example Usage:
            ```python
            @router.get("/tasks/")
            async def search_tasks(
                search: TaskSearch = Depends(),
                task_svc: TaskService = Depends(get_task_service)
            ):
                return await task_svc.search_tasks(search=search)
            ```
        """
        SEARCH_QUERIES_TOTAL.labels(entity="task", status="success").inc()
        return self._task_queries.get_task(is_active=True)

    @task_search
    async def search_my_tasks(
        self,
        search: TaskSearch,
        sort: TaskSearch,
        limit: int,
        offset: int,
        current_user: UserModel,
    ) -> Select[tuple[TaskModel]]:
        """
        Search tasks owned by current user (group admin).

        Details:
            Filters tasks by user's admin_groups.
            @task_search decorator applies additional filters.

        Arguments:
            current_user (UserModel): Authenticated group admin

        Returns:
            Select[tuple[TaskModel]]: Owner's tasks query

        Example Usage:
            tasks = await task_svc.search_my_tasks(current_user)
        """
        SEARCH_QUERIES_TOTAL.labels(entity="my_tasks", status="success").inc()
        group_ids = await self._get_id_admin_groups(current_user)
        return self._task_queries.by_owner(group_ids, is_active=True)

    @task_search
    async def search_group_tasks(
        self,
        group_id: int,
        search: TaskSearch,
        sort: TaskSearch,
        limit: int,
        offset: int,
        current_user: UserModel,
    ) -> Select[tuple[TaskModel]]:
        """
        Search tasks in specific group.

        Details:
            Group access validation + @task_search filtering.

        Arguments:
            group_id (int): Target group ID
            current_user (UserModel): Group admin

        Returns:
            Select[tuple[TaskModel]]: Group tasks query

        Example Usage:
            group_tasks = await task_svc.search_group_tasks(123, current_user)
        """
        SEARCH_QUERIES_TOTAL.labels(entity="group_tasks", status="success").inc()
        await self._check_group_access(group_id, current_user)
        return self._task_queries.get_task(group_id=group_id, is_active=True)

    @task_search
    async def search_assigned_tasks(
        self,
        search: TaskSearch,
        sort: TaskSearch,
        limit: int,
        offset: int,
        current_user: UserModel,
    ) -> Select[tuple[TaskModel]]:
        """
        Search tasks assigned to current user.

        Details:
            Tasks where user is TaskAssignee.
            @task_search decorator applies filtering.

        Arguments:
            current_user (UserModel): Authenticated user

        Returns:
            Select[tuple[TaskModel]]: Assigned tasks query

        Example Usage:
            assigned = await task_svc.search_assigned_tasks(current_user)
        """
        SEARCH_QUERIES_TOTAL.labels(entity="assigned_tasks", status="success").inc()
        return self._task_queries.by_assigned(current_user.id, is_active=True)

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
        await self._check_task_access(task_id, current_user)

        task = await self._db.scalar(
            self._task_queries.get_task(id=task_id, is_active=True)
        )

        if not task:
            raise task_exc.TaskNotFound(message="Task not found or inactive")

        for field, value in task_in.model_dump(exclude_unset=True).items():
            setattr(task, field, value)

        outbox_service = OutboxService(self._db)
        await outbox_service.publish(
            event_type=OutboxEventType.UPDATED,
            entity_type="task",
            entity_id=task_id,
        )

        await self._db.commit()
        TASKS_TOTAL.labels(action="update", status="success").inc()
        await self._db.refresh(task)
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
        await self._check_task_access(task_id, current_user)

        task = await self._db.scalar(
            self._task_queries.get_task(id=task_id, is_active=True)
        )

        if not task:
            raise task_exc.TaskNotFound(message="Task not found")

        task.is_active = False

        outbox_service = OutboxService(self._db)
        await outbox_service.publish(
            event_type=OutboxEventType.DELETED,
            entity_type="task",
            entity_id=task_id,
        )

        await self._db.commit()
        TASKS_TOTAL.labels(action="delete", status="deleted").inc()
        await self._indexer.delete({"type": "task", "id": task_id})
        await self._invalidate("tasks")

        logger.info(
            "Task deleted: task_id={task_id}, user_id={user_id}",
            task_id=task.id,
            user_id=current_user.id,
        )

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
        task = await self._validate_task_status_update(task_id, status)
        old_status = task.status
        task.status = status

        outbox_service = OutboxService(self._db)
        await outbox_service.publish(
            event_type=OutboxEventType.UPDATED,
            entity_type="task",
            entity_id=task_id,
            payload={
                "old_status": old_status.value,
                "new_status": status.value,
            },
        )

        await self._db.commit()
        TASKS_TOTAL.labels(
            action="update",
            status="success",
            sphere=task.sphere.value
            if hasattr(task, "sphere") and task.sphere
            else "general",
        ).inc()
        await self._db.refresh(task)
        await self._invalidate("tasks")

        # Handle XP calculation when task is completed
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
        task = await self._db.scalar(
            self._task_queries.get_task(id=task_id, is_active=True)
        )

        if not task:
            raise task_exc.TaskNotFound(message="Task not found or inactive")
        if task.status == status:
            raise task_exc.TaskStatusAlreadySet(
                message="Task status is already set to this value"
            )
        return task

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
        assignee = await self._db.scalar(
            self._task_assignee_queries.get_task_assignee(
                user_id=user_id, task_id=task_id, with_relations=True
            )
        )

        if not assignee:
            raise task_exc.UserNotInTask(message="User is not in the task")

        if not assignee.task.is_active or not assignee.user.is_active:
            raise task_exc.UserNotInTask(message="Inactive task/user")

        return assignee

    async def _cleanup_assignee_role_if_no_tasks(self, user_id: int) -> None:
        remaining = await self._db.scalar(
            self._task_assignee_queries.get_task_assignee(user_id=user_id).limit(1)
        )
        if not remaining:
            role_id = await self._get_role_id(self._role.ASSIGNEE.value)
            if role_id:
                user_role = await self._db.scalar(
                    self._user_role_queries.get_user_role(
                        user_id=user_id, role_id=role_id
                    )
                )
                if user_role:
                    await self._db.delete(user_role)

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
        await self._check_task_access(task_id, current_user)

        task_assignee = await self._db.scalar(
            self._task_assignee_queries.get_task_assignee(
                user_id=user_id, task_id=task_id
            )
        )

        if task_assignee:
            logger.warning(
                "Add user to task failed: user {user_id} already in task {task_id}",
                user_id=user_id,
                task_id=task_id,
            )
            raise task_exc.UserAlreadyInTask(message="User is already in the task")

        assignee = TaskAssignee(task_id=task_id, user_id=user_id)
        self._db.add(assignee)
        await self._db.commit()
        TASKS_TOTAL.labels(action="add_assignee", status="success").inc()
        await self._invalidate("tasks")

        if self._notification:
            task = await self._db.scalar(
                self._task_queries.get_task(id=task_id, is_active=True)
            )
            if task:
                await self._notification.notify_task_invite(
                    inviter_id=current_user.id,
                    invitee_id=user_id,
                    task_id=task_id,
                    task_title=task.title,
                )

        logger.info(
            "User added to task: user_id={user_id}, \
                task_id={task_id}, by_user_id={by_user_id}",
            user_id=user_id,
            task_id=task_id,
            by_user_id=current_user.id,
        )

    async def _add_member_directly(self, task_id: int, user_id: int) -> None:
        """Add user directly to task without admin checks (for free join)."""
        existing = await self._db.scalar(
            self._task_assignee_queries.get_task_assignee(
                user_id=user_id, task_id=task_id
            )
        )
        if existing:
            raise task_exc.UserAlreadyInTask(
                message="User is already assigned to this task"
            )

        assignee = TaskAssignee(task_id=task_id, user_id=user_id)
        self._db.add(assignee)
        await self._db.commit()
        TASKS_TOTAL.labels(action="join_direct").inc()
        await self._invalidate("tasks")

        logger.info(
            "User joined task directly: user_id={user_id}, task_id={task_id}",
            user_id=user_id,
            task_id=task_id,
        )

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
        await self._check_task_access(task_id, current_user)

        assignee = await self._get_active_task_assignee(task_id, user_id)
        await self._db.delete(assignee)
        await self._cleanup_assignee_role_if_no_tasks(user_id)
        await self._db.commit()
        TASKS_TOTAL.labels(action="remove_assignee").inc()
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
        task = await self._db.scalar(
            self._task_queries.get_task(id=task_id, is_active=True)
        )
        if not task:
            raise task_exc.TaskNotFound(message="Task not found")

        group = await self._db.scalar(
            self._group_queries.get_group(id=task.group_id, is_active=True)
        )
        if group and group.admin_id != current_user.id:
            raise task_exc.TaskAccessDenied(
                message="Only group admin can view join requests"
            )

        result = await self._db.scalars(
            self._join_queries.get_join_request(
                task_id=task_id, status=JoinRequestStatus.PENDING
            )
        )
        return [JoinRequestRead.model_validate(request) for request in result.all()]

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
        request = await self._get_join_request(request_id)
        task = await self._get_task_for_request(request)
        group = await self._get_group_for_task(task)

        await self._validate_join_request_approval(request, group, current_user)

        request.status = JoinRequestStatus.APPROVED
        await self._db.commit()
        TASKS_TOTAL.labels(action="approve_join", status="success").inc()

        await self._handle_group_membership(request, task, group, current_user)
        await self._add_user_to_task_assignees(request)

        notification = await self._notification.notify_join_request_approved(
            admin_id=current_user.id,
            user_id=request.user_id,
            group_id=group.id,
            group_name=group.name,
        )
        return notification

    async def _get_join_request(self, request_id: int) -> JoinRequestModel:
        """Get join request by ID."""
        request = await self._db.scalar(
            self._join_queries.get_join_request(id=request_id)
        )
        if not request:
            raise task_exc.JoinRequestNotFound(message="Join request not found")
        return request

    async def _get_task_for_request(self, request: JoinRequestModel) -> TaskModel:
        """Get task associated with join request."""
        task = await self._db.scalar(
            self._task_queries.get_task(id=request.task_id, is_active=True)
        )
        if not task or not task.group_id:
            raise task_exc.TaskNotFound(message=f"Task {request.task_id} not found")
        return task

    async def _get_group_for_task(self, task: TaskModel) -> UserGroupModel:
        """Get group associated with task."""
        group = await self._db.scalar(
            self._group_queries.get_group(id=task.group_id, is_active=True)
        )
        if not group:
            raise group_exc.GroupNotFound(message=f"Group {task.group_id} not found")
        return group

    async def _validate_join_request_approval(
        self, request: JoinRequestModel, group: UserGroupModel, current_user: UserModel
    ) -> None:
        """Validate that user can approve this join request."""
        if group.admin_id != current_user.id:
            raise task_exc.TaskAccessDenied(
                message="Only group admin can approve join requests"
            )

        if request.status != JoinRequestStatus.PENDING:
            raise task_exc.JoinRequestAlreadyHandled(
                message="Join request already processed"
            )

    async def _handle_group_membership(
        self,
        request: JoinRequestModel,
        task: TaskModel,
        group: UserGroupModel,
        current_user: UserModel,
    ) -> None:
        """Handle group membership for approved request."""
        is_member = await self._db.scalar(
            self._group_membership_queries.get_group_membership(
                user_id=request.user_id, group_id=task.group_id
            )
        )

        if not is_member:
            membership = UserGroupMembershipModel(
                user_id=request.user_id, group_id=task.group_id
            )
            self._db.add(membership)
            await self._db.commit()

            if self._notification:
                await self._notification.notify_group_join(
                    requester_id=current_user.id,
                    user_id=request.user_id,
                    group_id=group.id,
                    group_name=group.name,
                )

    async def _add_user_to_task_assignees(self, request: JoinRequestModel) -> None:
        """Add user to task assignees."""
        assignee = TaskAssignee(user_id=request.user_id, task_id=request.task_id)
        self._db.add(assignee)
        await self._db.commit()

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
        request = await self._db.scalar(
            self._join_queries.get_join_request(id=request_id)
        )
        if not request:
            raise task_exc.JoinRequestNotFound(message="Join request not found")

        if request.task_id != task_id:
            raise task_exc.JoinRequestNotFound(
                message="Join request does not belong to this task"
            )

        task = await self._db.scalar(
            self._task_queries.get_task(id=request.task_id, is_active=True)
        )

        if task is None:
            raise task_exc.TaskNotFound(message=f"Task {request.task_id} not found")

        group = await self._db.scalar(
            self._group_queries.get_group(id=task.group_id, is_active=True)
        )

        if group is None:
            raise group_exc.GroupNotFound(message=f"Group {task.group_id} not found")

        if group and group.admin_id != current_user.id:
            raise task_exc.TaskAccessDenied(
                message="Only group admin can reject join requests"
            )

        request.status = JoinRequestStatus.REJECTED
        await self._db.commit()
        TASKS_TOTAL.labels(action="reject_join", status="rejected").inc()

        notification = await self._notification.notify_join_request_rejected(
            admin_id=current_user.id,
            user_id=request.user_id,
            group_id=group.id,
            group_name=group.name,
        )
        return notification

    async def join_task(self, task_id: int, current_user: UserModel) -> None:
        """
        Join a task by either direct assignment or creating a join request.

        Args:
            task_id: ID of the task to join
            current_user: User joining the task
        """
        existing = await self._db.scalar(
            self._task_assignee_queries.get_task_assignee(
                task_id=task_id, user_id=current_user.id
            )
        )
        if existing:
            raise task_exc.UserAlreadyInTask(
                message="User is already assigned to this task"
            )
        task = await self._db.scalar(
            self._task_queries.get_task(id=task_id, is_active=True)
        )
        if not task:
            raise task_exc.TaskNotFound(message="Task not found")
        group = await self._db.scalar(
            self._group_queries.get_group(id=task.group_id, is_active=True)
        )
        if not group:
            raise task_exc.TaskNotInGroup(message="Task is not in a group")
        existing_request = await self._db.scalar(
            self._join_queries.get_join_request(
                user_id=current_user.id,
                task_id=task_id,
                status=JoinRequestStatus.PENDING,
            ),
        )
        if existing_request:
            raise task_exc.JoinRequestAlreadyExists(
                message="Join request already exists"
            )
        if group.join_policy == JoinPolicy.OPEN:
            await self._add_member_directly(task_id, current_user.id)
        else:
            request = JoinRequestModel(
                user_id=current_user.id,
                group_id=group.id,
                task_id=task_id,
                status=JoinRequestStatus.PENDING,
            )
            self._db.add(request)
            await self._db.commit()
            TASKS_TOTAL.labels(action="join_request").inc()

            if self._notification:
                await self._notification.notify_join_request_created(
                    requester_id=current_user.id,
                    admin_id=group.admin_id,
                    group_id=group.id,
                    group_name=group.name,
                )

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
        assignee = await self._get_active_task_assignee(task_id, current_user.id)
        await self._db.delete(assignee)
        await self._cleanup_assignee_role_if_no_tasks(current_user.id)
        await self._db.commit()
        TASKS_TOTAL.labels(action="exit_task").inc()
        await self._invalidate("tasks")

    async def bulk_index_tasks(self, tasks: list[TaskModel]) -> dict[str, Any]:
        """Bulk index multiple tasks to Elasticsearch."""
        return await self._indexer.bulk_index_tasks(tasks)


def get_task_service(
    db: AsyncSession = Depends(db_helper.get_session),
    indexer: ElasticsearchIndexer = Depends(get_es_indexer),
    notification_service: NotificationService = Depends(get_notification_service),
    xp_service: XPService = Depends(get_xp_service),
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
    )
