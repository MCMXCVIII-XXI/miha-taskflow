from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.log import logging
from app.core.log.mask import _mask_email
from app.core.security import (
    get_password_hash,
)
from app.db import db_helper
from app.models import User as UserModel
from app.repositories import UnitOfWork
from app.schemas import UserCreate
from app.schemas.enum import OutboxEventType

from ..exceptions import user_exc
from .base import BaseTransaction

logger = logging.get_logger(__name__)


class AuthTransaction(BaseTransaction):
    def __init__(
        self,
        uow_class: type[UnitOfWork],
        session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        super().__init__(uow_class=uow_class, session_factory=session_factory)

    async def register(self, user_in: UserCreate) -> UserModel:
        async with self._create_uow() as uow:
            existing = await uow.user.get_by_email_or_username(
                email=user_in.email,
                username=user_in.username,
                is_active=None,
            )
            if existing:
                logger.warning(
                    "Registration failed: \
                        duplicate email {email} or username {username}",
                    email=_mask_email(user_in.email),
                    username=user_in.username,
                )
                raise user_exc.UserAlreadyExists(
                    message="User with this email or username already exists"
                )
            user = await uow.user.add(
                username=user_in.username,
                email=user_in.email,
                first_name=user_in.first_name,
                last_name=user_in.last_name,
                patronymic=user_in.patronymic,
                hashed_password=get_password_hash(
                    user_in.hashed_password.get_secret_value()
                ),
            )
            await uow.outbox.add(
                event_type=OutboxEventType.CREATED,
                entity_type="user",
                entity_id=user.id,
            )
            fresh_user = await uow.user.get(id=user.id, is_active=True)
        return fresh_user


def get_auth_transaction() -> AuthTransaction:
    return AuthTransaction(
        uow_class=UnitOfWork,
        session_factory=db_helper.session_factory,
    )
