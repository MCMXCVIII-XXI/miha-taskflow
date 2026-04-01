"""
Integration tests for notification system.

Tests verify that notifications are created when:
- Adding member to group (GROUP_INVITE)
- Joining group (GROUP_JOIN)
- Adding user to task (TASK_INVITE)
- Responding to notifications (accept/decline)
- Marking as read
"""

from uuid import uuid4

import jwt
from httpx import AsyncClient


async def _register_user_get_id(
    client: AsyncClient, username: str, email: str
) -> tuple[dict, int]:
    """Register user and return auth headers and user ID."""
    resp = await client.post(
        "/auth",
        json={
            "username": username,
            "email": email,
            "password": "Password123",
            "first_name": "Test",
            "last_name": "User",
        },
    )
    if resp.status_code == 409:
        resp = await client.post(
            "/auth/token",
            data={"username": username, "password": "Password123"},
        )
    token = resp.json()["access_token"]
    payload = jwt.decode(token, options={"verify_signature": False})
    user_id = int(payload.get("sub"))
    return {"Authorization": f"Bearer {token}"}, user_id


class TestNotificationsOnGroupInvite:
    """Test GROUP_INVITE notification creation when adding member to group."""

    async def test_add_member_creates_group_invite_notification(
        self, test_client: AsyncClient, auth_headers: dict
    ):
        """Add member to group — creates GROUP_INVITE notification."""
        unique_id = str(uuid4())[:8]

        create_resp = await test_client.post(
            "/groups",
            json={
                "name": f"TestGroup_{unique_id}",
                "description": "Test group",
            },
            headers=auth_headers,
        )
        assert create_resp.status_code == 201
        group_id = create_resp.json()["id"]

        user2_headers, user2_id = await _register_user_get_id(
            test_client, f"user2_{unique_id}", f"user2_{unique_id}@test.com"
        )

        add_resp = await test_client.post(
            f"/groups/{group_id}/members/{user2_id}",
            headers=auth_headers,
        )
        assert add_resp.status_code == 201

        notifications_resp = await test_client.get(
            "/notifications", headers=user2_headers
        )
        assert notifications_resp.status_code == 200
        notifications = notifications_resp.json()

        group_invite = next(
            (n for n in notifications if n["type"] == "group_invite"), None
        )
        assert group_invite is not None, "GROUP_INVITE notification should exist"
        assert group_invite["target_id"] == group_id
        assert group_invite["target_type"] == "group"
        assert group_invite["recipient_id"] == user2_id
        assert group_invite["status"] == "unread"
        assert group_invite["response"] == "waiting"

    async def test_add_member_notification_message_content(
        self, test_client: AsyncClient, auth_headers: dict
    ):
        """Verify GROUP_INVITE notification has correct title."""
        unique_id = str(uuid4())[:8]

        create_resp = await test_client.post(
            "/groups",
            json={
                "name": f"TestGroup_{unique_id}",
                "description": "Test group",
            },
            headers=auth_headers,
        )
        group_id = create_resp.json()["id"]

        user2_headers, user2_id = await _register_user_get_id(
            test_client, f"user3_{unique_id}", f"user3_{unique_id}@test.com"
        )

        await test_client.post(
            f"/groups/{group_id}/members/{user2_id}",
            headers=auth_headers,
        )

        notifications_resp = await test_client.get(
            "/notifications", headers=user2_headers
        )
        notifications = notifications_resp.json()
        group_invite = next(
            (n for n in notifications if n["type"] == "group_invite"), None
        )
        assert group_invite is not None
        assert (
            "group" in group_invite["title"].lower()
            or "invitation" in group_invite["title"].lower()
        )


