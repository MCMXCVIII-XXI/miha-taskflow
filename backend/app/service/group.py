"""Group service for group management and membership operations.

This module provides the GroupService class for managing groups,
including creation, updates, membership, and join requests.

**Key Components:**
* `GroupService`: Main service class for group operations;
* `get_group_service`: FastAPI dependency injection factory.

**Dependencies:**
* `GroupRepository`: Group data access layer;
* `GroupMembershipRepository`: Membership data access layer;
* `JoinRequestRepository`: Join request data access layer;
* `UnitOfWork`: Transaction management (via BaseService);
* `NotificationService`: Notification service for notifications;
* `TaskService`: Task service for task-related operations;
* `ElasticsearchIndexer`: Search index management.

**Usage Example:**
    ```python
    from app.service.group import get_group_service

    @router.post("/groups")
    async def create_group(
        group_data: UserGroupCreate,
        group_svc: GroupService = Depends(get_group_service),
        current_user: User = Depends(get_current_user)
    ):
        return await group_svc.create_my_group(current_user, group_data)
    ```

**Notes:**
- Groups support hierarchical structure (parent groups);
- Membership can be open (auto-join) or require approval;
- Soft delete is used (is_active=False) rather than hard deletion;
- RBAC roles are managed automatically (MEMBER, GROUP_ADMIN).
"""

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.log import logging
from app.core.metrics import METRICS
from app.db import db_helper
from app.es import ElasticsearchIndexer, get_es_indexer
from app.models import User as UserModel
from app.models import UserGroup as UserGroupModel
from app.models import (
    UserGroupMembership as UserGroupMembershipModel,
)
from app.schemas import (
    JoinRequestRead,
    NotificationRead,
    UserGroupCreate,
    UserGroupRead,
    UserGroupUpdate,
)
from app.schemas.enum import (
    JoinRequestStatus,
)

from .base import GroupTaskBaseService
from .exceptions import group_exc
from .notification import NotificationService, get_notification_service
from .task import TaskService, get_task_service
from .transactions.group import GroupTransaction, get_group_transaction
from .utils import Indexer

logger = logging.get_logger(__name__)


