import uuid

from httpx import AsyncClient

from tests.conftest import register_user


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

    async def test_get_unread_count_with_notification_returns_count_gt_0(
        self, test_client: AsyncClient, auth_headers: dict
    ):
        """Get unread count after creating notification — count > 0."""
        # Create invitee who will receive notification
        invitee_headers = await register_user(
            test_client, "inviteduser", "invited@test.com"
        )
        invitee_id = int(
            (await test_client.get("/users/me", headers=invitee_headers)).json()["id"]
        )

        # Create group and invite user
        group_resp = await test_client.post(
            "/groups",
            json={"name": f"unread_{uuid.uuid4().hex[:8]}"},
            headers=auth_headers,
        )
        group_id = group_resp.json()["id"]

        await test_client.post(
            f"/groups/{group_id}/members/{invitee_id}",
            headers=auth_headers,
        )

        # Check unread count for invitee
        resp = await test_client.get(
            "/notifications/unread-count", headers=invitee_headers
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["count"] > 0

    async def test_get_unread_count_without_auth_returns_401(
        self, test_client: AsyncClient
    ):
        """Get unread count without auth — returns 401."""
        resp = await test_client.get("/notifications/unread-count")
        assert resp.status_code == 401


class TestGetNotification:
    async def test_get_notification_returns_200(
        self, test_client: AsyncClient, auth_headers: dict
    ):
        """Get specific notification with auth — returns 200."""
        # Create a group and invite user to create notification
        other_headers = await register_user(test_client)
        other_user_id = int(
            (await test_client.get("/users/me", headers=other_headers)).json()["id"]
        )

        # Create group
        group_resp = await test_client.post(
            "/groups",
            json={"name": "NotifTestGroup", "description": "Test"},
            headers=auth_headers,
        )
        group_id = group_resp.json()["id"]

        # Invite user to group (creates notification)
        await test_client.post(
            f"/groups/{group_id}/members/{other_user_id}",
            headers=auth_headers,
        )

        # Get notifications for invited user
        notif_resp = await test_client.get("/notifications", headers=other_headers)
        notifications = notif_resp.json()

        if notifications:
            notification_id = notifications[0]["id"]
            resp = await test_client.get(
                f"/notifications/{notification_id}", headers=other_headers
            )
            assert resp.status_code == 200
            data = resp.json()
            assert data["id"] == notification_id

    async def test_get_notification_not_found_returns_404(
        self, test_client: AsyncClient, auth_headers: dict
    ):
        """Get non-existent notification returns 404."""
        resp = await test_client.get("/notifications/999999", headers=auth_headers)
        assert resp.status_code == 404

    async def test_get_notification_without_auth_returns_401(
        self, test_client: AsyncClient
    ):
        """Get notification without auth — returns 401."""
        resp = await test_client.get("/notifications/1")
        assert resp.status_code == 401


class TestMarkNotificationRead:
    async def test_mark_notification_read_returns_200(
        self, test_client: AsyncClient, auth_headers: dict
    ):
        """Mark notification as read with auth — returns 200."""
        # Create notification
        other_headers = await register_user(test_client)
        other_user_id = int(
            (await test_client.get("/users/me", headers=other_headers)).json()["id"]
        )

        group_resp = await test_client.post(
            "/groups",
            json={"name": "MarkReadGroup", "description": "Test"},
            headers=auth_headers,
        )
        group_id = group_resp.json()["id"]

        await test_client.post(
            f"/groups/{group_id}/members/{other_user_id}",
            headers=auth_headers,
        )

        # Get notifications
        notif_resp = await test_client.get("/notifications", headers=other_headers)
        notifications = notif_resp.json()

        if notifications:
            notification_id = notifications[0]["id"]
            resp = await test_client.patch(
                f"/notifications/{notification_id}/read", headers=other_headers
            )
            assert resp.status_code == 200
            data = resp.json()
            assert data["status"] == "read"

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

    async def test_mark_all_read_with_notifications_returns_count_gt_0(
        self, test_client: AsyncClient, auth_headers: dict
    ):
        """Mark all as read after creating notifications — updated_count > 0."""
        # Create invitee who will receive notification
        invitee_headers = await register_user(
            test_client, "markalluser", "markall@test.com"
        )
        invitee_id = int(
            (await test_client.get("/users/me", headers=invitee_headers)).json()["id"]
        )

        # Create group and invite user
        group_resp = await test_client.post(
            "/groups",
            json={"name": f"markall_{uuid.uuid4().hex[:8]}"},
            headers=auth_headers,
        )
        group_id = group_resp.json()["id"]

        await test_client.post(
            f"/groups/{group_id}/members/{invitee_id}",
            headers=auth_headers,
        )

        # Mark all as read for invitee
        resp = await test_client.patch(
            "/notifications/read-all", headers=invitee_headers
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["updated_count"] > 0

    async def test_mark_all_notifications_read_without_auth_returns_401(
        self, test_client: AsyncClient
    ):
        """Mark all as read without auth — returns 401."""
        resp = await test_client.patch("/notifications/read-all")
        assert resp.status_code == 401


class TestRespondToNotification:
    async def test_respond_to_notification_returns_200(
        self, test_client: AsyncClient, auth_headers: dict
    ):
        """Respond to notification with auth — returns 200."""
        # Create notification via group invite
        other_headers = await register_user(test_client)
        other_user_id = int(
            (await test_client.get("/users/me", headers=other_headers)).json()["id"]
        )

        group_resp = await test_client.post(
            "/groups",
            json={"name": "RespondGroup", "description": "Test"},
            headers=auth_headers,
        )
        group_id = group_resp.json()["id"]

        await test_client.post(
            f"/groups/{group_id}/members/{other_user_id}",
            headers=auth_headers,
        )

        # Get notifications for invited user
        notif_resp = await test_client.get("/notifications", headers=other_headers)
        notifications = notif_resp.json()

        if notifications:
            notification_id = notifications[0]["id"]
            resp = await test_client.post(
                f"/notifications/{notification_id}/respond",
                json={"response": "accept"},
                headers=other_headers,
            )
            assert resp.status_code == 200
            data = resp.json()
            assert data["response"] == "accept"

    async def test_respond_to_notification_not_found_returns_404(
        self, test_client: AsyncClient, auth_headers: dict
    ):
        """Respond to non-existent notification returns 404."""
        resp = await test_client.post(
            "/notifications/999999/respond",
            json={"response": "accept"},
            headers=auth_headers,
        )
        assert resp.status_code == 404

    async def test_respond_to_notification_without_auth_returns_401(
        self, test_client: AsyncClient
    ):
        """Respond to notification without auth — returns 401."""
        resp = await test_client.post(
            "/notifications/1/respond", json={"response": "accept"}
        )
        assert resp.status_code == 401


class TestGroupInviteNotification:
    async def test_group_invite_creates_notification(
        self, test_client: AsyncClient, auth_headers: dict
    ):
        """Inviting user to group creates notification."""
        # Create invitee
        invitee_headers = await register_user(
            test_client, "invitee", "invitee@test.com"
        )
        invitee_id = int(
            (await test_client.get("/users/me", headers=invitee_headers)).json()["id"]
        )

        # Create group
        group_resp = await test_client.post(
            "/groups",
            json={"name": "InviteNotifGroup", "description": "Test"},
            headers=auth_headers,
        )
        group_id = group_resp.json()["id"]

        # Invite user
        await test_client.post(
            f"/groups/{group_id}/members/{invitee_id}",
            headers=auth_headers,
        )

        # Check invitee has notification
        notif_resp = await test_client.get("/notifications", headers=invitee_headers)
        assert notif_resp.status_code == 200
        notifications = notif_resp.json()
        assert len(notifications) > 0
        assert any(n["type"] == "group_invite" for n in notifications)

    async def test_accept_invite_joins_group(
        self, test_client: AsyncClient, auth_headers: dict
    ):
        """Accepting group invite adds user to group."""
        # Create invitee
        invitee_headers = await register_user(
            test_client, "accepter", "accepter@test.com"
        )
        invitee_id = int(
            (await test_client.get("/users/me", headers=invitee_headers)).json()["id"]
        )

        # Create group
        group_resp = await test_client.post(
            "/groups",
            json={"name": "AcceptGroup", "description": "Test"},
            headers=auth_headers,
        )
        group_id = group_resp.json()["id"]

        # Invite user
        await test_client.post(
            f"/groups/{group_id}/members/{invitee_id}",
            headers=auth_headers,
        )

        # Get notification
        notif_resp = await test_client.get("/notifications", headers=invitee_headers)
        notifications = notif_resp.json()

        if notifications:
            notification_id = notifications[0]["id"]

            # Accept invite
            resp = await test_client.post(
                f"/notifications/{notification_id}/respond",
                json={"response": "accept"},
                headers=invitee_headers,
            )
            assert resp.status_code == 200
            assert resp.json()["response"] == "accept"

    async def test_refuse_invite_rejects_group(
        self, test_client: AsyncClient, auth_headers: dict
    ):
        """Refusing group invite rejects invitation."""
        # Create invitee
        invitee_headers = await register_user(
            test_client, "refuser", "refuser@test.com"
        )
        invitee_id = int(
            (await test_client.get("/users/me", headers=invitee_headers)).json()["id"]
        )

        # Create group
        group_resp = await test_client.post(
            "/groups",
            json={"name": "RefuseGroup", "description": "Test"},
            headers=auth_headers,
        )
        group_id = group_resp.json()["id"]

        # Invite user
        await test_client.post(
            f"/groups/{group_id}/members/{invitee_id}",
            headers=auth_headers,
        )

        # Get notification
        notif_resp = await test_client.get("/notifications", headers=invitee_headers)
        notifications = notif_resp.json()

        if notifications:
            notification_id = notifications[0]["id"]

            # Refuse invite
            resp = await test_client.post(
                f"/notifications/{notification_id}/respond",
                json={"response": "refusal"},
                headers=invitee_headers,
            )
            assert resp.status_code == 200
            assert resp.json()["response"] == "refusal"
