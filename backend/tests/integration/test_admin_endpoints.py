import uuid

from httpx import AsyncClient


class TestAdminUsers:
    async def test_admin_get_all_users_returns_200(
        self, test_client: AsyncClient, admin_auth_headers: dict
    ):
        """Admin can get all users."""
        resp = await test_client.get("/admin/users", headers=admin_auth_headers)
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    async def test_admin_get_users_with_pagination(
        self, test_client: AsyncClient, admin_auth_headers: dict
    ):
        """Admin can get users with pagination."""
        resp = await test_client.get(
            "/admin/users?limit=10&offset=0", headers=admin_auth_headers
        )
        assert resp.status_code == 200

    async def test_admin_delete_user_returns_204(
        self, test_client: AsyncClient, admin_auth_headers: dict
    ):
        """Admin can delete user."""
        import jwt

        username = f"delete_{uuid.uuid4().hex[:8]}"
        resp = await test_client.post(
            "/auth",
            json={
                "username": username,
                "email": f"{username}@test.com",
                "password": "Password123",
                "first_name": "Delete",
                "last_name": "Test",
            },
        )
        token = resp.json()["access_token"]
        payload = jwt.decode(token, options={"verify_signature": False})
        new_user_id = int(payload.get("sub"))

        resp = await test_client.delete(
            f"/admin/users/{new_user_id}", headers=admin_auth_headers
        )
        assert resp.status_code == 204

    async def test_admin_cannot_delete_self(
        self, test_client: AsyncClient, admin_auth_headers: dict
    ):
        """Admin cannot delete themselves."""
        import jwt

        token = admin_auth_headers["Authorization"].replace("Bearer ", "")
        payload = jwt.decode(token, options={"verify_signature": False})
        admin_id = int(payload.get("sub"))

        resp = await test_client.delete(
            f"/admin/users/{admin_id}", headers=admin_auth_headers
        )
        assert resp.status_code == 403


class TestAdminStats:
    async def test_admin_get_stats_returns_200(
        self, test_client: AsyncClient, admin_auth_headers: dict
    ):
        """Admin can get statistics."""
        resp = await test_client.get("/admin/stats", headers=admin_auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "users" in data
        assert "groups" in data
        assert "tasks" in data


class TestAdminUnauthorized:
    async def test_unauthorized_cannot_access_admin(self, test_client: AsyncClient):
        """Non-admin cannot access admin endpoints."""
        resp = await test_client.get("/admin/users")
        assert resp.status_code == 401

    async def test_regular_user_cannot_access_admin(
        self, test_client: AsyncClient, auth_headers: dict
    ):
        """Regular user cannot access admin endpoints."""
        resp = await test_client.get("/admin/users", headers=auth_headers)
        assert resp.status_code == 403


class TestHealthCheck:
    async def test_health_check_returns_200(self, test_client: AsyncClient):
        """Health check endpoint returns 200."""
        resp = await test_client.get("/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"
        assert "version" in data

    async def test_metrics_returns_200(self, test_client: AsyncClient):
        """Metrics endpoint returns 200."""
        resp = await test_client.get("/metrics")
        assert resp.status_code == 200
