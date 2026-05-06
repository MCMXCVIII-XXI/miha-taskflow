import uuid

from httpx import AsyncClient


class TestSearchTasks:
    """Comprehensive tests for /search/tasks/search endpoint."""

    async def test_search_tasks_no_params(
        self, test_client: AsyncClient, admin_auth_headers: dict
    ):
        """Default search - no parameters."""
        response = await test_client.get(
            "/search/tasks/search", headers=admin_auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "results" in data
        assert "aggregations" in data
        assert "total" in data

    async def test_search_tasks_with_q(
        self, test_client: AsyncClient, admin_auth_headers: dict
    ):
        """Search with query string."""
        response = await test_client.get(
            "/search/tasks/search?q=bug", headers=admin_auth_headers
        )
        assert response.status_code == 200

    async def test_search_tasks_with_status(
        self, test_client: AsyncClient, admin_auth_headers: dict
    ):
        """Filter by status."""
        response = await test_client.get(
            "/search/tasks/search?status=pending", headers=admin_auth_headers
        )
        assert response.status_code == 200

    async def test_search_tasks_with_priority(
        self, test_client: AsyncClient, admin_auth_headers: dict
    ):
        """Filter by priority."""
        response = await test_client.get(
            "/search/tasks/search?priority=high", headers=admin_auth_headers
        )
        assert response.status_code == 200

    async def test_search_tasks_with_group_id(
        self, test_client: AsyncClient, admin_auth_headers: dict
    ):
        """Filter by group_id."""
        response = await test_client.get(
            "/search/tasks/search?group_id=1", headers=admin_auth_headers
        )
        assert response.status_code == 200

    async def test_search_tasks_with_facets_false(
        self, test_client: AsyncClient, admin_auth_headers: dict
    ):
        """Without facets."""
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
        """Custom limit."""
        response = await test_client.get(
            "/search/tasks/search?limit=5", headers=admin_auth_headers
        )
        assert response.status_code == 200

    async def test_search_tasks_with_offset(
        self, test_client: AsyncClient, admin_auth_headers: dict
    ):
        """Custom offset."""
        response = await test_client.get(
            "/search/tasks/search?offset=10", headers=admin_auth_headers
        )
        assert response.status_code == 200

    async def test_search_tasks_max_limit(
        self, test_client: AsyncClient, admin_auth_headers: dict
    ):
        """Max allowed limit."""
        response = await test_client.get(
            "/search/tasks/search?limit=100", headers=admin_auth_headers
        )
        assert response.status_code == 200

    async def test_search_tasks_combined_q_and_status(
        self, test_client: AsyncClient, admin_auth_headers: dict
    ):
        """Query + status filter."""
        response = await test_client.get(
            "/search/tasks/search?q=fix&status=pending", headers=admin_auth_headers
        )
        assert response.status_code == 200

    async def test_search_tasks_combined_q_and_priority(
        self, test_client: AsyncClient, admin_auth_headers: dict
    ):
        """Query + priority filter."""
        response = await test_client.get(
            "/search/tasks/search?q=fix&priority=high", headers=admin_auth_headers
        )
        assert response.status_code == 200

    async def test_search_tasks_combined_status_and_priority(
        self, test_client: AsyncClient, admin_auth_headers: dict
    ):
        """Status + priority filter."""
        response = await test_client.get(
            "/search/tasks/search?status=pending&priority=high",
            headers=admin_auth_headers,
        )
        assert response.status_code == 200

    async def test_search_tasks_combined_all_filters(
        self, test_client: AsyncClient, admin_auth_headers: dict
    ):
        """Query + all filters."""
        response = await test_client.get(
            "/search/tasks/search?q=bug&status=pending&priority=high&group_id=1",
            headers=admin_auth_headers,
        )
        assert response.status_code == 200

    async def test_search_tasks_combined_filters_with_pagination(
        self, test_client: AsyncClient, admin_auth_headers: dict
    ):
        """Filters + pagination."""
        response = await test_client.get(
            "/search/tasks/search?status=pending&limit=5&offset=10",
            headers=admin_auth_headers,
        )
        assert response.status_code == 200

    async def test_search_tasks_combined_q_with_facets(
        self, test_client: AsyncClient, admin_auth_headers: dict
    ):
        """Query + facets toggle."""
        response = await test_client.get(
            "/search/tasks/search?q=bug&facets=false", headers=admin_auth_headers
        )
        assert response.status_code == 200

    async def test_search_tasks_without_auth(self, test_client: AsyncClient):
        """Without auth returns 401."""
        response = await test_client.get("/search/tasks/search")
        assert response.status_code == 401


class TestSearchUsers:
    """Comprehensive tests for /search/users/search endpoint."""

    async def test_search_users_no_params(
        self, test_client: AsyncClient, admin_auth_headers: dict
    ):
        """Default search - no parameters."""
        response = await test_client.get(
            "/search/users/search", headers=admin_auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "results" in data
        assert "total" in data

    async def test_search_users_with_q(
        self, test_client: AsyncClient, admin_auth_headers: dict
    ):
        """Search with query string."""
        response = await test_client.get(
            "/search/users/search?q=john", headers=admin_auth_headers
        )
        assert response.status_code == 200

    async def test_search_users_with_role(
        self, test_client: AsyncClient, admin_auth_headers: dict
    ):
        """Filter by role."""
        response = await test_client.get(
            "/search/users/search?role=user", headers=admin_auth_headers
        )
        assert response.status_code == 200

    async def test_search_users_with_is_active_true(
        self, test_client: AsyncClient, admin_auth_headers: dict
    ):
        """Filter by is_active=true."""
        response = await test_client.get(
            "/search/users/search?is_active=true", headers=admin_auth_headers
        )
        assert response.status_code == 200

    async def test_search_users_with_is_active_false(
        self, test_client: AsyncClient, admin_auth_headers: dict
    ):
        """Filter by is_active=false."""
        response = await test_client.get(
            "/search/users/search?is_active=false", headers=admin_auth_headers
        )
        assert response.status_code == 200

    async def test_search_users_with_facets_false(
        self, test_client: AsyncClient, admin_auth_headers: dict
    ):
        """Without facets."""
        response = await test_client.get(
            "/search/users/search?facets=false", headers=admin_auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "results" in data

    async def test_search_users_with_limit(
        self, test_client: AsyncClient, admin_auth_headers: dict
    ):
        """Custom limit."""
        response = await test_client.get(
            "/search/users/search?limit=5", headers=admin_auth_headers
        )
        assert response.status_code == 200

    async def test_search_users_with_offset(
        self, test_client: AsyncClient, admin_auth_headers: dict
    ):
        """Custom offset."""
        response = await test_client.get(
            "/search/users/search?offset=10", headers=admin_auth_headers
        )
        assert response.status_code == 200

    async def test_search_users_max_limit(
        self, test_client: AsyncClient, admin_auth_headers: dict
    ):
        """Max allowed limit."""
        response = await test_client.get(
            "/search/users/search?limit=100", headers=admin_auth_headers
        )
        assert response.status_code == 200

    async def test_search_users_combined_q_and_role(
        self, test_client: AsyncClient, admin_auth_headers: dict
    ):
        """Query + role filter."""
        response = await test_client.get(
            "/search/users/search?q=john&role=admin", headers=admin_auth_headers
        )
        assert response.status_code == 200

    async def test_search_users_combined_q_and_is_active(
        self, test_client: AsyncClient, admin_auth_headers: dict
    ):
        """Query + is_active filter."""
        response = await test_client.get(
            "/search/users/search?q=john&is_active=true", headers=admin_auth_headers
        )
        assert response.status_code == 200

    async def test_search_users_combined_role_and_is_active(
        self, test_client: AsyncClient, admin_auth_headers: dict
    ):
        """Role + is_active filter."""
        response = await test_client.get(
            "/search/users/search?role=admin&is_active=true", headers=admin_auth_headers
        )
        assert response.status_code == 200

    async def test_search_users_combined_all_filters(
        self, test_client: AsyncClient, admin_auth_headers: dict
    ):
        """Query + all filters."""
        response = await test_client.get(
            "/search/users/search?q=john&role=admin&is_active=true",
            headers=admin_auth_headers,
        )
        assert response.status_code == 200

    async def test_search_users_combined_filters_with_pagination(
        self, test_client: AsyncClient, admin_auth_headers: dict
    ):
        """Filters + pagination."""
        response = await test_client.get(
            "/search/users/search?role=user&limit=5&offset=10",
            headers=admin_auth_headers,
        )
        assert response.status_code == 200

    async def test_search_users_without_auth(self, test_client: AsyncClient):
        """Without auth returns 401."""
        response = await test_client.get("/search/users/search")
        assert response.status_code == 401


class TestSearchGroups:
    """Comprehensive tests for /search/groups/search endpoint."""

    async def test_search_groups_no_params(
        self, test_client: AsyncClient, admin_auth_headers: dict
    ):
        """Default search - no parameters."""
        response = await test_client.get(
            "/search/groups/search", headers=admin_auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "results" in data
        assert "total" in data

    async def test_search_groups_with_q(
        self, test_client: AsyncClient, admin_auth_headers: dict
    ):
        """Search with query string."""
        response = await test_client.get(
            "/search/groups/search?q=developers", headers=admin_auth_headers
        )
        assert response.status_code == 200

    async def test_search_groups_with_visibility(
        self, test_client: AsyncClient, admin_auth_headers: dict
    ):
        """Filter by visibility."""
        response = await test_client.get(
            "/search/groups/search?visibility=public", headers=admin_auth_headers
        )
        assert response.status_code == 200

    async def test_search_groups_with_join_policy(
        self, test_client: AsyncClient, admin_auth_headers: dict
    ):
        """Filter by join_policy."""
        response = await test_client.get(
            "/search/groups/search?join_policy=open", headers=admin_auth_headers
        )
        assert response.status_code == 200

    async def test_search_groups_with_facets_false(
        self, test_client: AsyncClient, admin_auth_headers: dict
    ):
        """Without facets."""
        response = await test_client.get(
            "/search/groups/search?facets=false", headers=admin_auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "results" in data

    async def test_search_groups_with_limit(
        self, test_client: AsyncClient, admin_auth_headers: dict
    ):
        """Custom limit."""
        response = await test_client.get(
            "/search/groups/search?limit=5", headers=admin_auth_headers
        )
        assert response.status_code == 200

    async def test_search_groups_with_offset(
        self, test_client: AsyncClient, admin_auth_headers: dict
    ):
        """Custom offset."""
        response = await test_client.get(
            "/search/groups/search?offset=10", headers=admin_auth_headers
        )
        assert response.status_code == 200

    async def test_search_groups_max_limit(
        self, test_client: AsyncClient, admin_auth_headers: dict
    ):
        """Max allowed limit."""
        response = await test_client.get(
            "/search/groups/search?limit=100", headers=admin_auth_headers
        )
        assert response.status_code == 200

    async def test_search_groups_combined_q_and_visibility(
        self, test_client: AsyncClient, admin_auth_headers: dict
    ):
        """Query + visibility filter."""
        response = await test_client.get(
            "/search/groups/search?q=dev&visibility=public", headers=admin_auth_headers
        )
        assert response.status_code == 200

    async def test_search_groups_combined_q_and_join_policy(
        self, test_client: AsyncClient, admin_auth_headers: dict
    ):
        """Query + join_policy filter."""
        response = await test_client.get(
            "/search/groups/search?q=dev&join_policy=open", headers=admin_auth_headers
        )
        assert response.status_code == 200

    async def test_search_groups_combined_visibility_and_join_policy(
        self, test_client: AsyncClient, admin_auth_headers: dict
    ):
        """Visibility + join_policy filter."""
        response = await test_client.get(
            "/search/groups/search?visibility=public&join_policy=open",
            headers=admin_auth_headers,
        )
        assert response.status_code == 200

    async def test_search_groups_combined_all_filters(
        self, test_client: AsyncClient, admin_auth_headers: dict
    ):
        """Query + all filters."""
        response = await test_client.get(
            "/search/groups/search?q=dev&visibility=public&join_policy=open",
            headers=admin_auth_headers,
        )
        assert response.status_code == 200

    async def test_search_groups_combined_filters_with_pagination(
        self, test_client: AsyncClient, admin_auth_headers: dict
    ):
        """Filters + pagination."""
        response = await test_client.get(
            "/search/groups/search?visibility=public&limit=5&offset=10",
            headers=admin_auth_headers,
        )
        assert response.status_code == 200

    async def test_search_groups_without_auth(self, test_client: AsyncClient):
        """Without auth returns 401."""
        response = await test_client.get("/search/groups/search")
        assert response.status_code == 401


class TestSearchComments:
    """Comprehensive tests for /search/comments/search endpoint."""

    async def test_search_comments_no_params(
        self, test_client: AsyncClient, admin_auth_headers: dict
    ):
        """Default search - no parameters."""
        response = await test_client.get(
            "/search/comments/search", headers=admin_auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "results" in data
        assert "total" in data

    async def test_search_comments_with_q(
        self, test_client: AsyncClient, admin_auth_headers: dict
    ):
        """Search with query string."""
        response = await test_client.get(
            "/search/comments/search?q=bug", headers=admin_auth_headers
        )
        assert response.status_code == 200

    async def test_search_comments_with_task_id(
        self, test_client: AsyncClient, admin_auth_headers: dict
    ):
        """Filter by task_id."""
        response = await test_client.get(
            "/search/comments/search?task_id=1", headers=admin_auth_headers
        )
        assert response.status_code == 200

    async def test_search_comments_with_user_id(
        self, test_client: AsyncClient, admin_auth_headers: dict
    ):
        """Filter by user_id."""
        response = await test_client.get(
            "/search/comments/search?user_id=1", headers=admin_auth_headers
        )
        assert response.status_code == 200

    async def test_search_comments_with_facets_false(
        self, test_client: AsyncClient, admin_auth_headers: dict
    ):
        """Without facets."""
        response = await test_client.get(
            "/search/comments/search?facets=false", headers=admin_auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "results" in data

    async def test_search_comments_with_limit(
        self, test_client: AsyncClient, admin_auth_headers: dict
    ):
        """Custom limit."""
        response = await test_client.get(
            "/search/comments/search?limit=5", headers=admin_auth_headers
        )
        assert response.status_code == 200

    async def test_search_comments_with_offset(
        self, test_client: AsyncClient, admin_auth_headers: dict
    ):
        """Custom offset."""
        response = await test_client.get(
            "/search/comments/search?offset=10", headers=admin_auth_headers
        )
        assert response.status_code == 200

    async def test_search_comments_max_limit(
        self, test_client: AsyncClient, admin_auth_headers: dict
    ):
        """Max allowed limit."""
        response = await test_client.get(
            "/search/comments/search?limit=100", headers=admin_auth_headers
        )
        assert response.status_code == 200

    async def test_search_comments_combined_q_and_task_id(
        self, test_client: AsyncClient, admin_auth_headers: dict
    ):
        """Query + task_id filter."""
        response = await test_client.get(
            "/search/comments/search?q=fix&task_id=1", headers=admin_auth_headers
        )
        assert response.status_code == 200

    async def test_search_comments_combined_q_and_user_id(
        self, test_client: AsyncClient, admin_auth_headers: dict
    ):
        """Query + user_id filter."""
        response = await test_client.get(
            "/search/comments/search?q=fix&user_id=1", headers=admin_auth_headers
        )
        assert response.status_code == 200

    async def test_search_comments_combined_task_id_and_user_id(
        self, test_client: AsyncClient, admin_auth_headers: dict
    ):
        """task_id + user_id filter."""
        response = await test_client.get(
            "/search/comments/search?task_id=1&user_id=1", headers=admin_auth_headers
        )
        assert response.status_code == 200

    async def test_search_comments_combined_all_filters(
        self, test_client: AsyncClient, admin_auth_headers: dict
    ):
        """Query + all filters."""
        response = await test_client.get(
            "/search/comments/search?q=fix&task_id=1&user_id=1",
            headers=admin_auth_headers,
        )
        assert response.status_code == 200

    async def test_search_comments_combined_filters_with_pagination(
        self, test_client: AsyncClient, admin_auth_headers: dict
    ):
        """Filters + pagination."""
        response = await test_client.get(
            "/search/comments/search?task_id=1&limit=5&offset=10",
            headers=admin_auth_headers,
        )
        assert response.status_code == 200

    async def test_search_comments_without_auth(self, test_client: AsyncClient):
        """Without auth returns 401."""
        response = await test_client.get("/search/comments/search")
        assert response.status_code == 401


class TestSearchNotifications:
    """Comprehensive tests for /search/notifications/search endpoint."""

    async def test_search_notifications_no_params(
        self, test_client: AsyncClient, admin_auth_headers: dict
    ):
        """Default search - no parameters."""
        response = await test_client.get(
            "/search/notifications/search", headers=admin_auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "results" in data
        assert "total" in data

    async def test_search_notifications_with_q(
        self, test_client: AsyncClient, admin_auth_headers: dict
    ):
        """Search with query string."""
        response = await test_client.get(
            "/search/notifications/search?q=invite", headers=admin_auth_headers
        )
        assert response.status_code == 200

    async def test_search_notifications_with_user_id(
        self, test_client: AsyncClient, admin_auth_headers: dict
    ):
        """Filter by user_id."""
        response = await test_client.get(
            "/search/notifications/search?user_id=1", headers=admin_auth_headers
        )
        assert response.status_code == 200

    async def test_search_notifications_with_facets_false(
        self, test_client: AsyncClient, admin_auth_headers: dict
    ):
        """Without facets."""
        response = await test_client.get(
            "/search/notifications/search?facets=false", headers=admin_auth_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert "results" in data

    async def test_search_notifications_with_limit(
        self, test_client: AsyncClient, admin_auth_headers: dict
    ):
        """Custom limit."""
        response = await test_client.get(
            "/search/notifications/search?limit=5", headers=admin_auth_headers
        )
        assert response.status_code == 200

    async def test_search_notifications_with_offset(
        self, test_client: AsyncClient, admin_auth_headers: dict
    ):
        """Custom offset."""
        response = await test_client.get(
            "/search/notifications/search?offset=10", headers=admin_auth_headers
        )
        assert response.status_code == 200

    async def test_search_notifications_max_limit(
        self, test_client: AsyncClient, admin_auth_headers: dict
    ):
        """Max allowed limit."""
        response = await test_client.get(
            "/search/notifications/search?limit=100", headers=admin_auth_headers
        )
        assert response.status_code == 200

    async def test_search_notifications_combined_q_and_user_id(
        self, test_client: AsyncClient, admin_auth_headers: dict
    ):
        """Query + user_id filter."""
        response = await test_client.get(
            "/search/notifications/search?q=invite&user_id=1",
            headers=admin_auth_headers,
        )
        assert response.status_code == 200

    async def test_search_notifications_combined_filters_with_pagination(
        self, test_client: AsyncClient, admin_auth_headers: dict
    ):
        """Filters + pagination."""
        response = await test_client.get(
            "/search/notifications/search?user_id=1&limit=5&offset=10",
            headers=admin_auth_headers,
        )
        assert response.status_code == 200

    async def test_search_notifications_without_auth(self, test_client: AsyncClient):
        """Without auth returns 401."""
        response = await test_client.get("/search/notifications/search")
        assert response.status_code == 401


class TestSearchEdgeCases:
    """Edge case tests for search endpoints."""

    async def test_search_tasks_invalid_limit_zero(
        self, test_client: AsyncClient, admin_auth_headers: dict
    ):
        """Limit=0 returns 422."""
        response = await test_client.get(
            "/search/tasks/search?limit=0", headers=admin_auth_headers
        )
        assert response.status_code == 422

    async def test_search_tasks_invalid_limit_exceed(
        self, test_client: AsyncClient, admin_auth_headers: dict
    ):
        """Limit>100 returns 422."""
        response = await test_client.get(
            "/search/tasks/search?limit=101", headers=admin_auth_headers
        )
        assert response.status_code == 422

    async def test_search_tasks_invalid_offset_negative(
        self, test_client: AsyncClient, admin_auth_headers: dict
    ):
        """Negative offset returns 422."""
        response = await test_client.get(
            "/search/tasks/search?offset=-1", headers=admin_auth_headers
        )
        assert response.status_code == 422

    async def test_search_users_invalid_limit_exceed(
        self, test_client: AsyncClient, admin_auth_headers: dict
    ):
        """Limit>100 returns 422."""
        response = await test_client.get(
            "/search/users/search?limit=101", headers=admin_auth_headers
        )
        assert response.status_code == 422

    async def test_search_groups_invalid_limit_exceed(
        self, test_client: AsyncClient, admin_auth_headers: dict
    ):
        """Limit>100 returns 422."""
        response = await test_client.get(
            "/search/groups/search?limit=101", headers=admin_auth_headers
        )
        assert response.status_code == 422

    async def test_search_comments_invalid_limit_exceed(
        self, test_client: AsyncClient, admin_auth_headers: dict
    ):
        """Limit>100 returns 422."""
        response = await test_client.get(
            "/search/comments/search?limit=101", headers=admin_auth_headers
        )
        assert response.status_code == 422

    async def test_search_notifications_invalid_limit_exceed(
        self, test_client: AsyncClient, admin_auth_headers: dict
    ):
        """Limit>100 returns 422."""
        response = await test_client.get(
            "/search/notifications/search?limit=101", headers=admin_auth_headers
        )
        assert response.status_code == 422


class TestSearchMyGroups:
    """Tests for /search/groups/my endpoint."""

    async def test_search_my_groups_no_params(
        self, test_client: AsyncClient, auth_headers: dict
    ):
        """Default search - no parameters."""
        await test_client.post(
            "/groups",
            json={"name": f"Test Group {uuid.uuid4().hex[:8]}", "description": "Test"},
            headers=auth_headers,
        )
        response = await test_client.get("/search/groups/my", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "results" in data
        assert "total" in data

    async def test_search_my_groups_with_q(
        self, test_client: AsyncClient, auth_headers: dict
    ):
        """Search with query string."""
        await test_client.post(
            "/groups",
            json={"name": f"Test Group {uuid.uuid4().hex[:8]}", "description": "Test"},
            headers=auth_headers,
        )
        response = await test_client.get(
            "/search/groups/my?q=Test", headers=auth_headers
        )
        assert response.status_code == 200

    async def test_search_my_groups_with_visibility(
        self, test_client: AsyncClient, auth_headers: dict
    ):
        """Filter by visibility."""
        await test_client.post(
            "/groups",
            json={
                "name": f"Test Group {uuid.uuid4().hex[:8]}",
                "description": "Test",
                "visibility": "public",
            },
            headers=auth_headers,
        )
        response = await test_client.get(
            "/search/groups/my?visibility=public", headers=auth_headers
        )
        assert response.status_code == 200

    async def test_search_my_groups_with_limit(
        self, test_client: AsyncClient, auth_headers: dict
    ):
        """Custom limit."""
        await test_client.post(
            "/groups",
            json={"name": f"Test Group {uuid.uuid4().hex[:8]}", "description": "Test"},
            headers=auth_headers,
        )
        response = await test_client.get(
            "/search/groups/my?limit=5", headers=auth_headers
        )
        assert response.status_code == 200

    async def test_search_my_groups_without_auth(self, test_client: AsyncClient):
        """Without auth returns 401."""
        response = await test_client.get("/search/groups/my")
        assert response.status_code == 401

    async def test_search_my_groups_with_scope_admin(
        self, test_client: AsyncClient, auth_headers: dict
    ):
        """Filter by scope admin."""
        await test_client.post(
            "/groups",
            json={"name": f"Test Group {uuid.uuid4().hex[:8]}", "description": "Test"},
            headers=auth_headers,
        )
        response = await test_client.get(
            "/search/groups/my?scope=admin", headers=auth_headers
        )
        assert response.status_code == 200

    async def test_search_my_groups_with_scope_member(
        self, test_client: AsyncClient, auth_headers: dict
    ):
        """Filter by scope member."""
        await test_client.post(
            "/groups",
            json={"name": f"Test Group {uuid.uuid4().hex[:8]}", "description": "Test"},
            headers=auth_headers,
        )
        response = await test_client.get(
            "/search/groups/my?scope=member", headers=auth_headers
        )
        assert response.status_code == 200

    async def test_search_my_groups_with_join_policy(
        self, test_client: AsyncClient, auth_headers: dict
    ):
        """Filter by join_policy."""
        await test_client.post(
            "/groups",
            json={
                "name": f"Test Group {uuid.uuid4().hex[:8]}",
                "description": "Test",
                "join_policy": "open",
            },
            headers=auth_headers,
        )
        response = await test_client.get(
            "/search/groups/my?join_policy=open", headers=auth_headers
        )
        assert response.status_code == 200

    async def test_search_my_groups_with_facets(
        self, test_client: AsyncClient, auth_headers: dict
    ):
        """Filter by facets."""
        await test_client.post(
            "/groups",
            json={"name": f"Test Group {uuid.uuid4().hex[:8]}", "description": "Test"},
            headers=auth_headers,
        )
        response = await test_client.get(
            "/search/groups/my?facets=true", headers=auth_headers
        )
        assert response.status_code == 200

    async def test_search_my_groups_with_offset(
        self, test_client: AsyncClient, auth_headers: dict
    ):
        """Filter by offset."""
        await test_client.post(
            "/groups",
            json={"name": f"Test Group {uuid.uuid4().hex[:8]}", "description": "Test"},
            headers=auth_headers,
        )
        response = await test_client.get(
            "/search/groups/my?offset=10", headers=auth_headers
        )
        assert response.status_code == 200

    async def test_search_my_groups_limit_zero(
        self, test_client: AsyncClient, auth_headers: dict
    ):
        """Limit=0 returns 422."""
        await test_client.post(
            "/groups",
            json={"name": f"Test Group {uuid.uuid4().hex[:8]}", "description": "Test"},
            headers=auth_headers,
        )
        response = await test_client.get(
            "/search/groups/my?limit=0", headers=auth_headers
        )
        assert response.status_code == 422

    async def test_search_my_groups_limit_exceed(
        self, test_client: AsyncClient, auth_headers: dict
    ):
        """Limit>100 returns 422."""
        await test_client.post(
            "/groups",
            json={"name": f"Test Group {uuid.uuid4().hex[:8]}", "description": "Test"},
            headers=auth_headers,
        )
        response = await test_client.get(
            "/search/groups/my?limit=101", headers=auth_headers
        )
        assert response.status_code == 422


class TestSearchMyTasks:
    """Tests for /search/tasks/my endpoint."""

    async def test_search_my_tasks_no_params(
        self, test_client: AsyncClient, auth_headers: dict
    ):
        """Default search - no parameters."""
        group_resp = await test_client.post(
            "/groups",
            json={"name": f"Test Group {uuid.uuid4().hex[:8]}", "description": "Test"},
            headers=auth_headers,
        )
        group_id = group_resp.json()["id"]
        await test_client.post(
            f"/tasks/groups/{group_id}",
            json={"title": "Test Task", "priority": "medium", "group_id": group_id},
            headers=auth_headers,
        )
        response = await test_client.get("/search/tasks/my", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert "results" in data

    async def test_search_my_tasks_with_status(
        self, test_client: AsyncClient, auth_headers: dict
    ):
        """Filter by status."""
        group_resp = await test_client.post(
            "/groups",
            json={"name": f"Test Group {uuid.uuid4().hex[:8]}", "description": "Test"},
            headers=auth_headers,
        )
        group_id = group_resp.json()["id"]
        await test_client.post(
            f"/tasks/groups/{group_id}",
            json={"title": "Test Task", "priority": "medium", "group_id": group_id},
            headers=auth_headers,
        )
        response = await test_client.get(
            "/search/tasks/my?status=pending", headers=auth_headers
        )
        assert response.status_code == 200

    async def test_search_my_tasks_with_limit(
        self, test_client: AsyncClient, auth_headers: dict
    ):
        """Custom limit."""
        group_resp = await test_client.post(
            "/groups",
            json={"name": f"Test Group {uuid.uuid4().hex[:8]}", "description": "Test"},
            headers=auth_headers,
        )
        group_id = group_resp.json()["id"]
        await test_client.post(
            f"/tasks/groups/{group_id}",
            json={"title": "Test Task", "priority": "medium", "group_id": group_id},
            headers=auth_headers,
        )
        response = await test_client.get(
            "/search/tasks/my?limit=5", headers=auth_headers
        )
        assert response.status_code == 200

    async def test_search_my_tasks_without_auth(self, test_client: AsyncClient):
        """Without auth returns 401."""
        response = await test_client.get("/search/tasks/my")
        assert response.status_code == 401

    async def test_search_my_tasks_with_q(
        self, test_client: AsyncClient, auth_headers: dict
    ):
        """Search with query string."""
        group_resp = await test_client.post(
            "/groups",
            json={"name": f"Test Group {uuid.uuid4().hex[:8]}", "description": "Test"},
            headers=auth_headers,
        )
        group_id = group_resp.json()["id"]
        await test_client.post(
            f"/tasks/groups/{group_id}",
            json={"title": "Test Task", "priority": "medium", "group_id": group_id},
            headers=auth_headers,
        )
        response = await test_client.get(
            "/search/tasks/my?q=Test", headers=auth_headers
        )
        assert response.status_code == 200

    async def test_search_my_tasks_with_priority(
        self, test_client: AsyncClient, auth_headers: dict
    ):
        """Filter by priority."""
        group_resp = await test_client.post(
            "/groups",
            json={"name": f"Test Group {uuid.uuid4().hex[:8]}", "description": "Test"},
            headers=auth_headers,
        )
        group_id = group_resp.json()["id"]
        await test_client.post(
            f"/tasks/groups/{group_id}",
            json={"title": "Test Task", "priority": "high", "group_id": group_id},
            headers=auth_headers,
        )
        response = await test_client.get(
            "/search/tasks/my?priority=high", headers=auth_headers
        )
        assert response.status_code == 200

    async def test_search_my_tasks_with_difficulty(
        self, test_client: AsyncClient, auth_headers: dict
    ):
        """Filter by difficulty."""
        group_resp = await test_client.post(
            "/groups",
            json={"name": f"Test Group {uuid.uuid4().hex[:8]}", "description": "Test"},
            headers=auth_headers,
        )
        group_id = group_resp.json()["id"]
        await test_client.post(
            f"/tasks/groups/{group_id}",
            json={
                "title": "Test Task",
                "priority": "medium",
                "difficulty": "medium",
                "group_id": group_id,
            },
            headers=auth_headers,
        )
        response = await test_client.get(
            "/search/tasks/my?difficulty=medium", headers=auth_headers
        )
        assert response.status_code == 200

    async def test_search_my_tasks_with_facets(
        self, test_client: AsyncClient, auth_headers: dict
    ):
        """Filter by facets."""
        group_resp = await test_client.post(
            "/groups",
            json={"name": f"Test Group {uuid.uuid4().hex[:8]}", "description": "Test"},
            headers=auth_headers,
        )
        group_id = group_resp.json()["id"]
        await test_client.post(
            f"/tasks/groups/{group_id}",
            json={"title": "Test Task", "priority": "medium", "group_id": group_id},
            headers=auth_headers,
        )
        response = await test_client.get(
            "/search/tasks/my?facets=true", headers=auth_headers
        )
        assert response.status_code == 200

    async def test_search_my_tasks_with_offset(
        self, test_client: AsyncClient, auth_headers: dict
    ):
        """Filter by offset."""
        group_resp = await test_client.post(
            "/groups",
            json={"name": f"Test Group {uuid.uuid4().hex[:8]}", "description": "Test"},
            headers=auth_headers,
        )
        group_id = group_resp.json()["id"]
        await test_client.post(
            f"/tasks/groups/{group_id}",
            json={"title": "Test Task", "priority": "medium", "group_id": group_id},
            headers=auth_headers,
        )
        response = await test_client.get(
            "/search/tasks/my?offset=10", headers=auth_headers
        )
        assert response.status_code == 200

    async def test_search_my_tasks_limit_zero(
        self, test_client: AsyncClient, auth_headers: dict
    ):
        """Limit=0 returns 422."""
        group_resp = await test_client.post(
            "/groups",
            json={"name": f"Test Group {uuid.uuid4().hex[:8]}", "description": "Test"},
            headers=auth_headers,
        )
        group_id = group_resp.json()["id"]
        await test_client.post(
            f"/tasks/groups/{group_id}",
            json={"title": "Test Task", "priority": "medium", "group_id": group_id},
            headers=auth_headers,
        )
        response = await test_client.get(
            "/search/tasks/my?limit=0", headers=auth_headers
        )
        assert response.status_code == 422

    async def test_search_my_tasks_limit_exceed(
        self, test_client: AsyncClient, auth_headers: dict
    ):
        """Limit>100 returns 422."""
        group_resp = await test_client.post(
            "/groups",
            json={"name": f"Test Group {uuid.uuid4().hex[:8]}", "description": "Test"},
            headers=auth_headers,
        )
        group_id = group_resp.json()["id"]
        await test_client.post(
            f"/tasks/groups/{group_id}",
            json={"title": "Test Task", "priority": "medium", "group_id": group_id},
            headers=auth_headers,
        )
        response = await test_client.get(
            "/search/tasks/my?limit=101", headers=auth_headers
        )
        assert response.status_code == 422


class TestSearchUsersByGroup:
    """Tests for /search/users/by-group endpoint."""

    async def test_search_users_by_group_required_group_id(
        self, test_client: AsyncClient, auth_headers: dict
    ):
        """group_id is required."""
        response = await test_client.get("/search/users/by-group", headers=auth_headers)
        assert response.status_code == 422

    async def test_search_users_by_group_no_params(
        self, test_client: AsyncClient, auth_headers: dict
    ):
        """Default search - no parameters."""
        group_resp = await test_client.post(
            "/groups",
            json={"name": f"Test Group {uuid.uuid4().hex[:8]}", "description": "Test"},
            headers=auth_headers,
        )
        group_id = group_resp.json()["id"]
        response = await test_client.get(
            f"/search/users/by-group?group_id={group_id}", headers=auth_headers
        )
        assert response.status_code == 200

    async def test_search_users_by_group_without_auth(self, test_client: AsyncClient):
        """Without auth returns 401."""
        response = await test_client.get("/search/users/by-group?group_id=1")
        assert response.status_code == 401

    async def test_search_users_by_group_with_q(
        self, test_client: AsyncClient, auth_headers: dict
    ):
        """Search with query string."""
        group_resp = await test_client.post(
            "/groups",
            json={"name": f"Test Group {uuid.uuid4().hex[:8]}", "description": "Test"},
            headers=auth_headers,
        )
        group_id = group_resp.json()["id"]
        response = await test_client.get(
            f"/search/users/by-group?group_id={group_id}&q=Test",
            headers=auth_headers,
        )
        assert response.status_code == 200

    async def test_search_users_by_group_with_role(
        self, test_client: AsyncClient, auth_headers: dict
    ):
        """Filter by role."""
        group_resp = await test_client.post(
            "/groups",
            json={"name": f"Test Group {uuid.uuid4().hex[:8]}", "description": "Test"},
            headers=auth_headers,
        )
        group_id = group_resp.json()["id"]
        response = await test_client.get(
            f"/search/users/by-group?group_id={group_id}&role=member",
            headers=auth_headers,
        )
        assert response.status_code == 200

    async def test_search_users_by_group_with_is_active(
        self, test_client: AsyncClient, auth_headers: dict
    ):
        """Filter by is_active."""
        group_resp = await test_client.post(
            "/groups",
            json={"name": f"Test Group {uuid.uuid4().hex[:8]}", "description": "Test"},
            headers=auth_headers,
        )
        group_id = group_resp.json()["id"]
        response = await test_client.get(
            f"/search/users/by-group?group_id={group_id}&is_active=true",
            headers=auth_headers,
        )
        assert response.status_code == 200

    async def test_search_users_by_group_with_facets(
        self, test_client: AsyncClient, auth_headers: dict
    ):
        """Filter by facets."""
        group_resp = await test_client.post(
            "/groups",
            json={"name": f"Test Group {uuid.uuid4().hex[:8]}", "description": "Test"},
            headers=auth_headers,
        )
        group_id = group_resp.json()["id"]
        response = await test_client.get(
            f"/search/users/by-group?group_id={group_id}&facets=true",
            headers=auth_headers,
        )
        assert response.status_code == 200

    async def test_search_users_by_group_with_limit(
        self, test_client: AsyncClient, auth_headers: dict
    ):
        """Filter by limit."""
        group_resp = await test_client.post(
            "/groups",
            json={"name": f"Test Group {uuid.uuid4().hex[:8]}", "description": "Test"},
            headers=auth_headers,
        )
        group_id = group_resp.json()["id"]
        response = await test_client.get(
            f"/search/users/by-group?group_id={group_id}&limit=5",
            headers=auth_headers,
        )
        assert response.status_code == 200

    async def test_search_users_by_group_with_offset(
        self, test_client: AsyncClient, auth_headers: dict
    ):
        """Filter by offset."""
        group_resp = await test_client.post(
            "/groups",
            json={"name": f"Test Group {uuid.uuid4().hex[:8]}", "description": "Test"},
            headers=auth_headers,
        )
        group_id = group_resp.json()["id"]
        response = await test_client.get(
            f"/search/users/by-group?group_id={group_id}&offset=10",
            headers=auth_headers,
        )
        assert response.status_code == 200

    async def test_search_users_by_group_limit_exceed(
        self, test_client: AsyncClient, auth_headers: dict
    ):
        """Limit>100 returns 422."""
        response = await test_client.get(
            "/search/users/by-group?group_id=1&limit=101",
            headers=auth_headers,
        )
        assert response.status_code == 422

    async def test_search_users_by_group_invalid_group_id(
        self, test_client: AsyncClient, auth_headers: dict
    ):
        """Invalid group_id returns 422."""
        response = await test_client.get(
            "/search/users/by-group?group_id=abc",
            headers=auth_headers,
        )
        assert response.status_code == 422


class TestSearchTasksByGroup:
    """Tests for /search/tasks/by-group endpoint."""

    async def test_search_tasks_by_group_required_group_id(
        self, test_client: AsyncClient, auth_headers: dict
    ):
        """group_id is required."""
        response = await test_client.get("/search/tasks/by-group", headers=auth_headers)
        assert response.status_code == 422

    async def test_search_tasks_by_group_no_params(
        self, test_client: AsyncClient, auth_headers: dict
    ):
        """Default search - no parameters."""
        group_resp = await test_client.post(
            "/groups",
            json={"name": f"Test Group {uuid.uuid4().hex[:8]}", "description": "Test"},
            headers=auth_headers,
        )
        group_id = group_resp.json()["id"]
        response = await test_client.get(
            f"/search/tasks/by-group?group_id={group_id}", headers=auth_headers
        )
        assert response.status_code == 200

    async def test_search_tasks_by_group_without_auth(self, test_client: AsyncClient):
        """Without auth returns 401."""
        response = await test_client.get("/search/tasks/by-group?group_id=1")
        assert response.status_code == 401

    async def test_search_tasks_by_group_with_q(
        self, test_client: AsyncClient, auth_headers: dict
    ):
        """Search with query string."""
        group_resp = await test_client.post(
            "/groups",
            json={"name": f"Test Group {uuid.uuid4().hex[:8]}", "description": "Test"},
            headers=auth_headers,
        )
        group_id = group_resp.json()["id"]
        response = await test_client.get(
            f"/search/tasks/by-group?group_id={group_id}&q=Test",
            headers=auth_headers,
        )
        assert response.status_code == 200

    async def test_search_tasks_by_group_with_status(
        self, test_client: AsyncClient, auth_headers: dict
    ):
        """Filter by status."""
        group_resp = await test_client.post(
            "/groups",
            json={"name": f"Test Group {uuid.uuid4().hex[:8]}", "description": "Test"},
            headers=auth_headers,
        )
        group_id = group_resp.json()["id"]
        response = await test_client.get(
            f"/search/tasks/by-group?group_id={group_id}&status=pending",
            headers=auth_headers,
        )
        assert response.status_code == 200

    async def test_search_tasks_by_group_with_priority(
        self, test_client: AsyncClient, auth_headers: dict
    ):
        """Filter by priority."""
        group_resp = await test_client.post(
            "/groups",
            json={"name": f"Test Group {uuid.uuid4().hex[:8]}", "description": "Test"},
            headers=auth_headers,
        )
        group_id = group_resp.json()["id"]
        response = await test_client.get(
            f"/search/tasks/by-group?group_id={group_id}&priority=high",
            headers=auth_headers,
        )
        assert response.status_code == 200

    async def test_search_tasks_by_group_with_difficulty(
        self, test_client: AsyncClient, auth_headers: dict
    ):
        """Filter by difficulty."""
        group_resp = await test_client.post(
            "/groups",
            json={"name": f"Test Group {uuid.uuid4().hex[:8]}", "description": "Test"},
            headers=auth_headers,
        )
        group_id = group_resp.json()["id"]
        response = await test_client.get(
            f"/search/tasks/by-group?group_id={group_id}&difficulty=medium",
            headers=auth_headers,
        )
        assert response.status_code == 200

    async def test_search_tasks_by_group_with_spheres(
        self, test_client: AsyncClient, auth_headers: dict
    ):
        """Filter by spheres."""
        group_resp = await test_client.post(
            "/groups",
            json={"name": f"Test Group {uuid.uuid4().hex[:8]}", "description": "Test"},
            headers=auth_headers,
        )
        group_id = group_resp.json()["id"]
        response = await test_client.get(
            f"/search/tasks/by-group?group_id={group_id}&spheres=backend",
            headers=auth_headers,
        )
        assert response.status_code == 200

    async def test_search_tasks_by_group_with_assignee_ids(
        self, test_client: AsyncClient, auth_headers: dict
    ):
        """Filter by assignee_ids."""
        group_resp = await test_client.post(
            "/groups",
            json={"name": f"Test Group {uuid.uuid4().hex[:8]}", "description": "Test"},
            headers=auth_headers,
        )
        group_id = group_resp.json()["id"]
        response = await test_client.get(
            f"/search/tasks/by-group?group_id={group_id}&assignee_ids=1",
            headers=auth_headers,
        )
        assert response.status_code == 200

    async def test_search_tasks_by_group_with_facets(
        self, test_client: AsyncClient, auth_headers: dict
    ):
        """Filter by facets."""
        group_resp = await test_client.post(
            "/groups",
            json={"name": f"Test Group {uuid.uuid4().hex[:8]}", "description": "Test"},
            headers=auth_headers,
        )
        group_id = group_resp.json()["id"]
        response = await test_client.get(
            f"/search/tasks/by-group?group_id={group_id}&facets=true",
            headers=auth_headers,
        )
        assert response.status_code == 200

    async def test_search_tasks_by_group_with_limit(
        self, test_client: AsyncClient, auth_headers: dict
    ):
        """Filter by limit."""
        group_resp = await test_client.post(
            "/groups",
            json={"name": f"Test Group {uuid.uuid4().hex[:8]}", "description": "Test"},
            headers=auth_headers,
        )
        group_id = group_resp.json()["id"]
        response = await test_client.get(
            f"/search/tasks/by-group?group_id={group_id}&limit=5",
            headers=auth_headers,
        )
        assert response.status_code == 200

    async def test_search_tasks_by_group_with_offset(
        self, test_client: AsyncClient, auth_headers: dict
    ):
        """Filter by offset."""
        group_resp = await test_client.post(
            "/groups",
            json={"name": f"Test Group {uuid.uuid4().hex[:8]}", "description": "Test"},
            headers=auth_headers,
        )
        group_id = group_resp.json()["id"]
        response = await test_client.get(
            f"/search/tasks/by-group?group_id={group_id}&offset=10",
            headers=auth_headers,
        )
        assert response.status_code == 200

    async def test_search_tasks_by_group_limit_exceed(
        self, test_client: AsyncClient, auth_headers: dict
    ):
        """Limit>100 returns 422."""
        response = await test_client.get(
            "/search/tasks/by-group?group_id=1&limit=101",
            headers=auth_headers,
        )
        assert response.status_code == 422

    async def test_search_tasks_by_group_invalid_group_id(
        self, test_client: AsyncClient, auth_headers: dict
    ):
        """Invalid group_id returns 422."""
        response = await test_client.get(
            "/search/tasks/by-group?group_id=abc",
            headers=auth_headers,
        )
        assert response.status_code == 422
