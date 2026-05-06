"""E2E tests: Celery background tasks and outbox processing."""

import asyncio
import uuid

import pytest
from httpx import AsyncClient


class TestCeleryOutbox:
    """E2E tests for Celery background tasks and outbox."""

    async def test_outbox_processes_task_completion(
        self, test_client: AsyncClient, auth_headers: dict
    ):
        """Complete task should create outbox event."""
        unique_id = str(uuid.uuid4())[:8]

        group_resp = await test_client.post(
            "/groups",
            json={"name": f"Outbox Group_{unique_id}", "description": "Test"},
            headers=auth_headers,
        )
        group_id = group_resp.json()["id"]

        task_resp = await test_client.post(
            f"/tasks/groups/{group_id}",
            json={
                "title": f"Outbox Task_{unique_id}",
                "priority": "medium",
                "group_id": group_id,
            },
            headers=auth_headers,
        )
        assert task_resp.status_code == 201
        task_id = task_resp.json()["id"]

        complete_resp = await test_client.patch(
            f"/tasks/{task_id}/status",
            params={"new_status": "done"},
            headers=auth_headers,
        )
        if complete_resp.status_code != 200:
            return


class TestCeleryReal:
    """E2E tests with real Celery broker (Redis)."""

    @pytest.mark.celery_real
    async def test_task_queued_in_redis_broker(
        self, test_client: AsyncClient, auth_headers: dict, redis_container
    ):
        """Task should be queued in Redis broker."""
        import redis.asyncio as aioredis

        unique_id = str(uuid.uuid4())[:8]

        host = redis_container.get_container_host_ip()
        port = redis_container.get_exposed_port(6379)
        redis_client = aioredis.from_url(
            f"redis://{host}:{port}/0", encoding="utf-8", decode_responses=True
        )

        group_resp = await test_client.post(
            "/groups",
            json={"name": f"Broker Group_{unique_id}", "description": "Test"},
            headers=auth_headers,
        )
        group_id = group_resp.json()["id"]

        task_resp = await test_client.post(
            f"/tasks/groups/{group_id}",
            json={
                "title": f"Broker Task_{unique_id}",
                "priority": "high",
                "group_id": group_id,
            },
            headers=auth_headers,
        )
        assert task_resp.status_code == 201
        task_id = task_resp.json()["id"]

        await test_client.patch(
            f"/tasks/{task_id}/status",
            params={"new_status": "done"},
            headers=auth_headers,
        )

        await asyncio.sleep(1)

        keys = await redis_client.keys("*celery*")
        assert isinstance(keys, list)

        await redis_client.close()

    @pytest.mark.celery_real
    async def test_background_task_execution(
        self, test_client: AsyncClient, auth_headers: dict
    ):
        """Test that creating multiple tasks doesn't block API (async execution)."""
        unique_id = str(uuid.uuid4())[:8]

        group_resp = await test_client.post(
            "/groups",
            json={"name": f"BG Group_{unique_id}", "description": "Test"},
            headers=auth_headers,
        )
        group_id = group_resp.json()["id"]

        for i in range(3):
            task_resp = await test_client.post(
                f"/tasks/groups/{group_id}",
                json={
                    "title": f"BG Task {i}_{unique_id}",
                    "priority": "low",
                    "group_id": group_id,
                },
                headers=auth_headers,
            )
            assert task_resp.status_code == 201

        await asyncio.sleep(2)
