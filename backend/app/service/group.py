from typing import Any, Literal

from fastapi import Depends
from sqlalchemy import Select, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import db_helper
from app.models import User as UserModel
from app.models import UserGroup as UserGroupModel
from app.models import (
    UserGroupMembership as UserGroupMembershipModel,
)
from app.models import (
    UserRole,
)
from app.schemas import (
    UserGroupCreate,
    UserGroupRead,
    UserGroupSearch,
    UserGroupUpdate,
)

from .base import BaseService
from .exceptions import group_exc
from .query_db import GroupQueries
from .search import group_search


class GroupService(BaseService):
    """
    Group lifecycle management service with membership operations.

    Details:
        Complete group CRUD for group admins, membership management (add/remove/exit),
        advanced search via @group_search decorator, name conflict validation,
        soft-delete pattern (is_active=False), owner validation.

    Attributes:
        _db (AsyncSession): SQLAlchemy async database session
        _group_queries (GroupQueries): Group-specific optimized query builders

    Methods:
        • _get_my_group(group_id, user_id) → UserGroupModel
        • get_my_group(group_id, current_user) → UserGroupRead
        • search_groups() → Select[tuple[UserGroupModel]]
        • search_my_groups(current_user) → Select[tuple[UserGroupModel]]
        • search_member_groups(current_user) → Select[tuple[UserGroupModel]]
        • create_my_group(current_user, group_in) → UserGroupRead
        • add_member_to_group(group_id, user_id, current_user) → UserGroupRead
        • remove_member_from_group(group_id, user_id, current_user) → None
        • update_my_group(group_id, current_user, group_in) → UserGroupRead
        • delete_my_group(group_id, current_user) → None
        • exit_group(group_id, current_user) → None

    Returns:
        UserGroupRead, Select[tuple[UserGroupModel]], None

    Raises:
        group_exc.ForbiddenGroupAccess
        group_exc.GroupNotFound
        group_exc.GroupNameConflict
        group_exc.MemberNotFound
        group_exc.MemberAlreadyExists

    Example Usage:
        group_svc = GroupService(db)
        group = await group_svc.create_my_group(current_user, group_create)
        members = await group_svc.search_member_groups(current_user)
        await group_svc.add_member_to_group(group_id, user_id, current_user)
    """

    def __init__(self, db: AsyncSession) -> None:
        super().__init__(db)
        self._group_queries = GroupQueries

    async def _get_my_group(self, group_id: int, user_id: int) -> UserGroupModel:
        """
        Retrieve group where user is owner/admin.

        Details:
            Single scalar query via GroupQueries.by_admin_group.
            Only active groups (is_active=True).

        Arguments:
            group_id (int): Target group ID
            user_id (int): User ID to verify as owner

        Returns:
            UserGroupModel: Active owned group

        Raises:
            group_exc.ForbiddenGroupAccess: Not owner or inactive group

        Example Usage:
            group = await self._get_my_group(123, current_user.id)
        """
        group = await self._db.scalar(
            self._group_queries.by_admin_group(user_id, group_id, is_active=True)
        )

        if not group:
            raise group_exc.ForbiddenGroupAccess(
                message="You are not the owner of the group"
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

        Details:
            Name conflict check within user's groups only.
            Automatic cache invalidation for "groups".

        Arguments:
            current_user (UserModel): Group owner
            group_in (UserGroupCreate): Group creation payload

        Returns:
            UserGroupRead: Created group

        Raises:
            group_exc.GroupNameConflict: Duplicate name

        Example Usage:
            group = await group_svc.create_my_group(current_user, group_create)
        """
        if group_in.name:
            name_conflict = await self._db.scalar(
                self._group_queries.by_name(group_in.name, is_active=True).where(
                    UserGroupModel.admin_id == current_user.id
                )
            )
            if name_conflict:
                raise group_exc.GroupNameConflict(message="Name already exists")
        group = UserGroupModel(
            name=group_in.name,
            description=group_in.description,
            admin_id=current_user.id,
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
        await self._invalidate("groups")
        return UserGroupRead.model_validate(group)

    async def _get_active_group_member(
        self, group_id: int, user_id: int
    ) -> UserGroupModel:
        """
        Get active UserGroupMembership record.

        Details:
            Validates group/user active status.

        Arguments:
            group_id (int): Target group ID
            user_id (int): Target user ID

        Returns:
            UserGroupMembership: Active membership

        Raises:
            group_exc.MemberNotFound: No membership or inactive

        Example Usage:
            membership = await self._get_active_group_member(123, 456)
        """
        membership = await self._db.scalar(
            self._group_queries.by_user_member(user_id, group_id, is_active=True)
        )

        if not membership:
            raise group_exc.MemberNotFound(message="Member not found")

        if not getattr(membership, "user", None) or not getattr(
            membership, "group", None
        ):
            raise group_exc.MemberNotFound(message="Member not found")

        return membership

    async def _get_remaining_group_or_member(
        self, user_id: int, role: Literal["MEMBER", "GROUP_ADMIN"]
    ) -> UserGroupModel | UserGroupMembershipModel:
        if role == "MEMBER":
            return await self._db.scalar(
                select(UserGroupMembershipModel)
                .where(
                    UserGroupMembershipModel.user_id == user_id,
                    UserGroupMembershipModel.is_active == True,  # noqa: E712
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
                    select(UserRole).where(
                        UserRole.user_id == user_id,
                        UserRole.role_id == role_id,
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
            raise group_exc.MemberAlreadyExists(message="Member already exists")

        membership_create = UserGroupMembershipModel(group_id=group_id, user_id=user_id)
        self._db.add(membership_create)
        await self._db.commit()
        await self._db.refresh(membership_create)
        await self._invalidate("groups")

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
                raise group_exc.GroupNameConflict(message="Group name already exists")

        for key, value in group_update.items():
            setattr(group, key, value)

        await self._db.commit()
        await self._db.refresh(group)
        await self._invalidate("groups")
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
            select(UserRole).where(
                UserRole.user_id == current_user.id,
                UserRole.role_id == role_id,
                UserRole.group_id == group_id,
            )

        if not user_role:
            raise group_exc.GroupNotFound(message="Group not found")

        group.is_active = False
        await self._db.delete(user_role)
        await self._cleanup_role_if_no_groups(
            current_user.id, self._role.GROUP_ADMIN.value
        )
        await self._db.commit()
        await self._invalidate("groups")

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
        await self._invalidate("groups")

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


def get_group_service(
    db: AsyncSession = Depends(db_helper.get_session),
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
    return GroupService(db)
