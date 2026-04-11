from datetime import datetime
from typing import Literal

from sqlalchemy import Select, select
from sqlalchemy.orm import joinedload, selectinload

from app.models import Task, TaskAssignee, UserGroup, UserGroupMembership
from app.schemas.enum import TaskDifficulty, TaskPriority, TaskStatus, TaskVisibility


class TaskQueries:
    """Provides database query builders for task-related operations.

    This class implements the repository pattern for Task entities, providing
    reusable Select[tuple[Task]] builders for common filters (by ID, group,
    assignee, member, owner, etc.). All methods return Select objects, not
    concrete results; execution is performed by the service layer.

    Note:
        - Filters are combined with AND logic.
        - `is_active` filtering is shared via `_check_active`.
        - Relations are loaded only in `all_with_relations`.
    """

    @staticmethod
    def _check_active(
        base: Select[tuple[Task]], is_active: Literal[True, False, None]
    ) -> Select[tuple[Task]]:
        """
        Applies an `is_active` filter to a query.

        Args:
            base: The base query to filter.
            is_active: Controls which records to include:
                - True:  Only active tasks.
                - False: Only inactive tasks.
                - None:  All tasks (no filter).

        Returns:
            The filtered query.
        """
        if is_active is None:
            return base
        return base.where(Task.is_active == is_active)

    @staticmethod
    def get_task(
        id: int | None = None,
        title: str | None = None,
        status: TaskStatus | None = None,
        priority: TaskPriority | None = None,
        difficulty: TaskDifficulty | None = None,
        visibility: TaskVisibility | None = None,
        deadline: datetime | None = None,
        group_id: int | None = None,
        is_active: Literal[True, False, None] = None,
    ) -> Select[tuple[Task]]:
        """
        Returns a query for tasks by filters.

        Args:
            id: Task ID.
            title: Task title (exact match).
            status: Task status.
            priority: Task priority.
            difficulty: Task difficulty.
            visibility: Task visibility.
            deadline: Deadline date.
            group_id: Group ID.
            is_active: Filter by active status (True/False) or all (None).

        Returns:
            Select[tuple[Task]] for matching tasks.
        """
        base = select(Task)

        if id is not None:
            base = base.where(Task.id == id)
        if title is not None:
            base = base.where(Task.title == title)
        if status is not None:
            base = base.where(Task.status == status)
        if priority is not None:
            base = base.where(Task.priority == priority)
        if difficulty is not None:
            base = base.where(Task.difficulty == difficulty)
        if visibility is not None:
            base = base.where(Task.visibility == visibility)
        if deadline is not None:
            base = base.where(Task.deadline == deadline)
        if group_id is not None:
            base = base.where(Task.group_id == group_id)

        return TaskQueries._check_active(base, is_active)

    @staticmethod
    def by_assigned(
        user_id: int, is_active: Literal[True, False, None] = None
    ) -> Select[tuple[Task]]:
        """
        Returns tasks assigned to a given user.

        Joins `tasks` and `task_assignee` tables by `task_id` and filters
        by `user_id`.

        Args:
            user_id: ID of the user.
            is_active: Filter by active status (True/False) or all (None).

        Returns:
            Select[tuple[Task]] for tasks where user is assignee.
        """
        base = select(Task).join(TaskAssignee).where(TaskAssignee.user_id == user_id)
        return TaskQueries._check_active(base, is_active)

    @staticmethod
    def by_member(
        user_id: int, is_active: Literal[True, False, None] = None
    ) -> Select[tuple[Task]]:
        """
        Returns tasks in groups where user is member.

        Joins:
            - `tasks` → `user_group` by `group_id`
            - `user_group` → `user_group_membership` by `group_id`
        Then filters by `user_id` in membership.

        Args:
            user_id: ID of the user.
            is_active: Filter by active status (True/False) or all (None).

        Returns:
            Select[tuple[Task]] for tasks in user's groups.
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
        Returns tasks owned by given groups (admins of those groups).

        Filters tasks by `group_id` membership in `group_ids`.

        Args:
            group_ids: List of group IDs (admin groups).
            is_active: Filter by active status (True/False) or all (None).

        Returns:
            Select[tuple[Task]] for tasks in the specified groups.
        """

        base = select(Task).where(Task.group_id.in_(group_ids))
        return TaskQueries._check_active(base, is_active)

    @staticmethod
    def all_with_relations(
        is_active: Literal[True, False, None] = None,
    ) -> Select[tuple[Task]]:
        """
        Returns tasks with preloaded relations for ES indexing / bulk use.

        Loads `group`, `assignees`, `comments` eagerly to avoid N+1
        when serializing to Elasticsearch or similar.

        Args:
            is_active: Filter by active status (True/False) or all (None).

        Returns:
            Select[tuple[Task]] with preloaded relations.
        """
        base = select(Task).options(
            joinedload(Task.group),
            selectinload(Task.assignees),
            selectinload(Task.comments),
        )
        return TaskQueries._check_active(base, is_active)
