from sqlalchemy import Select, select

from app.models import JoinRequest
from app.schemas.enum import JoinRequestStatus


class JoinQueries:
    """
    Query builders for JoinRequest-related operations.

    Provides reusable Select[tuple[JoinRequest]] filters for join requests
    by ID, user, group, task, and status.
    """

    @staticmethod
    def get_join_request(
        id: int | None = None,
        user_id: int | None = None,
        group_id: int | None = None,
        task_id: int | None = None,
        status: JoinRequestStatus | None = None,
    ) -> Select[tuple[JoinRequest]]:
        """
        Builds a query to filter join requests by multiple criteria.

        Args:
            id: Filter by join request ID.
            user_id: Filter by user ID.
            group_id: Filter by group ID (context).
            task_id: Filter by task ID (context).
            status: Filter by join request status.

        Returns:
            Select[tuple[JoinRequest]] for matching join requests.
        """
        base = select(JoinRequest)

        if id is not None:
            base = base.where(JoinRequest.id == id)
        if user_id is not None:
            base = base.where(JoinRequest.user_id == user_id)
        if group_id is not None:
            base = base.where(JoinRequest.group_id == group_id)
        if task_id is not None:
            base = base.where(JoinRequest.task_id == task_id)
        if status is not None:
            base = base.where(JoinRequest.status == status)

        return base
