from collections.abc import Sequence

from sqlalchemy import Select, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import TaskAssignee


class TaskAssigneeRepository:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    def _apply_pagination(
        self,
        query: Select[tuple[TaskAssignee]],
        limit: int | None = None,
        offset: int | None = None,
    ) -> Select[tuple[TaskAssignee]]:
        if limit is not None:
            query = query.limit(limit)
        if offset is not None:
            query = query.offset(offset)
        return query

    def _build_query(
        self,
        id: int | None = None,
        task_id: int | None = None,
        user_id: int | None = None,
        with_relations: bool = False,
    ) -> Select[tuple[TaskAssignee]]:
        query = select(TaskAssignee)

        if with_relations:
            query = query.options(
                selectinload(TaskAssignee.task),
                selectinload(TaskAssignee.user),
            )

        if id is not None:
            query = query.where(TaskAssignee.id == id)
        if task_id is not None:
            query = query.where(TaskAssignee.task_id == task_id)
        if user_id is not None:
            query = query.where(TaskAssignee.user_id == user_id)

        return query

    async def get(
        self,
        id: int | None = None,
        task_id: int | None = None,
        user_id: int | None = None,
        with_relations: bool = False,
    ) -> TaskAssignee | None:
        query = self._build_query(
            id=id,
            task_id=task_id,
            user_id=user_id,
            with_relations=with_relations,
        )
        query = self._apply_pagination(query)
        return await self._db.scalar(query)

    async def find_many(
        self,
        id: int | None = None,
        task_id: int | None = None,
        user_id: int | None = None,
        with_relations: bool = False,
        limit: int | None = None,
        offset: int | None = None,
    ) -> Sequence[TaskAssignee]:
        query = self._build_query(
            id=id,
            task_id=task_id,
            user_id=user_id,
            with_relations=with_relations,
        )
        query = self._apply_pagination(query, limit=limit, offset=offset)

        result = await self._db.scalars(query)
        return result.unique().all()

    async def add(self, task_id: int, user_id: int) -> TaskAssignee:
        task_assignee = TaskAssignee(task_id=task_id, user_id=user_id)
        self._db.add(task_assignee)
        await self._db.flush()
        return task_assignee

    async def delete(self, task_assignee: TaskAssignee) -> None:
        await self._db.delete(task_assignee)
        await self._db.flush()

    async def by_task(self, task_id: int) -> Sequence[TaskAssignee]:
        query = select(TaskAssignee).where(TaskAssignee.task_id == task_id)
        result = await self._db.scalars(query)
        return result.all()

    async def by_user(self, user_id: int) -> Sequence[TaskAssignee]:
        query = select(TaskAssignee).where(TaskAssignee.user_id == user_id)
        result = await self._db.scalars(query)
        return result.all()

    async def by_task_and_user(self, task_id: int, user_id: int) -> TaskAssignee | None:
        query = (
            select(TaskAssignee)
            .where(TaskAssignee.task_id == task_id)
            .where(TaskAssignee.user_id == user_id)
        )
        return await self._db.scalar(query)
