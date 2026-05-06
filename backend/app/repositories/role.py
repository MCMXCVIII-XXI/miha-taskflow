from collections.abc import Sequence

from sqlalchemy import Select, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Role


class RoleRepository:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    def _apply_pagination(
        self,
        query: Select[tuple[Role]],
        limit: int | None = None,
        offset: int | None = None,
    ) -> Select[tuple[Role]]:
        if limit is not None:
            query = query.limit(limit)
        if offset is not None:
            query = query.offset(offset)
        return query

    def _build_query(
        self,
        id: int | None = None,
        name: str | None = None,
    ) -> Select[tuple[Role]]:
        query = select(Role)

        if id is not None:
            query = query.where(Role.id == id)
        if name is not None:
            query = query.where(Role.name == name)

        return query

    async def get(
        self,
        id: int | None = None,
        name: str | None = None,
    ) -> Role | None:
        query = self._build_query(id=id, name=name)
        return await self._db.scalar(query)

    async def find_many(
        self,
        id: int | None = None,
        name: str | None = None,
        limit: int | None = None,
        offset: int | None = None,
    ) -> Sequence[Role]:
        query = self._build_query(id=id, name=name)
        query = self._apply_pagination(query, limit=limit, offset=offset)

        result = await self._db.scalars(query)
        return result.all()

    async def add(self, name: str) -> Role:
        role = Role(name=name)
        self._db.add(role)
        await self._db.flush()
        return role

    async def get_id(
        self,
        id: int | None = None,
        name: str | None = None,
    ) -> int | None:
        query = select(Role.id)
        if id is not None:
            query = query.where(Role.id == id)
        if name is not None:
            query = query.where(Role.name == name)
        return await self._db.scalar(query)
