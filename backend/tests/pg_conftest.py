"""PostgreSQL test fixtures (via Testcontainers + alembic migrations)."""

import os
import subprocess

# Import uuid for fixtures
import uuid
from unittest.mock import AsyncMock, MagicMock

import jwt
import pytest
from fastapi import Depends
from fastapi_cache import FastAPICache
from fastapi_cache.backends.inmemory import InMemoryBackend
from httpx import AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool
from testcontainers.postgres import PostgresContainer

import app.cache as cache_module
from app.db import db_helper
from app.es import ElasticsearchIndexer, es_helper, get_es_indexer, get_es_search
from app.models import User
from app.schemas.enum import GlobalUserRole
from app.service.notification import NotificationService, get_notification_service
from main import app
from tests.base_conftest import (
    cleanup_db,  # noqa: F401
    create_group_and_task,  # noqa: F401
    create_mock_db,
    create_test_client,
    register_user,  # noqa: F401
    seed_rbac,
)


@pytest.fixture(scope="session")
def postgres_container():
    """Start PostgreSQL container for test session."""
    container = PostgresContainer("postgres:16-alpine")
    container.start()
    yield container
    container.stop()


def get_postgres_url(container: PostgresContainer | None = None):
    """Get PostgreSQL URL from container or environment."""
    if container:
        # Use container's connection URL
        db_url = container.get_connection_url().replace("psycopg2", "asyncpg")
        return db_url
    else:
        # Fallback to environment variables
        user = os.getenv("POSTGRES_USER", "user")
        password = os.getenv("POSTGRES_PASSWORD", "pass")
        host = os.getenv("POSTGRES_HOST", "localhost")
        port = os.getenv("POSTGRES_PORT", "5432")
        db = os.getenv("POSTGRES_DB", "taskflow_test")
        return f"postgresql+asyncpg://{user}:{password}@{host}:{port}/{db}"


@pytest.fixture(scope="session")
async def test_engine(postgres_container):
    """Create test DB engine (PostgreSQL via Testcontainers + alembic)."""
    db_url = get_postgres_url(postgres_container)

    # Set DATABASE_URL and DB_URL for alembic and config
    os.environ["DATABASE_URL"] = db_url
    os.environ["DB_URL"] = db_url

    engine = create_async_engine(
        db_url,
        poolclass=NullPool,
        echo=False,
    )

    # Run alembic migrations
    result = subprocess.run(
        ["uv", "run", "alembic", "upgrade", "head"],  # noqa: S607
        capture_output=True,
        text=True,
        env={**os.environ, "DATABASE_URL": db_url, "DB_URL": db_url},
    )
    if result.returncode != 0:
        pytest.fail(f"Alembic migration failed: {result.stderr}")

    yield engine
    await engine.dispose()


@pytest.fixture(scope="session")
async def session_factory(test_engine):
    """Create test session factory."""
    return async_sessionmaker(test_engine, expire_on_commit=False)


@pytest.fixture(autouse=True, scope="session")
async def init_rbac(session_factory):
    """Seed RBAC data matching production permission pyramid."""
    async with session_factory() as session:
        await seed_rbac(session)


