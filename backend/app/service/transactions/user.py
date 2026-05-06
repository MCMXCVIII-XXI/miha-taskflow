from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.log import logging
from app.db import db_helper
from app.models import User as UserModel
from app.repositories import UnitOfWork
from app.schemas.enum import OutboxEventType

from ..exceptions import user_exc
from .base import BaseTransaction

logger = logging.get_logger(__name__)


class UserTransaction(BaseTransaction):
    def __init__(
        self,
        uow_class: type[UnitOfWork],
        session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        super().__init__(uow_class=uow_class, session_factory=session_factory)

    async def update_my_profile(
        self,
        current_user: UserModel,
        user_update: dict[str, Any],
    ) -> UserModel:
        async with self._create_uow() as uow:
            user = await uow.user.get(id=current_user.id, is_active=True)
            if not user:
                raise user_exc.UserNotFound(message="User not found")

            email = user_update.get("email")
            username = user_update.get("username")

            if email:
                email_conflict = await uow.user.get(
                    email=email,
                    exclude_user_id=user.id,
                    is_active=True,
                )

                if email_conflict:
                    logger.warning(
                        "Profile update failed: duplicate email\
                            {email} for user {user_id}",
                        email=email,
                        user_id=user.id,
                    )
                    raise user_exc.UserEmailConflict(
                        message="User with this email already exists"
                    )

            if username:
                username_conflict = await uow.user.get(
                    username=username,
                    exclude_user_id=user.id,
                    is_active=True,
                )

                if username_conflict:
                    logger.warning(
                        "Profile update failed: duplicate username\
                            {username} for user {user_id}",
                        username=username,
                        user_id=user.id,
                    )
                    raise user_exc.UserUsernameConflict(
                        message="User with this username already exists"
                    )
            await uow.user.update(user=user, user_update=user_update)
            await uow.outbox.add(
                event_type=OutboxEventType.UPDATED,
                entity_type="user",
                entity_id=current_user.id,
            )
            fresh_user = await uow.user.get(id=current_user.id, is_active=True)
        return fresh_user

    async def delete_my_profile(self, current_user: UserModel) -> None:
        async with self._create_uow() as uow:
            db_user = await uow.user.get(id=current_user.id, is_active=True)
            if not db_user:
                raise user_exc.UserNotFound(message="User not found")

            db_user.is_active = False

            await uow.outbox.add(
                event_type=OutboxEventType.DELETED,
                entity_type="user",
                entity_id=current_user.id,
            )


def get_user_transaction() -> UserTransaction:
    return UserTransaction(
        uow_class=UnitOfWork,
        session_factory=db_helper.session_factory,
    )
