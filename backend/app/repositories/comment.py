from collections.abc import Sequence

from sqlalchemy import Select, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Comment


class CommentRepository:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    def _apply_pagination(
        self,
        query: Select[tuple[Comment]],
        limit: int | None = None,
        offset: int | None = None,
    ) -> Select[tuple[Comment]]:
        if limit is not None:
            query = query.limit(limit)
        if offset is not None:
            query = query.offset(offset)
        return query

    def _build_query(
        self,
        id: int | None = None,
        task_id: int | None = None,
        user_id: int | None = None,
        content: str | None = None,
        parent_id: int | None = None,
        limit: int | None = None,
        offset: int | None = None,
    ) -> Select[tuple[Comment]]:
        query = select(Comment)

        if id is not None:
            query = query.where(Comment.id == id)
        if task_id is not None:
            query = query.where(Comment.task_id == task_id)
        if user_id is not None:
            query = query.where(Comment.user_id == user_id)
        if content is not None:
            query = query.where(Comment.content == content)
        if parent_id is not None:
            query = query.where(Comment.parent_id == parent_id)

        return self._apply_pagination(query, limit=limit, offset=offset)

    async def get(
        self,
        id: int | None = None,
        task_id: int | None = None,
        user_id: int | None = None,
        content: str | None = None,
        parent_id: int | None = None,
    ) -> Comment | None:
        """Get comment by ID."""
        query = self._build_query(
            id=id,
            task_id=task_id,
            user_id=user_id,
            content=content,
            parent_id=parent_id,
        )
        return await self._db.scalar(query)

    async def find_many(
        self,
        id: int | None = None,
        task_id: int | None = None,
        user_id: int | None = None,
        content: str | None = None,
        parent_id: int | None = None,
        limit: int | None = None,
        offset: int | None = None,
    ) -> Sequence[Comment]:
        """Get comments with filters."""
        query = self._build_query(
            id=id,
            task_id=task_id,
            user_id=user_id,
            content=content,
            parent_id=parent_id,
            limit=limit,
            offset=offset,
        )
        result = await self._db.scalars(query)
        return result.all()

    async def add(
        self,
        task_id: int,
        user_id: int,
        content: str,
        parent_id: int | None = None,
    ) -> Comment:
        """Create new comment."""
        comment = Comment(
            task_id=task_id,
            user_id=user_id,
            content=content,
            parent_id=parent_id,
        )
        self._db.add(comment)
        await self._db.flush()
        return comment

    async def update(
        self,
        comment: Comment,
        content: str,
    ) -> Comment:
        """Update comment content."""
        comment.content = content
        await self._db.flush()
        return comment

    async def delete(
        self,
        comment: Comment,
    ) -> None:
        """Delete comment."""
        await self._db.delete(comment)
        await self._db.flush()
