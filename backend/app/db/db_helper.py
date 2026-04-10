"""Manages SQLAlchemy async database connections and session lifecycle.

This module provides a DatabaseHelper class for managing database connections
including engine setup, session factory creation, and resource cleanup.
Handles connection pooling and async session management for the application.

Also provides a global db_helper instance for application-wide database access.
"""

from collections.abc import AsyncGenerator, AsyncIterator
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import db_settings


class DatabaseHelper:
    """Manages database connection lifecycle and provides session interfaces.

    Handles the complete lifecycle of database connections including engine creation,
    session factory setup, and proper resource disposal. Provides both generator
    and context manager interfaces for session management with connection pooling.

    Attributes:
        engine: SQLAlchemy async engine for database connections
        session_factory: Factory for creating async sessions
    """

    def __init__(
        self,
        url: str,
        echo: bool = False,
        echo_pool: bool = False,
        pool_size: int = 5,
        max_overflow: int = 10,
    ) -> None:
        """Configures database connection with provided settings.

        Args:
            url (str): Database connection URL
            echo (bool): Whether to echo SQL statements for debugging
            echo_pool (bool): Whether to echo pool-related events
            pool_size (int): Number of connections in the connection pool
            max_overflow (int): Maximum number of overflow connections allowed
        """
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
        """Closes database engine and all active connections.

        Should be called during application shutdown to properly close
        all database connections and release system resources.
        """
        await self.engine.dispose()

    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """Provides database sessions through async generator interface.

        Yields:
            AsyncSession: Database session for use in async contexts
        """
        async with self.session_factory() as session:
            yield session

    @asynccontextmanager
    async def get_session_ctx(self) -> AsyncIterator[AsyncSession]:
        """Provides database sessions through async context manager interface.

        Returns:
            AsyncIterator[AsyncSession]: Database session context manager
        """
        async with self.session_factory() as session:
            yield session


# Global database helper instance for application-wide database access
db_helper = DatabaseHelper(
    url=str(db_settings.URL),
    echo=db_settings.ECHO,
    echo_pool=db_settings.ECHO_POOL,
    pool_size=db_settings.POOL_SIZE,
    max_overflow=db_settings.MAX_OVERFLOW,
)
