from sqlalchemy import Select, select

from app.models import UserRole


class UserRoleQueries:
    """
    Query builders for UserRole (RBAC) relations.

    Provides reusable Select[tuple[UserRole]] filters for user, role, group,
    and task context. All filters are combined with AND; if a parameter is None,
    it is ignored.
    """

    @staticmethod
    def get_user_role(
        id: int | None = None,
        user_id: int | None = None,
        role_id: int | None = None,
        group_id: int | None = None,
        task_id: int | None = None,
    ) -> Select[tuple[UserRole]]:
        """
        Builds a query to filter UserRole records by multiple optional criteria.

        Args:
            id: Filter by UserRole ID.
            user_id: Filter by user ID.
            role_id: Filter by role ID.
            group_id: Filter by group ID (context specific role).
            task_id: Filter by task ID (context specific role).

        Returns:
            Select[tuple[UserRole]] query for matching UserRole rows.
        """
        base = select(UserRole)

        if id is not None:
            base = base.where(UserRole.id == id)
        if user_id is not None:
            base = base.where(UserRole.user_id == user_id)
        if role_id is not None:
            base = base.where(UserRole.role_id == role_id)
        if group_id is not None:
            base = base.where(UserRole.group_id == group_id)
        if task_id is not None:
            base = base.where(UserRole.task_id == task_id)

        return base

    @staticmethod
    def by_user(user_id: int) -> Select[tuple[UserRole]]:
        """
        All roles assigned to a given user (any context).

        Args:
            user_id: ID of the user.

        Returns:
            Select[tuple[UserRole]] for all user roles.
        """
        return select(UserRole).where(UserRole.user_id == user_id)

    @staticmethod
    def by_user_and_role(user_id: int, role_id: int) -> Select[tuple[UserRole]]:
        """
        All role assignments for a given user and role ID.

        Args:
            user_id: ID of the user.
            role_id: ID of the role.

        Returns:
            Select[tuple[UserRole]] for the given user role pair.
        """
        return (
            select(UserRole)
            .where(UserRole.user_id == user_id)
            .where(UserRole.role_id == role_id)
        )

    @staticmethod
    def by_group(group_id: int) -> Select[tuple[UserRole]]:
        """
        All roles in a given group (typically group specific roles).

        Args:
            group_id: ID of the group.

        Returns:
            Select[tuple[UserRole]] for all group roles.
        """
        return select(UserRole).where(UserRole.group_id == group_id)

    @staticmethod
    def by_task(task_id: int) -> Select[tuple[UserRole]]:
        """
        All roles in a given task (task specific roles).

        Args:
            task_id: ID of the task.

        Returns:
            Select[tuple[UserRole]] for all task roles.
        """
        return select(UserRole).where(UserRole.task_id == task_id)
