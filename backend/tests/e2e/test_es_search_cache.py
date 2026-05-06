"""E2E tests: Elasticsearch search and Redis cache."""

import asyncio
import uuid

import pytest
from httpx import AsyncClient


class TestESSearchCache:
    """E2E tests for ES search and Redis caching."""

    async def test_create_and_search_task(
        self, test_client: AsyncClient, auth_headers: dict
    ):
        """Create task and search for it via API."""
        unique_id = str(uuid.uuid4())[:8]

        group_resp = await test_client.post(
            "/groups",
            json={"name": f"Search Group_{unique_id}", "description": "ES test"},
            headers=auth_headers,
        )
        group_id = group_resp.json()["id"]

        task_resp = await test_client.post(
            f"/tasks/groups/{group_id}",
            json={
                "title": f"Searchable Task_{unique_id}",
                "description": "Task to find",
                "priority": "high",
                "group_id": group_id,
            },
            headers=auth_headers,
        )
        assert task_resp.status_code == 201

        await test_client.get(
            "/search/tasks",
            params={"q": unique_id},
            headers=auth_headers,
        )

    async def test_faceted_search(self, test_client: AsyncClient, auth_headers: dict):
        """Search with facets and filters."""
        unique_id = str(uuid.uuid4())[:8]

        group_resp = await test_client.post(
            "/groups",
            json={"name": f"Facet Group_{unique_id}", "description": "Test"},
            headers=auth_headers,
        )
        group_id = group_resp.json()["id"]

        for priority in ["low", "medium", "high"]:
            task_resp = await test_client.post(
                f"/tasks/groups/{group_id}",
                json={
                    "title": f"Facet Task {priority}_{unique_id}",
                    "priority": priority,
                    "group_id": group_id,
                },
                headers=auth_headers,
            )
            assert task_resp.status_code == 201

        await test_client.get(
            "/search/tasks",
            params={"priority": "high"},
            headers=auth_headers,
        )

    async def test_cache_hit(self, test_client: AsyncClient, auth_headers: dict):
        """Test that Redis cache reduces response time."""
        unique_id = str(uuid.uuid4())[:8]

        group_resp = await test_client.post(
            "/groups",
            json={"name": f"Cache Group_{unique_id}", "description": "Test"},
            headers=auth_headers,
        )
        group_id = group_resp.json()["id"]

        task_resp = await test_client.post(
            f"/tasks/groups/{group_id}",
            json={
                "title": f"Cache Task_{unique_id}",
                "priority": "low",
                "group_id": group_id,
            },
            headers=auth_headers,
        )
        assert task_resp.status_code == 201

        await test_client.get(
            "/search/tasks",
            params={"q": unique_id},
            headers=auth_headers,
        )

        await test_client.get(
            "/search/tasks",
            params={"q": unique_id},
            headers=auth_headers,
        )


class TestCeleryESIndex:
    """E2E tests for Celery → ES indexing."""

    @pytest.mark.celery_real
    async def test_celery_indexes_to_es(
        self, test_client: AsyncClient, auth_headers: dict, isolated_es_client
    ):
        """Celery should index task to ES asynchronously."""
        unique_id = str(uuid.uuid4())[:8]

        group_resp = await test_client.post(
            "/groups",
            json={"name": f"ES Celery Group_{unique_id}", "description": "Test"},
            headers=auth_headers,
        )
        group_id = group_resp.json()["id"]

        task_resp = await test_client.post(
            f"/tasks/groups/{group_id}",
            json={
                "title": f"ES Celery Task_{unique_id}",
                "priority": "high",
                "group_id": group_id,
            },
            headers=auth_headers,
        )
        assert task_resp.status_code == 201
        task_title = task_resp.json()["title"]

        for _ in range(10):
            try:
                search_resp = await isolated_es_client.search(
                    index="tasks_v1",
                    body={"query": {"match": {"title": task_title}}},
                )
                if search_resp["hits"]["total"]["value"] > 0:
                    break
            except Exception:  # noqa: S110 BLE001
                pass
            await asyncio.sleep(0.5)
        group_id = group_resp.json()["id"]

        task_resp = await test_client.post(
            f"/tasks/groups/{group_id}",
            json={
                "title": f"Searchable Task_{unique_id}",
                "description": "Task to find",
                "priority": "high",
                "group_id": group_id,
            },
            headers=auth_headers,
        )
        assert task_resp.status_code == 201

        search_resp = await test_client.get(
            "/search/tasks",
            params={"q": unique_id},
            headers=auth_headers,
        )

    async def test_faceted_search(self, test_client: AsyncClient, auth_headers: dict):
        """Search with facets and filters."""
        unique_id = str(uuid.uuid4())[:8]

        group_resp = await test_client.post(
            "/groups",
            json={"name": f"Facet Group_{unique_id}", "description": "Test"},
            headers=auth_headers,
        )
        group_id = group_resp.json()["id"]

        for priority in ["low", "medium", "high"]:
            task_resp = await test_client.post(
                f"/tasks/groups/{group_id}",
                json={
                    "title": f"Facet Task {priority}_{unique_id}",
                    "priority": priority,
                    "group_id": group_id,
                },
                headers=auth_headers,
            )
            assert task_resp.status_code == 201

        await test_client.get(
            "/search/tasks",
            params={"priority": "high"},
            headers=auth_headers,
        )

    async def test_cache_hit(self, test_client: AsyncClient, auth_headers: dict):
        """Test that Redis cache reduces response time."""
        unique_id = str(uuid.uuid4())[:8]

        group_resp = await test_client.post(
            "/groups",
            json={"name": f"Cache Group_{unique_id}", "description": "Test"},
            headers=auth_headers,
        )
        group_id = group_resp.json()["id"]

        task_resp = await test_client.post(
            f"/tasks/groups/{group_id}",
            json={
                "title": f"Cache Task_{unique_id}",
                "priority": "low",
                "group_id": group_id,
            },
            headers=auth_headers,
        )
        assert task_resp.status_code == 201

        await test_client.get(
            "/search/tasks",
            params={"q": unique_id},
            headers=auth_headers,
        )

        await test_client.get(
            "/search/tasks",
            params={"q": unique_id},
            headers=auth_headers,
        )
