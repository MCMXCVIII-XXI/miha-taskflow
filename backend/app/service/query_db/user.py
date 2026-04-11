from typing import Any, Literal

from sqlalchemy import Select, func, select

from app.models import (
    Task,
    TaskAssignee,
    User,
    UserGroup,
    UserGroupMembership,
)
from app.schemas.enum import GlobalUserRole


class UserQueries:
    """
    Provides database query builders for user related operations.

    This class implements the repository pattern for the User entity, offering reusable
    SQLAlchemy Select builders for common filters
        (by ID, email, username, role, grouping,
    task assignment, etc.). All methods return Select objects, not concrete results,
    so execution is handled by the service layer (session.scalars/scalar/execute).

    NOTE:
        - Queries are built using SQLAlchemy 2.0 Core/ORM style.
        - Count queries use `func.count(User.id)` for precise row counting.
        - Joins are kept minimal and only added where necessary.
    """

    @staticmethod
    def _check_active(
        base: Select[tuple[Any]], is_active: Literal[True, False, None]
    ) -> Select[tuple[Any]]:
        """
        Applies an `is_active` filter to a query.

        Args:
            base: The base query to filter.
            is_active: Controls which records to include.
                - True:  Only active users.
                - False: Only inactive users.
                - None:  All users (no filter).

        Returns:
            The filtered query.
        """
        if is_active is None:
            return base
        return base.where(User.is_active == is_active)

    @staticmethod
    def _build_user_query(
        base: Select[tuple[User]],
        id: int | None = None,
        id__in: list[int] | None = None,
        username: str | None = None,
        first_name: str | None = None,
        last_name: str | None = None,
        patronymic: str | None = None,
        email: str | None = None,
        role: GlobalUserRole | None = None,
        is_active: Literal[True, False, None] = None,
    ) -> Select[tuple[User]]:
        """
        Adds filters to a `Select[tuple[User]]` query.

        Combines multiple WHERE conditions using AND logic and adds `is_active`
        filter via `_check_active`.

        Args:
            base: Base query (usually `select(User)`).
            id: Filter by user ID.
            id__in: Filter by list of user IDs.
            username: Filter by username.
            first_name: Filter by first name.
            last_name: Filter by last name.
            patronymic: Filter by patronymic.
            email: Filter by email.
            role: Filter by role.
            is_active: Filter by active status (True/False) or return all (None).

        Returns:
            The filtered `Select[tuple[User]]` query.
        """
        if id is not None:
            base = base.where(User.id == id)
        if id__in is not None:
            base = base.where(User.id.in_(id__in))
        if username is not None:
            base = base.where(User.username == username)
        if first_name is not None:
            base = base.where(User.first_name == first_name)
        if last_name is not None:
            base = base.where(User.last_name == last_name)
        if patronymic is not None:
            base = base.where(User.patronymic == patronymic)
        if email is not None:
            base = base.where(User.email == email)
        if role is not None:
            base = base.where(User.role == role)

        return UserQueries._check_active(base, is_active)

    @staticmethod
    def _build_user_count_query(
        base: Select[tuple[int]],
        id: int | None = None,
        username: str | None = None,
        first_name: str | None = None,
        last_name: str | None = None,
        patronymic: str | None = None,
        email: str | None = None,
        role: GlobalUserRole | None = None,
        is_active: Literal[True, False, None] = None,
    ) -> Select[tuple[int]]:
        """
        Adds the same filters as `_build_user_query` but for a count query.

        Uses `func.count(User.id)` under `base` and applies filters normally.
        Does not deduplicate users by primary key logic, only counts rows.

        Args:
            base: Base count query, e.g. `select(func.count(User.id))`.
            id: Count users with this ID.
            username: Count users with this username.
            first_name: Count users with this first name.
            last_name: Count users with this last name.
            patronymic: Count users with this patronymic.
            email: Count users with this email.
            role: Count users with this role.
            is_active: Filter counted users by active status.

        Returns:
            The filtered `Select[tuple[int]]` query.
        """
        if id is not None:
            base = base.where(User.id == id)
        if username is not None:
            base = base.where(User.username == username)
        if first_name is not None:
            base = base.where(User.first_name == first_name)
        if last_name is not None:
            base = base.where(User.last_name == last_name)
        if patronymic is not None:
            base = base.where(User.patronymic == patronymic)
        if email is not None:
            base = base.where(User.email == email)
        if role is not None:
            base = base.where(User.role == role)

        if is_active is not None:
            base = base.where(User.is_active == is_active)

        return UserQueries._check_active(base, is_active)

    @staticmethod
    def get_user(
        id: int | None = None,
        id__in: list[int] | None = None,
        username: str | None = None,
        first_name: str | None = None,
        last_name: str | None = None,
        patronymic: str | None = None,
        email: str | None = None,
        role: GlobalUserRole | None = None,
        is_active: Literal[True, False, None] = None,
    ) -> Select[tuple[User]]:
        """
        Builds a query to retrieve users by filters.

        Corresponds to `SELECT * FROM users WHERE ...`. Filters can be
        combined in any combination; undefined filters are ignored.

        Args:
            id: User ID to filter by.
            id__in: Filter by list of user IDs.
            username: Username to filter by.
            first_name: First name to filter by.
            last_name: Last name to filter by.
            patronymic: Patronymic to filter by.
            email: Email to filter by.
            role: Role to filter by.
            is_active: Filter by active status (True/False) or return all (None).

        Returns:
            A `Select[tuple[User]]` query that returns matching users.
        """
        base = select(User)
        return UserQueries._build_user_query(
            base=base,
            id=id,
            id__in=id__in,
            username=username,
            first_name=first_name,
            last_name=last_name,
            patronymic=patronymic,
            email=email,
            role=role,
            is_active=is_active,
        )

    @staticmethod
    def get_count_user(
        id: int | None = None,
        username: str | None = None,
        first_name: str | None = None,
        last_name: str | None = None,
        patronymic: str | None = None,
        email: str | None = None,
        role: GlobalUserRole | None = None,
        is_active: Literal[True, False, None] = None,
    ) -> Select[tuple[int]]:
        """
        Builds a count query for users matching given filters.

        Uses `SELECT COUNT(user.id) FROM users ...` structure, which is efficient
        for counting rows without loading full model instances.

        Args:
            id: Count users with this ID.
            username: Count users with this username.
            first_name: Count users with this first name.
            last_name: Count users with this last name.
            patronymic: Count users with this patronymic.
            email: Count users with this email.
            role: Count users with this role.
            is_active: Filter counted users by active status.

        Returns:
            A `Select[tuple[int]]` query that returns a single count value.
        """
        base = select(func.count(User.id)).select_from(User)
        return UserQueries._build_user_count_query(
            base=base,
            id=id,
            username=username,
            first_name=first_name,
            last_name=last_name,
            patronymic=patronymic,
            email=email,
            role=role,
            is_active=is_active,
        )

    @staticmethod
    def get_by_email_or_username(
        email: str, username: str, is_active: Literal[True, False, None] = None
    ) -> Select[tuple[User]]:
        """
        Returns users matching either the given email or username.

        Uses an OR condition on `email` and `username` columns.

        Args:
            email: Email to match.
            username: Username to match.
            is_active: Filter by active status (True/False) or return all (None).

        Returns:
            A `Select[tuple[User]]` query for users matching either condition.
        """
        base = select(User).where((User.email == email) | (User.username == username))
        return UserQueries._check_active(base, is_active)

    @staticmethod
    def by_group_membership(
        group_id: int, is_active: Literal[True, False, None] = None
    ) -> Select[tuple[User]]:
        """
        Returns users who are members of a given group.

        Joins `users` and `user_group_membership` tables via `user_id`.

        Args:
            group_id: ID of the group whose members are requested.
            is_active: Filter by active status (True/False) or return all (None).

        Returns:
            A `Select[tuple[User]]` query for group members.
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
        Returns users who are admins of a given group.

        Joins `users` and `user_group` tables via `admin_id` and filters by group ID.

        Args:
            group_id: ID of the group whose admin is requested.
            is_active: Filter by active status (True/False) or return all (None).

        Returns:
            A `Select[tuple[User]]` query for the group admin.
        """
        base = (
            select(User)
            .join(UserGroup, UserGroup.admin_id == User.id)
            .where(UserGroup.id == group_id)
        )
        return UserQueries._check_active(base, is_active)

    @staticmethod
    def by_task_assignee(
        task_id: int, is_active: Literal[True, False, None] = None
    ) -> Select[tuple[User]]:
        """
        Returns users assigned as assignees to a given task.

        Joins `users` and `task_assignee` tables via `user_id` and filters by task ID.

        Args:
            task_id: ID of the task whose assignees are requested.
            is_active: Filter by active status (True/False) or return all (None).

        Returns:
            A `Select[tuple[User]]` query for task assignees.
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
        Returns users associated with a given task via group admin chain.

        Joins:
            - `users` → `user_group` (via `admin_id`)
            - `user_group` → `task` (via `group_id`)
        Then filters tasks by `task_id`.

        Args:
            task_id: ID of the task whose linked users are requested.
            is_active: Filter by active status (True/False) or return all (None).

        Returns:
            A `Select[tuple[User]]` query for users linked to the task.
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
        Returns users who are owners of a given task (same chain as `by_task`).

        Currently uses the same logic as `by_task`; distinction can be refined
        later if ownership is modeled differently in the DB.

        Args:
            task_id: ID of the task whose owner is requested.
            is_active: Filter by active status (True/False) or return all (None).

        Returns:
            A `Select[tuple[User]]` query for task owners.
        """
        base = (
            select(User)
            .join(UserGroup, UserGroup.admin_id == User.id)
            .join(Task, Task.group_id == UserGroup.id)
            .where(Task.id == task_id)
        )
        return UserQueries._check_active(base, is_active)
