from types import TracebackType
from typing import Any, Self

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.log import get_logger
from app.db import db_helper

from . import (
    comment,
    group,
    group_membership,
    join,
    notification,
    outbox,
    rating,
    role,
    task,
    task_assignee,
    user,
    user_role,
    user_skill,
)

logger = get_logger(__name__)


class UnitOfWork:
    def __init__(
        self,
        session_factory: async_sessionmaker[AsyncSession] | None = None,
        session: AsyncSession | None = None,
    ) -> None:
        self._session_factory = session_factory
        self._db = session
        self._is_external = session is not None
        self._repos: dict[str, Any] = {}
        self.events: list[dict[str, Any]] = []

    @property
    def session(self) -> AsyncSession:
        if self._db is None:
            raise RuntimeError("Session is not initialized")
        return self._db

    def __getattr__(self, name: str) -> Any:
        if name not in self._repos:
            if self._db is None:
                raise RuntimeError("UnitOfWork not entered")

            repo_map = {
                "user": user.UserRepository,
                "group": group.GroupRepository,
                "group_membership": group_membership.GroupMembershipRepository,
                "join_request": join.JoinRequestRepository,
                "notification": notification.NotificationRepository,
                "rating": rating.RatingRepository,
                "role": role.RoleRepository,
                "task": task.TaskRepository,
                "task_assignee": task_assignee.TaskAssigneeRepository,
                "user_role": user_role.UserRoleRepository,
                "user_skill": user_skill.UserSkillRepository,
                "outbox": outbox.OutboxRepository,
                "comment": comment.CommentRepository,
            }
            if name not in repo_map:
                raise AttributeError(f"Repository {name} not found")
            self._repos[name] = repo_map[name](db=self._db)
        return self._repos[name]

    async def __aenter__(self) -> Self:
        if self._db is None:
            if not self._session_factory:
                raise ValueError("Requires session_factory or session")
            self._db = self._session_factory()
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        db = self._db
        try:
            if not self._is_external and db is not None:
                if exc_type is not None:
                    await db.rollback()
                else:
                    await db.commit()
        finally:
            if not self._is_external and db is not None:
                await db.close()

            self._db = None
            self._repos = {}

    async def commit(self) -> None:
        await self.session.commit()

    async def rollback(self) -> None:
        await self.session.rollback()

    def add_event(self, event_type: str, data: dict[str, Any]) -> None:
        self.events.append({"type": event_type, "data": data})

    def get_events(self) -> list[dict[str, Any]]:
        return self.events.copy()


def get_uow(
    db: AsyncSession = Depends(db_helper.get_session),
) -> UnitOfWork:
    return UnitOfWork(
        session=db,
    )