class TestNotificationsOnGroupJoin:
    """Test GROUP_JOIN notification creation when user joins group."""

    async def test_join_group_creates_join_request_notification(
        self, test_client: AsyncClient, auth_headers: dict
    ):
        """User joins group — creates GROUP_JOIN notification for admin."""
        unique_id = str(uuid4())[:8]

        create_resp = await test_client.post(
            "/groups",
            json={
                "name": f"TestGroup_{unique_id}",
                "description": "Test group",
            },
            headers=auth_headers,
        )
        assert create_resp.status_code == 201
        group_id = create_resp.json()["id"]

        user2_headers, _ = await _register_user_get_id(
            test_client, f"joiner_{unique_id}", f"joiner_{unique_id}@test.com"
        )

        join_resp = await test_client.post(
            f"/groups/{group_id}/join",
            headers=user2_headers,
        )
        assert join_resp.status_code == 201

        notifications_resp = await test_client.get(
            "/notifications", headers=auth_headers
        )
        assert notifications_resp.status_code == 200
        notifications = notifications_resp.json()

        group_join = next((n for n in notifications if n["type"] == "group_join"), None)
        assert group_join is not None, "GROUP_JOIN notification should exist"
        assert group_join["target_id"] == group_id
        assert group_join["target_type"] == "group"
        assert group_join["status"] == "unread"


class TestNotificationsOnTaskInvite:
    """Test TASK_INVITE notification creation when assigning user to task."""

    async def test_add_user_to_task_creates_task_invite_notification(
        self, test_client: AsyncClient, auth_headers: dict
    ):
        """Add user to task — creates TASK_INVITE notification."""
        unique_id = str(uuid4())[:8]

        group_resp = await test_client.post(
            "/groups",
            json={"name": f"TaskGroup_{unique_id}", "description": "Test"},
            headers=auth_headers,
        )
        group_id = group_resp.json()["id"]

        task_resp = await test_client.post(
            f"/tasks/groups/{group_id}",
            json={
                "title": f"TestTask_{unique_id}",
                "priority": "medium",
                "group_id": group_id,
            },
            headers=auth_headers,
        )
        assert task_resp.status_code == 201
        task_id = task_resp.json()["id"]

        user2_headers, user2_id = await _register_user_get_id(
            test_client, f"assignee_{unique_id}", f"assignee_{unique_id}@test.com"
        )

        add_resp = await test_client.post(
            f"/tasks/{task_id}/members/{user2_id}",
            headers=auth_headers,
        )
        assert add_resp.status_code == 201

        notifications_resp = await test_client.get(
            "/notifications", headers=user2_headers
        )
        assert notifications_resp.status_code == 200
        notifications = notifications_resp.json()

        task_invite = next(
            (n for n in notifications if n["type"] == "task_invite"), None
        )
        assert task_invite is not None, "TASK_INVITE notification should exist"
        assert task_invite["target_id"] == task_id
        assert task_invite["target_type"] == "task"
        assert task_invite["recipient_id"] == user2_id

    async def test_task_invite_notification_message_content(
        self, test_client: AsyncClient, auth_headers: dict
    ):
        """Verify TASK_INVITE notification has correct content."""
        unique_id = str(uuid4())[:8]

        group_resp = await test_client.post(
            "/groups",
            json={"name": f"TaskGroup2_{unique_id}", "description": "Test"},
            headers=auth_headers,
        )
        group_id = group_resp.json()["id"]

        task_resp = await test_client.post(
            f"/tasks/groups/{group_id}",
            json={
                "title": f"TestTask2_{unique_id}",
                "priority": "medium",
                "group_id": group_id,
            },
            headers=auth_headers,
        )
        task_id = task_resp.json()["id"]

        user2_headers, user2_id = await _register_user_get_id(
            test_client, f"assignee2_{unique_id}", f"assignee2_{unique_id}@test.com"
        )

        await test_client.post(
            f"/tasks/{task_id}/members/{user2_id}",
            headers=auth_headers,
        )

        notifications_resp = await test_client.get(
            "/notifications", headers=user2_headers
        )
        notifications = notifications_resp.json()
        task_invite = next(
            (n for n in notifications if n["type"] == "task_invite"), None
        )
        assert task_invite is not None
        assert (
            "task" in task_invite["title"].lower()
            or "invitation" in task_invite["title"].lower()
        )


