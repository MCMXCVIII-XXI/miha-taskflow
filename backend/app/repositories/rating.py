from collections.abc import Sequence
from typing import Any

from sqlalchemy import Row, Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Rating
from app.schemas.enum import RatingTarget


class RatingRepository:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    def _apply_pagination(
        self,
        query: Select[tuple[Rating]],
        limit: int | None = None,
        offset: int | None = None,
    ) -> Select[tuple[Rating]]:
        if limit is not None:
            query = query.limit(limit)
        if offset is not None:
            query = query.offset(offset)
        return query

    def _build_query(
        self,
        id: int | None = None,
        user_id: int | None = None,
        target_id: int | None = None,
        target_type: RatingTarget | None = None,
    ) -> Select[tuple[Rating]]:
        query = select(Rating)

        if id is not None:
            query = query.where(Rating.id == id)
        if user_id is not None:
            query = query.where(Rating.user_id == user_id)
        if target_id is not None:
            query = query.where(Rating.target_id == target_id)
        if target_type is not None:
            query = query.where(Rating.target_type == target_type)

        return query

    async def get(
        self,
        id: int | None = None,
        user_id: int | None = None,
        target_id: int | None = None,
        target_type: RatingTarget | None = None,
    ) -> Rating | None:
        query = self._build_query(
            id=id,
            user_id=user_id,
            target_id=target_id,
            target_type=target_type,
        )
        return await self._db.scalar(query)

    async def find_many(
        self,
        id: int | None = None,
        user_id: int | None = None,
        target_id: int | None = None,
        target_type: RatingTarget | None = None,
        limit: int | None = None,
        offset: int | None = None,
    ) -> Sequence[Rating]:
        query = self._build_query(
            id=id,
            user_id=user_id,
            target_id=target_id,
            target_type=target_type,
        )
        query = self._apply_pagination(query, limit=limit, offset=offset)

        result = await self._db.scalars(query)
        return result.all()

    async def add(
        self,
        user_id: int,
        target_id: int,
        target_type: RatingTarget,
        score: int,
    ) -> Rating:
        rating = Rating(
            user_id=user_id,
            target_id=target_id,
            target_type=target_type,
            score=score,
        )
        self._db.add(rating)
        await self._db.flush()
        return rating

    async def delete(
        self,
        rating: Rating,
    ) -> None:
        await self._db.delete(rating)
        await self._db.flush()

    async def aggregate_stats_by_target(
        self,
        target_id: int | None = None,
        target_type: RatingTarget | None = None,
    ) -> Sequence[Row[Any]]:
        query = select(
            Rating.target_id,
            func.avg(Rating.score).label("avg_score"),
            func.count(Rating.id).label("count"),
        ).group_by(Rating.target_id)

        if target_id is not None:
            query = query.where(Rating.target_id == target_id)
        if target_type is not None:
            query = query.where(Rating.target_type == target_type)

        result = await self._db.execute(query)
        return result.all()
