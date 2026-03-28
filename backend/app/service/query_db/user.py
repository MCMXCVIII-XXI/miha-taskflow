from typing import Literal

from sqlalchemy import Select, select

from app.models import Task, TaskAssignee, User, UserGroup, UserGroupMembership
from app.schemas import GlobalUserRole


class UserQueries:
    """
    User model repository pattern implementation.

    Details:
        This class provides static methods for querying users from the database.

    Methods:
        all: Returns all users.
        by_id: Returns a user by their ID.
        by_email: Returns a user by their email.
        by_username: Returns a user by their username.
        by_group_membership: Returns users by their group membership.
        get_admin_group: Returns users by their admin group.
        by_role: Returns users by their role.
    """

    @staticmethod
    def _check_active(
        base: Select[tuple[User]], is_active: Literal[True, False, None]
    ) -> Select[tuple[User]]:
        """
        Applies an is_active filter to a query.

        Args:
            base: The base query to filter.
            is_active: The is_active to filter by
                (True for active, False for inactive, None for all).
                True: Filter for active users.
                False: Filter for inactive users.
                None: Return all users.

        Returns:
            The filtered query.
        """
        return base if is_active is None else base.where(User.is_active == is_active)

    @staticmethod
    def all(is_active: Literal[True, False, None] = None) -> Select[tuple[User]]:
        """
        Returns all users.

        Args:
            is_active: The is_active to filter by
                (True for active, False for inactive, None for all).
                True: Filter for active users.
                False: Filter for inactive users.
                None: Return all users.

        Returns:
            A query of all users.
        """
        base = select(User)
        return UserQueries._check_active(base, is_active)

    @staticmethod
    def by_id(
        user_id: int, is_active: Literal[True, False, None] = None
    ) -> Select[tuple[User]]:
        """
        Returns a user by their ID.

        Args:
            user_id: The ID of the user.
            is_active: The is_active to filter by
                (True for active, False for inactive, None for all).
                True: Filter for active users.
                False: Filter for inactive users.
                None: Return all users.

        Returns:
            A query of the user.
        """
        base = select(User).where(User.id == user_id)
        return UserQueries._check_active(base, is_active)

    @staticmethod
    def by_email(
        email: str, is_active: Literal[True, False, None] = None
    ) -> Select[tuple[User]]:
        """
        Returns a user by their email.

        Args:
            email: The email of the user.
            is_active: The is_active to filter by
                (True for active, False for inactive, None for all).
                True: Filter for active users.
                False: Filter for inactive users.
                None: Return all users.

        Returns:
            A query of the user.
        """
        base = select(User).where(User.email == email)
        return UserQueries._check_active(base, is_active)

    @staticmethod
    def by_username(
        username: str, is_active: Literal[True, False, None] = None
    ) -> Select[tuple[User]]:
        """
        Returns a user by their username.

        Args:
            username: The username of the user.
            is_active: The is_active to filter by
                (True for active, False for inactive, None for all).
                True: Filter for active users.
                False: Filter for inactive users.
                None: Return all users.

        Returns:
            A query of the user.
        """
        base = select(User).where(User.username == username)
        return UserQueries._check_active(base, is_active)

    @staticmethod
    def by_group_membership(
        group_id: int, is_active: Literal[True, False, None] = None
    ) -> Select[tuple[User]]:
        """
        Returns users by their group membership.

        Args:
            group_id: The ID of the group.
            is_active: The is_active to filter by
                (True for active, False for inactive, None for all).
                True: Filter for active users.
                False: Filter for inactive users.
                None: Return all users.

        Returns:
            A query of the users.
        """
        base = (
            select(User)
            .join(UserGroupMembership, UserGroupMembership.user_id == User.id)
            .where(UserGroupMembership.group_id == group_id)
        )
        return UserQueries._check_active(base, is_active)

    @staticmethod
    def get_admin_group(
        group_id: int, is_active: Literal[True, False, None] = None
    ) -> Select[tuple[User]]:
        """
        Returns users by their admin group membership.

        Args:
            group_id: The ID of the group.
            is_active: The is_active to filter by
                (True for active, False for inactive, None for all).
                True: Filter for active users.
                False: Filter for inactive users.
                None: Return all users.

        Returns:
            A query of the users.
        """
        base = (
            select(User)
            .join(UserGroup, UserGroup.admin_id == User.id)
            .where(UserGroup.id == group_id)
        )
        return UserQueries._check_active(base, is_active)

    @staticmethod
    def by_main_role(
        role: GlobalUserRole, is_active: Literal[True, False, None] = None
    ) -> Select[tuple[User]]:
        """
        Returns users by their role.

        Args:
            role: The role of the user.
            is_active: The is_active to filter by
                (True for active, False for inactive, None for all).
                True: Filter for active users.
                False: Filter for inactive users.
                None: Return all users.

        Returns:
            A query of the users.
        """
        base = select(User).where(User.role == role)
        return UserQueries._check_active(base, is_active)

    @staticmethod
    def by_task_assignee(
        task_id: int, is_active: Literal[True, False, None] = None
    ) -> Select[tuple[User]]:
        """
        Returns users by their task assignee.

        Args:
            task_id: The ID of the task.
            is_active: The is_active to filter by
                (True for active, False for inactive, None for all).
                True: Filter for active users.
                False: Filter for inactive users.
                None: Return all users.

        Returns:
            A query of the users.
        """
        base = (
            select(User)
            .join(TaskAssignee, TaskAssignee.user_id == User.id)
            .where(TaskAssignee.task_id == task_id)
        )
        return UserQueries._check_active(base, is_active)

    @staticmethod
    def by_task(
        task_id: int, is_active: Literal[True, False, None] = None
    ) -> Select[tuple[User]]:
        """
        Returns users by their task.

        Args:
            task_id: The ID of the task.
            is_active: The is_active to filter by
                (True for active, False for inactive, None for all).
                True: Filter for active users.
                False: Filter for inactive users.
                None: Return all users.

        Returns:
            A query of the users.
        """
        base = (
            select(User)
            .join(UserGroup, UserGroup.admin_id == User.id)
            .join(Task, Task.group_id == UserGroup.id)
            .where(Task.id == task_id)
        )
        return UserQueries._check_active(base, is_active)

    @staticmethod
    def by_owner_task(
        task_id: int, is_active: Literal[True, False, None] = None
    ) -> Select[tuple[User]]:
        """
        Returns users by their task owner.

        Args:
            task_id: The ID of the task.
            is_active: The is_active to filter by
                (True for active, False for inactive, None for all).
                True: Filter for active users.
                False: Filter for inactive users.
                None: Return all users.

        Returns:
            A query of the users.
        """
        base = (
            select(User)
            .join(UserGroup, UserGroup.admin_id == User.id)
            .join(Task, Task.group_id == UserGroup.id)
            .where(Task.id == task_id)
        )
        return UserQueries._check_active(base, is_active)
