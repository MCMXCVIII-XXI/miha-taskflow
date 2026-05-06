from collections.abc import Sequence

from sqlalchemy import Select, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import UserRole


class UserRoleRepository:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    def _apply_pagination(
        self,
        query: Select[tuple[UserRole]],
        limit: int | None = None,
        offset: int | None = None,
    ) -> Select[tuple[UserRole]]:
        if limit is not None:
            query = query.limit(limit)
        if offset is not None:
            query = query.offset(offset)
        return query

    def _build_query(
        self,
        id: int | None = None,
        user_id: int | None = None,
        role_id: int | None = None,
        group_id: int | None = None,
        task_id: int | None = None,
    ) -> Select[tuple[UserRole]]:
        query = select(UserRole)

        if id is not None:
            query = query.where(UserRole.id == id)
        if user_id is not None:
            query = query.where(UserRole.user_id == user_id)
        if role_id is not None:
            query = query.where(UserRole.role_id == role_id)
        if group_id is not None:
            query = query.where(UserRole.group_id == group_id)
        if task_id is not None:
            query = query.where(UserRole.task_id == task_id)

        return query

    async def get(
        self,
        id: int | None = None,
        user_id: int | None = None,
        role_id: int | None = None,
        group_id: int | None = None,
        task_id: int | None = None,
    ) -> UserRole | None:
        query = self._build_query(
            id=id,
            user_id=user_id,
            role_id=role_id,
            group_id=group_id,
            task_id=task_id,
        )
        query = self._apply_pagination(query)
        return await self._db.scalar(query)

    async def find_many(
        self,
        id: int | None = None,
        user_id: int | None = None,
        role_id: int | None = None,
        group_id: int | None = None,
        task_id: int | None = None,
        limit: int | None = None,
        offset: int | None = None,
    ) -> Sequence[UserRole]:
        query = self._build_query(
            id=id,
            user_id=user_id,
            role_id=role_id,
            group_id=group_id,
            task_id=task_id,
        )
        query = self._apply_pagination(query, limit=limit, offset=offset)

        result = await self._db.scalars(query)
        return result.all()

    async def add(
        self,
        user_id: int,
        role_id: int,
        group_id: int | None = None,
        task_id: int | None = None,
    ) -> UserRole:
        user_role = UserRole(
            user_id=user_id,
            role_id=role_id,
            group_id=group_id,
            task_id=task_id,
        )
        self._db.add(user_role)
        await self._db.flush()
        return user_role

    async def delete(
        self,
        user_role: UserRole,
    ) -> None:
        await self._db.delete(user_role)
        await self._db.flush()
