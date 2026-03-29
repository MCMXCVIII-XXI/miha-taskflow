from typing import Literal

from sqlalchemy import Select, select

from app.models import Task, UserGroup, UserGroupMembership


class GroupQueries:
    """
    Group model repository pattern implementation.

    Details:
        This class provides static methods for querying the UserGroup model.

    Methods:
        all: Get all UserGroups, optionally filtered by is_active status.
        by_id: Get a UserGroup by its ID, optionally filtered by is_active status.
        by_my_member: Get UserGroups where the user is a member,
            optionally filtered by is_active status.
        by_user_member: Get a UserGroup by its ID and the user is a member,
            optionally filtered by is_active status.
        by_admin_groups: Get UserGroups where the user is an admin,
            optionally filtered by is_active status.
        by_admin_group: Get a UserGroup by its ID and the user is an admin,
            optionally filtered by is_active status.
        by_task: Get UserGroups by task ID, optionally filtered by is_active status.
    """

    @staticmethod
    def _check_active(
        base: Select[tuple[UserGroup]],
        is_active: Literal[True, False, None] = None,
    ) -> Select[tuple[UserGroup]]:
        """
        Filter a UserGroup Select by is_active status.

        Args:
            base: The base UserGroup Select to filter
            is_active: The is_active to filter by
                (True for active, False for inactive, None for all).
                True: Filter for active users.
                False: Filter for inactive users.
                None: Return all users.

        Returns:
            The filtered query.
        """
        return (
            base if is_active is None else base.where(UserGroup.is_active == is_active)
        )

    @staticmethod
    def all(is_active: Literal[True, False, None] = None) -> Select[tuple[UserGroup]]:
        """
        Get all UserGroups, optionally filtered by is_active status.

        Args:
            is_active: The is_active to filter by
                (True for active, False for inactive, None for all).
                True: Filter for active users.
                False: Filter for inactive users.
                None: Return all users.

        Returns:
            A query of all groups.
        """
        base = select(UserGroup)
        return GroupQueries._check_active(base, is_active)

    @staticmethod
    def by_id(
        group_id: int,
        is_active: Literal[True, False, None] = None,
    ) -> Select[tuple[UserGroup]]:
        """
        Get a UserGroup by its ID, optionally filtered by is_active status.

        Args:
            group_id: The ID of the UserGroup to retrieve
            is_active: The is_active to filter by
                (True for active, False for inactive, None for all).
                True: Filter for active users.
                False: Filter for inactive users.
                None: Return all users.

        Returns:
            The query of the group by its ID.
        """
        base = select(UserGroup).where(UserGroup.id == group_id)
        return GroupQueries._check_active(base, is_active)

    @staticmethod
    def by_my_member(
        user_id: int,
        is_active: Literal[True, False, None] = None,
    ) -> Select[tuple[UserGroup]]:
        """
        Get all UserGroups that a user is a member of,
            optionally filtered by is_active status.

        Args:
            user_id: The ID of the user to retrieve groups for
            is_active: The is_active to filter by
                (True for active, False for inactive, None for all).
                True: Filter for active users.
                False: Filter for inactive users.
                None: Return all users.

        Returns:
            The query of the groups the user is a member of.
        """
        base = (
            select(UserGroup)
            .join(UserGroupMembership)
            .where(UserGroupMembership.user_id == user_id)
        )
        return GroupQueries._check_active(base, is_active)

    @staticmethod
    def by_user_member(
        user_id: int,
        group_id: int,
        is_active: Literal[True, False, None] = None,
    ) -> Select[tuple[UserGroupMembership]]:
        """
        Get a UserGroupMembership by user_id and group_id.

        Args:
            user_id: The ID of the user
            group_id: The ID of the group
            is_active: The is_active to filter by

        Returns:
            The query of the membership.
        """
        base = (
            select(UserGroupMembership)
            .where(UserGroupMembership.user_id == user_id)
            .where(UserGroupMembership.group_id == group_id)
        )
        return base

    @staticmethod
    def by_admin_groups(
        user_id: int, is_active: Literal[True, False, None] = None
    ) -> Select[tuple[UserGroup]]:
        """
        Get all UserGroups that a user is an admin of,
            optionally filtered by is_active status.

        Args:
            user_id: The ID of the user to retrieve admin groups for
            is_active: The is_active to filter by
                (True for active, False for inactive, None for all).
                True: Filter for active users.
                False: Filter for inactive users.
                None: Return all users.

        Returns:
            The query of admin groups for the user.
        """
        base = select(UserGroup).where(UserGroup.admin_id == user_id)
        return GroupQueries._check_active(base, is_active)

    @staticmethod
    def by_admin_group(
        user_id: int,
        group_id: int,
        is_active: Literal[True, False, None] = None,
    ) -> Select[tuple[UserGroup]]:
        """
        Get a UserGroup that a user is an admin of by its ID,
            optionally filtered by is_active status.

        Args:
            user_id: The ID of the user to retrieve the admin group for
            group_id: The ID of the UserGroup to retrieve
            is_active: The is_active to filter by
                (True for active, False for inactive, None for all).
                True: Filter for active users.
                False: Filter for inactive users.
                None: Return all users.

        Returns:
            The query of the admin group by its ID.
        """
        base = select(UserGroup).where(
            UserGroup.admin_id == user_id, UserGroup.id == group_id
        )
        return GroupQueries._check_active(base, is_active)

    @staticmethod
    def by_task(
        task_id: int,
        is_active: Literal[True, False, None] = None,
    ) -> Select[tuple[UserGroup]]:
        """
        Get the UserGroup associated with a task,
            optionally filtered by is_active status.

        Args:
            task_id: The ID of the task to retrieve the group for
            is_active: The is_active to filter by
                (True for active, False for inactive, None for all).
                True: Filter for active users.
                False: Filter for inactive users.
                None: Return all users.

        Returns:
            The query of the group associated with the task.
        """
        base = (
            select(UserGroup)
            .join(Task, Task.group_id == UserGroup.id)
            .where(Task.id == task_id)
        )
        return GroupQueries._check_active(base, is_active)

    @staticmethod
    def by_name(
        name: str,
        is_active: Literal[True, False, None] = None,
    ) -> Select[tuple[UserGroup]]:
        """
        Get a UserGroup by its name, optionally filtered by is_active status.

        Args:
            name: The name of the UserGroup to retrieve
            is_active: The is_active to filter by
                (True for active, False for inactive, None for all).
                True: Filter for active users.
                False: Filter for inactive users.
                None: Return all users.

        Returns:
            The query of the group by its name.
        """
        base = select(UserGroup).where(UserGroup.name == name)
        return GroupQueries._check_active(base, is_active)