class GroupService(GroupTaskBaseService):
    """Service for group management and membership operations.

    Handles complete group lifecycle including creation, updates, and deletion.
    Provides membership management (add/remove/exit), join request handling,
    and role management. Uses soft delete pattern (is_active=False).

    Attributes:
        _db (AsyncSession): SQLAlchemy async session for database operations
        _group_repo (GroupRepository): Repository for group data operations
        _group_membership_repo (GroupMembershipRepository):
                Repository for membership ops
        _join_repo (JoinRequestRepository): Repository for join request ops
        _task_service (TaskService): Service for task operations
        _notification (NotificationService): Service for notifications
        _indexer (Indexer): Elasticsearch indexer wrapper

    Raises:
        group_exc.ForbiddenGroupAccess: When user is not authorized
        group_exc.GroupNotFound: When group is not found or inactive
        group_exc.GroupNameConflict: When group name already exists
        group_exc.MemberNotFound: When member is not found
        group_exc.MemberAlreadyExists: When member already exists
    """

    def __init__(
        self,
        db: AsyncSession,
        indexer: ElasticsearchIndexer,
        notification_service: NotificationService,
        task_service: TaskService,
        group_transaction: GroupTransaction,
    ) -> None:
        super().__init__(db)
        self._task_service = task_service
        self._notification = notification_service
        self._indexer = Indexer(indexer)
        self._group_transaction = group_transaction

    async def _get_my_group(self, group_id: int, user_id: int) -> UserGroupModel:
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
        group = await self._group_repo.get(
            admin_id=user_id, id=group_id, is_active=True
        )

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

    async def get_my_group(
        self, group_id: int, current_user: UserModel
    ) -> UserGroupRead:
        """
        Get owned group profile.

        Details:
            Wrapper around _get_my_group with schema validation.
            Zero additional DB calls.

        Arguments:
            group_id (int): Target group ID
            current_user (UserModel): Group owner

        Returns:
            UserGroupRead: Owned group profile

        Raises:
            group_exc.ForbiddenGroupAccess: Not owner

        Example Usage:
            group = await group_svc.get_my_group(123, current_user)
        """
        group = await self._get_my_group(group_id, current_user.id)
        return UserGroupRead.model_validate(group)

    async def create_my_group(
        self, current_user: UserModel, group_in: UserGroupCreate
    ) -> UserGroupRead:
        """
        Create new group owned by current user.

        Args:
            current_user: Group owner
            group_in: Group creation payload

        Returns:
            Created group

        Raises:
            group_exc.GroupNameConflict: Duplicate name
        """
        group = await self._group_transaction.create_my_group(
            current_user=current_user, group_in=group_in
        )

        METRICS.GROUP_ACTIONS_TOTAL.labels(action="create", status="success").inc()
        await self._indexer.index(group)
        await self._invalidate("groups")
        await self._invalidate("rbac")

        logger.info(
            "Group created: id={group_id}, name={name}, admin_id={user_id}",
            group_id=group.id,
            name=group.name,
            user_id=current_user.id,
        )

        return UserGroupRead.model_validate(group)

    async def _get_active_group_member(
        self, group_id: int, user_id: int
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
        membership = await self._group_membership_repo.get(
            user_id=user_id, group_id=group_id
        )

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

    async def add_member_to_group(
        self, group_id: int, user_id: int, current_user: UserModel
    ) -> None:
        """
        Add user as group member (group admin only).

        Details:
            Duplicate membership check + ownership validation.
            Returns updated group after adding member.

        Arguments:
            group_id (int): Target group ID
            user_id (int): User to add
            current_user (UserModel): Group admin

        Raises:
            group_exc.ForbiddenGroupAccess: Not owner
            group_exc.MemberAlreadyExists: User already member

        Example Usage:
            group = await group_svc.add_member_to_group(123, 456, current_user)
        """
        await self._group_transaction.add_member_to_group(
            current_user=current_user, group_id=group_id, user_id=user_id
        )

        METRICS.GROUP_ACTIONS_TOTAL.labels(action="add_member", status="success").inc()
        await self._invalidate("groups")

        logger.info(
            "Member added to group: group_id={group_id}, user_id={added_by}",
            group_id=group_id,
            added_by=user_id,
        )

    async def remove_member_from_group(
        self, group_id: int, user_id: int, current_user: UserModel
    ) -> None:
        """
        Remove user from group members (group admin only).

        Details:
            Uses _get_active_group_member for validation.

        Arguments:
            group_id (int): Target group ID
            user_id (int): User to remove
            current_user (UserModel): Group admin

        Raises:
            group_exc.ForbiddenGroupAccess: Not owner
            group_exc.MemberNotFound: No active membership

        Example Usage:
            await group_svc.remove_member_from_group(123, 456, current_user)
        """
        await self._group_transaction.remove_member_from_group(
            current_user=current_user, group_id=group_id, user_id=user_id
        )

        METRICS.GROUP_ACTIONS_TOTAL.labels(
            action="remove_member", status="success"
        ).inc()
        logger.info(
            "Member removed from group: group_id={group_id}, user_id={removed_user}",
            group_id=group_id,
            removed_user=user_id,
        )

    async def create_join_request(self, group_id: int, user_id: int) -> None:
        await self._group_transaction.create_join_request(
            group_id=group_id, user_id=user_id
        )
        METRICS.GROUP_ACTIONS_TOTAL.labels(
            action="join_request_created", status="success"
        ).inc()

    async def update_my_group(
        self, group_id: int, current_user: UserModel, group_in: UserGroupUpdate
    ) -> UserGroupRead:
        """
        Update owned group details.

        Details:
            Partial updates + global name conflict check (except self).
            Ownership validation + cache invalidation.

        Arguments:
            group_id (int): Target group ID
            current_user (UserModel): Group owner
            group_in (UserGroupUpdate): Update payload

        Returns:
            UserGroupRead: Updated group

        Raises:
            group_exc.ForbiddenGroupAccess: Not owner
            group_exc.GroupNotFound: Group inactive
            group_exc.GroupNameConflict: Global name collision

        Example Usage:
            updated = await group_svc.update_my_group(123, current_user, group_update)
        """
        group = await self._group_transaction.update_my_group(
            group_id=group_id, current_user=current_user, group_in=group_in
        )

        METRICS.GROUP_ACTIONS_TOTAL.labels(action="update", status="success").inc()
        await self._indexer.index(group)
        await self._invalidate("groups")

        logger.info(
            "Group updated: group_id={group_id}, fields={fields}",
            group_id=group_id,
            fields=list(group_in.model_dump().keys()),
        )

        return UserGroupRead.model_validate(group)

    async def delete_my_group(self, group_id: int, current_user: UserModel) -> None:
        """
        Soft-delete owned group.

        Details:
            Sets group.is_active = False.
            Ownership validation + cache invalidation.

        Arguments:
            group_id (int): Target group ID
            current_user (UserModel): Group owner

        Raises:
            group_exc.ForbiddenGroupAccess: Not owner

        Example Usage:
            await group_svc.delete_my_group(123, current_user)
        """
        await self._group_transaction.delete_my_group(
            group_id=group_id, current_user=current_user
        )

        METRICS.GROUP_ACTIONS_TOTAL.labels(action="delete", status="success").inc()
        await self._indexer.delete({"type": "group", "id": group_id})
        await self._invalidate("groups")

        logger.info(
            "Group deleted (soft delete): group_id={group_id}, admin_id={user_id}",
            group_id=group_id,
            user_id=current_user.id,
        )

    async def reject_join_request(
        self, request_id: int, current_user: UserModel
    ) -> NotificationRead | None:
        """Reject a join request.

        Details:
            Marks the join request as rejected and deletes it.
            Returns a notification to the user.

        Args:
            request_id (int): ID of the join request to reject
            current_user (UserModel): User rejecting the request

        Raises:
            group_exc.MemberNotFound: When request does not exist

        Example Usage:
            await group_svc.reject_join_request(123, current_user)
        """
        notifications = await self._group_transaction.reject_join_request(
            request_id=request_id, current_user=current_user
        )
        METRICS.GROUP_ACTIONS_TOTAL.labels(action="join_reject", status="success").inc()
        if notifications:
            return NotificationRead.model_validate(notifications[0])
        return None

    async def approve_join_request(
        self, group_id: int, request_id: int, current_user: UserModel
    ) -> NotificationRead:
        """Approve a join request.

        Details:
            Marks the join request as approved and deletes it.
            Returns a notification to the user.

        Args:
            group_id (int): ID of the group to approve the request for
            request_id (int): ID of the join request to approve
            current_user (UserModel): User approving the request

        Example Usage:
            await group_svc.approve_join_request(123, 456, current_user)
        """
        notifications = await self._group_transaction.approve_join_request(
            group_id=group_id, request_id=request_id, current_user=current_user
        )
        METRICS.GROUP_ACTIONS_TOTAL.labels(
            action="join_approve", status="success"
        ).inc()
        if notifications:
            return NotificationRead.model_validate(notifications[0])
        raise group_exc.JoinRequestNotFound(message="Notification not created")

    async def get_join_requests(
        self, group_id: int, current_user: UserModel
    ) -> list[JoinRequestRead]:
        """Get all join requests for a group.

        Details:
            Returns all join requests for a group, including
            the request status and the user who created it.

        Args:
            group_id (int): ID of the group to get join requests for
            current_user (UserModel): User requesting the join requests

        Example Usage:
            requests = await group_svc.get_join_requests(123, current_user)
        """
        group = await self._group_repo.get(id=group_id, is_active=True)
        if not group:
            raise group_exc.GroupNotFound(message="Group not found")

        if group.admin_id != current_user.id:
            raise group_exc.MemberNotAdmin(
                message="Only group admin can view join requests"
            )

        requests = await self._join_repo.find_many(
            group_id=group_id,
            status=JoinRequestStatus.PENDING,
        )
        return [JoinRequestRead.model_validate(req) for req in requests]

    async def join_group(self, group_id: int, current_user: UserModel) -> None:
        """Join a group.

        Details:
            Marks the user as a member of the group and
            creates a join request if the group is open.

        Args:
            group_id (int): ID of the group to join
            current_user (UserModel): User joining the group

        Example Usage:
            await group_svc.join_group(123, current_user)
        """
        await self._group_transaction.join_group(
            group_id=group_id, current_user=current_user
        )

        METRICS.GROUP_ACTIONS_TOTAL.labels(action="join_open", status="success").inc()
        await self._invalidate("groups")
        await self._invalidate("rbac")

        logger.info(
            "User joined group: user_id={user_id}, group_id={group_id}",
            user_id=current_user.id,
            group_id=group_id,
        )

    async def exit_group(self, group_id: int, current_user: UserModel) -> None:
        """
        User-initiated group membership removal.

        Details:
            No admin rights needed, self-exit only.

        Arguments:
            group_id (int): Target group ID
            current_user (UserModel): User exiting group

        Example Usage:
            await group_svc.exit_group(123, current_user)
        """
        await self._group_transaction.exit_group(
            group_id=group_id,
            current_user=current_user,
        )
        METRICS.GROUP_ACTIONS_TOTAL.labels(action="exit", status="success").inc()
        await self._invalidate("groups")

        logger.info(
            "User left group: user_id={user_id}, group_id={group_id}",
            user_id=current_user.id,
            group_id=group_id,
        )


def get_group_service(
    db: AsyncSession = Depends(db_helper.get_session),
    indexer: ElasticsearchIndexer = Depends(get_es_indexer),
    notification_service: NotificationService = Depends(get_notification_service),
    task_service: TaskService = Depends(get_task_service),
    group_transaction: GroupTransaction = Depends(get_group_transaction),
) -> GroupService:
    """Create GroupService instance with dependency injection.

    Factory function for FastAPI dependency injection that creates and configures
    a GroupService instance with all required dependencies.

    Args:
        db: Database session from FastAPI dependency injection.
            Type: AsyncSession.
        indexer: Elasticsearch client from FastAPI dependency injection.
            Type: ElasticsearchIndexer.
        notification_service: Notification service from FastAPI dependency injection.
            Type: NotificationService.
        task_service: Task service from FastAPI dependency injection.
            Type: TaskService.

    Example:
        ```python
        @router.get("/groups/my")
        async def get_my_groups(
            group_svc: GroupService = Depends(get_group_service),
            current_user: User = Depends(get_current_user)
        ):
            return await group_svc.search_my_groups(current_user)
        ```
    """

    return GroupService(
        db=db,
        indexer=indexer,
        notification_service=notification_service,
        task_service=task_service,
        group_transaction=group_transaction,
    )
