"""Rating service for user feedback on tasks and groups.

This module provides the RatingService class for managing user ratings
and feedback for tasks and groups, including creation, retrieval, and deletion.

**Key Components:**
* `RatingService`: Main service class for rating operations;
* `get_rating_service`: FastAPI dependency injection factory.

**Dependencies:**
* `RatingRepository`: Rating data access layer;
* `TaskRepository`: Task data access layer;
* `GroupRepository`: Group data access layer;
* `UnitOfWork`: Transaction management (via BaseService).

**Usage Example:**
    ```python
    from app.service.rating import get_rating_service

    @router.post("/tasks/{task_id}/rate")
    async def rate_task(
        task_id: int,
        score: int,
        rating_svc: RatingService = Depends(get_rating_service),
        current_user: User = Depends(get_current_user)
    ):
        return await rating_svc.create_rating(
            task_id, RatingTarget.TASK, score, current_user
        )
    ```

**Notes:**
- Tasks can only be rated when they have DONE status;
- Users can only rate once per target (task or group);
- Ratings support scores typically in range 1-10;
- Statistics are computed in real-time from database.
"""

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.log import logging
from app.core.metrics import METRICS
from app.db import db_helper
from app.models import User as UserModel
from app.schemas import RatingRead, RatingStats
from app.schemas.enum import RatingTarget

from .base import BaseService
from .transactions.rating import RatingTransaction, get_rating_transaction

logger = logging.get_logger(__name__)


