from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.log import logging
from app.db import db_helper
from app.es import ElasticsearchIndexer, get_es_indexer
from app.models import Comment as CommentModel
from app.models import User as UserModel
from app.schemas import (
    CommentRead,
)
from app.schemas.enum import OutboxEventType

from .base import BaseService
from .exceptions import comment_exc, task_exc
from .outbox import OutboxService
from .utils import Indexer

logger = logging.get_logger(__name__)


class CommentService(BaseService):
    def __init__(
        self,
        db: AsyncSession,
        indexer: ElasticsearchIndexer,
    ):
        super().__init__(db)
        self._indexer = Indexer(indexer)

    async def create_comment(
        self,
        task_id: int,
        content: str,
        current_user: UserModel,
        parent_id: int | None = None,
    ) -> CommentRead:
        task = await self._db.scalar(
            self._task_queries.get_task(id=task_id, is_active=True)
        )

        if not task:
            raise task_exc.TaskNotFound(message=f"Task {task_id} not found")

        if parent_id is not None:
            parent_comment = await self._db.scalar(
                self._comment_queries.get_comment(id=parent_id)
            )
            if not parent_comment:
                raise comment_exc.NotFoundParentError(
                    message=f"Parent comment {parent_id} not found"
                )

            if parent_comment.task_id != task_id:
                raise comment_exc.NotFoundParentError(
                    message=f"Parent comment {parent_id} \
                    does not belong to task {task_id}"
                )

        comment = CommentModel(
            task_id=task_id,
            user_id=current_user.id,
            content=content,
            parent_id=parent_id,
        )
        self._db.add(comment)
        await self._db.flush()

        outbox_service = OutboxService(self._db)
        await outbox_service.publish(
            event_type=OutboxEventType.CREATED,
            entity_type="comment",
            entity_id=comment.id,
        )

        await self._db.commit()
        await self._db.refresh(comment)
        await self._indexer.index(comment)
        return CommentRead.model_validate(comment)

    async def get_task_comments(
        self,
        task_id: int,
        limit: int = 50,
        offset: int = 0,
    ) -> list[CommentRead]:
        comments = await self._db.scalars(
            self._comment_queries.get_comment(task_id=task_id)
            .limit(limit)
            .offset(offset)
        )
        return [CommentRead.model_validate(comment) for comment in comments]

    async def get_comment(
        self,
        comment_id: int,
    ) -> CommentRead:
        comment = await self._db.scalar(
            self._comment_queries.get_comment(id=comment_id)
        )
        if not comment:
            raise comment_exc.CommentNotFoundError(
                message=f"Comment {comment_id} not found"
            )
        return CommentRead.model_validate(comment)

    async def update_comment(
        self,
        comment_id: int,
        content: str,
        current_user: UserModel,
    ) -> CommentRead:
        comment = await self._db.scalar(
            select(CommentModel).where(CommentModel.id == comment_id)
        )
        if not comment:
            raise comment_exc.CommentNotFoundError(
                message=f"Comment {comment_id} not found"
            )

        if comment.user_id != current_user.id:
            raise comment_exc.ForbiddenError(
                message="You can only update your own comments"
            )

        comment.content = content

        outbox_service = OutboxService(self._db)
        await outbox_service.publish(
            event_type=OutboxEventType.CREATED,
            entity_type="comment",
            entity_id=comment.id,
        )

        await self._db.commit()
        await self._db.refresh(comment)
        await self._indexer.index(comment)
        return CommentRead.model_validate(comment)

    async def delete_comment(
        self,
        comment_id: int,
        current_user: UserModel,
    ) -> None:
        comment = await self._db.scalar(
            self._comment_queries.get_comment(id=comment_id)
        )
        if not comment:
            raise comment_exc.CommentNotFoundError(
                message=f"Comment {comment_id} not found"
            )

        if comment.user_id != current_user.id:
            raise comment_exc.ForbiddenError(
                message="You can only delete your own comments"
            )

        outbox_service = OutboxService(self._db)
        await outbox_service.publish(
            event_type=OutboxEventType.DELETED,
            entity_type="comment",
            entity_id=comment.id,
        )

        await self._db.delete(comment)
        await self._db.commit()
        await self._indexer.delete({"type": "comment", "id": comment_id})


def get_comment_service(
    db: AsyncSession = Depends(db_helper.get_session),
    indexer: ElasticsearchIndexer = Depends(get_es_indexer),
) -> CommentService:
    return CommentService(db, indexer)
