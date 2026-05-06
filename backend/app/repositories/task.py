from collections.abc import Sequence
from datetime import datetime
from typing import Any, Literal

from sqlalchemy import Select, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload, selectinload

from app.models import Task, TaskAssignee, UserGroup, UserGroupMembership
from app.schemas.enum import TaskDifficulty, TaskPriority, TaskStatus, TaskVisibility


class TaskRepository:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    def _apply_pagination(
        self,
        query: Select[tuple[Task]],
        limit: int | None = None,
        offset: int | None = None,
    ) -> Select[tuple[Task]]:
        if limit is not None:
            query = query.limit(limit)
        if offset is not None:
            query = query.offset(offset)
        return query

    def _check_active(
        self,
        query: Select[tuple[Task]],
        is_active: Literal[True, False, None],
    ) -> Select[tuple[Task]]:
        if is_active is None:
            return query
        return query.where(Task.is_active == is_active)

    def _build_query(
        self,
        id: int | None = None,
        title: str | None = None,
        status: TaskStatus | None = None,
        priority: TaskPriority | None = None,
        difficulty: TaskDifficulty | None = None,
        visibility: TaskVisibility | None = None,
        deadline: datetime | None = None,
        group_id: int | None = None,
        is_active: Literal[True, False, None] = None,
    ) -> Select[tuple[Task]]:
        query = select(Task)

        if id is not None:
            query = query.where(Task.id == id)
        if title is not None:
            query = query.where(Task.title == title)
        if status is not None:
            query = query.where(Task.status == status)
        if priority is not None:
            query = query.where(Task.priority == priority)
        if difficulty is not None:
            query = query.where(Task.difficulty == difficulty)
        if visibility is not None:
            query = query.where(Task.visibility == visibility)
        if deadline is not None:
            query = query.where(Task.deadline == deadline)
        if group_id is not None:
            query = query.where(Task.group_id == group_id)
        if is_active is not None:
            query = query.where(Task.is_active == is_active)

        return self._check_active(query, is_active)

    async def get(
        self,
        id: int | None = None,
        title: str | None = None,
        status: TaskStatus | None = None,
        priority: TaskPriority | None = None,
        difficulty: TaskDifficulty | None = None,
        visibility: TaskVisibility | None = None,
        deadline: datetime | None = None,
        group_id: int | None = None,
        is_active: Literal[True, False, None] = None,
    ) -> Task | None:
        query = self._build_query(
            id=id,
            title=title,
            status=status,
            priority=priority,
            difficulty=difficulty,
            visibility=visibility,
            deadline=deadline,
            group_id=group_id,
            is_active=is_active,
        )
        return await self._db.scalar(query)

    async def find_many(
        self,
        id: int | None = None,
        title: str | None = None,
        status: TaskStatus | None = None,
        priority: TaskPriority | None = None,
        difficulty: TaskDifficulty | None = None,
        visibility: TaskVisibility | None = None,
        deadline: datetime | None = None,
        group_id: int | None = None,
        is_active: Literal[True, False, None] = None,
        limit: int | None = None,
        offset: int | None = None,
    ) -> Sequence[Task]:
        query = self._build_query(
            id=id,
            title=title,
            status=status,
            priority=priority,
            difficulty=difficulty,
            visibility=visibility,
            deadline=deadline,
            group_id=group_id,
            is_active=is_active,
        )
        query = self._apply_pagination(query, limit=limit, offset=offset)
        result = await self._db.scalars(query)
        return result.all()

    async def add(
        self,
        title: str,
        description: str | None,
        priority: TaskPriority,
        difficulty: TaskDifficulty | None,
        visibility: TaskVisibility,
        group_id: int | None,
        spheres: list[dict[str, Any]] | None,
        deadline: datetime | None,
    ) -> Task:
        task = Task(
            title=title,
            description=description,
            priority=priority,
            difficulty=difficulty,
            visibility=visibility,
            spheres=spheres,
            deadline=deadline,
            group_id=group_id,
        )
        self._db.add(task)
        await self._db.flush()
        return task

    async def update(
        self,
        task: Task,
        task_update: dict[str, Any] | None = None,
    ) -> Task:
        if not task_update:
            return task

        for key, value in task_update.items():
            setattr(task, key, value)
        await self._db.flush()
        return task

    async def delete(
        self,
        task: Task,
    ) -> None:
        await self._db.delete(task)
        await self._db.flush()

    async def by_assigned(
        self,
        user_id: int,
        is_active: Literal[True, False, None] = None,
    ) -> Sequence[Task]:
        query = select(Task).join(TaskAssignee).where(TaskAssignee.user_id == user_id)
        result = await self._db.scalars(self._check_active(query, is_active))
        return result.all()

    async def by_member(
        self,
        user_id: int,
        is_active: Literal[True, False, None] = None,
    ) -> Sequence[Task]:
        query = (
            select(Task)
            .join(UserGroup, Task.group_id == UserGroup.id)
            .join(UserGroupMembership, UserGroupMembership.group_id == UserGroup.id)
            .where(UserGroupMembership.user_id == user_id)
        )
        result = await self._db.scalars(self._check_active(query, is_active))
        return result.all()

    async def by_owner(
        self,
        group_ids: list[int],
        is_active: Literal[True, False, None] = None,
    ) -> Sequence[Task]:
        query = select(Task).where(Task.group_id.in_(group_ids))
        result = await self._db.scalars(self._check_active(query, is_active))
        return result.all()

    async def all_with_relations(
        self,
        is_active: Literal[True, False, None] = None,
    ) -> Sequence[Task]:
        query = select(Task).options(
            joinedload(Task.group),
            selectinload(Task.assignees),
            selectinload(Task.comments),
        )
        result = await self._db.scalars(query)
        return result.unique().all()

    async def get_task_select(
        self,
        id: int | None = None,
        title: str | None = None,
        status: TaskStatus | None = None,
        priority: TaskPriority | None = None,
        difficulty: TaskDifficulty | None = None,
        visibility: TaskVisibility | None = None,
        deadline: datetime | None = None,
        group_id: int | None = None,
        is_active: Literal[True, False, None] = None,
    ) -> Task | None:
        query = self._build_query(
            id=id,
            title=title,
            status=status,
            priority=priority,
            difficulty=difficulty,
            visibility=visibility,
            deadline=deadline,
            group_id=group_id,
            is_active=is_active,
        )
        return await self._db.scalar(query)

    async def by_assigned_select(
        self,
        user_id: int,
        is_active: Literal[True, False, None] = None,
    ) -> Task | None:
        query = select(Task).join(TaskAssignee).where(TaskAssignee.user_id == user_id)
        query = self._check_active(query, is_active)
        return await self._db.scalar(query)

    async def by_owner_select(
        self,
        group_ids: list[int],
        is_active: Literal[True, False, None] = None,
    ) -> Task | None:
        query = select(Task).where(Task.group_id.in_(group_ids))
        query = self._check_active(query, is_active)
        return await self._db.scalar(query)

    async def get_by_group_ids(
        self,
        task_id: int,
        group_ids: list[int] | Sequence[int],
        is_active: Literal[True, False, None] = True,
    ) -> Task | None:
        """
        Get task by ID if it belongs to any of the specified group IDs.

        Args:
            task_id: Task ID to find
            group_ids: List of group IDs to check ownership
            is_active: Filter by active status

        Returns:
            Task if found in any group, None otherwise

        Example:
            ```python
            task = await repo.get_by_group_ids(123, [1, 2, 3])
            ```
        """
        query = select(Task).where(
            Task.id == task_id,
            Task.group_id.in_(group_ids),
        )
        query = self._check_active(query, is_active)

        return await self._db.scalar(query)

    async def all_with_relations_select(
        self,
        is_active: Literal[True, False, None] = None,
    ) -> Task | None:
        query = select(Task).options(
            joinedload(Task.group),
            selectinload(Task.assignees),
            selectinload(Task.comments),
        )
        query = self._check_active(query, is_active)
        return await self._db.scalar(query)
