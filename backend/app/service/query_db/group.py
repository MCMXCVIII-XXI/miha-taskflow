from typing import Literal

from sqlalchemy import Select, select

from app.models import Task, UserGroup, UserGroupMembership, UserRole
from app.schemas.enum import GroupVisibility, InvitePolicy, JoinPolicy


class GroupQueries:
    """
    Group model repository pattern implementation.

    Provides static methods for building Select[tuple[UserGroup]] and
    Select[tuple[int]] queries for UserGroup entities, with optional
    is_active filtering and joins against UserGroupMembership/Task/Role.
    """

    @staticmethod
    def _check_active(
        base: Select[tuple[UserGroup]],
        is_active: Literal[True, False, None] = None,
    ) -> Select[tuple[UserGroup]]:
        """
        Filter a UserGroup Select by is_active status.

        Args:
            base: The base UserGroup Select to filter.
            is_active: Controls which records to include:
                - True:  Only active groups.
                - False: Only inactive groups.
                - None:  All groups (no filter).

        Returns:
            The filtered query.
        """
        if is_active is None:
            return base
        return base.where(UserGroup.is_active == is_active)

    @staticmethod
    def get_group(
        id: int | None = None,
        name: str | None = None,
        visibility: GroupVisibility | None = None,
        join_policy: JoinPolicy | None = None,
        level: int | None = None,
        invite_policy: InvitePolicy | None = None,
        admin_id: int | None = None,
        is_active: Literal[True, False, None] = None,
    ) -> Select[tuple[UserGroup]]:
        """
        Builds a query to filter UserGroup by ID, name, and other attributes.

        Does not automatically join relations; that is left for service layer.

        Args:
            id: Filter by group ID.
            name: Filter by group name.
            visibility: Filter by group visibility.
            join_policy: Filter by join policy.
            level: Filter by group level.
            invite_policy: Filter by invite policy.
            admin_id: Filter by admin user ID.
            is_active: Filter by active status (True/False) or all (None).

        Returns:
            Select[tuple[UserGroup]] for matching groups.
        """
        base = select(UserGroup)

        if id is not None:
            base = base.where(UserGroup.id == id)
        if name is not None:
            base = base.where(UserGroup.name == name)
        if visibility is not None:
            base = base.where(UserGroup.visibility == visibility)
        if join_policy is not None:
            base = base.where(UserGroup.join_policy == join_policy)
        if level is not None:
            base = base.where(UserGroup.level == level)
        if invite_policy is not None:
            base = base.where(UserGroup.invite_policy == invite_policy)
        if admin_id is not None:
            base = base.where(UserGroup.admin_id == admin_id)

        return GroupQueries._check_active(base, is_active)

    @staticmethod
    def by_my_member(
        user_id: int,
        is_active: Literal[True, False, None] = None,
    ) -> Select[tuple[UserGroup]]:
        """
        Get all groups that a user is a member of.

        Joins `groups` and `user_group_membership` by `group_id`.

        Args:
            user_id: ID of the user.
            is_active: Filter by active status (True/False) or all (None).

        Returns:
            Select[tuple[UserGroup]] for groups where user is a member.
        """
        base = (
            select(UserGroup)
            .join(UserGroupMembership, UserGroupMembership.group_id == UserGroup.id)
            .where(UserGroupMembership.user_id == user_id)
        )
        return GroupQueries._check_active(base, is_active)

    @staticmethod
    def by_admin_groups_get_id(
        user_id: int,
        is_active: Literal[True, False, None] = None,
    ) -> Select[tuple[int]]:
        """
        Get IDs of groups where a user is an admin.

        Uses `UserRole` table to find group admin assignments and optionally
        filters by `is_active` status.

        Args:
            user_id: ID of the user.
            is_active: Filter by active status (True/False) or all (None).

        Returns:
            Select[tuple[int]] for IDs of admin groups.
        """
        if is_active is None:
            base = (
                select(UserGroup.id)
                .join(UserRole, UserRole.group_id == UserGroup.id)
                .where(UserRole.user_id == user_id)
            )
            return base
        else:
            base = (
                select(UserGroup.id)
                .join(UserRole, UserRole.group_id == UserGroup.id)
                .where(UserRole.user_id == user_id)
                .where(UserGroup.is_active == is_active)
            )
            return base

    @staticmethod
    def by_task(
        task_id: int,
        is_active: Literal[True, False, None] = None,
    ) -> Select[tuple[UserGroup]]:
        """
        Get the group associated with a given task.

        Joins `groups` and `tasks` by `group_id`.

        Args:
            task_id: ID of the task.
            is_active: Filter by active status (True/False) or all (None).

        Returns:
            Select[tuple[UserGroup]] for the group linked to the task.
        """
        base = (
            select(UserGroup)
            .join(Task, Task.group_id == UserGroup.id)
            .where(Task.id == task_id)
        )
        return GroupQueries._check_active(base, is_active)
