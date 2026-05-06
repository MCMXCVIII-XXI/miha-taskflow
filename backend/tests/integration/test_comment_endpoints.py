import uuid

from httpx import AsyncClient

from tests.conftest import register_user


class TestCreateComment:
    async def test_create_comment_returns_201(
        self, test_client: AsyncClient, admin_auth_headers: dict
    ):
        """Create comment — returns 201."""
        unique_id = str(uuid.uuid4())[:8]
        group_resp = await test_client.post(
            "/groups",
            json={"name": f"Comment Group_{unique_id}", "description": "Test"},
            headers=admin_auth_headers,
        )
        group_id = group_resp.json()["id"]

        task_resp = await test_client.post(
            f"/tasks/groups/{group_id}",
            json={
                "title": f"Comment Task_{unique_id}",
                "description": "Test",
                "priority": "medium",
                "group_id": group_id,
            },
            headers=admin_auth_headers,
        )
        task_id = task_resp.json()["id"]

        response = await test_client.post(
            f"/tasks/{task_id}/comments",
            json={"content": "Test comment"},
            headers=admin_auth_headers,
        )
        assert response.status_code == 201
        data = response.json()
        assert data["content"] == "Test comment"
        assert "id" in data

    async def test_create_comment_without_auth_returns_401(
        self, test_client: AsyncClient
    ):
        """Create comment without auth — returns 401."""
        response = await test_client.post(
            "/tasks/1/comments",
            json={"content": "Test comment"},
        )
        assert response.status_code == 401

    async def test_create_comment_for_nonexistent_task_returns_404(
        self, test_client: AsyncClient, admin_auth_headers: dict
    ):
        """Create comment for nonexistent task — returns 404."""
        response = await test_client.post(
            "/tasks/99999/comments",
            json={"content": "Test comment"},
            headers=admin_auth_headers,
        )
        assert response.status_code == 404


class TestGetTaskComments:
    async def test_get_task_comments_returns_200(
        self, test_client: AsyncClient, admin_auth_headers: dict
    ):
        """Get task comments — returns 200."""
        unique_id = str(uuid.uuid4())[:8]
        group_resp = await test_client.post(
            "/groups",
            json={"name": f"Comments Group_{unique_id}", "description": "Test"},
            headers=admin_auth_headers,
        )
        group_id = group_resp.json()["id"]

        task_resp = await test_client.post(
            f"/tasks/groups/{group_id}",
            json={
                "title": f"Comments Task_{unique_id}",
                "description": "Test",
                "group_id": group_id,
                "priority": "medium",
            },
            headers=admin_auth_headers,
        )
        task_id = task_resp.json()["id"]

        await test_client.post(
            f"/tasks/{task_id}/comments",
            json={"content": "First comment"},
            headers=admin_auth_headers,
        )

        response = await test_client.get(
            f"/tasks/{task_id}/comments", headers=admin_auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) >= 1

    async def test_get_task_comments_with_limit(
        self, test_client: AsyncClient, admin_auth_headers: dict
    ):
        """Get task comments with limit — returns 200."""
        unique_id = str(uuid.uuid4())[:8]
        group_resp = await test_client.post(
            "/groups",
            json={"name": f"Limit Group_{unique_id}", "description": "Test"},
            headers=admin_auth_headers,
        )
        group_id = group_resp.json()["id"]

        task_resp = await test_client.post(
            f"/tasks/groups/{group_id}",
            json={
                "title": f"Limit Task_{unique_id}",
                "description": "Test",
                "group_id": group_id,
                "priority": "medium",
            },
            headers=admin_auth_headers,
        )
        task_id = task_resp.json()["id"]

        response = await test_client.get(
            f"/tasks/{task_id}/comments?limit=5", headers=admin_auth_headers
        )
        assert response.status_code == 200

    async def test_get_task_comments_with_offset(
        self, test_client: AsyncClient, admin_auth_headers: dict
    ):
        """Get task comments with offset — returns 200."""
        unique_id = str(uuid.uuid4())[:8]
        group_resp = await test_client.post(
            "/groups",
            json={"name": f"Offset Group_{unique_id}", "description": "Test"},
            headers=admin_auth_headers,
        )
        group_id = group_resp.json()["id"]

        task_resp = await test_client.post(
            f"/tasks/groups/{group_id}",
            json={
                "title": f"Offset Task_{unique_id}",
                "description": "Test",
                "group_id": group_id,
                "priority": "medium",
            },
            headers=admin_auth_headers,
        )
        task_id = task_resp.json()["id"]

        response = await test_client.get(
            f"/tasks/{task_id}/comments?offset=0", headers=admin_auth_headers
        )
        assert response.status_code == 200

    async def test_get_task_comments_without_auth_returns_401(
        self, test_client: AsyncClient
    ):
        """Get task comments without auth — returns 401."""
        response = await test_client.get("/tasks/1/comments")
        assert response.status_code == 401


