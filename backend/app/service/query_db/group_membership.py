from sqlalchemy import Select, select

from app.models import UserGroupMembership


class GroupMembershipQueries:
    """
    Query builders for UserGroupMembership-related operations.

    Provides reusable Select[tuple[UserGroupMembership]] filters for memberships
    by ID, user, and group. All filters are combined with AND.
    """

    @staticmethod
    def get_group_membership(
        id: int | None = None,
        user_id: int | None = None,
        group_id: int | None = None,
    ) -> Select[tuple[UserGroupMembership]]:
        """
        Builds a query to filter user group memberships by multiple criteria.

        Args:
            id: Filter by membership ID.
            user_id: Filter by user ID.
            group_id: Filter by group ID.

        Returns:
            Select[tuple[UserGroupMembership]] for matching memberships.
        """
        base = select(UserGroupMembership)

        if id is not None:
            base = base.where(UserGroupMembership.id == id)
        if user_id is not None:
            base = base.where(UserGroupMembership.user_id == user_id)
        if group_id is not None:
            base = base.where(UserGroupMembership.group_id == group_id)

        return base

    @staticmethod
    def by_user_and_group(
        user_id: int, group_id: int
    ) -> Select[tuple[UserGroupMembership]]:
        """
        Get membership for a specific user and group.

        Args:
            user_id: ID of the user.
            group_id: ID of the group.

        Returns:
            Select[tuple[UserGroupMembership]] for the user group pair (may be empty).
        """
        return (
            select(UserGroupMembership)
            .where(UserGroupMembership.user_id == user_id)
            .where(UserGroupMembership.group_id == group_id)
        )

    @staticmethod
    def by_user(user_id: int) -> Select[tuple[UserGroupMembership]]:
        """
        Get all memberships for a given user.

        Args:
            user_id: ID of the user.

        Returns:
            Select[tuple[UserGroupMembership]] for all user memberships.
        """
        return select(UserGroupMembership).where(UserGroupMembership.user_id == user_id)

    @staticmethod
    def by_group(group_id: int) -> Select[tuple[UserGroupMembership]]:
        """
        Get all memberships for a given group.

        Args:
            group_id: ID of the group.

        Returns:
            Select[tuple[UserGroupMembership]] for all group memberships.
        """
        return select(UserGroupMembership).where(
            UserGroupMembership.group_id == group_id
        )
