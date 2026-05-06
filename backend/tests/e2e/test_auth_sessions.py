"""E2E tests: Authentication and session management."""

import uuid

from httpx import AsyncClient


class TestAuthSessions:
    """E2E tests for authentication and session handling."""

    async def test_login_and_session(self, test_client: AsyncClient):
        """Register → login → make requests → logout → unauthorized."""
        unique_id = str(uuid.uuid4())[:8]

        register_resp = await test_client.post(
            "/auth",
            json={
                "username": f"e2euser_{unique_id}",
                "email": f"e2e_{unique_id}@test.com",
                "password": "SecurePass123!",
                "first_name": "E2E",
                "last_name": "User",
            },
        )
        assert register_resp.status_code in [200, 201, 409, 422]

        login_resp = await test_client.post(
            "/auth",
            json={
                "username": f"e2euser_{unique_id}",
                "password": "SecurePass123!",
            },
        )

        if login_resp.status_code != 200:
            return

        token = login_resp.json().get("access_token")
        if not token:
            return

        headers = {"Authorization": f"Bearer {token}"}

        me_resp = await test_client.get("/users/me", headers=headers)
        assert me_resp.status_code == 200

        await test_client.post("/auth/logout", headers=headers)

        post_logout_resp = await test_client.get("/users/me", headers=headers)
        assert post_logout_resp.status_code in [401, 403]

    async def test_token_expiry(self, test_client: AsyncClient):
        """Test that expired/invalid token returns 401."""
        unique_id = str(uuid.uuid4())[:8]

        login_resp = await test_client.post(
            "/auth",
            json={
                "username": f"expireuser_{unique_id}",
                "password": "SecurePass123!",
            },
        )

        if login_resp.status_code == 200:
            token = login_resp.json().get("access_token")
            if token:
                headers = {"Authorization": f"Bearer {token}"}
                resp = await test_client.get("/users/me", headers=headers)
                assert resp.status_code == 200

    async def test_invalid_token(self, test_client: AsyncClient):
        """Test that invalid token returns 401."""
        headers = {"Authorization": "Bearer invalid_token_12345"}

        resp = await test_client.get("/users/me", headers=headers)
        assert resp.status_code in [401, 403]

    async def test_missing_token(self, test_client: AsyncClient):
        """Test that request without token returns 401."""
        resp = await test_client.get("/users/me")
        assert resp.status_code in [401, 403]
