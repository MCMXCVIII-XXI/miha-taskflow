from typing import Any, Literal

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.exceptions import rbac_exc
from app.core.log import logging
from app.db import db_helper
from app.models import (
    JoinRequest as JoinRequestModel,
)
from app.models import User as UserModel
from app.models import UserGroup as UserGroupModel
from app.models import (
    UserGroupMembership as UserGroupMembershipModel,
)
from app.models import (
    UserRole as UserRoleModel,
)
from app.repositories import UnitOfWork
from app.schemas import (
    NotificationRead,
    UserGroupCreate,
    UserGroupUpdate,
)
from app.schemas.enum import (
    JoinPolicy,
    JoinRequestStatus,
    OutboxEventType,
    SecondaryUserRole,
)

from ..exceptions import group_exc, join_request_exc, task_exc, user_exc
from ..notification import NotificationService, get_notification_service
from ..task import TaskService, get_task_service
from .base import BaseTransaction

logger = logging.get_logger(__name__)


class GroupTransaction(BaseTransaction):
    def __init__(
        self,
        uow_class: type[UnitOfWork],
        session_factory: async_sessionmaker[AsyncSession],
        task_service: TaskService,
        notification_service: NotificationService,
    ) -> None:
        super().__init__(uow_class=uow_class, session_factory=session_factory)
        self._role = SecondaryUserRole
        self._notification = notification_service
        self._task_service = task_service

    async def _dispatch_events(
        self, events: list[dict[str, Any]]
    ) -> list[NotificationRead]:
        """Process collected events and dispatch notifications."""
        created_notifications = []
        for event in events:
            if not self._notification:
                continue
            if event["type"] == "group_join":
                notification = await self._notification.notify_group_join(
                    **event["data"]
                )
                created_notifications.append(notification)
            elif event["type"] == "group_invite":
                notification = await self._notification.notify_group_invite(
                    **event["data"]
                )
                created_notifications.append(notification)
            elif event["type"] == "join_request_created":
                notification = await self._notification.notify_join_request_created(
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
        return created_notifications

    async def _get_role_id(
        self, uow: UnitOfWork, role_name: Literal["MEMBER", "GROUP_ADMIN", "ASSIGNEE"]
    ) -> int | None:
        """Get the database ID for a role by name.

        Retrieves the internal database ID for a role based on its human-readable
        name. Used for role assignment and validation operations.

        Args:
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

    async def _get_my_group(
        self, uow: UnitOfWork, group_id: int, user_id: int
    ) -> UserGroupModel:
        """
        Retrieve group where user is owner/admin.

        Args:
            group_id: Target group ID
            user_id: User ID to verify as owner

        Returns:
            Active owned group

        Raises:
            group_exc.ForbiddenGroupAccess: Not owner or inactive group
        """
        group = await uow.group.get(admin_id=user_id, id=group_id, is_active=True)

        if not group:
            logger.warning(
                "Group access denied: user {user_id} not owner of group {group_id}",
                user_id=user_id,
                group_id=group_id,
            )
            raise group_exc.ForbiddenGroupAccess(
                message="You are not the owner of the group"
            )

        logger.info(
            "Group accessed: group_id={group_id}, user_id={user_id}",
            group_id=group_id,
            user_id=user_id,
        )
        return group

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

    async def _get_active_group_member(
        self, uow: UnitOfWork, group_id: int, user_id: int
    ) -> UserGroupMembershipModel:
        """
        Get active UserGroupMembership record.

        Args:
            group_id: Target group ID
            user_id: Target user ID

        Returns:
            Active membership record

        Raises:
            group_exc.MemberNotFound: No active membership
        """
        membership = await uow.group_membership.get(user_id=user_id, group_id=group_id)

        if not membership:
            logger.warning(
                "Member not found: group_id={group_id}, user_id={user_id}",
                group_id=group_id,
                user_id=user_id,
            )
            raise group_exc.MemberNotFound(message="Member not found")

        logger.info(
            "Member accessed: group_id={group_id}, user_id={user_id}",
            group_id=group_id,
            user_id=user_id,
        )
        return membership

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

    async def _handle_task_join_after_approval(
        self, uow: UnitOfWork, request: JoinRequestModel, current_user: UserModel
    ) -> None:
        task = await uow.task.get(id=request.task_id, is_active=True)
        if not task:
            return

        is_member = await uow.group_membership.get_by_user_and_group(
            user_id=request.user_id, group_id=task.group_id
        )

        if not is_member:
            await uow.group_membership.add(
                user_id=request.user_id,
                group_id=task.group_id,
            )

            if self._notification:
                group = await uow.group.get(id=task.group_id, is_active=True)
                if group:
                    uow.add_event(
                        "group_join",
                        {
                            "requester_id": request.user_id,
                            "user_id": request.user_id,
                            "group_id": group.id,
                            "group_name": group.name,
                        },
                    )

        if request.task_id is not None:
            await self._task_service.add_user_to_task(
                task_id=request.task_id,
                user_id=request.user_id,
                current_user=current_user,
            )

    async def _get_remaining_group_or_member(
        self, uow: UnitOfWork, user_id: int, role: Literal["MEMBER", "GROUP_ADMIN"]
    ) -> UserGroupModel | UserGroupMembershipModel | None:
        """Get remaining group or membership for role cleanup.

        Checks if user has any remaining groups or memberships before role cleanup.
        Used to determine if role should be removed when user leaves all groups.

        Args:
            uow: Unit of work for database operations
                Type: UnitOfWork
            user_id: ID of the user to check
                Type: int
            role: Role type to check for
                Type: Literal["MEMBER", "GROUP_ADMIN"]

        Returns:
            UserGroupModel | UserGroupMembershipModel | None:
                Remaining group or membership, or None if none exist

        Example:
            ```python
            remaining = await self._get_remaining_group_or_member(123, "MEMBER")
            ```
        """
        if role == "MEMBER":
            result = await uow.group_membership.find_many(
                user_id=user_id,
                limit=1,
            )
            return result[0] if result else None
        elif role == "GROUP_ADMIN":
            result = await uow.group.find_many(
                admin_id=user_id,
                is_active=True,
                limit=1,
            )
            return result[0] if result else None

    async def _cleanup_role_if_no_groups(
        self, uow: UnitOfWork, user_id: int, role: Literal["MEMBER", "GROUP_ADMIN"]
    ) -> None:
        """Clean up role when user has no remaining groups.

        Checks if user has any remaining groups/memberships. If none exist,
        removes the user's role assignment. Uses UnitOfWork for atomic operation.

        Args:
            uow: Unit of work for database operations
            user_id: ID of the user to clean up role for
                Type: int
            role: Role type to clean up
                Type: Literal["MEMBER", "GROUP_ADMIN"]

        Returns:
            None

        Example:
            ```python
            await self._cleanup_role_if_no_groups(db, 123, "MEMBER")
            ```
        """
        remaining = await self._get_remaining_group_or_member(
            uow=uow, user_id=user_id, role=role
        )
        if not remaining:
            role_id = await self._get_role_id(uow=uow, role_name=role)
            if role_id:
                user_role = await uow.user_role.get(user_id=user_id, role_id=role_id)
                if user_role:
                    await uow.user_role.delete(user_role=user_role)

    async def create_my_group(
        self, current_user: UserModel, group_in: UserGroupCreate
    ) -> UserGroupModel:
        async with self._create_uow() as uow:
            name_conflict = await uow.group.get(
                name=group_in.name,
                admin_id=current_user.id,
                is_active=True,
            )
            if name_conflict:
                logger.warning(
                    "Group creation failed: duplicate name {name} for user {user_id}",
                    name=group_in.name,
                    user_id=current_user.id,
                )
                raise group_exc.GroupNameConflict(message="Name already exists")

            group = await uow.group.add(
                name=group_in.name,
                description=group_in.description,
                admin_id=current_user.id,
                visibility=group_in.visibility,
                parent_group_id=group_in.parent_group_id,
                level=1 if group_in.parent_group_id is None else 2,
                invite_policy=group_in.invite_policy,
                join_policy=group_in.join_policy,
            )
            if not await uow.group_membership.exists(
                user_id=current_user.id,
                group_id=group.id,
            ):
                await uow.group_membership.add(
                    user_id=current_user.id,
                    group_id=group.id,
                )

            await uow.outbox.add(
                event_type=OutboxEventType.CREATED,
                entity_type="group",
                entity_id=group.id,
            )

            await self._grant_role_if_not_exists(
                uow=uow,
                user_id=current_user.id,
                group_id=group.id,
                role_name=self._role.GROUP_ADMIN.value,
            )
            fresh_group = await uow.group.get_with_admin(
                group_id=group.id, is_active=True
            )
            if not fresh_group:
                raise group_exc.GroupRuntimeError(
                    message="Created group with admin not found"
                )
        if uow.get_events():
            await self._dispatch_events(uow.get_events())

        return fresh_group

    async def reject_task_join_request(
        self, task_id: int, request_id: int, current_user: UserModel
    ) -> NotificationRead:
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

            group = await uow.group.get(
                id=task.group_id,
                is_active=True,
            )

            if group is None:
                raise group_exc.GroupNotFound(
                    message=f"Group {task.group_id} not found"
                )

            if group and group.admin_id != current_user.id:
                raise task_exc.TaskAccessDenied(
                    message="Only group admin can reject join requests"
                )

            await uow.join_request.update(
                join_request=request,
                status=JoinRequestStatus.REJECTED,
            )

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
        if uow.get_events():
            await self._dispatch_events(uow.get_events())
        return request

    async def add_member_to_group(
        self, current_user: UserModel, group_id: int, user_id: int
    ) -> None:
        async with self._create_uow() as uow:
            await self._get_my_group(
                uow=uow, group_id=group_id, user_id=current_user.id
            )

            existing_membership = await uow.group_membership.get_by_user_and_group(
                user_id=user_id, group_id=group_id
            )
            if existing_membership:
                logger.warning(
                    "Add member failed: \
                        user {user_id} already member of group {group_id}",
                    user_id=user_id,
                    group_id=group_id,
                )
                raise group_exc.MemberAlreadyExists(message="Member already exists")

            await uow.group_membership.add(
                user_id=user_id,
                group_id=group_id,
            )
            if self._notification:
                group = await self._get_my_group(
                    uow=uow, group_id=group_id, user_id=current_user.id
                )
                uow.add_event(
                    "group_invite",
                    {
                        "inviter_id": current_user.id,
                        "invitee_id": user_id,
                        "group_id": group_id,
                        "group_name": group.name,
                    },
                )
        if uow.get_events():
            await self._dispatch_events(uow.get_events())

    async def remove_member_from_group(
        self,
        group_id: int,
        user_id: int,
        current_user: UserModel,
    ) -> None:
        async with self._create_uow() as uow:
            await self._get_my_group(
                uow=uow, group_id=group_id, user_id=current_user.id
            )
            membership = await self._get_active_group_member(
                uow=uow, group_id=group_id, user_id=user_id
            )
            if not membership:
                raise user_exc.PermissionDenied(
                    message="User is not a member of this group"
                )
            await uow.group_membership.delete(membership=membership)
            await self._cleanup_role_if_no_groups(
                uow=uow, user_id=user_id, role=self._role.MEMBER.value
            )

    async def create_join_request(self, group_id: int, user_id: int) -> None:
        async with self._create_uow() as uow:
            existing_request = await uow.join_request.get(
                group_id=group_id, user_id=user_id
            )
            if existing_request:
                raise join_request_exc.JoinRequestAlreadyExists(
                    message="Join request already exists."
                )
            await uow.join_request.add(
                user_id=user_id,
                group_id=group_id,
            )

    async def update_my_group(
        self, group_id: int, current_user: UserModel, group_in: UserGroupUpdate
    ) -> UserGroupModel:
        async with self._create_uow() as uow:
            group = await self._get_my_group(
                uow=uow, group_id=group_id, user_id=current_user.id
            )
            group_update = group_in.model_dump(exclude_unset=True)

            name = group_update.get("name")

            if not group:
                raise group_exc.GroupNotFound(message="Group not found")

            if name:
                name_conflict = await uow.group.get(name=name, is_active=True)
                if name_conflict and name_conflict.id != group_id:
                    logger.warning(
                        "Group update failed: duplicate name {name} \
                            for group_id {group_id}",
                        name=name,
                        group_id=group_id,
                    )
                    raise group_exc.GroupNameConflict(
                        message="Group name already exists"
                    )

            group = await uow.group.update(group=group, group_update=group_update)
            await uow.outbox.add(
                event_type=OutboxEventType.UPDATED,
                entity_type="group",
                entity_id=group.id,
            )
            fresh_group = await uow.group.get(id=group.id, is_active=True)

        if uow.get_events():
            await self._dispatch_events(uow.get_events())

        return fresh_group

    async def delete_my_group(self, group_id: int, current_user: UserModel) -> None:
        async with self._create_uow() as uow:
            group = await self._get_my_group(
                uow=uow, group_id=group_id, user_id=current_user.id
            )
            role_id = await self._get_role_id(
                uow=uow, role_name=self._role.GROUP_ADMIN.value
            )
            user_role = await uow.user_role.get(
                user_id=current_user.id,
                role_id=role_id,
                group_id=group_id,
            )

            if not user_role:
                raise group_exc.GroupNotFound(message="Group not found")

            group.is_active = False
            await uow.group.update(group=group)
            await uow.user_role.delete(user_role=user_role)
            await uow.outbox.add(
                event_type=OutboxEventType.DELETED,
                entity_type="group",
                entity_id=group.id,
            )

            await self._cleanup_role_if_no_groups(
                uow=uow,
                user_id=current_user.id,
                role=self._role.GROUP_ADMIN.value,
            )

        if uow.get_events():
            await self._dispatch_events(uow.get_events())

    async def reject_join_request(
        self, request_id: int, current_user: UserModel
    ) -> list[NotificationRead]:
        notifications = []
        async with self._create_uow() as uow:
            request = await uow.join_request.get(id=request_id)
            if not request:
                raise group_exc.JoinRequestNotFound(message="Join request not found")

            group = await uow.group.get(id=request.group_id, is_active=True)

            if not group:
                raise group_exc.GroupNotFound(
                    message=f"Group {request.group_id} not found"
                )

            if group.admin_id != current_user.id:
                raise group_exc.MemberNotAdmin(
                    message="Only group admin can reject join requests"
                )

            await uow.join_request.update(
                join_request=request,
                status=JoinRequestStatus.REJECTED,
            )

            if self._notification and group:
                uow.add_event(
                    "join_request_rejected",
                    {
                        "admin_id": current_user.id,
                        "user_id": request.user_id,
                        "group_id": group.id,
                        "group_name": group.name,
                    },
                )

        if uow.get_events():
            notifications = await self._dispatch_events(uow.get_events())

        return notifications

    async def approve_join_request(
        self, group_id: int, request_id: int, current_user: UserModel
    ) -> list[NotificationRead]:
        async with self._create_uow() as uow:
            request = await uow.join_request.get(id=request_id)
            if not request:
                raise group_exc.JoinRequestNotFound(message="Join request not found")

            if request.group_id != group_id:
                raise group_exc.JoinRequestNotFound(
                    message="Join request does not belong to this group"
                )

            group = await uow.group.get(id=request.group_id, is_active=True)

            if not group:
                raise group_exc.GroupNotFound("Group not found")

            if group.admin_id != current_user.id:
                raise group_exc.MemberNotAdmin(
                    message="Only group admin can approve join requests"
                )

            if request.status != JoinRequestStatus.PENDING:
                raise group_exc.JoinRequestAlreadyHandled(
                    message="Join request already processed"
                )

            await uow.join_request.update(
                join_request=request,
                status=JoinRequestStatus.APPROVED,
            )
            await uow.group_membership.add(
                user_id=request.user_id,
                group_id=request.group_id,
            )

            await self._grant_role_if_not_exists(
                uow=uow,
                group_id=request.group_id,
                user_id=request.user_id,
                role_name=self._role.MEMBER.value,
            )

            if request.task_id:
                await self._handle_task_join_after_approval(
                    uow=uow, request=request, current_user=current_user
                )

            if self._notification and group:
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

    async def join_group(self, group_id: int, current_user: UserModel) -> None:
        async with self._create_uow() as uow:
            user_group_membership = await uow.group_membership.get_by_user_and_group(
                group_id=group_id, user_id=current_user.id
            )
            if user_group_membership:
                raise group_exc.MemberAlreadyExists(
                    message="User is already a member of this group"
                )
            group = await uow.group.get(id=group_id, is_active=True)
            if not group:
                raise group_exc.GroupNotFound(message="Group not found")

            existing_request = await uow.join_request.get(
                group_id=group_id,
                user_id=current_user.id,
                status=JoinRequestStatus.PENDING,
            )
            if existing_request:
                raise group_exc.JoinRequestAlreadyExists(
                    message="Join request already exists"
                )
            logger.debug(
                f"DEBUG: group.join_policy = {group.join_policy}, \
                    JoinPolicy.OPEN = {JoinPolicy.OPEN}, \
                        type = {type(group.join_policy)}"
            )
            if group.join_policy == JoinPolicy.OPEN:
                logger.info("DEBUG: Open group - adding membership directly")
                await uow.group_membership.add(
                    user_id=current_user.id,
                    group_id=group_id,
                )

                await self._grant_role_if_not_exists(
                    uow=uow,
                    group_id=group_id,
                    user_id=current_user.id,
                    role_name=self._role.MEMBER.value,
                )

                if self._notification:
                    uow.add_event(
                        "group_join",
                        {
                            "requester_id": current_user.id,
                            "user_id": group.admin_id,
                            "group_id": group_id,
                            "group_name": group.name,
                        },
                    )
            else:
                logger.info(
                    "DEBUG: Request group - creating join request and notification"
                )
                await uow.join_request.add(
                    user_id=current_user.id,
                    group_id=group_id,
                    task_id=None,
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
            events = uow.get_events()
            logger.info(f"DEBUG join_group: Dispatching {len(events)} events: {events}")
            await self._dispatch_events(events)

    async def exit_group(self, group_id: int, current_user: UserModel) -> None:
        async with self._create_uow() as uow:
            membership = await self._get_active_group_member(
                uow=uow, group_id=group_id, user_id=current_user.id
            )
            if not membership:
                raise user_exc.PermissionDenied(
                    message="User is not a member of this group"
                )
            await uow.group_membership.delete(membership=membership)
            await self._cleanup_role_if_no_groups(
                uow=uow,
                user_id=current_user.id,
                role=self._role.MEMBER.value,
            )

        if uow.get_events():
            await self._dispatch_events(uow.get_events())


def get_group_transaction(
    notification_service: NotificationService = Depends(get_notification_service),
    task_service: TaskService = Depends(get_task_service),
) -> GroupTransaction:
    return GroupTransaction(
        uow_class=UnitOfWork,
        session_factory=db_helper.session_factory,
        notification_service=notification_service,
        task_service=task_service,
    )
