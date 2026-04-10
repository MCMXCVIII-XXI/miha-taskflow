from typing import Any, Literal

from fastapi import Depends
from sqlalchemy import Select, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.log import get_logger
from app.db import db_helper
from app.es import ElasticsearchIndexer, get_es_indexer
from app.models import (
    JoinRequest as JoinRequestModel,
)
from app.models import (
    Task as TaskModel,
)
from app.models import User as UserModel
from app.models import UserGroup as UserGroupModel
from app.models import (
    UserGroupMembership as UserGroupMembershipModel,
)
from app.models import (
    UserRole as UserRoleModel,
)
from app.schemas import (
    JoinRequestRead,
    NotificationRead,
    UserGroupCreate,
    UserGroupRead,
    UserGroupSearch,
    UserGroupUpdate,
)
from app.schemas.enum import (
    JoinPolicy,
    JoinRequestStatus,
)

from .base import GroupTaskBaseService
from .exceptions import group_exc, join_request_exc
from .notification import NotificationService, get_notification_service
from .query_db import GroupQueries
from .search import group_search
from .task import TaskService, get_task_service
from .utils import Indexer

logger = get_logger("service.group")


class GroupService(GroupTaskBaseService):
    """
    Group lifecycle management service with membership operations.

    Complete group CRUD for group admins, membership management (add/remove/exit),
    advanced search via @group_search decorator, name conflict validation,
    soft-delete pattern (is_active=False), owner validation.

    Args:
        db: SQLAlchemy async database session
        indexer: Elasticsearch indexer instance
        notification_service: Notification service instance
        group_queries: Group-specific optimized query builders
        task_service: Task service instance

    Attributes:
        _db: SQLAlchemy async database session
        _group_queries: Group-specific optimized query builders
        _indexer: Elasticsearch indexer wrapper
        _notification: Notification service instance
        _task_svc: Task service instance

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
        group_queries: GroupQueries,
        task_service: TaskService,
    ) -> None:
        super().__init__(db)
        self._group_queries = group_queries
        self._task_service = task_service
        self._notification = notification_service
        self._indexer = Indexer(indexer)

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
        group = await self._db.scalar(
            self._group_queries.by_admin_group(user_id, group_id, is_active=True)
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

    @group_search
    async def search_groups(
        self,
        search: UserGroupSearch,
        sort: UserGroupSearch,
        limit: int,
        offset: int,
        **kwargs: Any,
    ) -> Select[tuple[UserGroupModel]]:
        """
        Base query for all active groups search/filter/sort.

        Details:
            @group_search decorator applies UserGroupSearch filters.
            Only active groups (is_active=True).

        Returns:
            Select[tuple[UserGroupModel]]: Base query for search

        Example Usage:
            ```python
            @router.get("/groups/")
            async def search_groups(
                search: UserGroupSearch = Depends(),
                group_svc: GroupService = Depends(get_group_service)
            ):
                return await group_svc.search_groups(search=search)
            ```
        """
        return self._group_queries.all(is_active=True)

    @group_search
    async def search_my_groups(
        self,
        search: UserGroupSearch,
        sort: UserGroupSearch,
        limit: int,
        offset: int,
        current_user: UserModel,
    ) -> Select[tuple[UserGroupModel]]:
        """
        Search groups owned by current user (admin).

        Details:
            Filters by current_user.id as admin_id.
            @group_search applies additional filters.

        Arguments:
            current_user (UserModel): Group owner

        Returns:
            Select[tuple[UserGroupModel]]: Owned groups query

        Example Usage:
            my_groups = await group_svc.search_my_groups(current_user)
        """
        return self._group_queries.by_admin_groups(current_user.id, is_active=True)

    @group_search
    async def search_member_groups(
        self,
        search: UserGroupSearch,
        sort: UserGroupSearch,
        limit: int,
        offset: int,
        current_user: UserModel,
    ) -> Select[tuple[UserGroupModel]]:
        """
        Search groups where user is member.

        Details:
            Via UserGroupMembership relationship.
            @group_search decorator filtering.

        Arguments:
            current_user (UserModel): Group member

        Returns:
            Select[tuple[UserGroupModel]]: Member groups query

        Example Usage:
            member_groups = await group_svc.search_member_groups(current_user)
        """
        return self._group_queries.by_my_member(current_user.id, is_active=True)

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
        if group_in.name:
            name_conflict = await self._db.scalar(
                self._group_queries.by_name(group_in.name, is_active=True).where(
                    UserGroupModel.admin_id == current_user.id
                )
            )
            if name_conflict:
                logger.warning(
                    "Group creation failed: duplicate name {name} for user {user_id}",
                    name=group_in.name,
                    user_id=current_user.id,
                )
                raise group_exc.GroupNameConflict(message="Name already exists")

        group = UserGroupModel(
            name=group_in.name,
            description=group_in.description,
            admin_id=current_user.id,
            visibility=group_in.visibility,
            parent_group_id=group_in.parent_group_id,
            level=1 if group_in.parent_group_id is None else 2,
        )
        self._db.add(group)
        await self._db.flush()
        await self._grant_role_if_not_exists(
            user_id=current_user.id,
            group_id=group.id,
            role_name=self._role.GROUP_ADMIN.value,
        )
        await self._db.commit()
        await self._db.refresh(group)
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
        membership = await self._db.scalar(
            self._group_queries.by_user_member(user_id, group_id, is_active=True)
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

    async def _get_remaining_group_or_member(
        self, user_id: int, role: Literal["MEMBER", "GROUP_ADMIN"]
    ) -> UserGroupModel | UserGroupMembershipModel:
        if role == "MEMBER":
            return await self._db.scalar(
                select(UserGroupMembershipModel)
                .where(
                    UserGroupMembershipModel.user_id == user_id,
                )
                .limit(1)
            )
        elif role == "GROUP_ADMIN":
            return await self._db.scalar(
                select(UserGroupModel)
                .where(
                    UserGroupModel.admin_id == user_id,
                    UserGroupModel.is_active,
                )
                .limit(1)
            )

    async def _cleanup_role_if_no_groups(
        self, user_id: int, role: Literal["MEMBER", "GROUP_ADMIN"]
    ) -> None:
        remaining = await self._get_remaining_group_or_member(user_id, role)
        if not remaining:
            role_id = await self._get_role_id(role)
            if role_id:
                user_role = await self._db.scalar(
                    select(UserRoleModel).where(
                        UserRoleModel.user_id == user_id,
                        UserRoleModel.role_id == role_id,
                    )
                )
                if user_role:
                    await self._db.delete(user_role)

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
        await self._get_my_group(group_id, current_user.id)

        membership = await self._db.scalar(
            self._group_queries.by_user_member(user_id, group_id, is_active=True)
        )
        if membership:
            logger.warning(
                "Add member failed: user {user_id} already member of group {group_id}",
                user_id=user_id,
                group_id=group_id,
            )
            raise group_exc.MemberAlreadyExists(message="Member already exists")

        membership_create = UserGroupMembershipModel(group_id=group_id, user_id=user_id)
        self._db.add(membership_create)
        await self._db.commit()
        await self._db.refresh(membership_create)
        await self._invalidate("groups")

        if self._notification:
            group = await self._get_my_group(group_id, current_user.id)
            await self._notification.notify_group_invite(
                inviter_id=current_user.id,
                invitee_id=user_id,
                group_id=group_id,
                group_name=group.name,
            )

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
        await self._get_my_group(group_id, current_user.id)

        membership = await self._get_active_group_member(group_id, user_id)
        await self._db.delete(membership)
        await self._cleanup_role_if_no_groups(user_id, self._role.MEMBER.value)
        await self._db.commit()

        logger.info(
            "Member removed from group: group_id={group_id}, user_id={removed_user}",
            group_id=group_id,
            removed_user=user_id,
        )

    async def create_join_request(self, group_id: int, user_id: int) -> None:
        join_request = await self._db.scalar(
            select(JoinRequestModel).where(
                JoinRequestModel.group_id == group_id,
                JoinRequestModel.user_id == user_id,
            )
        )
        if join_request:
            raise join_request_exc.JoinRequestAlreadyExists(
                message="Join request already exists."
            )

        join_request = JoinRequestModel(
            group_id=group_id,
            user_id=user_id,
        )
        self._db.add(join_request)
        await self._db.commit()

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
        group = await self._get_my_group(group_id, current_user.id)
        group_update = group_in.model_dump(exclude_unset=True)

        name = group_update.get("name")

        if not group:
            raise group_exc.GroupNotFound(message="Group not found")

        if name:
            name_conflict = await self._db.scalar(
                self._group_queries.by_name(name, is_active=True).where(
                    UserGroupModel.id != group_id
                )
            )
            if name_conflict:
                logger.warning(
                    "Group update failed: duplicate name {name} \
                        for group_id {group_id}",
                    name=name,
                    group_id=group_id,
                )
                raise group_exc.GroupNameConflict(message="Group name already exists")

        for key, value in group_update.items():
            setattr(group, key, value)

        await self._db.commit()
        await self._db.refresh(group)
        await self._indexer.index(group)
        await self._invalidate("groups")

        logger.info(
            "Group updated: group_id={group_id}, fields={fields}",
            group_id=group_id,
            fields=list(group_update.keys()),
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
        group = await self._get_my_group(group_id, current_user.id)
        role_id = await self._get_role_id(self._role.GROUP_ADMIN.value)
        user_role = await self._db.scalar(
            select(UserRoleModel).where(
                UserRoleModel.user_id == current_user.id,
                UserRoleModel.role_id == role_id,
                UserRoleModel.group_id == group_id,
            )
        )

        if not user_role:
            raise group_exc.GroupNotFound(message="Group not found")

        group.is_active = False
        await self._db.delete(user_role)
        await self._cleanup_role_if_no_groups(
            current_user.id, self._role.GROUP_ADMIN.value
        )
        await self._db.commit()
        await self._indexer.delete({"type": "group", "id": group_id})
        await self._invalidate("groups")

        logger.info(
            "Group deleted (soft delete): group_id={group_id}, admin_id={user_id}",
            group_id=group_id,
            user_id=current_user.id,
        )

    async def _handle_task_join_after_approval(
        self, request: JoinRequestModel, current_user: UserModel
    ) -> None:
        task = await self._db.get(TaskModel, request.task_id)
        if not task:
            return

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
                group = await self._db.get(UserGroupModel, task.group_id)
                if group:
                    await self._notification.notify_group_join(
                        requester_id=request.user_id,
                        user_id=request.user_id,
                        group_id=group.id,
                        group_name=group.name,
                    )

        if request.task_id is not None:
            await self._task_service.add_user_to_task(
                task_id=request.task_id,
                user_id=request.user_id,
                current_user=current_user,
            )

    async def reject_join_request(
        self, request_id: int, current_user: UserModel
    ) -> None:
        request = await self._db.get(JoinRequestModel, request_id)
        if not request:
            raise group_exc.JoinRequestNotFound(message="Join request not found")

        group = await self._db.get(UserGroupModel, request.group_id)

        if not group:
            raise group_exc.GroupNotFound(message=f"Group {request.group_id} not found")

        if group.admin_id != current_user.id:
            raise group_exc.MemberNotAdmin(
                message="Only group admin can reject join requests"
            )

        request.status = JoinRequestStatus.REJECTED
        await self._db.commit()

        if self._notification and group:
            await self._notification.notify_join_request_rejected(
                admin_id=current_user.id,
                user_id=request.user_id,
                group_id=group.id,
                group_name=group.name,
            )

    async def approve_join_request(
        self, request_id: int, current_user: UserModel
    ) -> NotificationRead:
        request = await self._db.get(JoinRequestModel, request_id)
        if not request:
            raise group_exc.JoinRequestNotFound(message="Join request not found")

        group = await self._db.get(UserGroupModel, request.group_id)

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

        request.status = JoinRequestStatus.APPROVED
        await self._db.commit()

        membership = UserGroupMembershipModel(
            user_id=request.user_id, group_id=request.group_id
        )
        self._db.add(membership)
        await self._db.commit()

        await self._grant_role_if_not_exists(
            group_id=request.group_id,
            user_id=request.user_id,
            role_name=self._role.MEMBER.value,
        )
        await self._db.commit()

        if request.task_id:
            await self._handle_task_join_after_approval(request, current_user)

        notification = await self._notification.notify_join_request_approved(
            admin_id=current_user.id,
            user_id=request.user_id,
            group_id=group.id,
            group_name=group.name,
        )
        return notification

    async def get_join_requests(
        self, group_id: int, current_user: UserModel
    ) -> list[JoinRequestRead]:
        group = await self._db.scalar(
            self._group_queries.by_id(group_id, is_active=True)
        )
        if not group:
            raise group_exc.GroupNotFound(message="Group not found")

        if group.admin_id != current_user.id:
            raise group_exc.MemberNotAdmin(
                message="Only group admin can view join requests"
            )

        result = await self._db.scalars(
            select(JoinRequestModel).where(
                JoinRequestModel.group_id == group_id,
                JoinRequestModel.task_id.is_(None),
                JoinRequestModel.status == JoinRequestStatus.PENDING,
            )
        )
        return [JoinRequestRead.model_validate(req) for req in result.all()]

    async def join_group(self, group_id: int, current_user: UserModel) -> None:
        user_group_membership = await self._db.scalar(
            select(UserGroupMembershipModel).where(
                UserGroupMembershipModel.user_id == current_user.id,
                UserGroupMembershipModel.group_id == group_id,
            )
        )
        if user_group_membership:
            raise group_exc.MemberAlreadyExists(
                message="User is already a member of this group"
            )
        group = await self._db.scalar(
            select(UserGroupModel).where(UserGroupModel.id == group_id)
        )
        if not group:
            raise group_exc.GroupNotFound(message="Group not found")

        existing_request = await self._db.scalar(
            select(JoinRequestModel).where(
                JoinRequestModel.user_id == current_user.id,
                JoinRequestModel.group_id == group_id,
                JoinRequestModel.task_id.is_(None),
                JoinRequestModel.status == JoinRequestStatus.PENDING,
            )
        )
        if existing_request:
            raise group_exc.JoinRequestAlreadyExists(
                message="Join request already exists"
            )
        if group.join_policy == JoinPolicy.OPEN:
            membership = UserGroupMembershipModel(
                user_id=current_user.id, group_id=group_id
            )
            self._db.add(membership)
            await self._db.commit()
            await self._grant_role_if_not_exists(
                group_id=group_id,
                user_id=current_user.id,
                role_name=self._role.MEMBER.value,
            )
            await self._db.commit()
            await self._invalidate("groups")
            await self._invalidate("rbac")

            if self._notification:
                await self._notification.notify_group_join(
                    requester_id=current_user.id,
                    user_id=current_user.id,
                    group_id=group_id,
                    group_name=group.name,
                )
        else:
            request = JoinRequestModel(
                user_id=current_user.id,
                group_id=group_id,
                task_id=None,
                status=JoinRequestStatus.PENDING,
            )
            self._db.add(request)
            await self._db.commit()

            if self._notification:
                await self._notification.notify_join_request_created(
                    requester_id=current_user.id,
                    admin_id=group.admin_id,
                    group_id=group_id,
                    group_name=group.name,
                )

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

        Raises:
            group_exc.MemberNotFound: Not a member

        Example Usage:
            await group_svc.exit_group(123, current_user)
        """
        membership = await self._get_active_group_member(group_id, current_user.id)
        await self._db.delete(membership)
        await self._cleanup_role_if_no_groups(current_user.id, self._role.MEMBER.value)
        await self._db.commit()
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
) -> GroupService:
    """
    FastAPI dependency factory for GroupService injection.

    Details:
        Creates GroupService with database session.
        Service layer isolation pattern.

    Arguments:
        db (AsyncSession): Database session

    Returns:
        GroupService: Fresh service instance

    Example Usage:
        ```python
        @router.get("/groups/my")
        async def get_my_groups(
            group_svc: GroupService = Depends(get_group_service)
        ):
            return await group_svc.search_my_groups(current_user)
        ```
    """

    return GroupService(
        db=db,
        indexer=indexer,
        notification_service=notification_service,
        group_queries=GroupQueries(),
        task_service=task_service,
    )
