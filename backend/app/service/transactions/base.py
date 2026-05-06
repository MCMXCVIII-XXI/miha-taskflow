from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.repositories import UnitOfWork


class BaseTransaction:
    def __init__(
        self,
        uow_class: type[UnitOfWork],
        session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        self._uow_class = uow_class
        self._session_factory = session_factory

    def _create_uow(self) -> UnitOfWork:
        return self._uow_class(session_factory=self._session_factory)
