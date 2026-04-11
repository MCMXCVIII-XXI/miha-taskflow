from sqlalchemy import Select, select
from sqlalchemy.orm import joinedload

from app.models import TaskAssignee


class TaskAssigneeQueries:
    """
    Query builders for TaskAssignee (user-task assignment) relations.

    Provides reusable Select[tuple[TaskAssignee]] filters for task and user.
    All filters are combined with AND; if a parameter is None, it is ignored.
    """

    @staticmethod
    def get_task_assignee(
        id: int | None = None,
        task_id: int | None = None,
        user_id: int | None = None,
        with_relations: bool = False,
    ) -> Select[tuple[TaskAssignee]]:
        """
        Builds a query to filter TaskAssignee records by multiple criteria.

        Args:
            id: Filter by TaskAssignee ID.
            task_id: Filter by task ID.
            user_id: Filter by user ID.
            with_relations: If True, eager-load task and user (avoids N+1).

        Returns:
            Select[tuple[TaskAssignee]] query for matching assignments.
        """
        base = select(TaskAssignee)

        if with_relations:
            base = base.options(
                joinedload(TaskAssignee.task),
                joinedload(TaskAssignee.user),
            )

        if id is not None:
            base = base.where(TaskAssignee.id == id)
        if task_id is not None:
            base = base.where(TaskAssignee.task_id == task_id)
        if user_id is not None:
            base = base.where(TaskAssignee.user_id == user_id)

        return base

    @staticmethod
    def by_task(task_id: int) -> Select[tuple[TaskAssignee]]:
        """
        All assignees for a given task.

        Args:
            task_id: ID of the task.

        Returns:
            Select[tuple[TaskAssignee]] for all task assignees.
        """
        return select(TaskAssignee).where(TaskAssignee.task_id == task_id)

    @staticmethod
    def by_user(user_id: int) -> Select[tuple[TaskAssignee]]:
        """
        All tasks assigned to a given user.

        Args:
            user_id: ID of the user.

        Returns:
            Select[tuple[TaskAssignee]] for all user assignments.
        """
        return select(TaskAssignee).where(TaskAssignee.user_id == user_id)

    @staticmethod
    def by_task_and_user(task_id: int, user_id: int) -> Select[tuple[TaskAssignee]]:
        """
        Specific assignment for a user on a task.

        Args:
            task_id: ID of the task.
            user_id: ID of the user.

        Returns:
            Select[tuple[TaskAssignee]] for the specific assignment (may be empty).
        """
        return (
            select(TaskAssignee)
            .where(TaskAssignee.task_id == task_id)
            .where(TaskAssignee.user_id == user_id)
        )
