from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.log import logging
from app.db import db_helper
from app.models import UserSkill
from app.repositories import UnitOfWork
from app.schemas.enum import TaskSphere

from .base import BaseTransaction

logger = logging.get_logger(__name__)


class XPTransaction(BaseTransaction):
    def __init__(
        self,
        uow_class: type[UnitOfWork],
        session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        super().__init__(uow_class=uow_class, session_factory=session_factory)

    async def get_or_create_skill(self, user_id: int, sphere: TaskSphere) -> UserSkill:
        async with self._create_uow() as uow:
            skill = await uow.user_skill.get(sphere=sphere, user_id=user_id)
            if not skill:
                skill = await uow.user_skill.add(
                    user_id=user_id,
                    sphere=sphere,
                )
                logger.info(
                    "New user skill created",
                    user_id=user_id,
                    skill_id=skill.id,
                    sphere=sphere,
                )
        return skill

    async def add_sphere_xp(
        self, user_id: int, sphere: TaskSphere, xp: int
    ) -> tuple[bool, int]:
        async with self._create_uow() as uow:
            skill = await uow.user_skill.get(user_id=user_id, sphere=sphere)
            if not skill:
                skill = await uow.user_skill.add(
                    user_id=user_id,
                    sphere=sphere,
                )

            if skill.is_frozen:
                return False, skill.level

        return True, skill.level


def get_xp_transaction() -> XPTransaction:
    return XPTransaction(
        uow_class=UnitOfWork,
        session_factory=db_helper.session_factory,
    )
