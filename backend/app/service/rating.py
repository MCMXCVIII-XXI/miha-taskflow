from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.log import get_logger
from app.db import db_helper
from app.models import Rating as RatingModel
from app.models import User as UserModel
from app.schemas import RatingRead, RatingStats
from app.schemas.enum import RatingTarget, TaskStatus

from .base import BaseService
from .exceptions import group_exc, rating_exc, task_exc

logger = get_logger("service.rating")


class RatingService(BaseService):
    """Service for managing user ratings and feedback for tasks and groups.

    This service handles creation, retrieval, and deletion of ratings for tasks
    and groups, along with statistical calculations for average ratings and counts.
    It enforces business rules such as preventing duplicate ratings and ensuring
    only completed tasks can be rated.

    Attributes:
        _db (AsyncSession): SQLAlchemy async database session
        _task_queries (TaskQueries): Task query service for verifying task status

    Raises:
        rating_exc.RatingAlreadyExists: When user tries to rate the same target twice
        rating_exc.RatingNotFound: When attempting to delete non-existent rating
        rating_exc.RatingForbiddenError: When user tries to delete another user's rating
        task_exc.TaskNotFound: When attempting to rate non-existent or incomplete task
    """

    def __init__(
        self,
        db: AsyncSession,
    ):
        """Initialize RatingService with database session.

        Args:
            db: SQLAlchemy async database session
            task_queries: Task query service for verifying task status
            group_queries: Group query service for verifying group status
            rating_queries: Rating query service for creating/retrieving ratings
        """
        super().__init__(db)

    async def create_rating(
        self,
        target_id: int,
        target_type: RatingTarget,
        score: int,
        current_user: UserModel,
    ) -> RatingRead:
        """Create a new rating for a task or group.

        Validates that target exists and is eligible for rating before creating
        a new rating entry. For tasks, ensures they are completed (DONE status).
        Prevents duplicate ratings from the same user for the same target.

        Args:
            target_id: ID of the task or group being rated
            target_type: Type of target (TASK or GROUP)
            score: Rating score (typically 1-5)
            current_user: User creating the rating

        Returns:
            RatingRead: Created rating information

        Raises:
            task_exc.TaskNotFound: If task not found or not completed
            rating_exc.RatingAlreadyExists: If user already rated this target
        """
        if target_type == RatingTarget.TASK:
            task = await self._db.scalar(
                self._task_queries.get_task(
                    id=target_id, status=TaskStatus.DONE, is_active=True
                )
            )
            if not task:
                raise task_exc.TaskNotFound(
                    message=f"Task {target_id} not found or not completed"
                )
        elif target_type == RatingTarget.GROUP:
            group = await self._db.scalar(
                self._group_queries.get_group(
                    id=target_id,
                    is_active=True,
                )
            )
            if not group:
                raise group_exc.GroupNotFound(message=f"Group {target_id} not found")

        existing = await self._db.scalar(
            self._rating_queries.get_rating(
                target_id=target_id, target_type=target_type, user_id=current_user.id
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
        """Get rating statistics for a specific target.

        Calculates average rating score and count of ratings for a given target.
        Returns zero stats if no ratings exist for the target.

        Args:
            target_id: ID of the task or group to get ratings for
            target_type: Type of target (TASK or GROUP)

        Returns:
            RatingStats: Rating statistics including average score and count
        """
        result = await self._db.execute(
            self._rating_queries.aggregate_stats_by_target(
                target_id=target_id, target_type=target_type
            )
        )
        row = result.one_or_none()

        if row is None:
            return RatingStats(target_id=target_id, average_score=0.0, count=0)

        return RatingStats(
            target_id=row.target_id,
            average_score=float(row.avg_score or 0.0),
            count=row.count,
        )

    async def get_task_rating(self, task_id: int) -> RatingStats:
        """Get rating statistics for a specific task.

        Convenience method that calls get_rating with TASK target type.

        Args:
            task_id: ID of the task to get ratings for

        Returns:
            RatingStats: Task rating statistics
        """
        return await self.get_rating(task_id, RatingTarget.TASK)

    async def get_group_rating(self, group_id: int) -> RatingStats:
        """Get rating statistics for a specific group.

        Convenience method that calls get_rating with GROUP target type.

        Args:
            group_id: ID of the group to get ratings for

        Returns:
            RatingStats: Group rating statistics
        """
        return await self.get_rating(group_id, RatingTarget.GROUP)

    async def delete_rating(
        self,
        rating_id: int,
        current_user: UserModel,
    ) -> None:
        """Delete a user's rating.

        Validates that the rating exists and belongs to the requesting user
        before deleting it from the database.

        Args:
            rating_id: ID of the rating to delete
            current_user: User requesting deletion (must own the rating)

        Returns:
            None: Success status only

        Raises:
            rating_exc.RatingNotFound: If rating doesn't exist
            rating_exc.RatingForbiddenError: If user doesn't own the rating
        """
        rating = await self._db.scalar(self._rating_queries.get_rating(id=rating_id))
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
    """Create RatingService instance with database dependency.

    Args:
        db: Database session dependency injected by FastAPI

    Returns:
        RatingService: Initialized rating service instance
    """
    return RatingService(
        db=db,
    )