@pytest.fixture(scope="session")
async def test_client(session_factory):
    """HTTP client with test DB."""

    original_init_cache = cache_module.init_cache

    FastAPICache.init(InMemoryBackend(), prefix="test")

    def override_get_notification_service(
        db: AsyncSession = Depends(db_helper.get_session),
        indexer: ElasticsearchIndexer = Depends(get_es_indexer),
    ) -> NotificationService:
        return NotificationService(db, indexer)

    def override_get_es_indexer() -> ElasticsearchIndexer:
        mock_indexer = MagicMock()
        mock_indexer.index_task = AsyncMock()
        mock_indexer.index_user = AsyncMock()
        mock_indexer.index_group = AsyncMock()
        mock_indexer.index_comment = AsyncMock()
        mock_indexer.index_notification = AsyncMock()
        mock_indexer.delete_task = AsyncMock(return_value=True)
        mock_indexer.delete_user = AsyncMock(return_value=True)
        mock_indexer.delete_group = AsyncMock(return_value=True)
        mock_indexer.delete_comment = AsyncMock(return_value=True)
        mock_indexer.delete_notification = AsyncMock(return_value=True)
        return mock_indexer

    def override_es_helper_get_client():
        mock_client = MagicMock()
        mock_client.ping = AsyncMock(return_value=True)
        mock_client.search = AsyncMock(return_value={"hits": {"hits": []}})
        mock_client.indices = MagicMock()
        mock_client.indices.refresh = AsyncMock()
        mock_client.indices.exists = AsyncMock(return_value=False)
        mock_client.indices.create = AsyncMock()
        return mock_client

    def override_get_es_search():
        mock_search = MagicMock()
        mock_search.search_tasks = AsyncMock(return_value=[])
        mock_search.search_tasks_faceted = AsyncMock(
            return_value={
                "results": [],
                "aggregations": {},
                "total": 0,
                "limit": 10,
                "offset": 0,
            }
        )
        mock_search.search_users = AsyncMock(return_value=[])
        mock_search.search_users_faceted = AsyncMock(
            return_value={
                "results": [],
                "aggregations": {},
                "total": 0,
                "limit": 10,
                "offset": 0,
            }
        )
        mock_search.search_groups = AsyncMock(return_value=[])
        mock_search.search_groups_faceted = AsyncMock(
            return_value={
                "results": [],
                "aggregations": {},
                "total": 0,
                "limit": 10,
                "offset": 0,
            }
        )
        mock_search.search_comments = AsyncMock(return_value=[])
        mock_search.search_comments_faceted = AsyncMock(
            return_value={
                "results": [],
                "aggregations": {},
                "total": 0,
                "limit": 10,
                "offset": 0,
            }
        )
        mock_search.search_notifications = AsyncMock(return_value=[])
        mock_search.search_notifications_faceted = AsyncMock(
            return_value={
                "results": [],
                "aggregations": {},
                "total": 0,
                "limit": 10,
                "offset": 0,
            }
        )
        return mock_search

    app.dependency_overrides[get_notification_service] = (
        override_get_notification_service
    )
    app.dependency_overrides[get_es_indexer] = override_get_es_indexer
    app.dependency_overrides[es_helper.get_client] = override_es_helper_get_client
    app.dependency_overrides[get_es_search] = override_get_es_search

    client = await create_test_client(session_factory)
    async with client as c:
        yield c

    # Restore original dependencies after session
    app.dependency_overrides.clear()
    cache_module.init_cache = original_init_cache  # type: ignore[assignment]


@pytest.fixture
async def auth_headers(test_client: AsyncClient, session_factory):
    """Create unique user for each test - returns auth headers."""

    uid = uuid.uuid4().hex[:8]
    resp = await test_client.post(
        "/auth",
        json={
            "username": f"user_{uid}",
            "email": f"user_{uid}@test.com",
            "password": "Test123456789",
            "first_name": "Test",
            "last_name": "User",
        },
    )
    token = resp.json()["access_token"]
    return {
        "Authorization": f"Bearer {token}",
        "username": f"user_{uid}",
        "email": f"user_{uid}@test.com",
    }


@pytest.fixture
async def admin_auth_headers(test_client: AsyncClient, session_factory):
    """Create unique admin for each test - returns auth headers."""

    uid = uuid.uuid4().hex[:8]
    resp = await test_client.post(
        "/auth",
        json={
            "username": f"admin_{uid}",
            "email": f"admin_{uid}@test.com",
            "password": "TestAdmin123456",
            "first_name": "Admin",
            "last_name": "Test",
        },
    )

    token = resp.json()["access_token"]
    payload = jwt.decode(token, options={"verify_signature": False})
    admin_id = int(payload.get("sub"))

    async with session_factory() as session:
        user = await session.get(User, admin_id)
        if user:
            user.role = GlobalUserRole.ADMIN
            await session.commit()

    return {
        "Authorization": f"Bearer {token}",
        "username": f"admin_{uid}",
        "email": f"admin_{uid}@test.com",
    }


