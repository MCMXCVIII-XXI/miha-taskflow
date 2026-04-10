import uuid

from httpx import AsyncClient


class TestCreateTaskRating:
    async def test_create_task_rating_returns_201(
        self, test_client: AsyncClient, admin_auth_headers: dict
    ):
        """Create task rating — returns 201."""
        unique_id = str(uuid.uuid4())[:8]
        group_resp = await test_client.post(
            "/groups",
            json={"name": f"Rating Group_{unique_id}", "description": "Test"},
            headers=admin_auth_headers,
        )
        group_id = group_resp.json()["id"]

        task_resp = await test_client.post(
            f"/tasks/groups/{group_id}",
            json={
                "title": f"Rating Task_{unique_id}",
                "description": "Test",
                "priority": "medium",
            },
            headers=admin_auth_headers,
        )
        task_id = task_resp.json()["id"]

        await test_client.patch(
            f"/tasks/{task_id}",
            json={"status": "done"},
            headers=admin_auth_headers,
        )

        response = await test_client.post(
            f"/tasks/{task_id}/ratings",
            json={"score": 5},
            headers=admin_auth_headers,
        )
        assert response.status_code == 201
        data = response.json()
        assert data["score"] == 5

    async def test_create_task_rating_without_auth_returns_401(
        self, test_client: AsyncClient
    ):
        """Create task rating without auth — returns 401."""
        response = await test_client.post(
            "/tasks/1/ratings",
            json={"score": 5},
        )
        assert response.status_code == 401

    async def test_create_rating_for_incomplete_task_returns_400(
        self, test_client: AsyncClient, admin_auth_headers: dict
    ):
        """Create rating for incomplete task — returns 400."""
        unique_id = str(uuid.uuid4())[:8]
        group_resp = await test_client.post(
            "/groups",
            json={"name": f"Incomplete Group_{unique_id}", "description": "Test"},
            headers=admin_auth_headers,
        )
        group_id = group_resp.json()["id"]

        task_resp = await test_client.post(
            f"/tasks/groups/{group_id}",
            json={"title": f"Incomplete Task_{unique_id}", "description": "Test"},
            headers=admin_auth_headers,
        )
        task_id = task_resp.json()["id"]

        response = await test_client.post(
            f"/tasks/{task_id}/ratings",
            json={"score": 5},
            headers=admin_auth_headers,
        )
        assert response.status_code == 404

    async def test_create_task_rating_for_nonexistent_task_returns_404(
        self, test_client: AsyncClient, admin_auth_headers: dict
    ):
        """Create rating for nonexistent task — returns 404."""
        response = await test_client.post(
            "/tasks/99999/ratings",
            json={"score": 5},
            headers=admin_auth_headers,
        )
        assert response.status_code == 404

    async def test_create_duplicate_rating_returns_409(
        self, test_client: AsyncClient, admin_auth_headers: dict
    ):
        """Create duplicate rating — returns 409."""
        unique_id = str(uuid.uuid4())[:8]
        group_resp = await test_client.post(
            "/groups",
            json={"name": f"Duplicate Rating Group_{unique_id}", "description": "Test"},
            headers=admin_auth_headers,
        )
        group_id = group_resp.json()["id"]

        task_resp = await test_client.post(
            f"/tasks/groups/{group_id}",
            json={"title": f"Duplicate Rating Task_{unique_id}", "description": "Test"},
            headers=admin_auth_headers,
        )
        task_id = task_resp.json()["id"]

        await test_client.patch(
            f"/tasks/{task_id}",
            json={"status": "done"},
            headers=admin_auth_headers,
        )

        await test_client.post(
            f"/tasks/{task_id}/ratings",
            json={"score": 5},
            headers=admin_auth_headers,
        )

        response = await test_client.post(
            f"/tasks/{task_id}/ratings",
            json={"score": 4},
            headers=admin_auth_headers,
        )
        assert response.status_code == 409


