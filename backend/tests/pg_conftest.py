"""PostgreSQL, Redis & ES test fixtures (via Testcontainers)."""

import asyncio
import os
import subprocess
import uuid
from collections.abc import AsyncGenerator
from typing import Any
from unittest.mock import MagicMock, patch

import elasticsearch
import pytest
import pytest_asyncio
import redis.asyncio as aioredis
import sqlalchemy
from elasticsearch import AsyncElasticsearch
from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend
from httpx import AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.orm import selectinload as _selectinload
from sqlalchemy.pool import NullPool
from testcontainers.elasticsearch import ElasticSearchContainer
from testcontainers.postgres import PostgresContainer
from testcontainers.redis import RedisContainer

from app.models import User
from app.schemas.enum import GlobalUserRole

from .base_conftest import (  # noqa: F401
    cleanup_db,
    create_group_and_task,
    create_test_client,
    register_user,
    seed_rbac,
)

if not hasattr(sqlalchemy, "selectinload"):
    sqlalchemy.selectinload = _selectinload

from app.background.celery import celery_app
from app.db import db_helper

# --- Global containers ---
_es_container = None


def pytest_configure(config):
    """Start ES container before app imports - set ES_URL env var."""
    global _es_container
    _es_container = ElasticSearchContainer(
        "docker.elastic.co/elasticsearch/elasticsearch:9.3.3"
    )
    _es_container.with_env("discovery.type", "single-node")
    _es_container.with_env("xpack.security.enabled", "false")
    _es_container.with_env("ES_JAVA_OPTS", "-Xms512m -Xmx512m")
    _es_container.start()

    es_port = _es_container.get_exposed_port(9200)
    es_url = f'["http://127.0.0.1:{es_port}"]'
    os.environ["ES_URL"] = es_url

    import app.es as es_module
    from app.core.config import es_settings
    from app.es.client import ElasticsearchHelper

    new_helper = ElasticsearchHelper(es_settings)
    new_helper._auto_setup_dsl = False
    es_module.es_helper = new_helper


def pytest_sessionfinish(session, exitstatus):
    """Stop ES container after all tests."""
    global _es_container
    if _es_container:
        _es_container.stop()
        _es_container = None


async def override_get_session():
    """Override for db_helper.get_session dependency."""
    from tests.pg_conftest import _test_session_factory

    if _test_session_factory:
        async with _test_session_factory() as session:
            yield session


_test_session_factory = None


# --- Infrastructure ---


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def postgres_container():
    with PostgresContainer("postgres:16-alpine") as container:
        yield container


@pytest.fixture(scope="session")
def es_container():
    """Return ES container started in pytest_configure."""
    return _es_container


@pytest.fixture(scope="session")
def redis_container():
    """Start Redis container."""
    with RedisContainer("redis:8.4.2-alpine") as container:
        yield container


# --- DB & Celery ---

_migrations_done = False


@pytest_asyncio.fixture(scope="session")
async def test_engine(postgres_container, event_loop):
    global _migrations_done

    db_url = postgres_container.get_connection_url().replace("psycopg2", "asyncpg")
    os.environ["DATABASE_URL"] = db_url
    os.environ["DB_URL"] = db_url

    if not _migrations_done:
        result = subprocess.run(
            ["uv", "run", "alembic", "upgrade", "head"],  # noqa: S607
            capture_output=True,
            text=True,
            env={**os.environ, "DATABASE_URL": db_url, "DB_URL": db_url},
        )
        if result.returncode != 0:
            pytest.fail(f"Alembic migration failed: {result.stderr}")
        _migrations_done = True

    engine = create_async_engine(db_url, poolclass=NullPool, echo=False)
    yield engine
    await engine.dispose()


_current_test_schema = None


def set_current_schema(schema_name: str) -> None:
    global _current_test_schema
    _current_test_schema = schema_name


