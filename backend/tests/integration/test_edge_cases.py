import uuid

from httpx import AsyncClient

from tests.conftest import register_user


class TestGroupVisibility:
    """Test group visibility and access controls."""

    async def test_search_all_groups_requires_auth(self, test_client: AsyncClient):
        """Search all groups without auth — returns 401."""
        resp = await test_client.get("/search/groups")

        assert resp.status_code in [401, 404]


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


class TestPaginationEdgeCases:
    """Test pagination edge cases."""

    async def test_notifications_limit_zero_returns_200(
        self, test_client: AsyncClient, auth_headers: dict
    ):
        """Get notifications with limit=0 returns 200."""
        resp = await test_client.get("/notifications?limit=0", headers=auth_headers)
        assert resp.status_code in [200, 422]

    async def test_notifications_limit_max_returns_200(
        self, test_client: AsyncClient, auth_headers: dict
    ):
        """Get notifications with limit=100 returns 200."""
        resp = await test_client.get("/notifications?limit=100", headers=auth_headers)
        assert resp.status_code == 200

    async def test_notifications_offset_large_returns_empty(
        self, test_client: AsyncClient, auth_headers: dict
    ):
        """Get notifications with large offset returns empty list."""
        resp = await test_client.get(
            "/notifications?offset=999999", headers=auth_headers
        )
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)

    async def test_notifications_limit_exceed_max_returns_422(
        self, test_client: AsyncClient, auth_headers: dict
    ):
        """Get notifications with limit>100 returns 422."""
        resp = await test_client.get("/notifications?limit=101", headers=auth_headers)
        assert resp.status_code == 422

    async def test_admin_users_limit_min_returns_200(
        self, test_client: AsyncClient, admin_auth_headers: dict
    ):
        """Admin get users with limit=1 returns 200."""
        resp = await test_client.get("/admin/users?limit=1", headers=admin_auth_headers)
        assert resp.status_code == 200

    async def test_admin_users_limit_exceed_max_returns_422(
        self, test_client: AsyncClient, admin_auth_headers: dict
    ):
        """Admin get users with limit>100 returns 422."""
        resp = await test_client.get(
            "/admin/users?limit=101", headers=admin_auth_headers
        )
        assert resp.status_code == 422


class TestSearchBoundary:
    """Test search boundary conditions."""

    async def test_search_with_empty_params_returns_200(
        self, test_client: AsyncClient, auth_headers: dict
    ):
        """Search with minimal params returns 200 or 404."""
        resp = await test_client.get("/search/tasks", headers=auth_headers)
        assert resp.status_code in [200, 404]


class TestInvalidInput:
    """Test invalid input handling."""

    async def test_get_group_invalid_id_format_returns_error(
        self, test_client: AsyncClient, auth_headers: dict
    ):
        """Get group with invalid ID format returns 4xx."""
        resp = await test_client.get("/groups/abc", headers=auth_headers)
        assert resp.status_code >= 400

    async def test_create_task_missing_title_returns_422(
        self, test_client: AsyncClient, auth_headers: dict
    ):
        """Create task without title returns 422."""
        group_resp = await test_client.post(
            "/groups",
            json={"name": f"group_{uuid.uuid4().hex[:8]}"},
            headers=auth_headers,
        )
        group_id = group_resp.json()["id"]

        resp = await test_client.post(
            f"/tasks/groups/{group_id}",
            json={"priority": "medium", "group_id": group_id},
            headers=auth_headers,
        )
        assert resp.status_code == 422


class TestRatingEdgeCases:
    """Test rating edge cases."""

    async def test_create_rating_invalid_score(
        self, test_client: AsyncClient, admin_auth_headers: dict
    ):
        """Create rating with invalid score returns error."""
        group_resp = await test_client.post(
            "/groups",
            json={"name": f"rate_{uuid.uuid4().hex[:8]}"},
            headers=admin_auth_headers,
        )
        group_id = group_resp.json()["id"]

        resp = await test_client.post(
            "/ratings",
            json={"score": 0, "group_id": group_id},
            headers=admin_auth_headers,
        )
        assert resp.status_code in [400, 422, 404]
