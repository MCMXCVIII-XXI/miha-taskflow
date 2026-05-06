"""SQLite test fixtures (default for unit tests and fast integration tests)."""

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import jwt
import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

import app.cache as cache_module
from app.db import Base
from app.models import User
from app.schemas.enum import GlobalUserRole
from main import app
from tests.base_conftest import (  # noqa: F401
    cleanup_db,
    create_group_and_task,
    create_mock_db,
    create_test_client,
    register_user,
    seed_rbac,
)


@pytest_asyncio.fixture(scope="session")
async def test_engine():
    """Create test DB engine (SQLite in-memory)."""
    engine = create_async_engine(
        "sqlite+aiosqlite:///:memory:",
        poolclass=StaticPool,
        connect_args={"check_same_thread": False},
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield engine
    await engine.dispose()


@pytest.fixture
def mock_uow():
    uow_mock = MagicMock()
    uow_mock.user = MagicMock()
    uow_mock.commit = AsyncMock()
    uow_mock.rollback = AsyncMock()
    return uow_mock


@pytest_asyncio.fixture(scope="session")
async def session_factory(test_engine):
    """Create test session factory."""
    return async_sessionmaker(test_engine, expire_on_commit=False)


@pytest_asyncio.fixture(autouse=True, scope="session")
async def init_rbac(session_factory):
    """Seed RBAC data matching production permission pyramid."""
    async with session_factory() as session:
        await seed_rbac(session)


@pytest_asyncio.fixture(scope="session")
async def test_client(session_factory):
    """HTTP client with test DB."""

    original_init_cache = cache_module.init_cache

    client = await create_test_client(session_factory)
    try:
        yield client
    finally:
        app.dependency_overrides.clear()
        cache_module.init_cache = original_init_cache  # type: ignore[assignment]


@pytest_asyncio.fixture
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


@pytest_asyncio.fixture
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


@pytest_asyncio.fixture
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


@pytest_asyncio.fixture
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


@pytest_asyncio.fixture(autouse=True)
async def cleanup_test_data(session_factory):
    """Clean up test data after each test."""
    yield
    await cleanup_db(session_factory)


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


@pytest.fixture(autouse=True)
def mock_prometheus_metrics():
    """Mock all Prometheus metrics to avoid label errors in tests."""

    mock_counter = MagicMock()
    mock_labels = MagicMock()
    mock_labels.inc.return_value = None
    mock_labels.set.return_value = None
    mock_labels.observe.return_value = None
    mock_counter.labels.return_value = mock_labels

    mock_metrics = MagicMock()

    metrics_list = [
        "USER_ACTIONS_TOTAL",
        "TASKS_TOTAL",
        "SEARCH_QUERIES_TOTAL",
        "GROUP_ACTIONS_TOTAL",
        "SOCIAL_ACTIONS_TOTAL",
        "NOTIFICATION_SENT_TOTAL",
        "XP_CHANGES_TOTAL",
        "SEARCH_LATENCY_SECONDS",
        "http_requests_total",
        "http_request_duration_seconds",
    ]

    for metric_name in metrics_list:
        setattr(mock_metrics, metric_name, mock_counter)

    with patch("app.core.metrics.METRICS", mock_metrics):
        yield mock_metrics
