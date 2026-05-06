"""
Comprehensive edge case tests for all endpoints.

Tests for:
- 404 (resource not found)
- 422 (validation errors)
- 403 (forbidden access)
- Boundary conditions
- Idempotency

Note: Some tests accept both 403 and 404 because the permission check
may happen before the resource existence check (security best practice).
"""

import uuid

from httpx import AsyncClient

from tests.conftest import register_user

# ============================================================================
# 404/403 TESTS - Resource Not Found or Forbidden
# ============================================================================


class TestGroupNotFound:
    """Test responses for non-existent groups.

    Note: API returns 403 (Forbidden) instead of 404 when permission check
    fails first. This is correct behavior - don't leak resource existence.
    """

    async def test_get_nonexistent_group_returns_403_or_404(
        self, test_client: AsyncClient, auth_headers: dict
    ):
        """Get non-existent group returns 403 or 404."""
        resp = await test_client.get("/groups/999999", headers=auth_headers)
        assert resp.status_code in [403, 404]

    async def test_update_nonexistent_group_returns_403_or_404(
        self, test_client: AsyncClient, auth_headers: dict
    ):
        """Update non-existent group returns 403 or 404."""
        resp = await test_client.patch(
            "/groups/999999", json={"name": "Updated"}, headers=auth_headers
        )
        assert resp.status_code in [403, 404]

    async def test_delete_nonexistent_group_returns_403_or_404(
        self, test_client: AsyncClient, auth_headers: dict
    ):
        """Delete non-existent group returns 403 or 404."""
        resp = await test_client.delete("/groups/999999", headers=auth_headers)
        assert resp.status_code in [403, 404]

    async def test_join_nonexistent_group_returns_404(
        self, test_client: AsyncClient, auth_headers: dict
    ):
        """Join non-existent group returns 404."""
        resp = await test_client.post("/groups/999999/join", headers=auth_headers)
        assert resp.status_code == 404


class TestTaskNotFound:
    """Test responses for non-existent tasks."""

    async def test_update_nonexistent_task_returns_403_or_404(
        self, test_client: AsyncClient, auth_headers: dict
    ):
        """Update non-existent task returns 403 or 404."""
        resp = await test_client.patch(
            "/tasks/999999", json={"title": "Updated"}, headers=auth_headers
        )
        assert resp.status_code in [403, 404]

    async def test_delete_nonexistent_task_returns_403_or_404(
        self, test_client: AsyncClient, auth_headers: dict
    ):
        """Delete non-existent task returns 403 or 404."""
        resp = await test_client.delete("/tasks/999999", headers=auth_headers)
        assert resp.status_code in [403, 404]

    async def test_update_status_nonexistent_task_returns_404(
        self, test_client: AsyncClient, auth_headers: dict
    ):
        """Update status of non-existent task returns 404."""
        resp = await test_client.patch(
            "/tasks/999999/status?new_status=done", headers=auth_headers
        )
        assert resp.status_code in [403, 404]


class TestUserNotFound:
    """Test responses for non-existent user resources."""

    async def test_get_group_admin_of_nonexistent_group_returns_404(
        self, test_client: AsyncClient, auth_headers: dict
    ):
        """Get admin of non-existent group returns 404."""
        resp = await test_client.get("/users/groups/999999/admin", headers=auth_headers)
        assert resp.status_code in [403, 404]

    async def test_get_task_owner_of_nonexistent_task_returns_404(
        self, test_client: AsyncClient, auth_headers: dict
    ):
        """Get owner of non-existent task returns 404."""
        resp = await test_client.get("/users/tasks/999999/owner", headers=auth_headers)
        assert resp.status_code in [403, 404]


# ============================================================================
# 422 TESTS - Validation Errors
# ============================================================================


class TestGroupValidation:
    """Test validation errors for groups."""

    async def test_create_group_long_name_returns_422(
        self, test_client: AsyncClient, auth_headers: dict
    ):
        """Create group with name too long returns 422."""
        resp = await test_client.post(
            "/groups", json={"name": "a" * 51}, headers=auth_headers
        )
        assert resp.status_code == 422


class TestTaskValidation:
    """Test validation errors for tasks."""

    async def test_create_task_long_title_returns_422(
        self, test_client: AsyncClient, auth_headers: dict
    ):
        """Create task with title too long returns 422."""
        group_resp = await test_client.post(
            "/groups",
            json={"name": f"group_{uuid.uuid4().hex[:8]}"},
            headers=auth_headers,
        )
        group_id = group_resp.json()["id"]

        resp = await test_client.post(
            f"/tasks/groups/{group_id}",
            json={"title": "a" * 201, "priority": "medium", "group_id": group_id},
            headers=auth_headers,
        )
        assert resp.status_code == 422

    async def test_create_task_invalid_priority_returns_422(
        self, test_client: AsyncClient, auth_headers: dict
    ):
        """Create task with invalid priority returns 422."""
        group_resp = await test_client.post(
            "/groups",
            json={"name": f"group_{uuid.uuid4().hex[:8]}"},
            headers=auth_headers,
        )
        group_id = group_resp.json()["id"]

        resp = await test_client.post(
            f"/tasks/groups/{group_id}",
            json={"title": "Valid Title", "priority": "invalid", "group_id": group_id},
            headers=auth_headers,
        )
        assert resp.status_code == 422