@pytest_asyncio.fixture(scope="function")
async def test_schema(test_engine: Any) -> AsyncGenerator[str, None]:
    schema_name = f"test_{uuid.uuid4().hex[:8]}"
    async with test_engine.connect() as conn:
        await conn.execute(text(f'CREATE SCHEMA IF NOT EXISTS "{schema_name}"'))
        await conn.commit()

        await conn.execute(text(f"SET search_path TO {schema_name}"))
        await conn.commit()

        if not hasattr(test_schema, "_migrations_done"):
            result = subprocess.run(
                ["uv", "run", "alembic", "upgrade", "head"],  # noqa: S607
                capture_output=True,
                text=True,
            )
            if result.returncode != 0:
                pytest.fail(...)
            test_schema._migrations_done = True

    session_factory = async_sessionmaker(test_engine, expire_on_commit=False)
    async with session_factory() as session:
        await session.execute(text(f"SET search_path TO {schema_name}"))
        await session.commit()
        await seed_rbac(session)

    yield schema_name

    async with test_engine.connect() as conn:
        await conn.execute(text(f'DROP SCHEMA IF EXISTS "{schema_name}" CASCADE'))
        await conn.commit()


@pytest.fixture
def schema_session_factory(test_engine, test_schema):
    set_current_schema(test_schema)
    return async_sessionmaker(test_engine, expire_on_commit=False)


@pytest_asyncio.fixture
async def es_client(es_container):
    """Create Elasticsearch client - one index for all tests."""
    host = es_container.get_container_host_ip()
    port = es_container.get_exposed_port(9200)

    os.environ["ELASTICSEARCH_URL"] = f'["http://{host}:{port}"]'

    client = AsyncElasticsearch(
        hosts=[f"http://{host}:{port}"],
        sniff_on_start=False,
        sniff_on_node_failure=False,
    )

    index_name = "test_index"
    await client.indices.create(index=index_name, ignore=400)

    alias_names = [
        "tasks_v1",
        "users_v1",
        "groups_v1",
        "comments_v1",
        "notifications_v1",
    ]
    for alias_name in alias_names:
        try:
            await client.indices.put_alias(index=index_name, name=alias_name)
        except elasticsearch.exceptions.RequestError:
            pass

    yield client

    await client.delete_by_query(
        index=index_name,
        body={"query": {"match_all": {}}},
        refresh=True,
    )
    await client.close()


@pytest_asyncio.fixture(scope="function")
async def isolated_es_client(es_container, request):
    """Create isolated Elasticsearch client with per-test indexes."""
    test_name = (
        request.node.name[:20].replace("[", "").replace("]", "").replace("/", "_")
    )
    host = es_container.get_container_host_ip()
    port = es_container.get_exposed_port(9200)

    client = AsyncElasticsearch(
        hosts=[f"http://{host}:{port}"],
        sniff_on_start=False,
        sniff_on_node_failure=False,
    )

    index_names = [
        "tasks_v1",
        "users_v1",
        "groups_v1",
        "comments_v1",
        "notifications_v1",
    ]
    for alias_name in index_names:
        idx = f"{test_name}_{alias_name}"
        try:
            await client.indices.create(index=idx, ignore=400)
            await client.indices.put_alias(index=idx, name=alias_name)
        except Exception:  # noqa: S110 BLE001
            pass

    yield client

    for alias_name in index_names:
        idx = f"{test_name}_{alias_name}"
        try:
            await client.indices.delete(index=idx, ignore=404)
        except Exception:  # noqa: S110 BLE001
            pass
    await client.close()


@pytest_asyncio.fixture(autouse=True, scope="session")
def setup_celery():
    """Configure Celery for synchronous execution in tests."""
    celery_app.conf.update(task_always_eager=True, task_eager_propagates=True)


# --- Test Client ---

_test_session_factory = None


@pytest_asyncio.fixture(scope="function")
async def test_client(
    schema_session_factory,
    isolated_es_client,
    redis_container,
    test_schema,
):
    db_helper.engine = schema_session_factory.kw["bind"]
    db_helper.session_factory = schema_session_factory

    redis_host = redis_container.get_container_host_ip()
    redis_port = redis_container.get_exposed_port(6379)
    redis_url = f"redis://{redis_host}:{redis_port}/0"
    os.environ["CACHE_URL"] = redis_url
    redis_client = aioredis.from_url(redis_url, encoding="utf-8", decode_responses=True)
    await redis_client.flushdb()
    FastAPICache.init(RedisBackend(redis_client), prefix="fastapi-cache")

    async with await create_test_client(schema_session_factory) as client:
        yield client

    FastAPICache.reset()
    await redis_client.close()


# --- Cleanup ---


