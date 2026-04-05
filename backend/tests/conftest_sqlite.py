"""SQLite test fixtures (default for unit tests and fast integration tests)."""

# Import uuid for fixtures
import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool
import jwt
import app.cache as cache_module
from app.models import User
from app.schemas.enum import GlobalUserRole
from app.db import Base
from main import app
from tests.base_conftest import (
    cleanup_db,
    create_group_and_task,  # noqa: F401
    create_mock_db,
    create_test_client,
    register_user,  # noqa: F401
    seed_rbac,
)


@pytest.fixture(scope="session")
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

    client = await create_test_client(session_factory)
    try:
        yield client
    finally:
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
    """Clean up test data after each test."""
    yield
    await cleanup_db(session_factory)


@pytest.fixture
def mock_db():
    """Mock session for unit tests."""
    return create_mock_db()
