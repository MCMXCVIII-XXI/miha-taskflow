from uuid import uuid4

from httpx import AsyncClient

from tests.conftest import register_user


class TestGetUser:
    """Test GET /users/{user_id} endpoint."""

    async def test_get_user_returns_200(
        self, test_client: AsyncClient, admin_auth_headers: dict
    ):
        """Get specific user profile — returns 200 (admin only)."""
        target_resp = await test_client.post(
            "/auth",
            json={
                "username": "targetuser",
                "email": "target@test.com",
                "password": "Test123456789",
                "first_name": "Target",
                "last_name": "User",
            },
        )
        target_token = target_resp.json()["access_token"]
        target_headers = {"Authorization": f"Bearer {target_token}"}

        me_resp = await test_client.get("/users/me", headers=target_headers)
        target_id = me_resp.json()["id"]
        resp = await test_client.get(f"/users/{target_id}", headers=admin_auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "username" in data
        assert "id" in data

    async def test_get_user_not_found_returns_404(
        self, test_client: AsyncClient, admin_auth_headers: dict
    ):
        """Get non-existent user — returns 404."""
        resp = await test_client.get("/users/999999", headers=admin_auth_headers)
        assert resp.status_code == 404

    async def test_get_user_without_auth_returns_401(self, test_client: AsyncClient):
        """Get user without auth — returns 401."""
        resp = await test_client.get("/users/1")
        assert resp.status_code == 401


class TestGetMyProfile:
    async def test_get_profile_returns_200(
        self, test_client: AsyncClient, testuser_auth_headers: dict
    ):
        """Get current user profile — returns 200."""
        resp = await test_client.get("/users/me", headers=testuser_auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "testuser" in data["username"]
        assert "@test.com" in data["email"]
        assert "id" in data
        assert "role" in data

    async def test_get_profile_without_auth_returns_401(self, test_client: AsyncClient):
        """Get profile without auth — returns 401."""
        resp = await test_client.get("/users/me")
        assert resp.status_code == 401


class TestUpdateProfile:
    async def test_update_profile_returns_200(
        self, test_client: AsyncClient, auth_headers: dict
    ):
        """Update own profile — returns 200."""
        resp = await test_client.patch(
            "/users/me",
            json={"first_name": "Updated"},
            headers=auth_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["first_name"] == "Updated"

    async def test_update_profile_email_returns_200(
        self, test_client: AsyncClient, auth_headers: dict
    ):
        """Update own email — returns 200."""
        resp = await test_client.patch(
            "/users/me",
            json={"email": "newemail@test.com"},
            headers=auth_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["email"] == "newemail@test.com"

    async def test_update_profile_duplicate_email_returns_409(
        self, test_client: AsyncClient, auth_headers: dict
    ):
        """Update email to already used — returns 409."""
        await test_client.post(
            "/auth",
            json={
                "username": "emailowner",
                "email": "taken@test.com",
                "password": "Password123",
                "first_name": "Email",
                "last_name": "Owner",
            },
        )
        resp = await test_client.patch(
            "/users/me",
            json={"email": "taken@test.com"},
            headers=auth_headers,
        )
        assert resp.status_code == 409

    async def test_update_profile_duplicate_username_returns_409(
        self, test_client: AsyncClient, auth_headers: dict
    ):
        """Update username to already used — returns 409."""
        await test_client.post(
            "/auth",
            json={
                "username": "takenuser",
                "email": "takenuser@test.com",
                "password": "Password123",
                "first_name": "Taken",
                "last_name": "User",
            },
        )
        resp = await test_client.patch(
            "/users/me",
            json={"username": "takenuser"},
            headers=auth_headers,
        )
        assert resp.status_code == 409

    async def test_update_profile_without_auth_returns_401(
        self, test_client: AsyncClient
    ):
        """Update profile without auth — returns 401."""
        resp = await test_client.patch(
            "/users/me",
            json={"first_name": "Hacked"},
        )
        assert resp.status_code == 401


class TestDeleteProfile:
    async def test_delete_profile_returns_204(self, test_client: AsyncClient):
        """Delete own profile — returns 204."""
        headers = await register_user(test_client, "deleteme", "deleteme@test.com")
        resp = await test_client.delete("/users/me", headers=headers)
        assert resp.status_code == 204

    async def test_deleted_user_cannot_access_profile(self, test_client: AsyncClient):
        """Deleted user cannot access profile — returns 401."""
        headers = await register_user(
            test_client, "deleteduser", "deleteduser@test.com"
        )
        await test_client.delete("/users/me", headers=headers)
        resp = await test_client.get("/users/me", headers=headers)
        assert resp.status_code == 401

    async def test_delete_profile_without_auth_returns_401(
        self, test_client: AsyncClient
    ):
        """Delete profile without auth — returns 401."""
        resp = await test_client.delete("/users/me")
        assert resp.status_code == 401


class TestGroupAdmin:
    async def test_get_group_admin_returns_200(
        self, test_client: AsyncClient, auth_headers: dict
    ):
        """Get group admin profile — returns 200."""
        create_resp = await test_client.post(
            "/groups",
            json={"name": "Admin Test Group", "description": "For admin test"},
            headers=auth_headers,
        )
        group_id = create_resp.json()["id"]
        await test_client.post(f"/groups/{group_id}/join", headers=auth_headers)

        resp = await test_client.get(
            f"/users/groups/{group_id}/admin", headers=auth_headers
        )
        assert resp.status_code == 200
        assert "username" in resp.json()

    async def test_get_group_admin_without_auth_returns_401(
        self, test_client: AsyncClient
    ):
        """Get group admin without auth — returns 401."""
        resp = await test_client.get("/users/groups/1/admin")
        assert resp.status_code == 401


class TestGetTaskOwner:
    async def test_get_task_owner_returns_200(
        self, test_client: AsyncClient, auth_headers: dict
    ):
        """Get task owner profile — returns 200."""
        unique_id = str(uuid4())[:8]
        group_resp = await test_client.post(
            "/groups",
            json={"name": f"Owner Group_{unique_id}", "description": "Test"},
            headers=auth_headers,
        )
        group_id = group_resp.json()["id"]

        task_resp = await test_client.post(
            f"/tasks/groups/{group_id}",
            json={
                "title": f"Owner Task_{unique_id}",
                "priority": "medium",
                "group_id": group_id,
            },
            headers=auth_headers,
        )
        task_id = task_resp.json()["id"]

        resp = await test_client.get(
            f"/users/tasks/{task_id}/owner", headers=auth_headers
        )
        assert resp.status_code == 200
        assert "username" in resp.json()

    async def test_get_task_owner_without_auth_returns_401(
        self, test_client: AsyncClient
    ):
        """Get task owner without auth — returns 401."""
        resp = await test_client.get("/users/tasks/1/owner")
        assert resp.status_code == 401
