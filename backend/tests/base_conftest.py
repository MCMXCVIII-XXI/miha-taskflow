"""Common fixtures and helpers for both SQLite and PostgreSQL tests."""

import logging
import uuid
from unittest.mock import AsyncMock

import jwt
from fastapi import Depends
from fastapi_cache import FastAPICache
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

import app.cache as cache_module
from app.core.permission import PERMISSIONS
from app.core.permission.role_permissions import (
    ADMIN_PERMISSIONS,
    ASSIGNEE_PERMISSIONS,
    GROUP_ADMIN_PERMISSIONS,
    MEMBER_PERMISSIONS,
    USER_PERMISSIONS,
)
from app.db import db_helper
from app.es import get_es_indexer
from app.models import Permission, Role, RolePermission, User
from app.schemas.enum import GlobalUserRole
from main import app

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════════
# RBAC SEEDING
# ═══════════════════════════════════════════════════════════════════════════


async def seed_rbac(session: AsyncSession) -> None:
    """Seed RBAC data matching production permission pyramid."""
    existing_roles = await session.execute(select(Role))
    if existing_roles.scalars().first() is not None:
        return

    for name in ["USER", "ADMIN", "MEMBER", "GROUP_ADMIN", "ASSIGNEE"]:
        session.add(Role(name=name))
    await session.flush()

    for perm in PERMISSIONS:
        session.add(perm)
    await session.flush()

    roles = {r.name: r for r in (await session.execute(select(Role))).scalars().all()}
    perms = {
        p.name: p for p in (await session.execute(select(Permission))).scalars().all()
    }

    user_perms = USER_PERMISSIONS
    member_perms = MEMBER_PERMISSIONS
    assignee_perms = ASSIGNEE_PERMISSIONS
    group_admin_perms = GROUP_ADMIN_PERMISSIONS
    admin_perms = ADMIN_PERMISSIONS

    role_perms = {
        "USER": user_perms,
        "MEMBER": user_perms | member_perms,
        "ASSIGNEE": user_perms | assignee_perms,
        "GROUP_ADMIN": user_perms | member_perms | group_admin_perms,
        "ADMIN": admin_perms,
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


# ═══════════════════════════════════════════════════════════════════════════
# CLIENT SETUP
# ═══════════════════════════════════════════════════════════════════════════


async def create_test_client(session_factory) -> AsyncClient:
    """Create HTTP client with test DB overrides."""
    app.dependency_overrides[db_helper.get_session] = override_session_factory(
        session_factory
    )

    from app.es import ElasticsearchIndexer, es_helper, get_es_search
    from app.service.notification import (
        NotificationService,
        get_notification_service,
    )

    def override_get_notification_service(
        db: AsyncSession = Depends(db_helper.get_session),
        indexer: ElasticsearchIndexer = Depends(get_es_indexer),
    ) -> NotificationService:
        return NotificationService(db, indexer)

    def override_get_es_indexer() -> ElasticsearchIndexer:
        from unittest.mock import AsyncMock, MagicMock

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
        from unittest.mock import AsyncMock, MagicMock

        mock_client = MagicMock()
        mock_client.ping = AsyncMock(return_value=True)
        mock_client.search = AsyncMock(return_value={"hits": {"hits": []}})
        mock_client.close = AsyncMock()
        mock_client.indices = MagicMock()
        mock_client.indices.refresh = AsyncMock()
        mock_client.indices.exists = AsyncMock(return_value=False)
        mock_client.indices.create = AsyncMock()
        return mock_client

    def override_get_es_search():
        from unittest.mock import AsyncMock, MagicMock

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
        mock_search.search_my_groups = AsyncMock(
            return_value={
                "results": [],
                "total": 0,
                "limit": 10,
                "offset": 0,
            }
        )
        mock_search.search_my_tasks = AsyncMock(
            return_value={
                "results": [],
                "total": 0,
                "limit": 10,
                "offset": 0,
            }
        )
        mock_search.search_tasks_by_user = AsyncMock(
            return_value={
                "results": [],
                "total": 0,
                "limit": 10,
                "offset": 0,
            }
        )
        mock_search.search_users_by_group = AsyncMock(
            return_value={
                "results": [],
                "total": 0,
                "limit": 10,
                "offset": 0,
            }
        )
        mock_search.search_tasks_by_group = AsyncMock(
            return_value={
                "results": [],
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

    async def _noop_init_cache() -> None:
        pass

    cache_module.init_cache = _noop_init_cache  # type: ignore[assignment]
    from tests.mock_cache import MockRedisBackend

    FastAPICache.init(MockRedisBackend(), prefix="fastapi-cache")

    transport = ASGITransport(app=app)
    return AsyncClient(transport=transport, base_url="http://test")


def override_session_factory(session_factory):
    """Create a dependency override for get_session."""

    async def override_get_session():
        async with session_factory() as session:
            yield session
            await session.close()

    return override_get_session


def restore_app_dependencies() -> None:
    """Restore original app dependencies after tests."""
    import app.cache as cache_module

    cache_module.init_cache = original_init_cache
    app.dependency_overrides.clear()


# ═══════════════════════════════════════════════════════════════════════════
# USER FIXTURES
# ═══════════════════════════════════════════════════════════════════════════


def _make_unique_user(prefix: str = "user") -> dict:
    """Generate unique user data."""
    uid = uuid.uuid4().hex[:8]
    return {
        "username": f"{prefix}_{uid}",
        "email": f"{prefix}_{uid}@test.com",
        "password": "Test123456789",
        "first_name": "Test",
        "last_name": "User",
    }


async def _register_or_login(
    test_client: AsyncClient,
    user_data: dict,
    session_factory=None,
    set_admin: bool = False,
) -> dict:
    """Register user or login if exists, return auth headers."""
    resp = await test_client.post("/auth", json=user_data)
    if resp.status_code == 409:
        resp = await test_client.post(
            "/auth/token",
            data={
                "username": user_data["username"],
                "password": user_data["password"],
            },
        )

    token = resp.json()["access_token"]

    if set_admin:
        payload = jwt.decode(token, options={"verify_signature": False})
        admin_id = int(payload.get("sub"))
        async with session_factory() as session:
            user = await session.get(User, admin_id)
            if user:
                user.role = GlobalUserRole.ADMIN
                await session.commit()
        token = resp.json()["access_token"]

    return {
        "Authorization": f"Bearer {token}",
        "username": user_data["username"],
        "email": user_data["email"],
    }


# ═══════════════════════════════════════════════════════════════════════════
# HELPER FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════


async def register_user(
    client: AsyncClient,
    username: str | None = None,
    email: str | None = None,
    password: str = "Password123",  # noqa: S107
) -> dict:
    """Register user (or login if exists) and return auth headers."""
    test_username = username or f"user_{uuid.uuid4().hex[:8]}"
    test_email = email or f"{test_username}@test.com"

    resp = await client.post(
        "/auth",
        json={
            "username": test_username,
            "email": test_email,
            "password": password,
            "first_name": "Test",
            "last_name": "User",
        },
    )
    if resp.status_code == 409:
        resp = await client.post(
            "/auth/token",
            data={"username": test_username, "password": password},
        )
    token = resp.json()["access_token"]
    return {
        "Authorization": f"Bearer {token}",
        "username": test_username,
        "email": test_email,
    }


async def create_group_and_task(
    client: AsyncClient, headers: dict, group_name: str, task_title: str
) -> tuple[int, int]:
    """Helper to create a group and task, return (group_id, task_id)."""
    unique_id = str(uuid.uuid4())[:8]
    group_resp = await client.post(
        "/groups",
        json={"name": f"{group_name}_{unique_id}", "description": "For test"},
        headers=headers,
    )
    assert group_resp.status_code == 201, (
        f"Group creation failed: {group_resp.status_code} - {group_resp.text}"
    )
    group_id = group_resp.json()["id"]

    task_resp = await client.post(
        f"/tasks/groups/{group_id}",
        json={
            "title": f"{task_title}_{unique_id}",
            "description": "Test description",
            "priority": "medium",
            "group_id": group_id,
        },
        headers=headers,
    )
    assert task_resp.status_code == 201, (
        f"Task creation failed: {task_resp.status_code} - {task_resp.text}"
    )
    task_id = task_resp.json()["id"]
    return group_id, task_id


# ═══════════════════════════════════════════════════════════════════════════
# CLEANUP
# ═══════════════════════════════════════════════════════════════════════════


async def cleanup_db(session_factory) -> None:
    """Clean up all test data between tests."""
    async with session_factory() as session:
        try:
            await session.execute(text("DELETE FROM ratings"))
            await session.execute(text("DELETE FROM comments"))
            await session.execute(text("DELETE FROM task_assignees"))
            await session.execute(text("DELETE FROM tasks"))
            await session.execute(text("DELETE FROM user_group_memberships"))
            await session.execute(text("DELETE FROM user_groups"))
            await session.execute(text("DELETE FROM notifications"))
            await session.execute(text("DELETE FROM join_requests"))
            await session.execute(text("DELETE FROM user_roles"))
            await session.execute(text("DELETE FROM users"))
            await session.commit()
        except Exception as exc:  # noqa: BLE001
            logger.warning("Cleanup error: %s", exc)
            await session.rollback()

    try:
        backend = FastAPICache.get_backend()
        if hasattr(backend, "_store"):
            backend._store.clear()
    except Exception as exc:  # noqa: BLE001
        logger.warning("Cache cleanup error: %s", exc)


# ═══════════════════════════════════════════════════════════════════════════
# MOCK DB
# ═══════════════════════════════════════════════════════════════════════════


def create_mock_db() -> AsyncMock:
    """Create mock database session for unit tests."""
    return AsyncMock(spec=AsyncSession)