class RatingService(BaseService):
    """Service for managing user ratings and feedback for tasks and groups.

    Handles creation, retrieval, and deletion of ratings for tasks and groups.
    Enforces business rules such as preventing duplicate ratings and ensuring
    only completed tasks can be rated.

    Attributes:
        _db (AsyncSession): SQLAlchemy async database session
        _task_repo (TaskRepository): Repository for task data operations
        _group_repo (GroupRepository): Repository for group data operations
        _rating_repo (RatingRepository): Repository for rating data operations

    Example:
        ```python
        rating_service = RatingService(db_session)
        rating = await rating_service.create_rating(
            target_id=123,
            target_type=RatingTarget.TASK,
            score=8,
            current_user=user
        )
        ```
    """

    def __init__(
        self,
        db: AsyncSession,
        rating_transaction: RatingTransaction,
    ) -> None:
        """Initialize RatingService with database session.

        Args:
            db: SQLAlchemy async database session
        """
        super().__init__(db)
        self._rating_transaction = rating_transaction

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
                Type: int
                Constraints: Must be > 0, target must exist
            target_type: Type of target being rated
                Type: RatingTarget
                Values: TASK, GROUP
            score: Rating score value
                Type: int
                Constraints: Typically 1-10
            current_user: User creating the rating
                Type: UserModel

        Returns:
            RatingRead: Created rating serialized according to RatingRead schema

        Raises:
            task_exc.TaskNotFound: If task not found or not completed
            group_exc.GroupNotFound: If group not found
            rating_exc.RatingAlreadyExists: If user already rated this target

        Example:
            ```python
            rating = await rating_svc.create_rating(
                target_id=123,
                target_type=RatingTarget.TASK,
                score=8,
                current_user=user
            )
            ```
        """
        rating = await self._rating_transaction.create_rating(
            target_id=target_id,
            target_type=target_type,
            score=score,
            current_user=current_user,
        )

        logger.info(
            "Rating created: id={rating_id}, target_id={target_id},\
                target_type={target_type}, score={score}, user_id={user_id}",
            rating_id=rating.id,
            target_id=target_id,
            target_type=target_type.value,
            score=score,
            user_id=current_user.id,
        )
        METRICS.SOCIAL_ACTIONS_TOTAL.labels(
            type="rating", action="create", status="success"
        ).inc()
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
                Type: int
                Constraints: Must be > 0
            target_type: Type of target to get ratings for
                Type: RatingTarget
                Values: TASK, GROUP

        Returns:
            RatingStats: Statistics containing average_score and count

        Raises:
            None

        Example:
            ```python
            stats = await rating_svc.get_rating(123, RatingTarget.TASK)
            # Returns: RatingStats(target_id=123, average_score=7.5, count=10)
            ```
        """
        result = await self._rating_repo.aggregate_stats_by_target(
            target_id=target_id,
            target_type=target_type,
        )

        if not result:
            logger.info(
                "Rating stats retrieved (no ratings):\
                    target_id={target_id}, target_type={target_type}",
                target_id=target_id,
                target_type=target_type.value,
            )
            return RatingStats(target_id=target_id, average_score=0.0, count=0)

        row = result[0]
        stats = RatingStats(
            target_id=row[0],
            average_score=float(row[1]) if row[1] is not None else 0.0,
            count=row[2],
        )

        logger.info(
            "Rating stats retrieved: target_id={target_id},\
                target_type={target_type}, average={average}, count={count}",
            target_id=target_id,
            target_type=target_type.value,
            average=stats.average_score,
            count=stats.count,
        )

        return stats

    async def get_task_rating(self, task_id: int) -> RatingStats:
        """Get rating statistics for a specific task.

        Convenience method that calls get_rating with TASK target type.

        Args:
            task_id: ID of the task to get ratings for
                Type: int
                Constraints: Must be > 0

        Returns:
            RatingStats: Task rating statistics

        Raises:
            None

        Example:
            ```python
            stats = await rating_svc.get_task_rating(123)
            ```
        """
        result = await self.get_rating(task_id, RatingTarget.TASK)

        logger.info(
            "Task rating retrieved: task_id={task_id},\
                average={average}, count={count}",
            task_id=task_id,
            average=result.average_score,
            count=result.count,
        )

        return result

    async def get_group_rating(self, group_id: int) -> RatingStats:
        """Get rating statistics for a specific group.

        Convenience method that calls get_rating with GROUP target type.

        Args:
            group_id: ID of the group to get ratings for
                Type: int
                Constraints: Must be > 0

        Returns:
            RatingStats: Group rating statistics

        Raises:
            None

        Example:
            ```python
            stats = await rating_svc.get_group_rating(123)
            ```
        """
        result = await self.get_rating(group_id, RatingTarget.GROUP)

        logger.info(
            "Group rating retrieved: group_id={group_id},\
                average={average}, count={count}",
            group_id=group_id,
            average=result.average_score,
            count=result.count,
        )

        return result

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
                Type: int
                Constraints: Must be > 0
            current_user: User requesting deletion (must own the rating)
                Type: UserModel

        Returns:
            None

        Raises:
            rating_exc.RatingNotFound: If rating doesn't exist
            rating_exc.RatingForbiddenError: If user doesn't own the rating

        Example:
            ```python
            await rating_svc.delete_rating(rating_id=123, current_user=user)
            ```
        """
        await self._rating_transaction.delete_rating(
            rating_id=rating_id, current_user=current_user
        )

        logger.info(
            "Rating deleted: id={rating_id}, user_id={user_id}",
            rating_id=rating_id,
            user_id=current_user.id,
        )
        METRICS.SOCIAL_ACTIONS_TOTAL.labels(
            type="rating", action="delete", status="success"
        ).inc()


def get_rating_service(
    db: AsyncSession = Depends(db_helper.get_session),
    rating_transaction: RatingTransaction = Depends(get_rating_transaction),
) -> RatingService:
    """Create RatingService instance with dependency injection.

    Factory function for FastAPI dependency injection that creates and configures
    a RatingService instance with all required dependencies.

    Args:
        db: Database session from FastAPI dependency injection.
            Type: AsyncSession.

    Returns:
        RatingService: Configured rating service instance

    Example:
        ```python
        @router.post("/tasks/{task_id}/rate")
        async def rate_task(
            task_id: int,
            score: int,
            rating_svc: RatingService = Depends(get_rating_service),
            current_user: User = Depends(get_current_user)
        ):
            return await rating_svc.create_rating(
                task_id, RatingTarget.TASK, score, current_user
            )
        ```
    """
    return RatingService(
        db=db,
        rating_transaction=rating_transaction,
    )
