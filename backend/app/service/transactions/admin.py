from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.log import get_logger
from app.db import db_helper
from app.repositories.uow import UnitOfWork
from app.schemas.enum import GlobalUserRole

from ..exceptions import user_exc
from .base import BaseTransaction

logger = get_logger(__name__)


class AdminTransaction(BaseTransaction):
    def __init__(
        self,
        uow_class: type[UnitOfWork],
        session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        super().__init__(uow_class=uow_class, session_factory=session_factory)

    async def delete_user(self, user_id: int, admin_id: int) -> None:
        async with self._create_uow() as uow:
            user = await uow.user.get(
                id=user_id,
                is_active=True,
            )
            if user is None:
                raise user_exc.UserNotFound(message=f"User with id {user_id} not found")

            if user.role == GlobalUserRole.ADMIN:
                admin_count = await uow.user.count(
                    role=GlobalUserRole.ADMIN,
                    is_active=True,
                )
                if admin_count and admin_count <= 1:
                    logger.warning(
                        "Admin {admin_id} attempted to delete last admin {user_id}",
                        admin_id=admin_id,
                        user_id=user_id,
                    )
                    raise user_exc.CannotDeleteLastAdmin(
                        message="Cannot delete the last admin"
                    )

            await uow.user.delete(
                id=user_id,
                is_active=False,
            )


def get_admin_transaction() -> AdminTransaction:
    return AdminTransaction(
        uow_class=UnitOfWork,
        session_factory=db_helper.session_factory,
    )
