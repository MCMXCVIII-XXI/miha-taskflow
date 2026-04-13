"""PostgreSQL test fixtures (via Testcontainers + alembic migrations)."""

import os
import subprocess

# Import uuid for fixtures
import uuid
from unittest.mock import AsyncMock, MagicMock

import jwt
import pytest
from elasticsearch import AsyncElasticsearch
from elasticsearch.dsl import async_connections
from fastapi import Depends
from fastapi_cache import FastAPICache
from httpx import AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool
from testcontainers.elasticsearch import ElasticSearchContainer
from testcontainers.postgres import PostgresContainer

import app.cache as cache_module
from app.db import db_helper
from app.es import (
    ElasticsearchIndexer,
    ElasticsearchSearch,
    es_helper,
    get_es_indexer,
    get_es_search,
)
from app.indexes import (
    CommentDoc,
    NotificationDoc,
    TaskDoc,
    UserDoc,
    UserGroupDoc,
)
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
from tests.mock_cache import MockRedisBackend


@pytest.fixture(scope="session")
def postgres_container():
    """Start PostgreSQL container for test session."""
    container = PostgresContainer("postgres:16-alpine")
    container.start()
    yield container
    container.stop()


@pytest.fixture(scope="session")
def es_container():
    """Start Elasticsearch container for test session (available for manual testing)."""
    container = ElasticSearchContainer(
        "docker.elastic.co/elasticsearch/elasticsearch:9.3.3",
        port=9200,
    )
    container.with_env("discovery.type", "single-node")
    container.with_env("xpack.security.enabled", "false")
    container.with_env("ES_JAVA_OPTS", "-Xms512m -Xmx512m")
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


class MockESClient:
    """Mock Elasticsearch client for tests."""

    def __init__(self):
        self._documents: dict = {
            "tasks_v1": {},
            "users_v1": {},
            "groups_v1": {},
            "comments_v1": {},
            "notifications_v1": {},
        }

    async def index(self, index: str, id: int, document: dict):
        if index not in self._documents:
            self._documents[index] = {}
        self._documents[index][str(id)] = document
        return {"result": "created", "_id": str(id), "_index": index}

    async def delete(self, index: str, id: int):
        if index in self._documents and str(id) in self._documents[index]:
            del self._documents[index][str(id)]
        return {"result": "deleted"}

    async def search(
        self, index: str | None = None, body: dict | None = None, **kwargs
    ):
        hits = []
        facets = {
            "status": {
                "buckets": [
                    {"key": "pending", "doc_count": 1},
                    {"key": "in_progress", "doc_count": 1},
                ]
            },
            "priority": {
                "buckets": [
                    {"key": "high", "doc_count": 1},
                    {"key": "medium", "doc_count": 1},
                ]
            },
        }

        target_index = index or list(self._documents.keys())[0]
        if "*" in target_index:
            docs = {}
            for idx, doc in self._documents.items():
                docs.update(doc)
        else:
            docs = self._documents.get(target_index, {})

        query_dict = body if body else kwargs.get("query", {})

        if query_dict and "query" in query_dict:
            query = query_dict["query"]
            if "bool" in query:
                for clause in query["bool"]:
                    if "multi_match" in clause:
                        search_term = clause["multi_match"].get("query", "").lower()
                        for doc in docs.values():
                            if any(search_term in str(v).lower() for v in doc.values()):
                                hits.append({"_source": dict(doc), "_score": 1.0})

        if not hits:
            for doc in docs.values():
                hits.append({"_source": dict(doc), "_score": 1.0})

        return {
            "hits": {"total": {"value": len(hits)}, "hits": hits},
            "aggregations": facets,
            "facets": facets,
        }

    async def ping(self):
        return True

    async def close(self):
        pass

    @property
    def indices(self):
        return MockESClient._IndicesManager(self)

    class _IndicesManager:
        def __init__(self, client):
            self._client = client

        async def exists(self, index: str):
            return True

        async def create(self, index: str, **kwargs):
            return {"acknowledged": True}

        async def delete(self, index: str, **kwargs):
            return {"acknowledged": True}

        async def refresh(self, index: str = "*"):
            return {"_shards": {"total": 1, "successful": 1}}


@pytest.fixture(scope="session")
async def test_client(session_factory):
    """HTTP client with test DB and mocked Elasticsearch."""

    original_init_cache = cache_module.init_cache

    FastAPICache.init(MockRedisBackend(), prefix="fastapi-cache")

    es_client = MockESClient()

    test_tasks = [
        {
            "id": 1,
            "title": "Fix bug",
            "description": "Fix critical bug",
            "status": "pending",
            "priority": "high",
            "group_id": 1,
            "created_at": "2026-04-13T00:00:00Z",
            "updated_at": "2026-04-13T00:00:00Z",
        },
        {
            "id": 2,
            "title": "Write tests",
            "description": "Write integration tests",
            "status": "in_progress",
            "priority": "medium",
            "group_id": 1,
            "created_at": "2026-04-13T00:00:00Z",
            "updated_at": "2026-04-13T00:00:00Z",
        },
    ]
    for task in test_tasks:
        await es_client.index(index="tasks_v1", id=task["id"], document=task)

    test_users = [
        {
            "id": 1,
            "username": "john",
            "email": "john@test.com",
            "first_name": "John",
            "last_name": "Doe",
            "role": "user",
            "is_active": True,
        },
        {
            "id": 2,
            "username": "admin",
            "email": "admin@test.com",
            "first_name": "Admin",
            "last_name": "User",
            "role": "admin",
            "is_active": True,
        },
    ]
    for user in test_users:
        await es_client.index(index="users_v1", id=user["id"], document=user)

    test_groups = [
        {
            "id": 1,
            "name": "Developers",
            "description": "Dev team",
            "admin_id": 1,
            "visibility": "public",
            "join_policy": "open",
        },
        {
            "id": 2,
            "name": "Admins",
            "description": "Admin team",
            "admin_id": 2,
            "visibility": "private",
            "join_policy": "request",
        },
    ]
    for group in test_groups:
        await es_client.index(index="groups_v1", id=group["id"], document=group)

    test_comments = [
        {"id": 1, "content": "Great work!", "task_id": 1, "user_id": 1},
        {"id": 2, "content": "Need fixes", "task_id": 1, "user_id": 2},
    ]
    for comment in test_comments:
        await es_client.index(index="comments_v1", id=comment["id"], document=comment)

    test_notifications = [
        {
            "id": 1,
            "title": "New invite",
            "message": "You have invite",
            "user_id": 1,
            "type": "invite",
        },
    ]
    for notif in test_notifications:
        await es_client.index(index="notifications_v1", id=notif["id"], document=notif)

    def override_get_notification_service(
        db: AsyncSession = Depends(db_helper.get_session),
        indexer: ElasticsearchIndexer = Depends(get_es_indexer),
    ) -> NotificationService:
        return NotificationService(db, indexer)

    def override_get_es_indexer() -> ElasticsearchIndexer:
        return ElasticsearchIndexer(es_client)

    def override_get_es_search() -> ElasticsearchSearch:
        return ElasticsearchSearch(es_client)

    def override_es_helper_get_client():
        return es_client

    app.dependency_overrides[get_notification_service] = (
        override_get_notification_service
    )
    app.dependency_overrides[get_es_indexer] = override_get_es_indexer
    app.dependency_overrides[get_es_search] = override_get_es_search
    app.dependency_overrides[es_helper.get_client] = override_es_helper_get_client

    client = await create_test_client(session_factory)
    async with client as c:
        yield c

    app.dependency_overrides.clear()
    cache_module.init_cache = original_init_cache


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
