from httpx import AsyncClient


class TestGetNotifications:
    async def test_get_notifications_returns_200(
        self, test_client: AsyncClient, auth_headers: dict
    ):
        """Get all notifications — returns 200."""
        resp = await test_client.get("/notifications", headers=auth_headers)
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    async def test_get_notifications_without_auth_returns_401(
        self, test_client: AsyncClient
    ):
        """Get notifications without auth — returns 401."""
        resp = await test_client.get("/notifications")
        assert resp.status_code == 401

    async def test_get_notifications_with_status_filter_returns_200(
        self, test_client: AsyncClient, auth_headers: dict
    ):
        """Get notifications filtered by status — returns 200."""
        resp = await test_client.get(
            "/notifications?status=unread", headers=auth_headers
        )
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    async def test_get_notifications_with_type_filter_returns_200(
        self, test_client: AsyncClient, auth_headers: dict
    ):
        """Get notifications filtered by type — returns 200."""
        resp = await test_client.get(
            "/notifications?type=comment", headers=auth_headers
        )
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    async def test_get_notifications_with_limit_returns_200(
        self, test_client: AsyncClient, auth_headers: dict
    ):
        """Get notifications with limit — returns 200."""
        resp = await test_client.get("/notifications?limit=10", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) <= 10

    async def test_get_notifications_with_offset_returns_200(
        self, test_client: AsyncClient, auth_headers: dict
    ):
        """Get notifications with offset — returns 200."""
        resp = await test_client.get("/notifications?offset=0", headers=auth_headers)
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)


class TestGetUnreadCount:
    async def test_get_unread_count_returns_200(
        self, test_client: AsyncClient, auth_headers: dict
    ):
        """Get unread notifications count — returns 200."""
        resp = await test_client.get(
            "/notifications/unread-count", headers=auth_headers
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "count" in data
        assert isinstance(data["count"], int)

    async def test_get_unread_count_without_auth_returns_401(
        self, test_client: AsyncClient
    ):
        """Get unread count without auth — returns 401."""
        resp = await test_client.get("/notifications/unread-count")
        assert resp.status_code == 401


class TestGetNotification:
    async def test_get_notification_without_auth_returns_401(
        self, test_client: AsyncClient
    ):
        """Get notification without auth — returns 401."""
        resp = await test_client.get("/notifications/1")
        assert resp.status_code == 401


class TestMarkNotificationRead:
    async def test_mark_notification_read_without_auth_returns_401(
        self, test_client: AsyncClient
    ):
        """Mark notification as read without auth — returns 401."""
        resp = await test_client.patch("/notifications/1/read")
        assert resp.status_code == 401


class TestMarkAllNotificationsRead:
    async def test_mark_all_notifications_read_returns_200(
        self, test_client: AsyncClient, auth_headers: dict
    ):
        """Mark all notifications as read — returns 200."""
        resp = await test_client.patch("/notifications/read-all", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "updated_count" in data
        assert isinstance(data["updated_count"], int)

    async def test_mark_all_notifications_read_without_auth_returns_401(
        self, test_client: AsyncClient
    ):
        """Mark all as read without auth — returns 401."""
        resp = await test_client.patch("/notifications/read-all")
        assert resp.status_code == 401


class TestRespondToNotification:
    async def test_respond_to_notification_without_auth_returns_401(
        self, test_client: AsyncClient
    ):
        """Respond to notification without auth — returns 401."""
        resp = await test_client.post(
            "/notifications/1/respond", json={"response": "accept"}
        )
        assert resp.status_code == 401
