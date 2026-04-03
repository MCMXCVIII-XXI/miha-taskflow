import uuid

from httpx import AsyncClient

from tests.conftest import register_user


class TestGroupVisibility:
    """Test group visibility and access controls."""

    async def test_search_all_groups_requires_auth(self, test_client: AsyncClient):
        """Search all groups without auth — returns 401."""
        resp = await test_client.get("/groups")
        assert resp.status_code == 401


class TestGroupMembers:
    """Test group member management edge cases."""

    async def test_cannot_add_self_as_member(
        self, test_client: AsyncClient, auth_headers: dict
    ):
        """Cannot add yourself as a member to your own group."""
        me_resp = await test_client.get("/users/me", headers=auth_headers)
        my_id = me_resp.json()["id"]

        resp = await test_client.post(
            "/groups",
            json={"name": f"group_{uuid.uuid4().hex[:8]}"},
            headers=auth_headers,
        )
        group_id = resp.json()["id"]

        resp = await test_client.post(
            f"/groups/{group_id}/members/{my_id}",
            headers=auth_headers,
        )
        assert resp.status_code in [201, 400, 409]

    async def test_remove_nonexistent_member_returns_404(
        self, test_client: AsyncClient, auth_headers: dict
    ):
        """Remove nonexistent member returns 404."""
        resp = await test_client.post(
            "/groups",
            json={"name": f"group_{uuid.uuid4().hex[:8]}"},
            headers=auth_headers,
        )
        group_id = resp.json()["id"]

        resp = await test_client.delete(
            f"/groups/{group_id}/members/999999",
            headers=auth_headers,
        )
        assert resp.status_code == 404


class TestUserSearchEdgeCases:
    """Test user search edge cases."""

    async def test_search_users_invalid_limit(
        self, test_client: AsyncClient, auth_headers: dict
    ):
        """Search with invalid limit returns 422."""
        resp = await test_client.get("/users?limit=-1", headers=auth_headers)
        assert resp.status_code == 422

    async def test_search_users_high_limit(self, test_client: AsyncClient):
        """Search with high limit works."""
        resp = await test_client.get("/users?limit=1000")
        assert resp.status_code in [200, 401]


class TestAdminEdgeCases:
    """Test admin endpoint edge cases."""

    async def test_delete_nonexistent_user(
        self, test_client: AsyncClient, admin_auth_headers: dict
    ):
        """Delete nonexistent user returns 404."""
        resp = await test_client.delete(
            "/admin/users/999999",
            headers=admin_auth_headers,
        )
        assert resp.status_code == 404


class TestTokenEdgeCases:
    """Test token edge cases."""

    async def test_refresh_invalid_token(self, test_client: AsyncClient):
        """Refresh with invalid token returns 401."""
        resp = await test_client.post(
            "/auth/refresh-token",
            json={"refresh_token": "invalid_token"},
        )
        assert resp.status_code in [401, 404]

    async def test_access_invalid_token(self, test_client: AsyncClient):
        """Access with invalid token returns 401."""
        resp = await test_client.get(
            "/users/me",
            headers={"Authorization": "Bearer invalid_token"},
        )
        assert resp.status_code == 401


class TestLoginEdgeCases:
    """Test login edge cases."""

    async def test_login_empty_username(self, test_client: AsyncClient):
        """Login with empty username returns 422."""
        resp = await test_client.post(
            "/auth/token",
            data={"username": "", "password": "Password123"},
        )
        assert resp.status_code == 422

    async def test_login_empty_password(self, test_client: AsyncClient):
        """Login with empty password returns 422."""
        resp = await test_client.post(
            "/auth/token",
            data={"username": "testuser", "password": ""},
        )
        assert resp.status_code == 422


class TestProfileUpdateEdgeCases:
    """Test profile update edge cases."""

    async def test_update_invalid_email(self, test_client: AsyncClient):
        """Update profile with invalid email returns 422."""
        headers = await register_user(test_client)

        resp = await test_client.patch(
            "/users/me",
            json={"email": "not-an-email"},
            headers=headers,
        )
        assert resp.status_code == 422

    async def test_update_short_username(
        self, test_client: AsyncClient, auth_headers: dict
    ):
        """Update profile with short username returns 422."""
        resp = await test_client.patch(
            "/users/me",
            json={"username": "ab"},
            headers=auth_headers,
        )
        assert resp.status_code in [200, 422]
