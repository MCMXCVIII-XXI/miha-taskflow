from abc import ABC, abstractmethod
from typing import Any

from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Task as TaskModel
from app.models import User as UserModel
from app.models import UserGroup as UserGroupModel
from app.schemas.enum import (
    GlobalUserRole,
    TaskPriority,
    TaskStatus,
)


class AbstractStatsModel(ABC):
    @abstractmethod
    async def _convert_result(self, result: Any) -> dict[str, Any]:
        pass

    @abstractmethod
    async def get_stats(self) -> dict[str, Any]:
        pass


class StatsUsers:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def _convert_result(self, result: Any) -> dict[str, Any]:
        if result:
            data = dict(result.mappings().first() or {})
            return {
                "total": data.get("total", 0),
                "active": data.get("active", 0),
                "not_active": data.get("not_active", 0),
                "admins": data.get("admins", 0),
            }
        return {"total": 0, "active": 0, "not_active": 0, "admins": 0}

    async def get_stats(self) -> dict[str, Any]:
        query = select(
            func.count(UserModel.id).label("total"),
            func.count(case((UserModel.is_active, 1))).label("active"),
            func.count(case((UserModel.is_active == False, 1))).label("not_active"),  # noqa: E712
            func.count(case((UserModel.role == GlobalUserRole.ADMIN, 1))).label(
                "admins"
            ),
        )
        result = await self._db.execute(query)
        return await self._convert_result(result)


class StatsGroups:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def _convert_result(self, result: Any) -> dict[str, Any]:
        if result:
            data = dict(result.mappings().first() or {})
            return {
                "total": data.get("total", 0),
                "active": data.get("active", 0),
                "not_active": data.get("not_active", 0),
            }
        return {"total": 0, "active": 0, "not_active": 0}

    async def get_stats(self) -> dict[str, Any]:
        query = select(
            func.count(UserGroupModel.id).label("total"),
            func.count(case((UserGroupModel.is_active, 1))).label("active"),
            func.count(case((UserGroupModel.is_active == False, 1))).label(  # noqa: E712
                "not_active"
            ),
        )
        result = await self._db.execute(query)
        return await self._convert_result(result)


class StatsTasks:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def _convert_result(self, result: Any) -> dict[str, Any]:
        if result:
            data = dict(result.mappings().first() or {})
            return {
                "total": data.get("total", 0),
                "active": data.get("active", 0),
                "not_active": data.get("not_active", 0),
                "status": {
                    "pending": data.get("pending", 0),
                    "in_progress": data.get("in_progress", 0),
                    "completed": data.get("completed", 0),
                },
                "priority": {
                    "low": data.get("low", 0),
                    "medium": data.get("medium", 0),
                    "high": data.get("high", 0),
                },
            }
        return {
            "total": 0,
            "active": 0,
            "not_active": 0,
            "status": {"pending": 0, "in_progress": 0, "completed": 0},
            "priority": {"low": 0, "medium": 0, "high": 0},
        }

    async def get_stats(self) -> dict[str, Any]:
        query = select(
            func.count(TaskModel.id).label("total"),
            func.count(case((TaskModel.is_active, 1))).label("active"),
            func.count(case((TaskModel.is_active == False, 1))).label("not_active"),  # noqa: E712
            func.count(case((TaskModel.status == TaskStatus.PENDING, 1))).label(
                "pending"
            ),
            func.count(case((TaskModel.status == TaskStatus.IN_PROGRESS, 1))).label(
                "in_progress"
            ),
            func.count(case((TaskModel.status == TaskStatus.DONE, 1))).label(
                "completed"
            ),
            func.count(case((TaskModel.priority == TaskPriority.HIGH, 1))).label(
                "high"
            ),
            func.count(case((TaskModel.priority == TaskPriority.MEDIUM, 1))).label(
                "medium"
            ),
            func.count(case((TaskModel.priority == TaskPriority.LOW, 1))).label("low"),
        )
        result = await self._db.execute(query)
        return await self._convert_result(result)
