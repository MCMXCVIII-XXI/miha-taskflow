from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.log import logging
from app.db import db_helper
from app.models import Comment as CommentModel
from app.models import User as UserModel
from app.repositories import (
    UnitOfWork,
)
from app.schemas.enum import OutboxEventType

from ..exceptions import comment_exc, task_exc
from .base import BaseTransaction

logger = logging.get_logger(__name__)


class CommentTransaction(BaseTransaction):
    def __init__(
        self,
        uow_class: type[UnitOfWork],
        session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        super().__init__(uow_class=uow_class, session_factory=session_factory)

    async def create_comment(
        self,
        task_id: int,
        content: str,
        current_user: UserModel,
        parent_id: int | None = None,
    ) -> CommentModel:
        async with self._create_uow() as uow:
            task = await uow.task.get(
                id=task_id,
                is_active=True,
            )

            if not task:
                raise task_exc.TaskNotFound(message=f"Task {task_id} not found")

            if parent_id is not None:
                parent_comment = await uow.comment.get(
                    id=parent_id,
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

            comment = await uow.comment.add(
                task_id=task_id,
                user_id=current_user.id,
                content=content,
                parent_id=parent_id,
            )
            await uow.outbox.add(
                event_type=OutboxEventType.CREATED,
                entity_type="comment",
                entity_id=comment.id,
            )
            fresh_comment = await uow.comment.get(
                id=comment.id,
            )
        return fresh_comment

    async def update_comment(
        self,
        comment_id: int,
        content: str,
        current_user: UserModel,
    ) -> CommentModel:
        async with self._create_uow() as uow:
            comment = await uow.comment.get(
                id=comment_id,
            )
            if not comment:
                raise comment_exc.CommentNotFoundError(
                    message=f"Comment {comment_id} not found"
                )

            if comment.user_id != current_user.id:
                raise comment_exc.ForbiddenError(
                    message="You can only update your own comments"
                )

            comment = await uow.comment.update(
                comment=comment,
                content=content,
            )
            comment.content = content
            await uow.outbox.add(
                event_type=OutboxEventType.UPDATED,
                entity_type="comment",
                entity_id=comment.id,
            )
            fresh_comment = await uow.comment.get(
                id=comment.id,
            )
        return fresh_comment

    async def delete_comment(
        self,
        comment_id: int,
        current_user: UserModel,
    ) -> None:
        async with self._create_uow() as uow:
            comment = await uow.comment.get(
                id=comment_id,
            )
            if not comment:
                raise comment_exc.CommentNotFoundError(
                    message=f"Comment {comment_id} not found"
                )

            if comment.user_id != current_user.id:
                raise comment_exc.ForbiddenError(
                    message="You can only delete your own comments"
                )

            await uow.comment.delete(
                comment=comment,
            )
            await uow.outbox.add(
                event_type=OutboxEventType.DELETED,
                entity_type="comment",
                entity_id=comment.id,
            )


def get_comment_transaction() -> CommentTransaction:
    return CommentTransaction(
        uow_class=UnitOfWork,
        session_factory=db_helper.session_factory,
    )
