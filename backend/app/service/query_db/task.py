from typing import Literal

from sqlalchemy import Select, select
from sqlalchemy.orm import joinedload, selectinload

from app.models import Task, TaskAssignee, UserGroup, UserGroupMembership


class TaskQueries:
    """Provides database query builders for task-related operations.

    This class implements the repository pattern for task entities, providing
    reusable query builders for common task database operations. All methods
    return SQLAlchemy Select objects that can be executed by services.

    Note:
        All query methods return Select objects, not actual results.
        Execution is performed by the calling service layer.
    Methods:
        all: Returns a query for all tasks.
        by_id: Returns a query for a task by its ID.
        by_group: Returns a query for tasks by their group ID.
        by_assigned: Returns a query for tasks by their assigned user ID.
        by_member: Returns a query for tasks by their member user ID.
        by_owner: Returns a query for tasks by their owner user ID.
        all_with_relations: Returns a query with preloaded relations for ES indexing.
    """

    @staticmethod
    def _check_active(
        base: Select[tuple[Task]], is_active: Literal[True, False, None]
    ) -> Select[tuple[Task]]:
        """
        Applies an is_active filter to a query.

        Args:
            base: The base query to filter.
            is_active: The is_active to filter by
                (True for active, False for inactive, None for all).
                True: Filter for active tasks.
                False: Filter for inactive tasks.
                None: Return all tasks.

        Returns:
            The filtered query.

        Example usage:
            >>> TaskQueries._check_active(select(Task), True)
            select(Task).where(Task.is_active == True)
        """
        return base if is_active is None else base.where(Task.is_active == is_active)

    @staticmethod
    def all(is_active: Literal[True, False, None] = None) -> Select[tuple[Task]]:
        """
        Returns a query for all tasks.

        Args:
            is_active: The is_active to filter by
                (True for active, False for inactive, None for all).
                True: Filter for active tasks.
                False: Filter for inactive tasks.
                None: Return all tasks.

        Returns:
            The query for all tasks.

        Example usage:
            >>> TaskQueries.all(True)
            select(Task).where(Task.is_active == True)
        """
        base = select(Task)
        return TaskQueries._check_active(base, is_active)

    @staticmethod
    def by_id(
        task_id: int, is_active: Literal[True, False, None] = None
    ) -> Select[tuple[Task]]:
        """
        Returns a query for a task by its ID.

        Args:
            task_id: The ID of the task to retrieve.
            is_active: The is_active to filter by
                (True for active, False for inactive, None for all).
                True: Filter for active tasks.
                False: Filter for inactive tasks.
                None: Return all tasks.

        Returns:
            The query for the task by its ID.

        Example usage:
            >>> TaskQueries.by_id(1, True)
            select(Task).where(Task.id == 1).where(Task.is_active == True)
        """
        base = select(Task).where(Task.id == task_id)
        return TaskQueries._check_active(base, is_active)

    @staticmethod
    def by_group(
        group_id: int, is_active: Literal[True, False, None] = None
    ) -> Select[tuple[Task]]:
        """
        Returns a query for tasks in a group.

        Args:
            group_id: The ID of the group to retrieve tasks for.
            is_active: The is_active to filter by
                (True for active, False for inactive, None for all).
                True: Filter for active tasks.
                False: Filter for inactive tasks.
                None: Return all tasks.

        Returns:
            The query for tasks in a group.

        Example usage:
            >>> TaskQueries.by_group(1, True)
            select(Task).where(Task.group_id == 1).where(Task.is_active == True)
        """
        base = select(Task).where(Task.group_id == group_id)
        return TaskQueries._check_active(base, is_active)

    @staticmethod
    def by_assigned(
        user_id: int, is_active: Literal[True, False, None] = None
    ) -> Select[tuple[Task]]:
        """
        Returns a query for tasks by a user.

        Args:
            user_id: The ID of the user to retrieve tasks for.
            is_active: The is_active to filter by
                (True for active, False for inactive, None for all).
                True: Filter for active tasks.
                False: Filter for inactive tasks.
                None: Return all tasks.

        Returns:
            The query for tasks by a user.

        Example usage:
            >>> TaskQueries.by_assigned(1, True)
            select(Task)
            .join(TaskAssignee)
            .where(TaskAssignee.user_id == 1)
            .where(Task.is_active == True)
        """
        base = select(Task).join(TaskAssignee).where(TaskAssignee.user_id == user_id)
        return TaskQueries._check_active(base, is_active)

    @staticmethod
    def by_member(
        user_id: int, is_active: Literal[True, False, None] = None
    ) -> Select[tuple[Task]]:
        """
        Returns tasks in user's groups (as participant).

        Args:
            user_id: The ID of the user to retrieve tasks for.
            is_active: The is_active to filter by
                (True for active, False for inactive, None for all).
                True: Filter for active tasks.
                False: Filter for inactive tasks.
                None: Return all tasks.

        Returns:
            The query for tasks in a group.

        Example usage:
            >>> TaskQueries.by_member(1, True)
            select(Task)
            .join(UserGroup, Task.group_id == UserGroup.id)
            .join(UserGroupMembership, UserGroupMembership.group_id == UserGroup.id)
            .where(UserGroupMembership.user_id == 1)
            .where(Task.is_active == True)
        """
        base = (
            select(Task)
            .join(UserGroup, Task.group_id == UserGroup.id)
            .join(UserGroupMembership, UserGroupMembership.group_id == UserGroup.id)
            .where(UserGroupMembership.user_id == user_id)
        )
        return TaskQueries._check_active(base, is_active)

    @staticmethod
    def by_owner(
        group_ids: list[int], is_active: Literal[True, False, None] = None
    ) -> Select[tuple[Task]]:
        """
        Returns tasks in specified groups (admin-owned groups).

        Args:
            group_ids: Список ID админ-групп (self._get_id_admin_groups())
            is_active: The is_active to filter by
                (True for active, False for inactive, None for all).
                True: Filter for active tasks.
                False: Filter for inactive tasks.
                None: Return all tasks.

        Returns:
            The query for tasks owned by a group.

        Example usage:
            >>> TaskQueries.by_owner([1, 2], True)
            select(Task).where(Task.group_id.in_([1, 2])).where(Task.is_active == True)
        """
        base = select(Task).where(Task.group_id.in_(group_ids))
        return TaskQueries._check_active(base, is_active)

    @staticmethod
    def all_with_relations(
        is_active: Literal[True, False, None] = None,
    ) -> Select[tuple[Task]]:
        """
        Returns a query for all tasks with preloaded relations for ES indexing.

        Args:
            is_active: The is_active to filter by
                (True for active, False for inactive, None for all).
                True: Filter for active tasks.
                False: Filter for inactive tasks.
                None: Return all tasks.

        Returns:
            The query for all tasks with preloaded relations.

        Example usage:
            >>> TaskQueries.all_with_relations(True)
            select(Task).options(...).where(Task.is_active == True)
        """
        base = select(Task).options(
            joinedload(Task.group),
            selectinload(Task.assignees),
            selectinload(Task.comments),
        )
        return TaskQueries._check_active(base, is_active)
