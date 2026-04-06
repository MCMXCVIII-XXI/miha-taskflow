from fastapi import Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.log import get_logger
from app.db import db_helper
from app.models import Rating as RatingModel
from app.models import Task as TaskModel
from app.models import User as UserModel
from app.schemas import RatingRead, RatingStats
from app.schemas.enum import RatingTarget, TaskStatus

from .base import BaseService
from .exceptions import rating_exc, task_exc

logger = get_logger("service.rating")


class RatingService(BaseService):
    def __init__(self, db: AsyncSession):
        super().__init__(db)

    async def create_rating(
        self,
        target_id: int,
        target_type: RatingTarget,
        score: int,
        current_user: UserModel,
    ) -> RatingRead:
        if target_type == RatingTarget.TASK:
            task = await self._db.scalar(
                select(TaskModel).where(
                    TaskModel.id == target_id,
                    TaskModel.is_active == True,  # noqa: E712
                    TaskModel.status == TaskStatus.DONE,
                )
            )
            if not task:
                raise task_exc.TaskNotFound(
                    message=f"Task {target_id} not found or not completed"
                )

        existing = await self._db.scalar(
            select(RatingModel).where(
                RatingModel.user_id == current_user.id,
                RatingModel.target_id == target_id,
                RatingModel.target_type == target_type,
            )
        )
        if existing:
            raise rating_exc.RatingAlreadyExists(
                message="You have already rated this target"
            )

        rating = RatingModel(
            user_id=current_user.id,
            target_id=target_id,
            target_type=target_type,
            score=score,
        )
        self._db.add(rating)
        await self._db.commit()
        return RatingRead.model_validate(rating)

    async def get_rating(
        self,
        target_id: int,
        target_type: RatingTarget,
    ) -> RatingStats:
        result = await self._db.execute(
            select(
                RatingModel.target_id,
                func.avg(RatingModel.score).label("avg_score"),
                func.count(RatingModel.id).label("count"),
            )
            .where(
                RatingModel.target_id == target_id,
                RatingModel.target_type == target_type,
            )
            .group_by(RatingModel.target_id)
        )
        row = result.one_or_none()

        if row is None:
            return RatingStats(target_id=target_id, avg_score=0.0, count=0)

        return RatingStats(
            target_id=row.target_id,
            avg_score=float(row.avg_score or 0.0),
            count=row.count,
        )

    async def get_task_rating(self, task_id: int) -> RatingStats:
        return await self.get_rating(task_id, RatingTarget.TASK)

    async def get_group_rating(self, group_id: int) -> RatingStats:
        return await self.get_rating(group_id, RatingTarget.GROUP)

    async def delete_rating(
        self,
        rating_id: int,
        current_user: UserModel,
    ) -> None:
        rating = await self._db.scalar(
            select(RatingModel).where(RatingModel.id == rating_id)
        )
        if not rating:
            raise rating_exc.RatingNotFound(message=f"Rating {rating_id} not found")

        if rating.user_id != current_user.id:
            raise rating_exc.RatingForbiddenError(
                message="You can only delete your own ratings"
            )

        await self._db.delete(rating)
        await self._db.commit()


def get_rating_service(
    db: AsyncSession = Depends(db_helper.get_session),
) -> RatingService:
    return RatingService(db)
