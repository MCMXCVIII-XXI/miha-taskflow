from typing import Any

from fastapi import Depends
from sqlalchemy import Select, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.core.log import get_logger
from app.db import db_helper
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
    TaskStatus,
    TaskSphere,
)
from .notification import NotificationService

from .base import GroupTaskBaseService
from .exceptions import group_exc, task_exc
from .query_db import TaskQueries
from .search import task_search
from .xp import XPService
from datetime import datetime, UTC

logger = get_logger("service.task")


class TaskService(GroupTaskBaseService):
    """
    Task lifecycle management service with advanced search and assignee operations.

    Details:
        Complete task CRUD with group ownership validation, assignee management,
        advanced search via @task_search decorator, conflict-checked updates,
        soft-delete pattern (is_active=False), status transitions.

    Attributes:
        _db (AsyncSession): SQLAlchemy async database session
        _task_queries (TaskQueries): Task-specific optimized query builders

    Methods:
        • _check_task_access(task_id, current_user) → None
        • _check_group_access(group_id, current_user) → None
        • create_task_for_group(group_id, task_in, current_user) → TaskRead
        • search_tasks() → Select[tuple[TaskModel]]
        • search_my_tasks(current_user) → Select[tuple[TaskModel]]
        • search_group_tasks(group_id, current_user) → Select[tuple[TaskModel]]
        • search_assigned_tasks(current_user) → Select[tuple[TaskModel]]
        • update_my_task(task_id, task_in, current_user) → TaskRead
        • delete_my_task(task_id, current_user) → None
        • update_status_task(task_id, status, current_user) → TaskRead
        • add_user_to_task(task_id, user_id, current_user) → None
        • remove_user_from_task(task_id, user_id, current_user) → None
        • exit_task(task_id, current_user) → None

    Returns:
        TaskRead, Select[tuple[TaskModel]], None

    Raises:
        task_exc.ForbiddenTaskAccess
        task_exc.TaskNotFound
        task_exc.TaskTitleConflict
        task_exc.TaskStatusAlreadySet
        task_exc.UserNotInTask
        task_exc.UserAlreadyInTask
        group_exc.GroupNotFound

    Example Usage:
        task_svc = TaskService(db)
        task = await task_svc.create_task_for_group(group_id, task_in, current_user)
        tasks = await task_svc.search_my_tasks(current_user)
        await task_svc.add_user_to_task(task_id, user_id, current_user)
    """

    def __init__(
        self,
        db: AsyncSession,
    ) -> None:
        super().__init__(db)
        self._task_queries = TaskQueries
        self._notification = NotificationService(db)
        self._xp_service = XPService(db)

    async def _get_task_assignees(self, task_id: int) -> list[TaskAssignee]:
        result = await self._db.scalars(
            select(TaskAssignee).where(TaskAssignee.task_id == task_id)
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
            select(UserGroupModel.id)
            .join(UserRoleModel, UserRoleModel.group_id == UserGroupModel.id)
            .where(UserRoleModel.user_id == current_user.id)
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
            self._task_queries.by_id(task_id, is_active=True).where(
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

        Details:
            Group ownership validation + title conflict check.
            Automatic cache invalidation for "tasks" namespace.

        Arguments:
            group_id (int): Target group ID
            task_in (TaskCreate): Task creation payload
            current_user (UserModel): Authenticated group admin

        Returns:
            TaskRead: Created task

        Raises:
            group_exc.GroupNotFound: Group inactive/not owned
            task_exc.TaskTitleConflict: Duplicate title in group

        Example Usage:
            task = await task_svc.create_task_for_group(123, task_create, current_user)
        """
        await self._check_group_access(group_id, current_user)

        result = await self._db.scalars(
            self._task_queries.by_group(group_id).where(
                TaskModel.title == task_in.title,
            )
        )
        if result.first():
            logger.warning(
                "Task creation failed: duplicate title {title} \
                    in group {group_id} by user {user_id}",
                title=task_in.title,
                group_id=group_id,
                user_id=current_user.id,
            )
            raise task_exc.TaskTitleConflict(
                message="Task with this title already exists"
            )
        group = await self._db.scalar(
            select(UserGroupModel).where(
                UserGroupModel.id == group_id, UserGroupModel.is_active
            )
        )
        if not group:
            raise group_exc.GroupNotFound(message="Group not found or inactive")

        task = TaskModel(
            title=task_in.title,
            description=task_in.description,
            priority=task_in.priority,
            group_id=group.id,
        )
        self._db.add(task)
        await self._db.flush()
        role_id = await self._get_role_id(self._role.GROUP_ADMIN.value)
        user_role = UserRoleModel(
            task_id=task.id,
            user_id=current_user.id,
            role_id=role_id,
            group_id=group_id,
        )
        self._db.add(user_role)
        await self._db.commit()
        await self._db.refresh(task)
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
        return self._task_queries.all(is_active=True)

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
        await self._check_group_access(group_id, current_user)
        return self._task_queries.by_group(group_id, is_active=True)

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

        task = await self._db.scalar(self._task_queries.by_id(task_id, is_active=True))

        if not task:
            raise task_exc.TaskNotFound(message="Task not found or inactive")

        for field, value in task_in.model_dump(exclude_unset=True).items():
            setattr(task, field, value)

        await self._db.commit()
        await self._db.refresh(task)
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

        task = await self._db.scalar(self._task_queries.by_id(task_id, is_active=True))

        if not task:
            raise task_exc.TaskNotFound(message="Task not found")

        task.is_active = False
        await self._db.commit()
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

        Details:
            Validates status change (no duplicate).
            Ownership + cache invalidation.

        Arguments:
            task_id (int): Target task ID
            status (TaskStatus): New status enum
            current_user (UserModel): Group admin

        Returns:
            TaskRead: Updated task

        Raises:
            task_exc.ForbiddenTaskAccess: Not owner
            task_exc.TaskNotFound: Task inactive
            task_exc.TaskStatusAlreadySet: No change

        Example Usage:
            task = await task_svc.update_status_task(123, TaskStatus.DONE, current_user)
        """

        task = await self._db.scalar(self._task_queries.by_id(task_id, is_active=True))

        if not task:
            raise task_exc.TaskNotFound(message="Task not found or inactive")
        if task.status == status:
            raise task_exc.TaskStatusAlreadySet(
                message="Task status is already set to this value"
            )

        old_status = task.status
        task.status = status
        await self._db.commit()
        await self._db.refresh(task)
        await self._invalidate("tasks")

        if status == TaskStatus.DONE and task.spheres:
            assignees = await self._get_task_assignees(task_id)

            story_points = task.difficulty.value if task.difficulty else 1
            actual_days = max(1, (datetime.now(UTC) - task.created_at).days)
            deadline_days = task.deadline.days if task.deadline else 7

            for assignee in assignees:
                for sphere_data in task.spheres:
                    sphere = TaskSphere[sphere_data["sphere"].upper()]
                    skill = await self._xp.get_or_create_skill(assignee.user_id, sphere)
                    streak = skill.streak

                    xp_distribution = self._xp.calculate_task_xp(
                        spheres=task.spheres,
                        story_points=story_points,
                        deadline_days=deadline_days,
                        actual_days=actual_days,
                        streak=streak,
                    )

                    xp = xp_distribution.get(sphere.value, 0)
                    leveled_up, new_level = await self._xp.add_sphere_xp(
                        assignee.user_id, sphere, xp
                    )

                    if leveled_up:
                        title = self._xp.get_title(sphere, new_level)
                        await self._notification.notify_level_up(
                            user_id=assignee.user_id,
                            sphere=sphere.value,
                            new_level=new_level,
                            title=title,
                        )

        logger.info(
            "Task status updated: task_id={task_id}, \
                {old_status} -> {new_status}, user_id={user_id}",
            task_id=task.id,
            old_status=old_status.value,
            new_status=status.value,
            user_id=current_user.id,
        )

        return TaskRead.model_validate(task)

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
            select(TaskAssignee)
            .options(joinedload(TaskAssignee.task), joinedload(TaskAssignee.user))
            .where(TaskAssignee.task_id == task_id, TaskAssignee.user_id == user_id)
        )

        if not assignee:
            raise task_exc.UserNotInTask(message="User is not in the task")

        if not assignee.task.is_active or not assignee.user.is_active:
            raise task_exc.UserNotInTask(message="Inactive task/user")

        return assignee

    async def _cleanup_assignee_role_if_no_tasks(self, user_id: int) -> None:
        remaining = await self._db.scalar(
            select(TaskAssignee)
            .where(
                TaskAssignee.user_id == user_id,
            )
            .limit(1)
        )
        if not remaining:
            role_id = await self._get_role_id(self._role.ASSIGNEE.value)
            if role_id:
                user_role = await self._db.scalar(
                    select(UserRoleModel).where(
                        UserRoleModel.user_id == user_id,
                        UserRoleModel.role_id == role_id,
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
            select(TaskAssignee)
            .options(joinedload(TaskAssignee.task), joinedload(TaskAssignee.user))
            .where(TaskAssignee.task_id == task_id, TaskAssignee.user_id == user_id)
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
        await self._invalidate("tasks")

        if self._notification:
            task = await self._db.scalar(
                select(TaskModel).where(TaskModel.id == task_id)
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
            select(TaskAssignee).where(
                TaskAssignee.task_id == task_id,
                TaskAssignee.user_id == user_id,
            )
        )
        if existing:
            raise task_exc.UserAlreadyInTask(
                message="User is already assigned to this task"
            )

        assignee = TaskAssignee(task_id=task_id, user_id=user_id)
        self._db.add(assignee)
        await self._db.commit()
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
        task = await self._db.get(TaskModel, task_id)
        if not task:
            raise task_exc.TaskNotFound(message="Task not found")

        group = await self._db.get(UserGroupModel, task.group_id)
        if group and group.admin_id != current_user.id:
            raise task_exc.TaskAccessDenied(
                message="Only group admin can view join requests"
            )

        result = await self._db.scalars(
            select(JoinRequestModel).where(
                JoinRequestModel.task_id == task_id,
                JoinRequestModel.status == JoinRequestStatus.PENDING,
            )
        )
        return [JoinRequestRead.model_validate(request) for request in result.all()]

    async def approve_task_join_request(
        self, request_id: int, current_user: UserModel
    ) -> NotificationRead:
        request = await self._db.scalar(
            select(JoinRequestModel).where(
                JoinRequestModel.id == request_id,
            )
        )
        if not request:
            raise task_exc.JoinRequestNotFound(message="Join request not found")

        task = await self._db.scalar(
            select(TaskModel).where(
                TaskModel.id == request.task_id,
            )
        )
        if not task or not task.group_id:
            raise task_exc.TaskNotFound(message=f"Task {request.task_id} not found")
        group = await self._db.scalar(
            select(UserGroupModel).where(
                UserGroupModel.id == task.group_id,
            )
        )
        if not group:
            raise group_exc.GroupNotFound(message=f"Group {task.group_id} not found")

        if group.admin_id != current_user.id:
            raise task_exc.TaskAccessDenied(
                message="Only group admin can approve join requests"
            )

        if request.status != JoinRequestStatus.PENDING:
            raise task_exc.JoinRequestAlreadyHandled(
                message="Join request already processed"
            )

        request.status = JoinRequestStatus.APPROVED
        await self._db.commit()

        is_member = await self._db.scalar(
            select(UserGroupMembershipModel).where(
                UserGroupMembershipModel.user_id == request.user_id,
                UserGroupMembershipModel.group_id == task.group_id,
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

        assignee = TaskAssignee(user_id=request.user_id, task_id=request.task_id)
        self._db.add(assignee)
        await self._db.commit()

        notification = await self._notification.notify_join_request_approved(
            admin_id=current_user.id,
            user_id=request.user_id,
            group_id=group.id,
            group_name=group.name,
        )
        return notification

    async def reject_task_join_request(
        self, request_id: int, current_user: UserModel
    ) -> NotificationRead:
        request = await self._db.get(JoinRequestModel, request_id)
        if not request:
            raise task_exc.JoinRequestNotFound(message="Join request not found")

        task = await self._db.get(TaskModel, request.task_id)

        if task is None:
            raise task_exc.TaskNotFound(message=f"Task {request.task_id} not found")

        group = await self._db.get(UserGroupModel, task.group_id)

        if group is None:
            raise group_exc.GroupNotFound(message=f"Group {task.group_id} not found")

        if group and group.admin_id != current_user.id:
            raise task_exc.TaskAccessDenied(
                message="Only group admin can reject join requests"
            )

        request.status = JoinRequestStatus.REJECTED
        await self._db.commit()

        notification = await self._notification.notify_join_request_rejected(
            admin_id=current_user.id,
            user_id=request.user_id,
            group_id=group.id,
            group_name=group.name,
        )
        return notification

    async def join_task(self, task_id: int, current_user: UserModel) -> None:
        existing = await self._db.scalar(
            select(TaskAssignee).where(
                TaskAssignee.user_id == current_user.id,
                TaskAssignee.task_id == task_id,
            )
        )
        if existing:
            raise task_exc.UserAlreadyInTask(
                message="User is already assigned to this task"
            )
        task = await self._db.get(TaskModel, task_id)
        if not task:
            raise task_exc.TaskNotFound(message="Task not found")
        group = await self._db.get(UserGroupModel, task.group_id)
        if not group:
            raise task_exc.TaskNotInGroup(message="Task is not in a group")
        existing_request = await self._db.scalar(
            select(JoinRequestModel).where(
                JoinRequestModel.user_id == current_user.id,
                JoinRequestModel.task_id == task_id,
                JoinRequestModel.status == JoinRequestStatus.PENDING,
            )
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

        Details:
            User-initiated task exit (no admin rights needed).

        Arguments:
            task_id (int): Target task ID
            current_user (UserModel): User exiting task

        Raises:
            task_exc.UserNotInTask: User not assigned

        Example Usage:
            await task_svc.exit_task(123, current_user)
        """
        assignee = await self._get_active_task_assignee(task_id, current_user.id)
        await self._db.delete(assignee)
        await self._cleanup_assignee_role_if_no_tasks(current_user.id)
        await self._db.commit()
        await self._invalidate("tasks")

        logger.info(
            "User exited task: user_id={user_id}, task_id={task_id}",
            user_id=current_user.id,
            task_id=task_id,
        )


def get_task_service(db: AsyncSession = Depends(db_helper.get_session)) -> TaskService:
    """
    FastAPI dependency factory for TaskService injection.

    Details:
        Automatically creates TaskService with database session.
        Follows FastAPI service layer isolation pattern.

    Arguments:
        db (AsyncSession): Database session from db_helper.get_session

    Returns:
        TaskService: Fresh TaskService instance

    Example Usage:
        ```python
        @router.get("/tasks/")
        async def search_tasks(
            task_service: TaskService = Depends(get_task_service)
        ):
            return await task_service.search_tasks()
        ```
    """

    return TaskService(db)
