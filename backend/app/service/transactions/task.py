from typing import Any, Literal

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.exceptions import rbac_exc
from app.core.log import logging
from app.db import db_helper
from app.models import JoinRequest as JoinRequestModel
from app.models import Task as TaskModel
from app.models import TaskAssignee
from app.models import User as UserModel
from app.models import UserGroup as UserGroupModel
from app.models import UserRole as UserRoleModel
from app.repositories import UnitOfWork
from app.schemas import (
    TaskCreate,
    TaskUpdate,
)
from app.schemas.enum import (
    JoinPolicy,
    JoinRequestStatus,
    OutboxEventType,
    SecondaryUserRole,
    TaskStatus,
)
from app.schemas.notification import NotificationRead

from ..exceptions import group_exc, task_exc
from ..notification import NotificationService, get_notification_service
from .base import BaseTransaction

logger = logging.get_logger(__name__)


class TaskTransaction(BaseTransaction):
    def __init__(
        self,
        uow_class: type[UnitOfWork],
        session_factory: async_sessionmaker[AsyncSession],
        notification_service: NotificationService,
    ) -> None:
        super().__init__(uow_class=uow_class, session_factory=session_factory)
        self._role = SecondaryUserRole
        self._notification = notification_service

    async def _get_task_assignees(
        self, uow: UnitOfWork, task_id: int
    ) -> list[TaskAssignee]:
        """Get all assignees for a task.

        Args:
            db: Database session
                Type: AsyncSession
            task_id: ID of the task to get assignees for
                Type: int

        Returns:
            list[TaskAssignee]: List of assignees for the task

        Example:
            ```python
            assignees = await self._get_task_assignees(db, 123)
            ```
        """
        result = await uow.task_assignee.by_task(
            task_id=task_id,
        )
        return list(result)

    async def _grant_role_if_not_exists(
        self,
        uow: UnitOfWork,
        user_id: int,
        role_name: Literal["MEMBER", "ASSIGNEE", "GROUP_ADMIN"],
        group_id: int | None = None,
        task_id: int | None = None,
    ) -> None:
        """Grant a role to a user if they don't already have it.

        Checks if a user already has the specified role in the given context.
        If not, creates a new role assignment. Uses UnitOfWork for atomic operation.

        Args:
            user_id: ID of user to grant role to
                Type: int
            role_name: Name of role to grant
                Type: Literal["MEMBER", "ASSIGNEE", "GROUP_ADMIN"]
                Values: "MEMBER" for group members, "ASSIGNEE" for task assignees,
                    "GROUP_ADMIN" for administrators
            group_id: Optional group ID for group-specific roles
                Type: int | None
                Defaults to None
            task_id: Optional task ID for task-specific roles
                Type: int | None
                Defaults to None

        Returns:
            None

        Raises:
            rbac_exc.RoleNotFound: If the role doesn't exist in the database
            group_exc.GroupMissingContextIdError:
                If neither group_id nor task_id provided

        Example:
            ```python
            # Grant MEMBER role in group 1 to user 5
            await self._grant_role_if_not_exists(
                user_id=5,
                role_name="MEMBER",
                group_id=1
            )

            # Grant ASSIGNEE role on task 10 to user 5
            await self._grant_role_if_not_exists(
                user_id=5,
                role_name="ASSIGNEE",
                group_id=1,
                task_id=10
            )
            ```
        """
        role_id = await self._get_role_id(uow=uow, role_name=role_name)

        if not role_id:
            raise rbac_exc.RoleNotFound(message=f"Role {role_name} not found")

        existing = await self._build_query_for_user_role(
            uow=uow,
            group_id=group_id,
            task_id=task_id,
            user_id=user_id,
            role_id=role_id,
        )

        if not existing:
            await uow.user_role.add(
                user_id=user_id,
                role_id=role_id,
                group_id=group_id,
                task_id=task_id,
            )

    async def _get_id_admin_groups(
        self, uow: UnitOfWork, current_user: UserModel
    ) -> list[int]:
        """
        Extract admin group IDs from current user.

        Details:
            Fast list comprehension from user.admin_groups relationship.
            Used for task/group access validation.

        Arguments:
            db: Database session
                Type: AsyncSession
            current_user: Authenticated user
                Type: UserModel

        Returns:
            list[int]: Group IDs where user is admin
        """
        group_ids = await uow.group.get_admin_group_ids(
            user_id=current_user.id,
            is_active=True,
        )
        return list(group_ids)

    async def _cleanup_assignee_role_if_no_tasks(
        self, uow: UnitOfWork, user_id: int
    ) -> None:
        """
        Clean up ASSIGNEE role if user has no active task assignees.

        Scans for any active task assignees for the user.
        If none found, deletes the ASSIGNEE role from the user.

        Arguments:
            db: Database session
                Type: AsyncSession
            user_id: Target user ID
                Type: int

        Raises:
            NotFoundError: If ASSIGNEE role cannot be found

        Example Usage:
            await self._cleanup_assignee_role_if_no_tasks(db, user_id)
        """
        remaining = await uow.task_assignee.find_many(user_id=user_id, limit=1)

        if not remaining:
            role_id = await self._get_role_id(
                uow=uow, role_name=self._role.ASSIGNEE.value
            )
            if role_id:
                user_role = await uow.user_role.get(user_id=user_id, role_id=role_id)
                if user_role:
                    await uow.user_role.delete(user_role=user_role)

    async def _build_query_for_user_role(
        self,
        uow: UnitOfWork,
        group_id: int | None,
        task_id: int | None,
        user_id: int,
        role_id: int,
    ) -> UserRoleModel | None:
        """Check if user has specific role assignment.

        Queries the database to determine if a user already has a specific
        role assignment within a given context (group and/or task).

        Args:
            group_id: Group ID for group-specific roles
                Type: int | None
                Can be None for task-only roles
            task_id: Task ID for task-specific roles
                Type: int | None
                Can be None for group-only roles
            user_id: User ID to check role for
                Type: int
            role_id: Role ID to check
                Type: int

        Returns:
            UserRoleModel | None: User role record if exists, None otherwise

        Raises:
            group_exc.GroupMissingContextIdError:
                If neither group_id nor task_id provided

        Example:
            ```python
            user_role = await self._build_query_for_user_role(
                group_id=1,
                task_id=None,
                user_id=5,
                role_id=2
            )
            ```
        """
        if not group_id and not task_id:
            raise group_exc.GroupMissingContextIdError(
                message="You must pass the group_id or task_id."
            )
        return await uow.user_role.get(
            user_id=user_id,
            role_id=role_id,
            group_id=group_id,
            task_id=task_id,
        )

    async def _dispatch_events(
        self, events: list[dict[str, Any]]
    ) -> list[NotificationRead]:
        """Process collected events and dispatch notifications."""
        created_notifications = []
        for event in events:
            if not self._notification:
                continue
            if event["type"] == "task_invite":
                notification = await self._notification.notify_task_invite(
                    **event["data"]
                )
                created_notifications.append(notification)
            elif event["type"] == "group_join":
                notification = await self._notification.notify_group_join(
                    **event["data"]
                )
                created_notifications.append(notification)
            elif event["type"] == "join_request_approved":
                notification = await self._notification.notify_join_request_approved(
                    **event["data"]
                )
                created_notifications.append(notification)
            elif event["type"] == "join_request_rejected":
                notification = await self._notification.notify_join_request_rejected(
                    **event["data"]
                )
                created_notifications.append(notification)
            elif event["type"] == "join_request_created":
                notification = await self._notification.notify_join_request_created(
                    **event["data"]
                )
                created_notifications.append(notification)
        return created_notifications

    async def _get_role_id(
        self, uow: UnitOfWork, role_name: Literal["MEMBER", "GROUP_ADMIN", "ASSIGNEE"]
    ) -> int | None:
        """Get the database ID for a role by name.

        Retrieves the internal database ID for a role based on its human-readable
        name. Used for role assignment and validation operations.

        Args:
            uow: Unit of work for database operations
                Type: UnitOfWork
            role_name: Name of the role to look up
                Type: Literal["MEMBER", "GROUP_ADMIN", "ASSIGNEE"]
                Values: "MEMBER" for group members, "GROUP_ADMIN" for administrators,
                    "ASSIGNEE" for task assignees

        Returns:
            int | None: Database ID of the role, or None if role not found

        Raises:
            None

        Example:
            ```python
            role_id = await self._get_role_id("MEMBER")
            # Returns: 1 (or whatever the DB ID is for MEMBER role)
            ```
        """
        if role_name == self._role.MEMBER.value:
            return await uow.role.get_id(name=self._role.MEMBER.value)
        elif role_name == self._role.GROUP_ADMIN.value:
            return await uow.role.get_id(name=self._role.GROUP_ADMIN.value)
        elif role_name == self._role.ASSIGNEE.value:
            return await uow.role.get_id(name=self._role.ASSIGNEE.value)

    async def _get_active_task_assignee(
        self, uow: UnitOfWork, task_id: int, user_id: int
    ) -> TaskAssignee:
        """
        Get active TaskAssignee with joined loads.
        Details:
            Validates task/user active status.
            joinedload(task, user) for relationship prefetch.
        Arguments:
            db: Database session
                Type: AsyncSession
            task_id: Target task ID
                Type: int
            user_id: Target user ID
                Type: int
        Returns:
            TaskAssignee: Active assignee record
        Raises:
            task_exc.UserNotInTask: No assignee or inactive
        Example Usage:
            assignee = await self._get_active_task_assignee(123, 456)
        """
        assignee = await uow.task_assignee.get(
            user_id=user_id, task_id=task_id, with_relations=True
        )
        if not assignee:
            raise task_exc.UserNotInTask(message="User is not in the task")
        if not assignee.task.is_active or not assignee.user.is_active:
            raise task_exc.UserNotInTask(message="Inactive task/user")
        return assignee

    async def _check_task_access(
        self, uow: UnitOfWork, task_id: int, current_user: UserModel
    ) -> None:
        """
        Validate user owns task's group.

        Details:
            Checks task.group_id in user's admin_groups.
            Single scalar query via TaskQueries.by_id.

        Arguments:
            uow: Unit of work for database operations
                Type: UnitOfWork
            task_id: Target task ID
                Type: int
            current_user: Authenticated user
                Type: UserModel

        Raises:
            task_exc.ForbiddenTaskAccess: Task not in user's groups

        Example Usage:
            await self._check_task_access(db, 123, current_user)
        """
        group_ids = await self._get_id_admin_groups(uow=uow, current_user=current_user)

        if not group_ids:
            raise task_exc.ForbiddenTaskAccess(message="User is not admin of any group")

        task_in_user_group = await uow.task.get(
            id=task_id,
            is_active=True,
            group_id=group_ids[0] if group_ids else None,
        )
        if not task_in_user_group:
            task = await uow.task.get_by_group_ids(task_id, group_ids)
            if not task:
                raise task_exc.ForbiddenTaskAccess(
                    message="Task does not belong to your group"
                )

        if not task_in_user_group:
            raise task_exc.ForbiddenTaskAccess(
                message="Task does not belong to your group"
            )

    async def _validate_task_status_update(
        self, uow: UnitOfWork, task_id: int, status: TaskStatus
    ) -> TaskModel:
        """
        Validate that task exists and status is changing.

        Args:
            uow: Unit of work for database operations
                Type: UnitOfWork
            task_id: Target task ID
                Type: int
            status: New status to set
                Type: TaskStatus
        Returns:
            Validated task model

        Raises:
            task_exc.TaskNotFound: Task not found or inactive
            task_exc.TaskStatusAlreadySet: Status is already set to this value
        """
        task = await uow.task.get(id=task_id, is_active=True)
        if not task:
            raise task_exc.TaskNotFound(message="Task not found or inactive")
        if task.status == status:
            raise task_exc.TaskStatusAlreadySet(
                message="Task status is already set to this value"
            )
        return task

    async def _check_group_access(
        self, uow: UnitOfWork, group_id: int, current_user: UserModel
    ) -> None:
        """
        Validate user owns target group.

        Details:
            Fast list membership check on admin_groups.

        Arguments:
            uow: Unit of work for database operations
                Type: UnitOfWork
            group_id: Target group ID
                Type: int
            current_user: Authenticated user
                Type: UserModel

        Raises:
            group_exc.GroupNotFound: User not group admin

        Example Usage:
            await self._check_group_access(db, 123, current_user)
        """
        if group_id not in await self._get_id_admin_groups(
            uow=uow, current_user=current_user
        ):
            raise group_exc.ForbiddenGroupAccess("Group not found or inactive")

    async def _get_join_request(
        self, uow: UnitOfWork, request_id: int
    ) -> JoinRequestModel:
        """Get join request by ID with validation.

        Args:
            uow: Unit of work for database operations
                Type: UnitOfWork
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
        request = await uow.join_request.get(id=request_id)
        if not request:
            raise task_exc.JoinRequestNotFound(message="Join request not found")
        return request

    async def _get_task_for_request(
        self, uow: UnitOfWork, request: JoinRequestModel
    ) -> TaskModel:
        """Get task associated with join request.

        Args:
            uow: Unit of work for database operations
                Type: UnitOfWork
            request: Join request to get task for
                Type: JoinRequestModel

        Returns:
            TaskModel: Associated task instance

        Raises:
            task_exc.TaskNotFound: When task not found
        """
        task = await uow.task.get(
            id=request.task_id,
            is_active=True,
        )
        if not task or not task.group_id:
            raise task_exc.TaskNotFound(message=f"Task {request.task_id} not found")
        return task

    async def _get_group_for_task(
        self, uow: UnitOfWork, task: TaskModel
    ) -> UserGroupModel:
        """Get group associated with task.

        Args:
            task: Task to get group for
                Type: TaskModel

        Returns:
            UserGroupModel: Associated group instance
        """
        group = await uow.group.get(
            id=task.group_id,
            is_active=True,
        )
        if not group:
            raise group_exc.GroupNotFound(message=f"Group {task.group_id} not found")
        return group

    async def _validate_task_title_unique(
        self, uow: UnitOfWork, group_id: int, title: str, current_user: UserModel
    ) -> None:
        """Validate that task title is unique within the group.

        Checks if a task with the same title already exists in the group.
        Prevents duplicate titles within a group.

        Args:
            uow: Unit of work for database operations
                Type: UnitOfWork
            group_id: ID of the group
                Type: int
            title: Task title to validate
                Type: str
            current_user: The authenticated user
                Type: UserModel

        Returns:
            None

        Raises:
            task_exc.TaskTitleConflict: When task title already exists

        Example:
            ```python
            await self._validate_task_title_unique(123, "New Task", current_user)
            ```
        """
        existing = await uow.task.get(
            group_id=group_id,
            title=title,
            is_active=True,
        )
        if existing:
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

    async def _validate_join_request_approval(
        self,
        uow: UnitOfWork,
        request: JoinRequestModel,
        task: TaskModel,
        current_user: UserModel,
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

    async def _handle_group_membership(
        self,
        uow: UnitOfWork,
        request: JoinRequestModel,
        task: TaskModel,
        group: UserGroupModel,
        current_user: UserModel,
    ) -> None:
        """Handle group membership for approved request.

        Adds user to group membership if not already member.

        Args:
            request: Approved join request
                Type: JoinRequestModel
            task: Associated task
                Type: TaskModel
            group: Associated group
                Type: UserGroupModel
            current_user: User who approved
                Type: UserModel

        Returns:
            None
        """
        is_member = await uow.group_membership.get(
            user_id=request.user_id,
            group_id=task.group_id,
        )

        if not is_member:
            await uow.group_membership.add(
                user_id=request.user_id,
                group_id=task.group_id,
            )

            if self._notification:
                uow.add_event(
                    "group_join",
                    {
                        "requester_id": current_user.id,
                        "user_id": request.user_id,
                        "group_id": group.id,
                        "group_name": group.name,
                    },
                )

    async def _add_user_to_task_assignees(
        self, uow: UnitOfWork, request: JoinRequestModel
    ) -> None:
        """Add user to task assignees.

        Adds the requesting user as assignee to the task.

        Args:
            request: Approved join request
                Type: JoinRequestModel

        Returns:
            None
        """
        if not request.task_id:
            logger.error("To join, you need to specify the task_id")
            raise task_exc.TaskAssigneeNotFound(
                message="To join, you need to specify the task_id"
            )

        await uow.task_assignee.add(
            user_id=request.user_id,
            task_id=request.task_id,
        )

    async def create_task_for_group(
        self, group_id: int, task_in: TaskCreate, current_user: UserModel
    ) -> TaskModel:
        """
        Create a task for the specified group.

        Arguments:
            group_id: Target group ID
                Type: int
            task_in: Task creation data
                Type: TaskCreate
            current_user: Authenticated user
                Type: UserModel

        Returns:
            TaskModel: Created task
        """
        async with self._create_uow() as uow:
            await self._check_group_access(
                uow=uow, group_id=group_id, current_user=current_user
            )
            await self._validate_task_title_unique(
                uow=uow,
                group_id=group_id,
                title=task_in.title,
                current_user=current_user,
            )
            role_id = await self._get_role_id(
                uow=uow, role_name=self._role.ASSIGNEE.value
            )
            if not role_id:
                logger.error("Assignee role not found")
                raise rbac_exc.RoleNotFound(message="Assignee role not found")

            task = await uow.task.add(
                title=task_in.title,
                description=task_in.description or None,
                priority=task_in.priority,
                difficulty=task_in.difficulty,
                visibility=task_in.visibility,
                spheres=[s.model_dump() for s in task_in.spheres]
                if task_in.spheres
                else None,
                deadline=task_in.deadline,
                group_id=group_id,
            )

            task_id = task.id

            await uow.user_role.add(
                user_id=current_user.id,
                role_id=role_id,
                group_id=group_id,
                task_id=task.id,
            )
            await uow.task_assignee.add(
                user_id=current_user.id,
                task_id=task.id,
            )
            await uow.outbox.add(
                event_type=OutboxEventType.CREATED,
                entity_type="task",
                entity_id=task_id,
            )
            if not await uow.group_membership.exists(
                user_id=current_user.id,
                group_id=group_id,
            ):
                await uow.group_membership.add(
                    user_id=current_user.id,
                    group_id=group_id,
                )

            await self._grant_role_if_not_exists(
                uow=uow,
                user_id=current_user.id,
                group_id=group_id,
                role_name=self._role.MEMBER.value,
            )
            fresh_task = await uow.task.get(id=task_id, is_active=True)
        return fresh_task

    async def add_user_to_task(
        self,
        task_id: int,
        user_id: int,
        current_user: UserModel,
    ) -> None:
        async with self._create_uow() as uow:
            await self._check_task_access(
                uow=uow, task_id=task_id, current_user=current_user
            )

            existing = await uow.task_assignee.by_task_and_user(
                task_id=task_id,
                user_id=user_id,
            )

            if existing:
                logger.warning(
                    "Add user to task failed: user {user_id} already in task {task_id}",
                    user_id=user_id,
                    task_id=task_id,
                )
                raise task_exc.UserAlreadyInTask(message="User is already in the task")

            await uow.task_assignee.add(
                task_id=task_id,
                user_id=user_id,
            )

            if self._notification:
                task = await uow.task.get(
                    id=task_id,
                    is_active=True,
                )
                if task:
                    uow.add_event(
                        "task_invite",
                        {
                            "inviter_id": current_user.id,
                            "invitee_id": user_id,
                            "task_id": task_id,
                            "task_title": task.title,
                        },
                    )

        if uow.get_events():
            await self._dispatch_events(uow.get_events())

    async def update_my_task(
        self,
        task_id: int,
        task_in: TaskUpdate,
        current_user: UserModel,
    ) -> TaskModel:
        async with self._create_uow() as uow:
            await self._check_task_access(
                uow=uow, task_id=task_id, current_user=current_user
            )
            task = await uow.task.get(id=task_id, is_active=True)
            task_update = task_in.model_dump(exclude_unset=True)
            title = task_update.get("name")
            if not task:
                raise task_exc.TaskNotFound(message="Task not found or inactive")
            if title:
                title_conflict = await uow.task.get(
                    title=title, group_id=task.group_id, is_active=True
                )
                if title_conflict and title_conflict.id != task_id:
                    logger.warning(
                        "Task update failed: duplicate title {title} \
                            for task_id {task_id}",
                        title=title,
                        group_id=task_id,
                    )
                    raise task_exc.TaskTitleConflict(
                        message=f"Task {task_id=}, {title=} title already exists"
                    )

            task = await uow.task.update(task=task, task_update=task_update)

            await uow.outbox.add(
                event_type=OutboxEventType.UPDATED,
                entity_type="task",
                entity_id=task_id,
            )
            fresh_task = await uow.task.get(id=task_id, is_active=True)
        return fresh_task

    async def delete_my_task(
        self,
        task_id: int,
        current_user: UserModel,
    ) -> None:
        async with self._create_uow() as uow:
            await self._check_task_access(
                uow=uow, task_id=task_id, current_user=current_user
            )
            task = await uow.task.get(id=task_id, is_active=True)
            if not task:
                raise task_exc.TaskNotFound(message="Task not found")
            task.is_active = False

            await uow.outbox.add(
                event_type=OutboxEventType.DELETED,
                entity_type="task",
                entity_id=task_id,
            )

    async def update_status_task(
        self,
        task_id: int,
        status: TaskStatus,
        current_user: UserModel,
    ) -> TaskModel:
        async with self._create_uow() as uow:
            task = await self._validate_task_status_update(
                uow=uow, task_id=task_id, status=status
            )
            old_status = task.status
            task.status = status

            await uow.outbox.add(
                event_type=OutboxEventType.UPDATED,
                entity_type="task",
                entity_id=task_id,
                payload={
                    "old_status": old_status.value,
                    "new_status": status.value,
                },
            )
            fresh_task = await uow.task.get(id=task_id, is_active=True)
        return fresh_task

    async def _add_member_directly(
        self, uow: UnitOfWork, task_id: int, user_id: int
    ) -> None:
        """Add user directly to task without admin checks (for free join).

        Used for open join policy tasks where users can join freely
        without admin approval.

        Args:
            task_id: ID of the task
                Type: int
            user_id: ID of the user to add
                Type: int

        Returns:
            None
        """
        await uow.task_assignee.add(
            task_id=task_id,
            user_id=user_id,
        )

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
        async with self._create_uow() as uow:
            await self._check_task_access(
                uow=uow, task_id=task_id, current_user=current_user
            )
            assignee = await self._get_active_task_assignee(
                uow=uow, task_id=task_id, user_id=user_id
            )
            await uow.session.delete(assignee)
            await self._cleanup_assignee_role_if_no_tasks(uow=uow, user_id=user_id)

    async def approve_task_join_request(
        self, request_id: int, current_user: UserModel
    ) -> list[NotificationRead]:
        async with self._create_uow() as uow:
            request = await self._get_join_request(uow=uow, request_id=request_id)
            task = await self._get_task_for_request(uow=uow, request=request)
            group = await self._get_group_for_task(uow=uow, task=task)

            await self._validate_join_request_approval(
                uow=uow, request=request, task=task, current_user=current_user
            )
            await uow.join_request.update(
                join_request=request,
                status=JoinRequestStatus.APPROVED,
            )

            await self._handle_group_membership(
                uow=uow,
                request=request,
                task=task,
                group=group,
                current_user=current_user,
            )
            await self._add_user_to_task_assignees(uow=uow, request=request)

            if self._notification:
                uow.add_event(
                    "join_request_approved",
                    {
                        "admin_id": current_user.id,
                        "user_id": request.user_id,
                        "group_id": group.id,
                        "group_name": group.name,
                    },
                )

        notifications = []
        if uow.get_events():
            notifications = await self._dispatch_events(uow.get_events())
        return notifications

    async def reject_task_join_request(
        self, task_id: int, request_id: int, current_user: UserModel
    ) -> list[NotificationRead]:
        async with self._create_uow() as uow:
            request = await uow.join_request.get(id=request_id)

            if not request:
                raise task_exc.JoinRequestNotFound(message="Join request not found")

            if request.task_id != task_id:
                raise task_exc.JoinRequestNotFound(
                    message="Join request does not belong to this task"
                )

            task = await uow.task.get(
                id=request.task_id,
                is_active=True,
            )

            if task is None:
                raise task_exc.TaskNotFound(message=f"Task {request.task_id} not found")

            group = await uow.group.get(id=task.group_id, is_active=True)

            if group is None:
                raise group_exc.GroupNotFound(
                    message=f"Group {task.group_id} not found"
                )

            if group and group.admin_id != current_user.id:
                raise task_exc.TaskAccessDenied(
                    message="Only group admin can reject join requests"
                )

            request.status = JoinRequestStatus.REJECTED

            if self._notification:
                uow.add_event(
                    "join_request_rejected",
                    {
                        "admin_id": current_user.id,
                        "user_id": request.user_id,
                        "group_id": group.id,
                        "group_name": group.name,
                    },
                )

        notifications = []
        if uow.get_events():
            notifications = await self._dispatch_events(uow.get_events())
        return notifications

    async def join_task(self, task_id: int, current_user: UserModel) -> None:
        async with self._create_uow() as uow:
            existing = await uow.task_assignee.by_task_and_user(
                task_id=task_id,
                user_id=current_user.id,
            )
            if existing:
                raise task_exc.UserAlreadyInTask(
                    message="User is already assigned to this task"
                )
            task = await uow.task.get(
                id=task_id,
                is_active=True,
            )
            if not task:
                raise task_exc.TaskNotFound(message="Task not found")
            group = await uow.group.get(
                id=task.group_id,
                is_active=True,
            )
            if not group:
                raise task_exc.TaskNotInGroup(message="Task is not in a group")
            existing_request = await uow.join_request.get(
                user_id=current_user.id,
                task_id=task_id,
                status=JoinRequestStatus.PENDING,
            )
            if existing_request:
                raise task_exc.JoinRequestAlreadyExists(
                    message="Join request already exists"
                )
            if group.join_policy == JoinPolicy.OPEN:
                await self._add_member_directly(
                    uow=uow, task_id=task_id, user_id=current_user.id
                )
            else:
                await uow.join_request.add(
                    user_id=current_user.id,
                    group_id=group.id,
                    task_id=task_id,
                    status=JoinRequestStatus.PENDING,
                )

                if self._notification:
                    uow.add_event(
                        "join_request_created",
                        {
                            "requester_id": current_user.id,
                            "admin_id": group.admin_id,
                            "group_id": group.id,
                            "group_name": group.name,
                        },
                    )

        if uow.get_events():
            await self._dispatch_events(uow.get_events())

    async def exit_task(self, task_id: int, current_user: UserModel) -> None:
        async with self._create_uow() as uow:
            assignee = await self._get_active_task_assignee(
                uow=uow, task_id=task_id, user_id=current_user.id
            )
            await uow.session.delete(assignee)
            await self._cleanup_assignee_role_if_no_tasks(
                uow=uow, user_id=current_user.id
            )


def get_task_transaction(
    notification_service: NotificationService = Depends(get_notification_service),
) -> TaskTransaction:
    return TaskTransaction(
        uow_class=UnitOfWork,
        session_factory=db_helper.session_factory,
        notification_service=notification_service,
    )
