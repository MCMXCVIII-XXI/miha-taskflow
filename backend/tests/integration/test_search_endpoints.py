from httpx import AsyncClient


class TestSearchTasks:
    async def test_search_tasks_returns_200(
        self, test_client: AsyncClient, admin_auth_headers: dict
    ):
        """Search tasks — returns 200 with empty results (ES mocked)."""
        response = await test_client.get(
            "/search/tasks/search", headers=admin_auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "results" in data or "aggregations" in data

    async def test_search_tasks_with_query(
        self, test_client: AsyncClient, admin_auth_headers: dict
    ):
        """Search tasks with query — returns 200."""
        response = await test_client.get(
            "/search/tasks/search?q=test", headers=admin_auth_headers
        )
        assert response.status_code == 200

    async def test_search_tasks_with_filters(
        self, test_client: AsyncClient, admin_auth_headers: dict
    ):
        """Search tasks with status filter — returns 200."""
        response = await test_client.get(
            "/search/tasks/search?status=pending", headers=admin_auth_headers
        )
        assert response.status_code == 200

    async def test_search_tasks_with_priority_filter(
        self, test_client: AsyncClient, admin_auth_headers: dict
    ):
        """Search tasks with priority filter — returns 200."""
        response = await test_client.get(
            "/search/tasks/search?priority=high", headers=admin_auth_headers
        )
        assert response.status_code == 200

    async def test_search_tasks_with_facets_false(
        self, test_client: AsyncClient, admin_auth_headers: dict
    ):
        """Search tasks without facets — returns 200."""
        response = await test_client.get(
            "/search/tasks/search?facets=false", headers=admin_auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "results" in data
        assert "total" in data

    async def test_search_tasks_with_limit(
        self, test_client: AsyncClient, admin_auth_headers: dict
    ):
        """Search tasks with custom limit — returns 200."""
        response = await test_client.get(
            "/search/tasks/search?limit=5", headers=admin_auth_headers
        )
        assert response.status_code == 200

    async def test_search_tasks_with_offset(
        self, test_client: AsyncClient, admin_auth_headers: dict
    ):
        """Search tasks with offset — returns 200."""
        response = await test_client.get(
            "/search/tasks/search?offset=10", headers=admin_auth_headers
        )
        assert response.status_code == 200

    async def test_search_tasks_without_auth_returns_401(
        self, test_client: AsyncClient
    ):
        """Search tasks without auth — returns 401."""
        response = await test_client.get("/search/tasks/search")
        assert response.status_code == 401


class TestSearchUsers:
    async def test_search_users_returns_200(
        self, test_client: AsyncClient, admin_auth_headers: dict
    ):
        """Search users — returns 200 with empty results (ES mocked)."""
        response = await test_client.get(
            "/search/users/search", headers=admin_auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "results" in data or "aggregations" in data

    async def test_search_users_with_query(
        self, test_client: AsyncClient, admin_auth_headers: dict
    ):
        """Search users with query — returns 200."""
        response = await test_client.get(
            "/search/users/search?q=john", headers=admin_auth_headers
        )
        assert response.status_code == 200

    async def test_search_users_with_role_filter(
        self, test_client: AsyncClient, admin_auth_headers: dict
    ):
        """Search users with role filter — returns 200."""
        response = await test_client.get(
            "/search/users/search?role=user", headers=admin_auth_headers
        )
        assert response.status_code == 200

    async def test_search_users_with_is_active_filter(
        self, test_client: AsyncClient, admin_auth_headers: dict
    ):
        """Search users with is_active filter — returns 200."""
        response = await test_client.get(
            "/search/users/search?is_active=true", headers=admin_auth_headers
        )
        assert response.status_code == 200

    async def test_search_users_with_facets_false(
        self, test_client: AsyncClient, admin_auth_headers: dict
    ):
        """Search users without facets — returns 200."""
        response = await test_client.get(
            "/search/users/search?facets=false", headers=admin_auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "results" in data
        assert "total" in data

    async def test_search_users_without_auth_returns_401(
        self, test_client: AsyncClient
    ):
        """Search users without auth — returns 401."""
        response = await test_client.get("/search/users/search")
        assert response.status_code == 401


class TestSearchGroups:
    async def test_search_groups_returns_200(
        self, test_client: AsyncClient, admin_auth_headers: dict
    ):
        """Search groups — returns 200 with empty results (ES mocked)."""
        response = await test_client.get(
            "/search/groups/search", headers=admin_auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "results" in data or "aggregations" in data

    async def test_search_groups_with_query(
        self, test_client: AsyncClient, admin_auth_headers: dict
    ):
        """Search groups with query — returns 200."""
        response = await test_client.get(
            "/search/groups/search?q=developers", headers=admin_auth_headers
        )
        assert response.status_code == 200

    async def test_search_groups_with_visibility_filter(
        self, test_client: AsyncClient, admin_auth_headers: dict
    ):
        """Search groups with visibility filter — returns 200."""
        response = await test_client.get(
            "/search/groups/search?visibility=public", headers=admin_auth_headers
        )
        assert response.status_code == 200

    async def test_search_groups_with_join_policy_filter(
        self, test_client: AsyncClient, admin_auth_headers: dict
    ):
        """Search groups with join_policy filter — returns 200."""
        response = await test_client.get(
            "/search/groups/search?join_policy=open", headers=admin_auth_headers
        )
        assert response.status_code == 200

    async def test_search_groups_with_facets_false(
        self, test_client: AsyncClient, admin_auth_headers: dict
    ):
        """Search groups without facets — returns 200."""
        response = await test_client.get(
            "/search/groups/search?facets=false", headers=admin_auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "results" in data
        assert "total" in data

    async def test_search_groups_without_auth_returns_401(
        self, test_client: AsyncClient
    ):
        """Search groups without auth — returns 401."""
        response = await test_client.get("/search/groups/search")
        assert response.status_code == 401


class TestSearchComments:
    async def test_search_comments_returns_200(
        self, test_client: AsyncClient, admin_auth_headers: dict
    ):
        """Search comments — returns 200 with empty results (ES mocked)."""
        response = await test_client.get(
            "/search/comments/search", headers=admin_auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "results" in data or "aggregations" in data

    async def test_search_comments_with_query(
        self, test_client: AsyncClient, admin_auth_headers: dict
    ):
        """Search comments with query — returns 200."""
        response = await test_client.get(
            "/search/comments/search?q=bug", headers=admin_auth_headers
        )
        assert response.status_code == 200

    async def test_search_comments_with_task_id_filter(
        self, test_client: AsyncClient, admin_auth_headers: dict
    ):
        """Search comments with task_id filter — returns 200."""
        response = await test_client.get(
            "/search/comments/search?task_id=1", headers=admin_auth_headers
        )
        assert response.status_code == 200

    async def test_search_comments_with_user_id_filter(
        self, test_client: AsyncClient, admin_auth_headers: dict
    ):
        """Search comments with user_id filter — returns 200."""
        response = await test_client.get(
            "/search/comments/search?user_id=1", headers=admin_auth_headers
        )
        assert response.status_code == 200

    async def test_search_comments_with_facets_false(
        self, test_client: AsyncClient, admin_auth_headers: dict
    ):
        """Search comments without facets — returns 200."""
        response = await test_client.get(
            "/search/comments/search?facets=false", headers=admin_auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "results" in data
        assert "total" in data

    async def test_search_comments_without_auth_returns_401(
        self, test_client: AsyncClient
    ):
        """Search comments without auth — returns 401."""
        response = await test_client.get("/search/comments/search")
        assert response.status_code == 401


class TestSearchNotifications:
    async def test_search_notifications_returns_200(
        self, test_client: AsyncClient, admin_auth_headers: dict
    ):
        """Search notifications — returns 200 with empty results (ES mocked)."""
        response = await test_client.get(
            "/search/notifications/search", headers=admin_auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "results" in data or "aggregations" in data

    async def test_search_notifications_with_query(
        self, test_client: AsyncClient, admin_auth_headers: dict
    ):
        """Search notifications with query — returns 200."""
        response = await test_client.get(
            "/search/notifications/search?q=invite", headers=admin_auth_headers
        )
        assert response.status_code == 200

    async def test_search_notifications_with_user_id_filter(
        self, test_client: AsyncClient, admin_auth_headers: dict
    ):
        """Search notifications with user_id filter — returns 200."""
        response = await test_client.get(
            "/search/notifications/search?user_id=1", headers=admin_auth_headers
        )
        assert response.status_code == 200

    async def test_search_notifications_with_facets_false(
        self, test_client: AsyncClient, admin_auth_headers: dict
    ):
        """Search notifications without facets — returns 200."""
        response = await test_client.get(
            "/search/notifications/search?facets=false", headers=admin_auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "results" in data
        assert "total" in data

    async def test_search_notifications_without_auth_returns_401(
        self, test_client: AsyncClient
    ):
        """Search notifications without auth — returns 401."""
        response = await test_client.get("/search/notifications/search")
        assert response.status_code == 401


class TestSearchEdgeCases:
    async def test_search_tasks_invalid_limit(
        self, test_client: AsyncClient, admin_auth_headers: dict
    ):
        """Search tasks with invalid limit — returns 422."""
        response = await test_client.get(
            "/search/tasks/search?limit=0", headers=admin_auth_headers
        )
        assert response.status_code == 422

    async def test_search_groups_invalid_limit(
        self, test_client: AsyncClient, admin_auth_headers: dict
    ):
        """Search groups with invalid limit — returns 422."""
        response = await test_client.get(
            "/search/groups/search?limit=101", headers=admin_auth_headers
        )
        assert response.status_code == 422
