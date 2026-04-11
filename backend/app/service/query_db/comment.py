from sqlalchemy import Select, select

from app.models import Comment


class CommentQueries:
    """
    Query builders for Comment-related operations.

    Provides reusable Select[tuple[Comment]] filters for comments by ID,
    task, user, content, and parent comment.
    """

    @staticmethod
    def get_comment(
        id: int | None = None,
        task_id: int | None = None,
        user_id: int | None = None,
        content: str | None = None,
        parent_id: int | None = None,
    ) -> Select[tuple[Comment]]:
        """
        Builds a query to filter comments by multiple criteria.

        Args:
            id: Filter by comment ID.
            task_id: Filter by task ID.
            user_id: Filter by user ID (author).
            content: Filter by exact content text.
            parent_id: Filter by parent comment ID (for replies).

        Returns:
            Select[tuple[Comment]] for matching comments.
        """
        base = select(Comment)

        if id is not None:
            base = base.where(Comment.id == id)
        if task_id is not None:
            base = base.where(Comment.task_id == task_id)
        if user_id is not None:
            base = base.where(Comment.user_id == user_id)
        if content is not None:
            base = base.where(Comment.content == content)
        if parent_id is not None:
            base = base.where(Comment.parent_id == parent_id)

        return base