@pytest.fixture
async def testuser_auth_headers(test_client: AsyncClient, session_factory):
    """Fixed user 'testuser' for strict assertions."""
    resp = await test_client.post(
        "/auth",
        json={
            "username": "testuser",
            "email": "test@test.com",
            "password": "Test123456789",
            "first_name": "Test",
            "last_name": "Userov",
            "patronymic": "Testovich",
        },
    )
    if resp.status_code == 409:
        token_resp = await test_client.post(
            "/auth/token",
            data={"username": "testuser", "password": "Test123456789"},
        )
        token = token_resp.json()["access_token"]
    else:
        token = resp.json()["access_token"]

    return {
        "Authorization": f"Bearer {token}",
        "username": "testuser",
        "email": "test@test.com",
    }


@pytest.fixture
async def testadmin_auth_headers(test_client: AsyncClient, session_factory):
    """Fixed admin 'testadmin' for strict assertions."""

    resp = await test_client.post(
        "/auth",
        json={
            "username": "testadmin",
            "email": "admin@test.com",
            "password": "TestAdmin123456",
            "first_name": "Admin",
            "last_name": "Test",
        },
    )
    if resp.status_code == 409:
        token_resp = await test_client.post(
            "/auth/token",
            data={"username": "testadmin", "password": "TestAdmin123456"},
        )
        token = token_resp.json()["access_token"]
    else:
        token = resp.json()["access_token"]
        payload = jwt.decode(token, options={"verify_signature": False})
        admin_id = int(payload.get("sub"))

        async with session_factory() as session:
            user = await session.get(User, admin_id)
            if user:
                user.role = GlobalUserRole.ADMIN
                await session.commit()

        token_resp = await test_client.post(
            "/auth/token",
            data={"username": "testadmin", "password": "TestAdmin123456"},
        )
        token = token_resp.json()["access_token"]

    return {
        "Authorization": f"Bearer {token}",
        "username": "testadmin",
        "email": "admin@test.com",
    }


@pytest.fixture(autouse=True)
async def cleanup_test_data(session_factory):
    """Clean up test data after each test (TRUNCATE for PostgreSQL)."""
    yield
    async with session_factory() as session:
        try:
            for table in [
                "task_assignees",
                "tasks",
                "user_group_memberships",
                "user_groups",
                "notifications",
                "user_roles",
                "users",
            ]:
                await session.execute(text(f"TRUNCATE TABLE {table} CASCADE"))
            await session.commit()
        except Exception:  # noqa: BLE001
            await session.rollback()

        from fastapi_cache import FastAPICache

        try:
            backend = FastAPICache.get_backend()
            if hasattr(backend, "_store"):
                backend._store.clear()
        except AssertionError:
            pass  # Cache not initialized


@pytest.fixture
def mock_db():
    """Mock session for unit tests."""
    return create_mock_db()


@pytest.fixture
def mock_es():
    """Mock Elasticsearch client for unit tests."""
    client = MagicMock()
    client.index = AsyncMock()
    client.delete = AsyncMock()
    client.search = AsyncMock()
    client.ping = AsyncMock(return_value=True)
    client.indices = MagicMock()
    client.indices.refresh = AsyncMock()
    client.indices.exists = AsyncMock(return_value=False)
    client.indices.create = AsyncMock()
    return client


@pytest.fixture
def mock_indexer(mock_es):
    """Mock ElasticsearchIndexer for unit tests."""
    mock_indexer_instance = MagicMock()
    mock_indexer_instance.index_task = AsyncMock()
    mock_indexer_instance.index_user = AsyncMock()
    mock_indexer_instance.index_group = AsyncMock()
    mock_indexer_instance.index_comment = AsyncMock()
    mock_indexer_instance.index_notification = AsyncMock()
    mock_indexer_instance.delete_task = AsyncMock(return_value=True)
    mock_indexer_instance.delete_user = AsyncMock(return_value=True)
    mock_indexer_instance.delete_group = AsyncMock(return_value=True)
    mock_indexer_instance.delete_comment = AsyncMock(return_value=True)
    mock_indexer_instance.delete_notification = AsyncMock(return_value=True)
    return mock_indexer_instance