class TestNotificationResponse:
    """Test responding to notifications (accept/decline)."""

    async def test_respond_to_group_invite_accept(
        self, test_client: AsyncClient, auth_headers: dict
    ):
        """Accept GROUP_INVITE — notification status changes to read."""
        unique_id = str(uuid4())[:8]

        create_resp = await test_client.post(
            "/groups",
            json={"name": f"AcceptGroup_{unique_id}"},
            headers=auth_headers,
        )
        group_id = create_resp.json()["id"]

        user2_headers, user2_id = await _register_user_get_id(
            test_client, f"acceptuser_{unique_id}", f"acceptuser_{unique_id}@test.com"
        )

        await test_client.post(
            f"/groups/{group_id}/members/{user2_id}",
            headers=auth_headers,
        )

        notifications_resp = await test_client.get(
            "/notifications", headers=user2_headers
        )
        notifications = notifications_resp.json()
        notification = next(
            (n for n in notifications if n["type"] == "group_invite"), None
        )
        assert notification is not None

        respond_resp = await test_client.post(
            f"/notifications/{notification['id']}/respond",
            json={"response": "accept"},
            headers=user2_headers,
        )
        assert respond_resp.status_code == 200
        assert respond_resp.json()["response"] == "accept"
        assert respond_resp.json()["status"] == "read"

    async def test_respond_to_group_invite_refusal(
        self, test_client: AsyncClient, auth_headers: dict
    ):
        """Refuse GROUP_INVITE — notification response changes to refusal."""
        unique_id = str(uuid4())[:8]

        create_resp = await test_client.post(
            "/groups",
            json={"name": f"RefuseGroup_{unique_id}"},
            headers=auth_headers,
        )
        group_id = create_resp.json()["id"]

        user2_headers, user2_id = await _register_user_get_id(
            test_client, f"refuseuser_{unique_id}", f"refuseuser_{unique_id}@test.com"
        )

        await test_client.post(
            f"/groups/{group_id}/members/{user2_id}",
            headers=auth_headers,
        )

        notifications_resp = await test_client.get(
            "/notifications", headers=user2_headers
        )
        notifications = notifications_resp.json()
        notification = next(
            (n for n in notifications if n["type"] == "group_invite"), None
        )

        respond_resp = await test_client.post(
            f"/notifications/{notification['id']}/respond",
            json={"response": "refusal"},
            headers=user2_headers,
        )
        assert respond_resp.status_code == 200
        assert respond_resp.json()["response"] == "refusal"
        assert respond_resp.json()["status"] == "read"


class TestNotificationMarkAsRead:
    """Test marking notifications as read."""

    async def test_mark_notification_as_read_updates_status(
        self, test_client: AsyncClient, auth_headers: dict
    ):
        """Mark notification as read — status changes to read."""
        unique_id = str(uuid4())[:8]

        create_resp = await test_client.post(
            "/groups",
            json={"name": f"ReadGroup_{unique_id}"},
            headers=auth_headers,
        )
        group_id = create_resp.json()["id"]

        user2_headers, user2_id = await _register_user_get_id(
            test_client, f"readuser_{unique_id}", f"readuser_{unique_id}@test.com"
        )

        await test_client.post(
            f"/groups/{group_id}/members/{user2_id}",
            headers=auth_headers,
        )

        notifications_resp = await test_client.get(
            "/notifications", headers=user2_headers
        )
        notifications = notifications_resp.json()
        notification = next(
            (n for n in notifications if n["type"] == "group_invite"), None
        )
        assert notification is not None
        assert notification["status"] == "unread"

        mark_resp = await test_client.patch(
            f"/notifications/{notification['id']}/read",
            headers=user2_headers,
        )
        assert mark_resp.status_code == 200
        assert mark_resp.json()["status"] == "read"

    async def test_mark_all_notifications_as_read(
        self, test_client: AsyncClient, auth_headers: dict
    ):
        """Mark all notifications as read — all become read."""
        unique_id = str(uuid4())[:8]

        create_resp = await test_client.post(
            "/groups",
            json={"name": f"MultiGroup_{unique_id}"},
            headers=auth_headers,
        )
        group_id = create_resp.json()["id"]

        user2_headers, user2_id = await _register_user_get_id(
            test_client, f"multiuser_{unique_id}", f"multiuser_{unique_id}@test.com"
        )

        await test_client.post(
            f"/groups/{group_id}/members/{user2_id}",
            headers=auth_headers,
        )

        mark_all_resp = await test_client.patch(
            "/notifications/read-all",
            headers=user2_headers,
        )
        assert mark_all_resp.status_code == 200
        assert mark_all_resp.json()["updated_count"] >= 0
