from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.log import logging
from app.db import db_helper
from app.models import Rating as RatingModel
from app.models import User as UserModel
from app.repositories import UnitOfWork
from app.schemas.enum import RatingTarget, TaskStatus

from ..exceptions import group_exc, rating_exc, task_exc
from .base import BaseTransaction

logger = logging.get_logger(__name__)


class RatingTransaction(BaseTransaction):
    def __init__(
        self,
        uow_class: type[UnitOfWork],
        session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        super().__init__(uow_class=uow_class, session_factory=session_factory)

    async def create_rating(
        self,
        target_id: int,
        target_type: RatingTarget,
        score: int,
        current_user: UserModel,
    ) -> RatingModel:
        async with self._create_uow() as uow:
            if target_type == RatingTarget.TASK:
                task = await uow.task.get(
                    id=target_id,
                    status=TaskStatus.DONE,
                    is_active=True,
                )
                if not task:
                    raise task_exc.TaskNotFound(
                        message=f"Task {target_id} not found or not completed"
                    )
            elif target_type == RatingTarget.GROUP:
                group = await uow.group.get(
                    id=target_id,
                    is_active=True,
                )
                if not group:
                    raise group_exc.GroupNotFound(
                        message=f"Group {target_id} not found"
                    )

            existing = await uow.rating.get(
                target_id=target_id,
                target_type=target_type,
                user_id=current_user.id,
            )
            if existing:
                logger.warning(
                    "Rating failed: \
                        user {user_id} already rated {target_type} {target_id}",
                    user_id=current_user.id,
                    target_type=target_type.value,
                    target_id=target_id,
                )
                raise rating_exc.RatingAlreadyExists(
                    message="You have already rated this target"
                )

            rating = await uow.rating.add(
                user_id=current_user.id,
                target_id=target_id,
                target_type=target_type,
                score=score,
            )

        return rating

    async def delete_rating(
        self,
        rating_id: int,
        current_user: UserModel,
    ) -> None:
        async with self._create_uow() as uow:
            rating = await uow.rating.get(id=rating_id)
            if not rating:
                raise rating_exc.RatingNotFound(message=f"Rating {rating_id} not found")

            if rating.user_id != current_user.id:
                raise rating_exc.RatingForbiddenError(
                    message="You can only delete your own ratings"
                )

            await uow.rating.delete(rating=rating)


def get_rating_transaction() -> RatingTransaction:
    return RatingTransaction(
        uow_class=UnitOfWork,
        session_factory=db_helper.session_factory,
    )