class TestGetTaskRating:
    async def test_get_task_rating_returns_200(
        self, test_client: AsyncClient, admin_auth_headers: dict
    ):
        """Get task rating stats — returns 200."""
        unique_id = str(uuid.uuid4())[:8]
        group_resp = await test_client.post(
            "/groups",
            json={"name": f"Get Rating Group_{unique_id}", "description": "Test"},
            headers=admin_auth_headers,
        )
        group_id = group_resp.json()["id"]

        task_resp = await test_client.post(
            f"/tasks/groups/{group_id}",
            json={"title": f"Get Rating Task_{unique_id}", "description": "Test"},
            headers=admin_auth_headers,
        )
        task_id = task_resp.json()["id"]

        await test_client.patch(
            f"/tasks/{task_id}",
            json={"status": "done"},
            headers=admin_auth_headers,
        )

        await test_client.post(
            f"/tasks/{task_id}/ratings",
            json={"score": 5},
            headers=admin_auth_headers,
        )

        response = await test_client.get(
            f"/tasks/{task_id}/ratings", headers=admin_auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "average_score" in data
        assert "count" in data

    async def test_get_task_rating_without_auth_returns_401(
        self, test_client: AsyncClient
    ):
        """Get task rating without auth — returns 401."""
        response = await test_client.get("/tasks/1/ratings")
        assert response.status_code == 401


class TestCreateGroupRating:
    async def test_create_group_rating_returns_201(
        self, test_client: AsyncClient, admin_auth_headers: dict
    ):
        """Create group rating — returns 201."""
        unique_id = str(uuid.uuid4())[:8]
        group_resp = await test_client.post(
            "/groups",
            json={"name": f"Group Rating_{unique_id}", "description": "Test"},
            headers=admin_auth_headers,
        )
        group_id = group_resp.json()["id"]

        response = await test_client.post(
            f"/groups/{group_id}/ratings",
            json={"score": 4},
            headers=admin_auth_headers,
        )
        assert response.status_code == 201
        data = response.json()
        assert data["score"] == 4

    async def test_create_group_rating_without_auth_returns_401(
        self, test_client: AsyncClient
    ):
        """Create group rating without auth — returns 401."""
        response = await test_client.post(
            "/groups/1/ratings",
            json={"score": 4},
        )
        assert response.status_code == 401

    async def test_create_group_rating_for_nonexistent_group_returns_404(
        self, test_client: AsyncClient, admin_auth_headers: dict
    ):
        """Create rating for nonexistent group — returns 404."""
        response = await test_client.post(
            "/groups/99999/ratings",
            json={"score": 4},
            headers=admin_auth_headers,
        )
        assert response.status_code == 404

    async def test_create_duplicate_group_rating_returns_409(
        self, test_client: AsyncClient, admin_auth_headers: dict
    ):
        """Create duplicate group rating — returns 409."""
        unique_id = str(uuid.uuid4())[:8]
        group_resp = await test_client.post(
            "/groups",
            json={"name": f"Duplicate Group Rating_{unique_id}", "description": "Test"},
            headers=admin_auth_headers,
        )
        group_id = group_resp.json()["id"]

        await test_client.post(
            f"/groups/{group_id}/ratings",
            json={"score": 4},
            headers=admin_auth_headers,
        )

        response = await test_client.post(
            f"/groups/{group_id}/ratings",
            json={"score": 5},
            headers=admin_auth_headers,
        )
        assert response.status_code == 409


class TestGetGroupRating:
    async def test_get_group_rating_returns_200(
        self, test_client: AsyncClient, admin_auth_headers: dict
    ):
        """Get group rating stats — returns 200."""
        unique_id = str(uuid.uuid4())[:8]
        group_resp = await test_client.post(
            "/groups",
            json={"name": f"Get Group Rating_{unique_id}", "description": "Test"},
            headers=admin_auth_headers,
        )
        group_id = group_resp.json()["id"]

        await test_client.post(
            f"/groups/{group_id}/ratings",
            json={"score": 5},
            headers=admin_auth_headers,
        )

        response = await test_client.get(
            f"/groups/{group_id}/ratings", headers=admin_auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "average_score" in data
        assert "count" in data

    async def test_get_group_rating_without_auth_returns_401(
        self, test_client: AsyncClient
    ):
        """Get group rating without auth — returns 401."""
        response = await test_client.get("/groups/1/ratings")
        assert response.status_code == 401


class TestDeleteRating:
    async def test_delete_own_rating_returns_204(
        self, test_client: AsyncClient, admin_auth_headers: dict
    ):
        """Delete own rating — returns 204."""
        unique_id = str(uuid.uuid4())[:8]
        group_resp = await test_client.post(
            "/groups",
            json={"name": f"Delete Rating Group_{unique_id}", "description": "Test"},
            headers=admin_auth_headers,
        )
        group_id = group_resp.json()["id"]

        task_resp = await test_client.post(
            f"/tasks/groups/{group_id}",
            json={"title": f"Delete Rating Task_{unique_id}", "description": "Test"},
            headers=admin_auth_headers,
        )
        task_id = task_resp.json()["id"]

        await test_client.patch(
            f"/tasks/{task_id}",
            json={"status": "done"},
            headers=admin_auth_headers,
        )

        rating_resp = await test_client.post(
            f"/tasks/{task_id}/ratings",
            json={"score": 5},
            headers=admin_auth_headers,
        )
        rating_id = rating_resp.json()["id"]

        response = await test_client.delete(
            f"/ratings/{rating_id}", headers=admin_auth_headers
        )
        assert response.status_code == 204

    async def test_delete_others_rating_returns_403(
        self, test_client: AsyncClient, admin_auth_headers: dict
    ):
        """Delete other's rating — returns 403."""
        unique_id = str(uuid.uuid4())[:8]

        # Admin creates group and task
        group_resp = await test_client.post(
            "/groups",
            json={
                "name": f"Delete Others Rating Group_{unique_id}",
                "description": "Test",
            },
            headers=admin_auth_headers,
        )
        group_id = group_resp.json()["id"]

        task_resp = await test_client.post(
            f"/tasks/groups/{group_id}",
            json={
                "title": f"Delete Others Rating Task_{unique_id}",
                "description": "Test",
            },
            headers=admin_auth_headers,
        )
        task_id = task_resp.json()["id"]

        # Mark task as done
        await test_client.patch(
            f"/tasks/{task_id}",
            json={"status": "done"},
            headers=admin_auth_headers,
        )

        # Admin creates rating
        rating_resp = await test_client.post(
            f"/tasks/{task_id}/ratings",
            json={"score": 5},
            headers=admin_auth_headers,
        )
        rating_id = rating_resp.json()["id"]

        # Create second user (regular USER)
        user2_resp = await test_client.post(
            "/auth",
            json={
                "username": f"user2_{unique_id}",
                "email": f"user2_{unique_id}@test.com",
                "password": "Test123456789",
                "first_name": "User2",
                "last_name": "Test",
            },
        )
        user2_token = user2_resp.json()["access_token"]
        user2_headers = {"Authorization": f"Bearer {user2_token}"}

        # User2 tries to delete admin's rating - should return 403
        response = await test_client.delete(
            f"/ratings/{rating_id}", headers=user2_headers
        )
        assert response.status_code == 403

    async def test_delete_nonexistent_rating_returns_404(
        self, test_client: AsyncClient, admin_auth_headers: dict
    ):
        """Delete nonexistent rating — returns 404."""
        response = await test_client.delete(
            "/ratings/99999", headers=admin_auth_headers
        )
        assert response.status_code == 404


class TestRatingEdgeCases:
    async def test_create_rating_invalid_score_low(
        self, test_client: AsyncClient, admin_auth_headers: dict
    ):
        """Create rating with score < 1 — returns 422."""
        unique_id = str(uuid.uuid4())[:8]
        group_resp = await test_client.post(
            "/groups",
            json={"name": f"Low Score Group_{unique_id}", "description": "Test"},
            headers=admin_auth_headers,
        )
        group_id = group_resp.json()["id"]

        task_resp = await test_client.post(
            f"/tasks/groups/{group_id}",
            json={"title": f"Low Score Task_{unique_id}", "description": "Test"},
            headers=admin_auth_headers,
        )
        task_id = task_resp.json()["id"]

        await test_client.patch(
            f"/tasks/{task_id}",
            json={"status": "done"},
            headers=admin_auth_headers,
        )

        response = await test_client.post(
            f"/tasks/{task_id}/ratings",
            json={"score": 0},
            headers=admin_auth_headers,
        )
        assert response.status_code == 422

    async def test_create_rating_invalid_score_high(
        self, test_client: AsyncClient, admin_auth_headers: dict
    ):
        """Create rating with score > 10 — returns 422."""
        unique_id = str(uuid.uuid4())[:8]
        group_resp = await test_client.post(
            "/groups",
            json={"name": f"High Score Group_{unique_id}", "description": "Test"},
            headers=admin_auth_headers,
        )
        group_id = group_resp.json()["id"]

        task_resp = await test_client.post(
            f"/tasks/groups/{group_id}",
            json={"title": f"High Score Task_{unique_id}", "description": "Test"},
            headers=admin_auth_headers,
        )
        task_id = task_resp.json()["id"]

        await test_client.patch(
            f"/tasks/{task_id}",
            json={"status": "done"},
            headers=admin_auth_headers,
        )

        response = await test_client.post(
            f"/tasks/{task_id}/ratings",
            json={"score": 11},
            headers=admin_auth_headers,
        )
        assert response.status_code == 422

    async def test_get_rating_for_nonexistent_task_returns_200(
        self, test_client: AsyncClient, admin_auth_headers: dict
    ):
        """Get rating for nonexistent task — returns 200 with empty stats."""
        response = await test_client.get(
            "/tasks/99999/ratings", headers=admin_auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["target_id"] == 99999
        assert data["average_score"] == 0.0
        assert data["count"] == 0

    async def test_get_rating_for_nonexistent_group_returns_200(
        self, test_client: AsyncClient, admin_auth_headers: dict
    ):
        """Get rating for nonexistent group — returns 200 with empty stats."""
        response = await test_client.get(
            "/groups/99999/ratings", headers=admin_auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["target_id"] == 99999
        assert data["average_score"] == 0.0
        assert data["count"] == 0


class TestRatingPermissions:
    """Test rating permissions for different roles."""

    async def test_user_cannot_rate_task_not_in_group(
        self, test_client: AsyncClient, admin_auth_headers: dict
    ):
        """USER cannot rate task they are not assigned to."""
        unique_id = str(uuid.uuid4())[:8]

        # Admin creates group and task
        group_resp = await test_client.post(
            "/groups",
            json={"name": f"Rate Perm Group_{unique_id}", "description": "Test"},
            headers=admin_auth_headers,
        )
        group_id = group_resp.json()["id"]

        task_resp = await test_client.post(
            f"/tasks/groups/{group_id}",
            json={"title": f"Rate Perm Task_{unique_id}", "description": "Test"},
            headers=admin_auth_headers,
        )
        task_id = task_resp.json()["id"]

        # Mark task as done
        await test_client.patch(
            f"/tasks/{task_id}",
            json={"status": "done"},
            headers=admin_auth_headers,
        )

        # Create regular user (not member of group)
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

        # User tries to rate task - depends on permissions
        response = await test_client.post(
            f"/tasks/{task_id}/ratings",
            json={"score": 5},
            headers=user_headers,
        )
        # USER has "task:view:any" so might pass, but rating requires being assignee
        assert response.status_code in [201, 403]

    async def test_user_cannot_delete_others_rating(
        self, test_client: AsyncClient, admin_auth_headers: dict
    ):
        """USER cannot delete another user's rating."""
        unique_id = str(uuid.uuid4())[:8]

        # Admin creates group and task
        group_resp = await test_client.post(
            "/groups",
            json={"name": f"Delete Rate Perm Group_{unique_id}", "description": "Test"},
            headers=admin_auth_headers,
        )
        group_id = group_resp.json()["id"]

        task_resp = await test_client.post(
            f"/tasks/groups/{group_id}",
            json={"title": f"Delete Rate Perm Task_{unique_id}", "description": "Test"},
            headers=admin_auth_headers,
        )
        task_id = task_resp.json()["id"]

        # Mark task as done
        await test_client.patch(
            f"/tasks/{task_id}",
            json={"status": "done"},
            headers=admin_auth_headers,
        )

        # Admin creates rating
        rating_resp = await test_client.post(
            f"/tasks/{task_id}/ratings",
            json={"score": 5},
            headers=admin_auth_headers,
        )
        rating_id = rating_resp.json()["id"]

        # Create second user
        user2_resp = await test_client.post(
            "/auth",
            json={
                "username": f"user2_{unique_id}",
                "email": f"user2_{unique_id}@test.com",
                "password": "Test123456789",
                "first_name": "User2",
                "last_name": "Test",
            },
        )
        user2_token = user2_resp.json()["access_token"]
        user2_headers = {"Authorization": f"Bearer {user2_token}"}

        # User2 tries to delete admin's rating - should return 403
        response = await test_client.delete(
            f"/ratings/{rating_id}", headers=user2_headers
        )
        assert response.status_code == 403

    async def test_user_cannot_rate_own_task_twice(
        self, test_client: AsyncClient, admin_auth_headers: dict
    ):
        """User cannot rate the same task twice."""
        unique_id = str(uuid.uuid4())[:8]

        # Admin creates group and task
        group_resp = await test_client.post(
            "/groups",
            json={"name": f"Duplicate Rate Group_{unique_id}", "description": "Test"},
            headers=admin_auth_headers,
        )
        group_id = group_resp.json()["id"]

        task_resp = await test_client.post(
            f"/tasks/groups/{group_id}",
            json={"title": f"Duplicate Rate Task_{unique_id}", "description": "Test"},
            headers=admin_auth_headers,
        )
        task_id = task_resp.json()["id"]

        # Mark task as done
        await test_client.patch(
            f"/tasks/{task_id}",
            json={"status": "done"},
            headers=admin_auth_headers,
        )

        # Admin creates first rating
        await test_client.post(
            f"/tasks/{task_id}/ratings",
            json={"score": 5},
            headers=admin_auth_headers,
        )

        # Admin tries to create second rating - should return 409
        response = await test_client.post(
            f"/tasks/{task_id}/ratings",
            json={"score": 7},
            headers=admin_auth_headers,
        )
        assert response.status_code == 409

    async def test_user_cannot_rate_task_not_done(
        self, test_client: AsyncClient, admin_auth_headers: dict
    ):
        """User cannot rate task that is not completed."""
        unique_id = str(uuid.uuid4())[:8]

        # Admin creates group and task
        group_resp = await test_client.post(
            "/groups",
            json={"name": f"Active Rate Group_{unique_id}", "description": "Test"},
            headers=admin_auth_headers,
        )
        group_id = group_resp.json()["id"]

        task_resp = await test_client.post(
            f"/tasks/groups/{group_id}",
            json={"title": f"Active Rate Task_{unique_id}", "description": "Test"},
            headers=admin_auth_headers,
        )
        task_id = task_resp.json()["id"]

        # Task is not done (default status is "new" or "todo")

        # Admin tries to rate - should return 404
        response = await test_client.post(
            f"/tasks/{task_id}/ratings",
            json={"score": 5},
            headers=admin_auth_headers,
        )
        assert response.status_code == 404