@pytest_asyncio.fixture(autouse=True)
async def cleanup_schemas(test_engine, isolated_es_client, redis_container):
    """Only Redis/ES cleanup, DB is dropped via test schema."""
    yield

    redis_host = redis_container.get_container_host_ip()
    redis_port = redis_container.get_exposed_port(6379)
    cleanup_redis = aioredis.from_url(
        f"redis://{redis_host}:{redis_port}/0", encoding="utf-8", decode_responses=True
    )
    await cleanup_redis.flushdb()
    await cleanup_redis.flushall()
    FastAPICache.reset()
    await cleanup_redis.close()

    try:
        test_name = isolated_es_client._transport.hosts[0].get("url", "").split("/")[-1]
        if test_name:
            for alias in [
                "tasks_v1",
                "users_v1",
                "groups_v1",
                "comments_v1",
                "notifications_v1",
            ]:
                idx_name = f"{test_name}_{alias}"
                try:
                    await isolated_es_client.indices.delete(
                        index=idx_name, ignore=[404]
                    )
                except Exception:  # noqa: S110 BLE001
                    pass
    except Exception:  # noqa: S110 BLE001
        pass


# --- Auth Fixtures ---


@pytest_asyncio.fixture
async def auth_headers(test_client: AsyncClient, schema_session_factory):
    uid = uuid.uuid4().hex[:8]
    username = f"user_{uid}"
    email = f"user_{uid}@test.com"

    async with schema_session_factory() as session:
        await session.execute(
            text("DELETE FROM users WHERE username = :username"),
            {"username": username},
        )
        await session.commit()

    resp = await test_client.post(
        "/auth",
        json={
            "username": username,
            "email": email,
            "password": "TestUser123",
            "first_name": "Test",
            "last_name": "User",
        },
    )
    assert resp.status_code == 201

    async with schema_session_factory() as session:
        await session.execute(
            text("UPDATE users SET role = 'USER' WHERE username = :username"),
            {"username": username},
        )
        await session.commit()

    login_resp = await test_client.post(
        "/auth/token",
        data={"username": username, "password": "TestUser123"},
    )
    assert login_resp.status_code == 200

    token = login_resp.json()["access_token"]
    return {
        "Authorization": f"Bearer {token}",
        "username": username,
        "email": email,
    }


@pytest_asyncio.fixture
async def admin_auth_headers(
    test_client: AsyncClient,
    schema_session_factory,
):
    """Create admin and seed RBAC (ADMIN role) for this schema."""
    uid = uuid.uuid4().hex[:8]
    username = f"admin_{uid}"
    email = f"admin_{uid}@test.com"

    resp = await test_client.post(
        "/auth",
        json={
            "username": username,
            "email": email,
            "password": "TestAdmin123456",
            "first_name": "Admin",
            "last_name": "Test",
        },
    )
    assert resp.status_code == 201

    login_resp = await test_client.post(
        "/auth/token",
        data={"username": username, "password": "TestAdmin123456"},
    )
    assert login_resp.status_code == 200

    async with schema_session_factory() as session:
        user = await session.execute(
            text("SELECT id FROM users WHERE username = :username"),
            {"username": username},
        )
        user_id = user.scalar()

        await session.execute(
            text("UPDATE users SET role = 'ADMIN' WHERE id = :id"), {"id": user_id}
        )

        await seed_rbac(session)

        await session.commit()

    token = login_resp.json()["access_token"]
    return {
        "Authorization": f"Bearer {token}",
        "username": username,
        "email": email,
    }


@pytest_asyncio.fixture
async def testuser_auth_headers(test_client: AsyncClient, schema_session_factory):
    username = "testuser"
    email = "test@test.com"
    password = "Test123456789"  # noqa: S105

    async with schema_session_factory() as session:
        await session.execute(
            text("DELETE FROM users WHERE username = :username"),
            {"username": username},
        )
        await session.commit()

    resp = await test_client.post(
        "/auth",
        json={
            "username": username,
            "email": email,
            "password": password,
            "first_name": "Test",
            "last_name": "User",
        },
    )
    assert resp.status_code == 201

    async with schema_session_factory() as session:
        await session.execute(
            text("UPDATE users SET role = 'USER' WHERE username = :username"),
            {"username": username},
        )
        await session.commit()

    login_resp = await test_client.post(
        "/auth/token",
        data={"username": username, "password": password},
    )
    assert login_resp.status_code == 200

    token = login_resp.json()["access_token"]
    return {
        "Authorization": f"Bearer {token}",
        "username": username,
        "email": email,
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

        async with schema_session_factory() as session:
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
def mock_prometheus_metrics():
    """Mock Prometheus metrics."""

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
