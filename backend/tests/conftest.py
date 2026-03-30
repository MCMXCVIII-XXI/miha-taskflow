from unittest.mock import AsyncMock

import pytest
from fastapi_cache import FastAPICache
from fastapi_cache.backends.inmemory import InMemoryBackend
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

import app.cache as cache_module
from app.core.permission import PERMISSIONS
from app.db.base import Base
from app.db.db_helper import db_helper
from app.models import Permission, Role, RolePermission
from main import app

TEST_USER_USERNAME = "testuser"
TEST_USER_PASSWORD = "Test123456789"  # noqa: S105


@pytest.fixture(scope="session")
async def test_engine():
    """Create test DB engine."""
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
        for name in ["USER", "ADMIN", "MEMBER", "GROUP_ADMIN", "ASSIGNEE"]:
            session.add(Role(name=name))
        await session.flush()
        for perm in PERMISSIONS:
            session.add(perm)
        await session.flush()
        roles = {
            r.name: r for r in (await session.execute(select(Role))).scalars().all()
        }
        perms = {
            p.name: p
            for p in (await session.execute(select(Permission))).scalars().all()
        }

        user_perms = {
            "user:view:any",
            "user:view:own",
            "user:update:own",
            "user:delete:own",
            "group:create:own",
            "group:view:any",
            "group:join:any",
            "task:view:any",
            "task:join:any",
            "task:exit:assignee",
        }
        member_perms = {"group:view:group", "group:exit:member", "task:view:group"}
        assignee_perms = {"task:update:status"}
        group_admin_perms = {
            "group:view:own",
            "group:update:own",
            "group:delete:own",
            "group:add:own",
            "group:remove:own",
            "task:create:own",
            "task:view:own",
            "task:add:own",
            "task:remove:own",
            "task:update:own",
            "task:delete:own",
            "task:update:status",
        }
        all_perm_names = {p.name for p in PERMISSIONS}

        role_perms = {
            "USER": user_perms,
            "MEMBER": user_perms | member_perms,
            "ASSIGNEE": user_perms | assignee_perms,
            "GROUP_ADMIN": user_perms | member_perms | group_admin_perms,
            "ADMIN": all_perm_names,
        }

        for role_name, perm_names in role_perms.items():
            for perm_name in perm_names:
                if perm_name in perms:
                    session.add(
                        RolePermission(
                            role_id=roles[role_name].id,
                            permission_id=perms[perm_name].id,
                        )
                    )
        await session.commit()


@pytest.fixture(scope="session")
async def test_client(session_factory):
    """HTTP-client with test DB."""

    async def override_get_session():
        async with session_factory() as session:
            yield session

    app.dependency_overrides[db_helper.get_session] = override_get_session

    # Prevent lifespan from initializing Redis cache
    original_init_cache = cache_module.init_cache

    async def _noop_init_cache() -> None:
        pass

    cache_module.init_cache = _noop_init_cache  # type: ignore[assignment]

    FastAPICache.init(InMemoryBackend(), prefix="test")
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client

    cache_module.init_cache = original_init_cache  # type: ignore[assignment]
    app.dependency_overrides.clear()


@pytest.fixture(scope="session")
async def testuser_id(test_client):
    """Register testuser once and return its ID."""
    import jwt

    resp = await test_client.post(
        "/auth",
        json={
            "username": TEST_USER_USERNAME,
            "email": "test@test.com",
            "password": TEST_USER_PASSWORD,
            "first_name": "Test",
            "last_name": "Testov",
            "patronymic": "Testovich",
        },
    )
    token = resp.json()["access_token"]
    payload = jwt.decode(token, options={"verify_signature": False})
    return int(payload.get("sub"))


@pytest.fixture
async def auth_headers(test_client, testuser_id):
    """Fresh auth headers — re-logs in each test so token always matches DB state."""
    resp = await test_client.post(
        "/auth/token",
        data={
            "username": TEST_USER_USERNAME,
            "password": TEST_USER_PASSWORD,
        },
    )
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


TEST_ADMIN_USERNAME = "testadmin"
TEST_ADMIN_PASSWORD = "TestAdmin123456"  # noqa: S105


@pytest.fixture(scope="session")
async def testadmin_id(test_client, session_factory):
    """Register testadmin once and return its ID."""
    import jwt

    from app.models import User
    from app.schemas import GlobalUserRole

    resp = await test_client.post(
        "/auth",
        json={
            "username": TEST_ADMIN_USERNAME,
            "email": "admin@test.com",
            "password": TEST_ADMIN_PASSWORD,
            "first_name": "Admin",
            "last_name": "Test",
        },
    )
    token = resp.json()["access_token"]
    payload = jwt.decode(token, options={"verify_signature": False})
    admin_id = int(payload.get("sub"))

    async with session_factory() as session:
        user = await session.get(User, admin_id)
        user.role = GlobalUserRole.ADMIN
        await session.commit()

    return admin_id


@pytest.fixture
async def admin_auth_headers(test_client, testadmin_id):
    """Fresh auth headers for admin."""
    resp = await test_client.post(
        "/auth/token",
        data={
            "username": TEST_ADMIN_USERNAME,
            "password": TEST_ADMIN_PASSWORD,
        },
    )
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture(autouse=True)
async def cleanup_test_data(session_factory, testuser_id):
    """Cleanup test data after each test to prevent side effects."""
    yield

    async with session_factory() as session:
        try:
            from sqlalchemy import text

            await session.execute(text("DELETE FROM task_assignees"))
            await session.execute(text("DELETE FROM tasks"))
            await session.execute(text("DELETE FROM user_group_membership"))
            await session.execute(text("DELETE FROM user_groups"))
            await session.execute(
                text("DELETE FROM user_roles WHERE user_id != :uid"),
                {"uid": testuser_id},
            )
            await session.execute(
                text("DELETE FROM users WHERE id != :uid"),
                {"uid": testuser_id},
            )
            await session.commit()
        except Exception:  # noqa: BLE001
            await session.rollback()

    # InMemoryBackend._store is a class variable shared across instances.
    # clear(namespace) doesn't work because keys have a prefix.
    # Must wipe the store directly.
    backend = FastAPICache.get_backend()
    if hasattr(backend, "_store"):
        backend._store.clear()


@pytest.fixture
def mock_db():
    """Mock session for unit tests."""
    return AsyncMock(spec=AsyncSession)
