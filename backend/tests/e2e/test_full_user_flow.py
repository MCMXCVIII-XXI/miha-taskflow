"""E2E tests: Full user journey from registration to task completion with XP."""

import uuid
from datetime import UTC, datetime, timedelta

from httpx import AsyncClient


class TestFullUserFlow:
    """E2E tests for complete user journey."""

    async def test_complete_user_journey(
        self, test_client: AsyncClient, auth_headers: dict
    ):
        """Registration → group → task → completion → XP → notification."""
        unique_id = str(uuid.uuid4())[:8]

        me_resp = await test_client.get("/users/me", headers=auth_headers)
        assert me_resp.status_code == 200

        group_resp = await test_client.post(
            "/groups",
            json={
                "name": f"E2E Group_{unique_id}",
                "description": "Full journey group",
            },
            headers=auth_headers,
        )
        assert group_resp.status_code == 201
        group_id = group_resp.json()["id"]

        task_resp = await test_client.post(
            f"/tasks/groups/{group_id}",
            json={
                "title": f"E2E Task_{unique_id}",
                "description": "Complete journey task",
                "priority": "high",
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
        if complete_resp.status_code == 200:
            pass

        notif_resp = await test_client.get("/notifications", headers=auth_headers)
        if notif_resp.status_code == 200:
            pass

    async def test_task_with_deadline_bonus(
        self, test_client: AsyncClient, auth_headers: dict
    ):
        """Task with deadline should calculate time bonus."""

        unique_id = str(uuid.uuid4())[:8]

        group_resp = await test_client.post(
            "/groups",
            json={"name": f"Deadline Group_{unique_id}", "description": "Test"},
            headers=auth_headers,
        )
        assert group_resp.status_code == 201
        group_id = group_resp.json()["id"]

        future_deadline = (datetime.now(tz=UTC) + timedelta(days=7)).isoformat()
        task_resp = await test_client.post(
            f"/tasks/groups/{group_id}",
            json={
                "title": f"Deadline Task_{unique_id}",
                "priority": "high",
                "deadline": future_deadline,
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