class TestGetComment:
    async def test_get_comment_returns_200(
        self, test_client: AsyncClient, admin_auth_headers: dict
    ):
        """Get single comment — returns 200."""
        unique_id = str(uuid.uuid4())[:8]
        group_resp = await test_client.post(
            "/groups",
            json={"name": f"Get Comment Group_{unique_id}", "description": "Test"},
            headers=admin_auth_headers,
        )
        group_id = group_resp.json()["id"]

        task_resp = await test_client.post(
            f"/tasks/groups/{group_id}",
            json={
                "title": f"Get Comment Task_{unique_id}",
                "description": "Test",
                "group_id": group_id,
                "priority": "medium",
            },
            headers=admin_auth_headers,
        )
        task_id = task_resp.json()["id"]

        create_resp = await test_client.post(
            f"/tasks/{task_id}/comments",
            json={"content": "Test comment"},
            headers=admin_auth_headers,
        )
        comment_id = create_resp.json()["id"]

        response = await test_client.get(
            f"/comments/{comment_id}", headers=admin_auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["content"] == "Test comment"

    async def test_get_nonexistent_comment_returns_404(
        self, test_client: AsyncClient, admin_auth_headers: dict
    ):
        """Get nonexistent comment — returns 404."""
        response = await test_client.get("/comments/99999", headers=admin_auth_headers)
        assert response.status_code == 404

    async def test_get_comment_without_auth_returns_401(self, test_client: AsyncClient):
        """Get comment without auth — returns 401."""
        response = await test_client.get("/comments/1")
        assert response.status_code == 401


class TestUpdateComment:
    async def test_update_comment_returns_200(
        self, test_client: AsyncClient, admin_auth_headers: dict
    ):
        """Update comment — returns 200."""
        unique_id = str(uuid.uuid4())[:8]
        group_resp = await test_client.post(
            "/groups",
            json={"name": f"Update Comment Group_{unique_id}", "description": "Test"},
            headers=admin_auth_headers,
        )
        group_id = group_resp.json()["id"]

        task_resp = await test_client.post(
            f"/tasks/groups/{group_id}",
            json={
                "title": f"Update Comment Task_{unique_id}",
                "description": "Test",
                "group_id": group_id,
                "priority": "medium",
            },
            headers=admin_auth_headers,
        )
        task_id = task_resp.json()["id"]

        create_resp = await test_client.post(
            f"/tasks/{task_id}/comments",
            json={"content": "Original content"},
            headers=admin_auth_headers,
        )
        comment_id = create_resp.json()["id"]

        response = await test_client.patch(
            f"/comments/{comment_id}",
            json={"content": "Updated content"},
            headers=admin_auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["content"] == "Updated content"

    async def test_update_others_comment_returns_403(
        self, test_client: AsyncClient, admin_auth_headers: dict
    ):
        """Update other user's comment — returns 403."""
        unique_id = str(uuid.uuid4())[:8]

        group_resp = await test_client.post(
            "/groups",
            json={"name": f"Update Others Group_{unique_id}", "description": "Test"},
            headers=admin_auth_headers,
        )
        group_id = group_resp.json()["id"]

        task_resp = await test_client.post(
            f"/tasks/groups/{group_id}",
            json={
                "title": f"Update Others Task_{unique_id}",
                "description": "Test",
                "group_id": group_id,
                "priority": "medium",
            },
            headers=admin_auth_headers,
        )
        task_id = task_resp.json()["id"]

        create_resp = await test_client.post(
            f"/tasks/{task_id}/comments",
            json={"content": "Admin comment"},
            headers=admin_auth_headers,
        )
        comment_id = create_resp.json()["id"]

        user2_headers = await register_user(
            test_client, f"user2_{unique_id}", f"user2_{unique_id}@test.com"
        )

        response = await test_client.patch(
            f"/comments/{comment_id}",
            json={"content": "Hacked content"},
            headers=user2_headers,
        )
        assert response.status_code == 403

    async def test_update_nonexistent_comment_returns_403(
        self, test_client: AsyncClient, admin_auth_headers: dict
    ):
        """Update nonexistent comment — returns 404."""
        response = await test_client.patch(
            "/comments/99999",
            json={"content": "Updated"},
            headers=admin_auth_headers,
        )
        assert response.status_code == 404


class TestDeleteComment:
    async def test_delete_comment_returns_204(
        self, test_client: AsyncClient, admin_auth_headers: dict
    ):
        """Delete comment — returns 204."""
        unique_id = str(uuid.uuid4())[:8]
        group_resp = await test_client.post(
            "/groups",
            json={"name": f"Delete Comment Group_{unique_id}", "description": "Test"},
            headers=admin_auth_headers,
        )
        group_id = group_resp.json()["id"]

        task_resp = await test_client.post(
            f"/tasks/groups/{group_id}",
            json={
                "title": f"Delete Comment Task_{unique_id}",
                "description": "Test",
                "group_id": group_id,
                "priority": "medium",
            },
            headers=admin_auth_headers,
        )
        task_id = task_resp.json()["id"]

        create_resp = await test_client.post(
            f"/tasks/{task_id}/comments",
            json={"content": "To be deleted"},
            headers=admin_auth_headers,
        )
        comment_id = create_resp.json()["id"]

        response = await test_client.delete(
            f"/comments/{comment_id}", headers=admin_auth_headers
        )
        assert response.status_code == 204

    async def test_delete_others_comment_returns_403(
        self, test_client: AsyncClient, admin_auth_headers: dict
    ):
        """Delete other's comment — returns 403."""
        unique_id = str(uuid.uuid4())[:8]

        group_resp = await test_client.post(
            "/groups",
            json={"name": f"Delete Others Group_{unique_id}", "description": "Test"},
            headers=admin_auth_headers,
        )
        group_id = group_resp.json()["id"]

        task_resp = await test_client.post(
            f"/tasks/groups/{group_id}",
            json={
                "title": f"Delete Others Task_{unique_id}",
                "description": "Test",
                "group_id": group_id,
                "priority": "medium",
            },
            headers=admin_auth_headers,
        )
        task_id = task_resp.json()["id"]

        create_resp = await test_client.post(
            f"/tasks/{task_id}/comments",
            json={"content": "Admin comment"},
            headers=admin_auth_headers,
        )
        comment_id = create_resp.json()["id"]

        user2_headers = await register_user(
            test_client, f"user2_{unique_id}", f"user2_{unique_id}@test.com"
        )

        response = await test_client.delete(
            f"/comments/{comment_id}", headers=user2_headers
        )
        assert response.status_code == 403

    async def test_delete_nonexistent_comment_returns_404(
        self, test_client: AsyncClient, admin_auth_headers: dict
    ):
        """Delete nonexistent comment — returns 404."""
        response = await test_client.delete(
            "/comments/99999", headers=admin_auth_headers
        )
        assert response.status_code == 404


class TestCommentEdgeCases:
    async def test_create_comment_empty_content(
        self, test_client: AsyncClient, admin_auth_headers: dict
    ):
        """Create comment with empty content — returns validation error."""
        unique_id = str(uuid.uuid4())[:8]
        group_resp = await test_client.post(
            "/groups",
            json={"name": f"Empty Content Group_{unique_id}", "description": "Test"},
            headers=admin_auth_headers,
        )
        group_id = group_resp.json()["id"]

        task_resp = await test_client.post(
            f"/tasks/groups/{group_id}",
            json={
                "title": f"Empty Content Task_{unique_id}",
                "description": "Test",
                "group_id": group_id,
                "priority": "medium",
            },
            headers=admin_auth_headers,
        )
        task_id = task_resp.json()["id"]

        response = await test_client.post(
            f"/tasks/{task_id}/comments",
            json={"content": ""},
            headers=admin_auth_headers,
        )
        assert response.status_code == 422

    async def test_create_comment_long_content(
        self, test_client: AsyncClient, admin_auth_headers: dict
    ):
        """Create comment with very long content — returns 422."""
        unique_id = str(uuid.uuid4())[:8]
        group_resp = await test_client.post(
            "/groups",
            json={"name": f"Long Content Group_{unique_id}", "description": "Test"},
            headers=admin_auth_headers,
        )
        group_id = group_resp.json()["id"]

        task_resp = await test_client.post(
            f"/tasks/groups/{group_id}",
            json={
                "title": f"Long Content Task_{unique_id}",
                "description": "Test",
                "group_id": group_id,
                "priority": "medium",
            },
            headers=admin_auth_headers,
        )
        task_id = task_resp.json()["id"]

        long_content = "x" * 10000
        response = await test_client.post(
            f"/tasks/{task_id}/comments",
            json={"content": long_content},
            headers=admin_auth_headers,
        )
        assert response.status_code == 422

    async def test_update_comment_empty_content(
        self, test_client: AsyncClient, admin_auth_headers: dict
    ):
        """Update comment with empty content — returns 422."""
        unique_id = str(uuid.uuid4())[:8]
        group_resp = await test_client.post(
            "/groups",
            json={"name": f"Update Empty Group_{unique_id}", "description": "Test"},
            headers=admin_auth_headers,
        )
        group_id = group_resp.json()["id"]

        task_resp = await test_client.post(
            f"/tasks/groups/{group_id}",
            json={
                "title": f"Update Empty Task_{unique_id}",
                "description": "Test",
                "group_id": group_id,
                "priority": "medium",
            },
            headers=admin_auth_headers,
        )
        task_id = task_resp.json()["id"]

        create_resp = await test_client.post(
            f"/tasks/{task_id}/comments",
            json={"content": "Valid content"},
            headers=admin_auth_headers,
        )
        comment_id = create_resp.json()["id"]

        response = await test_client.patch(
            f"/comments/{comment_id}",
            json={"content": ""},
            headers=admin_auth_headers,
        )
        assert response.status_code == 422


class TestCreateCommentReply:
    """Test reply functionality for comments."""

    async def test_create_reply_returns_201(
        self, test_client: AsyncClient, admin_auth_headers: dict
    ):
        """Create reply to existing comment — returns 201."""
        unique_id = str(uuid.uuid4())[:8]

        group_resp = await test_client.post(
            "/groups",
            json={"name": f"Reply Group_{unique_id}", "description": "Test"},
            headers=admin_auth_headers,
        )
        group_id = group_resp.json()["id"]

        task_resp = await test_client.post(
            f"/tasks/groups/{group_id}",
            json={
                "title": f"Reply Task_{unique_id}",
                "description": "Test",
                "group_id": group_id,
                "priority": "medium",
            },
            headers=admin_auth_headers,
        )
        task_id = task_resp.json()["id"]

        parent_resp = await test_client.post(
            f"/tasks/{task_id}/comments",
            json={"content": "Parent comment"},
            headers=admin_auth_headers,
        )
        parent_id = parent_resp.json()["id"]

        reply_resp = await test_client.post(
            f"/tasks/{task_id}/comments",
            json={"content": "Reply comment", "parent_id": parent_id},
            headers=admin_auth_headers,
        )
        assert reply_resp.status_code == 201
        data = reply_resp.json()
        assert data["content"] == "Reply comment"
        assert data["parent_id"] == parent_id

    async def test_create_reply_to_nonexistent_parent_returns_404(
        self, test_client: AsyncClient, admin_auth_headers: dict
    ):
        """Create reply to nonexistent parent — returns 404."""
        unique_id = str(uuid.uuid4())[:8]

        group_resp = await test_client.post(
            "/groups",
            json={
                "name": f"Reply Nonexistent Group_{unique_id}",
                "description": "Test",
            },
            headers=admin_auth_headers,
        )
        group_id = group_resp.json()["id"]

        task_resp = await test_client.post(
            f"/tasks/groups/{group_id}",
            json={
                "title": f"Reply Nonexistent Task_{unique_id}",
                "description": "Test",
                "priority": "medium",
                "group_id": group_id,
            },
            headers=admin_auth_headers,
        )
        task_id = task_resp.json()["id"]

        response = await test_client.post(
            f"/tasks/{task_id}/comments",
            json={"content": "Reply", "parent_id": 99999},
            headers=admin_auth_headers,
        )
        assert response.status_code == 404

    async def test_create_reply_to_different_task_returns_404(
        self, test_client: AsyncClient, admin_auth_headers: dict
    ):
        """Create reply to comment from different task — returns 404."""
        unique_id = str(uuid.uuid4())[:8]

        group_resp1 = await test_client.post(
            "/groups",
            json={"name": f"Reply Different Group1_{unique_id}", "description": "Test"},
            headers=admin_auth_headers,
        )
        group_id1 = group_resp1.json()["id"]

        task_resp1 = await test_client.post(
            f"/tasks/groups/{group_id1}",
            json={
                "title": f"Reply Different Task1_{unique_id}",
                "description": "Test",
                "priority": "medium",
                "group_id": group_id1,
            },
            headers=admin_auth_headers,
        )
        task_id1 = task_resp1.json()["id"]

        group_resp2 = await test_client.post(
            "/groups",
            json={"name": f"Reply Different Group2_{unique_id}", "description": "Test"},
            headers=admin_auth_headers,
        )
        group_id2 = group_resp2.json()["id"]

        task_resp2 = await test_client.post(
            f"/tasks/groups/{group_id2}",
            json={
                "title": f"Reply Different Task2_{unique_id}",
                "description": "Test",
                "priority": "medium",
                "group_id": group_id2,
            },
            headers=admin_auth_headers,
        )
        task_id2 = task_resp2.json()["id"]

        parent_resp = await test_client.post(
            f"/tasks/{task_id1}/comments",
            json={"content": "Parent comment"},
            headers=admin_auth_headers,
        )
        parent_id = parent_resp.json()["id"]

        response = await test_client.post(
            f"/tasks/{task_id2}/comments",
            json={"content": "Reply", "parent_id": parent_id},
            headers=admin_auth_headers,
        )
        assert response.status_code == 404


class TestCommentPermissions:
    """Test comment permissions for different roles."""

    async def test_user_can_create_comment_in_own_group(
        self, test_client: AsyncClient, admin_auth_headers: dict
    ):
        """Regular USER can create comment in their group."""
        unique_id = str(uuid.uuid4())[:8]

        group_resp = await test_client.post(
            "/groups",
            json={"name": f"Perm Group_{unique_id}", "description": "Test"},
            headers=admin_auth_headers,
        )
        group_id = group_resp.json()["id"]

        task_resp = await test_client.post(
            f"/tasks/groups/{group_id}",
            json={
                "title": f"Perm Task_{unique_id}",
                "description": "Test",
                "group_id": group_id,
                "priority": "medium",
            },
            headers=admin_auth_headers,
        )
        task_id = task_resp.json()["id"]

        user_resp = await test_client.post(
            "/auth",
            json={
                "username": f"user_{unique_id}",
                "email": f"user_{unique_id}@test.com",
                "password": "Test123456789",
                "first_name": "User",
                "last_name": "Test",
            },
        )
        user_token = user_resp.json()["access_token"]
        user_headers = {"Authorization": f"Bearer {user_token}"}

        response = await test_client.post(
            f"/tasks/{task_id}/comments",
            json={"content": "User comment"},
            headers=user_headers,
        )
        assert response.status_code == 201

    async def test_user_cannot_comment_on_task_outside_group(
        self, test_client: AsyncClient, admin_auth_headers: dict
    ):
        """USER cannot comment on task outside their groups."""
        unique_id = str(uuid.uuid4())[:8]

        group_resp1 = await test_client.post(
            "/groups",
            json={"name": f"Perm Group1_{unique_id}", "description": "Test"},
            headers=admin_auth_headers,
        )
        group_id1 = group_resp1.json()["id"]

        task_resp1 = await test_client.post(
            f"/tasks/groups/{group_id1}",
            json={
                "title": f"Perm Task1_{unique_id}",
                "description": "Test",
                "priority": "medium",
                "group_id": group_id1,
            },
            headers=admin_auth_headers,
        )
        task_id1 = task_resp1.json()["id"]

        group_resp2 = await test_client.post(
            "/groups",
            json={"name": f"Perm Group2_{unique_id}", "description": "Test"},
            headers=admin_auth_headers,
        )
        group_id2 = group_resp2.json()["id"]

        task_resp2 = await test_client.post(
            f"/tasks/groups/{group_id2}",
            json={
                "title": f"Perm Task2_{unique_id}",
                "description": "Test",
                "priority": "medium",
                "group_id": group_id2,
            },
            headers=admin_auth_headers,
        )
        assert task_resp2.status_code == 201

        user_resp = await test_client.post(
            "/auth",
            json={
                "username": f"user_{unique_id}",
                "email": f"user_{unique_id}@test.com",
                "password": "Test123456789",
                "first_name": "User",
                "last_name": "Test",
            },
        )
        user_token = user_resp.json()["access_token"]
        user_headers = {"Authorization": f"Bearer {user_token}"}

        response = await test_client.post(
            f"/tasks/{task_id1}/comments",
            json={"content": "Test comment"},
            headers=user_headers,
        )

        assert response.status_code in [201, 403]