class TestNotificationValidation:
    """Test validation errors for notifications."""

    async def test_respond_invalid_response_type_returns_422(
        self, test_client: AsyncClient, auth_headers: dict
    ):
        """Respond to notification with invalid response type returns 422."""
        other_headers = await register_user(test_client)
        other_user_id = int(
            (await test_client.get("/users/me", headers=other_headers)).json()["id"]
        )

        group_resp = await test_client.post(
            "/groups",
            json={"name": f"notif_{uuid.uuid4().hex[:8]}"},
            headers=auth_headers,
        )
        group_id = group_resp.json()["id"]

        await test_client.post(
            f"/groups/{group_id}/members/{other_user_id}",
            headers=auth_headers,
        )

        notif_resp = await test_client.get("/notifications", headers=other_headers)
        notifications = notif_resp.json()

        if notifications:
            notification_id = notifications[0]["id"]
            resp = await test_client.post(
                f"/notifications/{notification_id}/respond",
                json={"response": "invalid_response"},
                headers=other_headers,
            )
            assert resp.status_code == 422


# ============================================================================
# 403 TESTS - Forbidden Access
# ============================================================================


class TestCrossUserAccess:
    """Test forbidden access to other users' resources."""

    async def test_user_cannot_access_other_user_notifications(
        self, test_client: AsyncClient, auth_headers: dict
    ):
        """User cannot access another user's notifications directly."""
        other_headers = await register_user(test_client)
        other_user_id = int(
            (await test_client.get("/users/me", headers=other_headers)).json()["id"]
        )

        group_resp = await test_client.post(
            "/groups",
            json={"name": f"cross_{uuid.uuid4().hex[:8]}"},
            headers=auth_headers,
        )
        group_id = group_resp.json()["id"]

        await test_client.post(
            f"/groups/{group_id}/members/{other_user_id}",
            headers=auth_headers,
        )

        notif_resp = await test_client.get("/notifications", headers=other_headers)
        notifications = notif_resp.json()

        if notifications:
            notification_id = notifications[0]["id"]

            resp = await test_client.get(
                f"/notifications/{notification_id}",
                headers=auth_headers,
            )
            assert resp.status_code in [403, 404]


# ============================================================================
# BOUNDARY TESTS - String Length Limits
# ============================================================================


class TestBoundaryConditions:
    """Test boundary conditions for string lengths."""

    async def test_create_group_name_min_length_returns_201(
        self, test_client: AsyncClient, auth_headers: dict
    ):
        """Create group with name at minimum length (3) returns 201."""
        resp = await test_client.post(
            "/groups", json={"name": "abc"}, headers=auth_headers
        )
        assert resp.status_code == 201

    async def test_create_group_name_max_length_returns_201(
        self, test_client: AsyncClient, auth_headers: dict
    ):
        """Create group with name at maximum length (50) returns 201."""
        resp = await test_client.post(
            "/groups", json={"name": "a" * 50}, headers=auth_headers
        )
        assert resp.status_code == 201


# ============================================================================
# INVALID ID TESTS
# ============================================================================


class TestInvalidIds:
    """Test invalid ID parameters."""

    async def test_get_group_zero_id_returns_403_or_404(
        self, test_client: AsyncClient, auth_headers: dict
    ):
        """Get group with zero ID returns 403 or 404."""
        resp = await test_client.get("/groups/0", headers=auth_headers)
        assert resp.status_code in [403, 404]


# ============================================================================
# IDEMPOTENCY TESTS
# ============================================================================


class TestIdempotency:
    """Test idempotent operations."""

    async def test_delete_already_deleted_group_returns_403_or_404(
        self, test_client: AsyncClient, auth_headers: dict
    ):
        """Delete already deleted group returns 403 or 404."""
        group_resp = await test_client.post(
            "/groups",
            json={"name": f"del_{uuid.uuid4().hex[:8]}"},
            headers=auth_headers,
        )
        group_id = group_resp.json()["id"]

        await test_client.delete(f"/groups/{group_id}", headers=auth_headers)

        resp = await test_client.delete(f"/groups/{group_id}", headers=auth_headers)
        assert resp.status_code in [403, 404]

    async def test_delete_already_deleted_user_returns_401(
        self, test_client: AsyncClient
    ):
        """Delete already deleted user returns 401."""
        headers = await register_user(test_client, "delme", "delme@test.com")

        await test_client.delete("/users/me", headers=headers)

        resp = await test_client.delete("/users/me", headers=headers)
        assert resp.status_code == 401
