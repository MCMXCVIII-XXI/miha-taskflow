from collections.abc import Sequence

from sqlalchemy import Select, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import UserSkill
from app.schemas.enum import TaskSphere


class UserSkillRepository:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    def _apply_pagination(
        self,
        query: Select[tuple[UserSkill]],
        limit: int | None = None,
        offset: int | None = None,
    ) -> Select[tuple[UserSkill]]:
        if limit is not None:
            query = query.limit(limit)
        if offset is not None:
            query = query.offset(offset)
        return query

    def _build_query(
        self,
        id: int | None = None,
        user_id: int | None = None,
        sphere: TaskSphere | None = None,
        xp_total: int | None = None,
        level: int | None = None,
        streak: int | None = None,
        is_frozen: bool | None = None,
    ) -> Select[tuple[UserSkill]]:
        query = select(UserSkill)

        if id is not None:
            query = query.where(UserSkill.id == id)
        if user_id is not None:
            query = query.where(UserSkill.user_id == user_id)
        if sphere is not None:
            query = query.where(UserSkill.sphere == sphere)
        if xp_total is not None:
            query = query.where(UserSkill.xp_total == xp_total)
        if level is not None:
            query = query.where(UserSkill.level == level)
        if streak is not None:
            query = query.where(UserSkill.streak == streak)
        if is_frozen is not None:
            query = query.where(UserSkill.is_frozen == is_frozen)

        return query

    async def get(
        self,
        id: int | None = None,
        user_id: int | None = None,
        sphere: TaskSphere | None = None,
        xp_total: int | None = None,
        level: int | None = None,
        streak: int | None = None,
        is_frozen: bool | None = None,
    ) -> UserSkill | None:
        query = self._build_query(
            id=id,
            user_id=user_id,
            sphere=sphere,
            xp_total=xp_total,
            level=level,
            streak=streak,
            is_frozen=is_frozen,
        )
        return await self._db.scalar(query)

    async def find_many(
        self,
        id: int | None = None,
        user_id: int | None = None,
        sphere: TaskSphere | None = None,
        xp_total: int | None = None,
        level: int | None = None,
        streak: int | None = None,
        is_frozen: bool | None = None,
        limit: int | None = None,
        offset: int | None = None,
    ) -> Sequence[UserSkill]:
        query = self._build_query(
            id=id,
            user_id=user_id,
            sphere=sphere,
            xp_total=xp_total,
            level=level,
            streak=streak,
            is_frozen=is_frozen,
        )
        query = self._apply_pagination(query, limit=limit, offset=offset)

        result = await self._db.scalars(query)
        return result.all()

    async def add(
        self,
        user_id: int,
        sphere: TaskSphere,
        xp_total: int = 0,
        xp_today: int = 0,
        level: int = 1,
        streak: int = 0,
        is_frozen: bool = False,
    ) -> UserSkill:
        user_skill = UserSkill(
            user_id=user_id,
            sphere=sphere,
            xp_total=xp_total,
            xp_today=xp_today,
            level=level,
            streak=streak,
            is_frozen=is_frozen,
        )
        self._db.add(user_skill)
        await self._db.flush()
        return user_skill

    async def by_user(
        self,
        user_id: int,
    ) -> Sequence[UserSkill]:
        query = select(UserSkill).where(UserSkill.user_id == user_id)
        result = await self._db.scalars(query)
        return result.all()

    async def get_user_skill_select(
        self,
        user_id: int | None = None,
        sphere: TaskSphere | None = None,
        limit: int | None = None,
        offset: int | None = None,
    ) -> Sequence[UserSkill]:
        query = self._build_query(user_id=user_id, sphere=sphere)
        query = self._apply_pagination(query, limit=limit, offset=offset)
        result = await self._db.scalars(query)
        return result.all()
