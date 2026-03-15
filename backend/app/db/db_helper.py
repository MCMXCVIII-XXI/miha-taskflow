from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import db_settings


class DatabaseHelper:
    """
    Database helper class
    This class is responsible for creating and disposing of the database.
    It also provides an async generator for getting a session.

    Args:
        url (str): Database URL
        echo (bool): Whether to echo SQL statements
        echo_pool (bool): Whether to echo SQL statements for pool
        pool_size (int): Number of connections in the pool
        max_overflow (int): Maximum number of connections in the pool

    Methods:
        dispose: Dispose of the database
        get_session: Async generator for getting a session
        get_session_ctx: Async context manager for getting a session
    """

    def __init__(
        self,
        url: str,
        echo: bool = False,
        echo_pool: bool = False,
        pool_size: int = 5,
        max_overflow: int = 10,
    ) -> None:
        self.engine = create_async_engine(
            url=url,
            echo=echo,
            echo_pool=echo_pool,
            pool_size=pool_size,
            max_overflow=max_overflow,
        )
        self.session_factory = async_sessionmaker(
            self.engine,
            class_=AsyncSession,
            autoflush=False,
            autocommit=False,
            expire_on_commit=False,
        )

    async def dispose(self) -> None:
        """Dispose of the database"""
        await self.engine.dispose()

    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """Async generator for getting a session"""
        async with self.session_factory() as session:
            yield session

    @asynccontextmanager
    async def get_session_ctx(self) -> AsyncSession:
        """Async context manager for getting a session"""
        async with self.session_factory() as session:
            yield session


db_helper = DatabaseHelper(
    url=str(db_settings.URL),
    echo=db_settings.echo,
    echo_pool=db_settings.echo_pool,
    pool_size=db_settings.pool_size,
    max_overflow=db_settings.max_overflow,
)
