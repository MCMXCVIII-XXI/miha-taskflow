from sqlalchemy import Select, func, select

from app.models import Rating
from app.schemas.enum import RatingTarget


class RatingQueries:
    """
    Query builders for Rating-related operations.

    Provides reusable Select[tuple[Rating]] filters for ratings by ID, user,
    target, and target type.
    """

    @staticmethod
    def get_rating(
        id: int | None = None,
        user_id: int | None = None,
        target_id: int | None = None,
        target_type: RatingTarget | None = None,
    ) -> Select[tuple[Rating]]:
        """
        Builds a query to filter ratings by multiple criteria.

        Args:
            id: Filter by rating ID.
            user_id: Filter by user ID (who rated).
            target_id: Filter by target ID (e.g., task/user ID).
            target_type: Filter by target type (enum).

        Returns:
            Select[tuple[Rating]] for matching ratings.
        """
        base = select(Rating)

        if id is not None:
            base = base.where(Rating.id == id)
        if user_id is not None:
            base = base.where(Rating.user_id == user_id)
        if target_id is not None:
            base = base.where(Rating.target_id == target_id)
        if target_type is not None:
            base = base.where(Rating.target_type == target_type)

        return base

    @staticmethod
    def aggregate_stats_by_target(
        target_id: int | None = None,
        target_type: RatingTarget | None = None,
    ) -> Select[tuple[int, float, int]]:
        """
        Builds a query to get aggregated rating stats for a specific target.

        Returns:
            - target_id
            - avg_score
            - count of ratings
        grouped by target_id.

        Args:
            target_id: Target ID to filter by (optional).
            target_type: Target type to filter by (optional).

        Returns:
            Select[tuple[int, float, int]] for (target_id, avg_score, count).
        """
        base = select(
            Rating.target_id,
            func.avg(Rating.score).label("avg_score"),
            func.count(Rating.id).label("count"),
        ).group_by(Rating.target_id)

        if target_id is not None:
            base = base.where(Rating.target_id == target_id)
        if target_type is not None:
            base = base.where(Rating.target_type == target_type)

        return base
