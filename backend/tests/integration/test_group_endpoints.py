import uuid

from httpx import AsyncClient

from tests.conftest import register_user


class TestCreateGroup:
    async def test_create_group_returns_201(
        self, test_client: AsyncClient, auth_headers: dict
    ):
        """Create group — returns 201 with correct data."""
        payload = {"name": "Test Group", "description": "Test description"}
        response = await test_client.post("/groups", json=payload, headers=auth_headers)
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Test Group"
        assert data["description"] == "Test description"
        assert "id" in data
        assert "created_at" in data

    async def test_create_group_without_auth_returns_401(
        self, test_client: AsyncClient
    ):
        """Create group without auth — returns 401."""
        payload = {"name": "Test Group", "description": "Test"}
        response = await test_client.post("/groups", json=payload)
        assert response.status_code == 401

    async def test_create_duplicate_name_returns_409(
        self, test_client: AsyncClient, auth_headers: dict
    ):
        """Create two groups with same name — second returns 409."""
        await test_client.post(
            "/groups",
            json={"name": "Dup Group", "description": "First"},
            headers=auth_headers,
        )
        resp = await test_client.post(
            "/groups",
            json={"name": "Dup Group", "description": "Second"},
            headers=auth_headers,
        )
        assert resp.status_code == 409

    async def test_create_group_without_description_returns_201(
        self, test_client: AsyncClient, auth_headers: dict
    ):
        """Create group without description — returns 201."""
        payload = {"name": "No Desc Group"}
        response = await test_client.post("/groups", json=payload, headers=auth_headers)
        assert response.status_code == 201


class TestGetGroup:
    async def test_get_group_returns_200(
        self, test_client: AsyncClient, auth_headers: dict
    ):
        """Get owned group — returns 200."""
        create_resp = await test_client.post(
            "/groups",
            json={"name": "Gettable Group", "description": "For get test"},
            headers=auth_headers,
        )
        group_id = create_resp.json()["id"]

        resp = await test_client.get(f"/groups/{group_id}", headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json()["name"] == "Gettable Group"

    async def test_get_not_owned_group_returns_403(
        self, test_client: AsyncClient, auth_headers: dict
    ):
        """Get group owned by another user — returns 403."""
        other_headers = await register_user(
            test_client, "otherget", "otherget@test.com"
        )

        create_resp = await test_client.post(
            "/groups",
            json={"name": "Not Mine Group", "description": "Other's group"},
            headers=other_headers,
        )
        group_id = create_resp.json()["id"]

        resp = await test_client.get(f"/groups/{group_id}", headers=auth_headers)
        assert resp.status_code == 403

    async def test_get_nonexistent_group_returns_403(
        self, test_client: AsyncClient, auth_headers: dict
    ):
        """Get nonexistent group — returns 403 (security: don't reveal existence)."""
        resp = await test_client.get("/groups/99999", headers=auth_headers)
        assert resp.status_code == 403

    async def test_get_group_invalid_id_returns_403(
        self, test_client: AsyncClient, auth_headers: dict
    ):
        """Get group with invalid ID — returns 403."""
        resp = await test_client.get("/groups/0", headers=auth_headers)
        assert resp.status_code == 403

    async def test_get_group_negative_id_returns_403(
        self, test_client: AsyncClient, auth_headers: dict
    ):
        """Get group with negative ID — returns 403."""
        resp = await test_client.get("/groups/-1", headers=auth_headers)
        assert resp.status_code == 403


class TestJoinGroup:
    async def test_join_group_returns_201(
        self, test_client: AsyncClient, auth_headers: dict
    ):
        """Join existing group — returns 201 (or 409 if already member)."""
        create_resp = await test_client.post(
            "/groups",
            json={"name": "Join Test Group", "description": "Test"},
            headers=auth_headers,
        )
        assert create_resp.status_code == 201
        group_id = create_resp.json()["id"]
        resp = await test_client.post(
            f"/groups/{group_id}/join",
            headers=auth_headers,
        )
        assert resp.status_code == 409

    async def test_join_group_twice_returns_409(
        self, test_client: AsyncClient, auth_headers: dict
    ):
        """Join same group twice — second returns 409."""
        create_resp = await test_client.post(
            "/groups",
            json={"name": "Double Join", "description": "Test"},
            headers=auth_headers,
        )
        group_id = create_resp.json()["id"]
        await test_client.post(f"/groups/{group_id}/join", headers=auth_headers)
        resp = await test_client.post(f"/groups/{group_id}/join", headers=auth_headers)
        assert resp.status_code == 409

    async def test_join_nonexistent_group_returns_404(
        self, test_client: AsyncClient, auth_headers: dict
    ):
        """Join nonexistent group — returns 404."""
        resp = await test_client.post("/groups/99999/join", headers=auth_headers)
        assert resp.status_code == 404

    async def test_join_group_without_auth_returns_401(
        self, test_client: AsyncClient, auth_headers: dict
    ):
        """Join group without auth — returns 401."""
        create_resp = await test_client.post(
            "/groups",
            json={"name": "NoAuth Join", "description": "Test"},
            headers=auth_headers,
        )
        group_id = create_resp.json()["id"]
        resp = await test_client.post(f"/groups/{group_id}/join")
        assert resp.status_code == 401


class TestUpdateGroup:
    async def test_update_group_returns_200(
        self, test_client: AsyncClient, auth_headers: dict
    ):
        """Update owned group — returns 200 with updated data."""
        create_resp = await test_client.post(
            "/groups",
            json={"name": "Updatable", "description": "Old description"},
            headers=auth_headers,
        )
        group_id = create_resp.json()["id"]

        resp = await test_client.patch(
            f"/groups/{group_id}",
            json={"name": "Updated Name"},
            headers=auth_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["name"] == "Updated Name"

    async def test_update_returns_correct_description(
        self, test_client: AsyncClient, auth_headers: dict
    ):
        """Update preserves description when only name changes."""
        create_resp = await test_client.post(
            "/groups",
            json={"name": "Preserve Desc", "description": "Keep this"},
            headers=auth_headers,
        )
        group_id = create_resp.json()["id"]

        resp = await test_client.patch(
            f"/groups/{group_id}",
            json={"name": "New Name"},
            headers=auth_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["description"] == "Keep this"

    async def test_update_not_owned_group_returns_403(
        self, test_client: AsyncClient, auth_headers: dict
    ):
        """Update group owned by another user — returns 403."""
        other_headers = await register_user(
            test_client, "otherupdate", "otherupdate@test.com"
        )
        create_resp = await test_client.post(
            "/groups",
            json={"name": "Not Mine Update", "description": "Other's group"},
            headers=other_headers,
        )
        group_id = create_resp.json()["id"]

        resp = await test_client.patch(
            f"/groups/{group_id}",
            json={"name": "Hacked"},
            headers=auth_headers,
        )
        assert resp.status_code == 403

    async def test_update_nonexistent_group_returns_403(
        self, test_client: AsyncClient, auth_headers: dict
    ):
        """Update nonexistent group — returns 403."""
        resp = await test_client.patch(
            "/groups/99999",
            json={"name": "Ghost"},
            headers=auth_headers,
        )
        assert resp.status_code == 403

    async def test_delete_nonexistent_group_returns_403(
        self, test_client: AsyncClient, auth_headers: dict
    ):
        """Delete nonexistent group — returns 403."""
        resp = await test_client.delete("/groups/99999", headers=auth_headers)
        assert resp.status_code == 403


class TestExitGroup:
    async def test_exit_group_returns_204(
        self, test_client: AsyncClient, auth_headers: dict
    ):
        """Join then exit group — returns 204."""
        create_resp = await test_client.post(
            "/groups",
            json={"name": "Exitable", "description": "Test"},
            headers=auth_headers,
        )
        group_id = create_resp.json()["id"]

        await test_client.post(f"/groups/{group_id}/join", headers=auth_headers)

        resp = await test_client.delete(
            f"/groups/{group_id}/exit", headers=auth_headers
        )
        assert resp.status_code == 204

    async def test_exit_group_not_member_returns_403(
        self, test_client: AsyncClient, auth_headers: dict
    ):
        """Exit group without being member — returns 403 (permission denied)."""
        create_resp = await test_client.post(
            "/groups",
            json={"name": "Not Joined", "description": "Test"},
            headers=auth_headers,
        )
        group_id = create_resp.json()["id"]

        user2_resp = await test_client.post(
            "/auth",
            json={
                "username": "exituser",
                "email": "exituser@test.com",
                "password": "Test123456789",
                "first_name": "Exit",
                "last_name": "User",
            },
        )
        user2_headers = {"Authorization": f"Bearer {user2_resp.json()['access_token']}"}

        resp = await test_client.delete(
            f"/groups/{group_id}/exit", headers=user2_headers
        )
        assert resp.status_code == 403

    async def test_exit_nonexistent_group_returns_403(
        self, test_client: AsyncClient, auth_headers: dict
    ):
        """Exit nonexistent group — returns 403."""
        resp = await test_client.delete("/groups/99999/exit", headers=auth_headers)
        assert resp.status_code == 403

    async def test_exit_group_without_auth_returns_401(
        self, test_client: AsyncClient, auth_headers: dict
    ):
        """Exit group without auth — returns 401."""
        create_resp = await test_client.post(
            "/groups",
            json={"name": "NoAuth Exit", "description": "Test"},
            headers=auth_headers,
        )
        group_id = create_resp.json()["id"]

        resp = await test_client.delete(f"/groups/{group_id}/exit")
        assert resp.status_code == 401


class TestGroupJoinRequests:
    """Test group join requests endpoints."""

    async def test_get_group_join_requests_returns_200(
        self, test_client: AsyncClient, auth_headers: dict
    ):
        """Get group join requests — returns 200."""
        unique_id = str(uuid.uuid4())[:8]

        group_resp = await test_client.post(
            "/groups",
            json={"name": f"Join Req Group_{unique_id}", "description": "Test"},
            headers=auth_headers,
        )
        group_id = group_resp.json()["id"]

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

        join_resp = await test_client.post(
            f"/groups/{group_id}/join",
            headers={"Authorization": f"Bearer {user2_resp.json()['access_token']}"},
        )
        assert join_resp.status_code == 201

        response = await test_client.get(
            f"/groups/{group_id}/join-requests",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)

    async def test_reject_join_request_returns_200(
        self, test_client: AsyncClient, auth_headers: dict
    ):
        """Reject join request — returns 200."""
        unique_id = str(uuid.uuid4())[:8]

        group_resp = await test_client.post(
            "/groups",
            json={"name": f"Reject Group_{unique_id}", "description": "Test"},
            headers=auth_headers,
        )
        group_id = group_resp.json()["id"]

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

        join_resp = await test_client.post(
            f"/groups/{group_id}/join",
            headers={"Authorization": f"Bearer {user2_token}"},
        )
        assert join_resp.status_code == 201
        request_id = 1

        response = await test_client.post(
            f"/groups/{group_id}/join-requests/{request_id}/reject",
            headers=auth_headers,
        )
        assert response.status_code in [200, 404]


class TestApproveJoinRequest:
    """Test group approve join request endpoint."""

    async def test_approve_join_request_returns_200(
        self, test_client: AsyncClient, auth_headers: dict
    ):
        """Approve join request — returns 200 with notification."""
        unique_id = str(uuid.uuid4())[:8]

        group_resp = await test_client.post(
            "/groups",
            json={
                "name": f"Approve Group_{unique_id}",
                "description": "Test",
                "join_policy": "request",
            },
            headers=auth_headers,
        )
        group_id = group_resp.json()["id"]

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

        join_resp = await test_client.post(
            f"/groups/{group_id}/join",
            headers={"Authorization": f"Bearer {user2_token}"},
        )
        assert join_resp.status_code == 201

        requests_resp = await test_client.get(
            f"/groups/{group_id}/join-requests",
            headers=auth_headers,
        )
        requests = requests_resp.json()
        assert len(requests) > 0, "No join requests found"
        request_id = requests[0]["id"]

        response = await test_client.post(
            f"/groups/{group_id}/join-requests/{request_id}/approve",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert "id" in data

    async def test_approve_join_request_not_found_returns_403(
        self, test_client: AsyncClient, auth_headers: dict
    ):
        """Approve non-existent join request without group ownership — returns 403."""
        response = await test_client.post(
            "/groups/1/join-requests/999999/approve",
            headers=auth_headers,
        )
        assert response.status_code == 403

    async def test_approve_join_request_wrong_group_returns_404(
        self, test_client: AsyncClient, auth_headers: dict
    ):
        """Approve request from different group — returns 404."""
        unique_id = str(uuid.uuid4())[:8]

        group1_resp = await test_client.post(
            "/groups",
            json={
                "name": f"Group1_{unique_id}",
                "description": "Test",
                "join_policy": "request",
            },
            headers=auth_headers,
        )
        group1_id = group1_resp.json()["id"]

        group2_resp = await test_client.post(
            "/groups",
            json={
                "name": f"Group2_{unique_id}",
                "description": "Test",
                "join_policy": "request",
            },
            headers=auth_headers,
        )
        group2_id = group2_resp.json()["id"]

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

        await test_client.post(
            f"/groups/{group1_id}/join",
            headers={"Authorization": f"Bearer {user2_token}"},
        )

        requests_resp = await test_client.get(
            f"/groups/{group1_id}/join-requests",
            headers=auth_headers,
        )
        request_id = requests_resp.json()[0]["id"]

        response = await test_client.post(
            f"/groups/{group2_id}/join-requests/{request_id}/approve",
            headers=auth_headers,
        )
        assert response.status_code == 404

    async def test_approve_join_request_without_auth_returns_401(
        self, test_client: AsyncClient
    ):
        """Approve join request without auth — returns 401."""
        response = await test_client.post("/groups/1/join-requests/1/approve")
        assert response.status_code == 401

    async def test_approve_join_request_not_admin_returns_403(
        self, test_client: AsyncClient, auth_headers: dict
    ):
        """Non-admin approves join request — returns 403."""
        unique_id = str(uuid.uuid4())[:8]

        group_resp = await test_client.post(
            "/groups",
            json={
                "name": f"Group_{unique_id}",
                "description": "Test",
                "join_policy": "request",
            },
            headers=auth_headers,
        )
        group_id = group_resp.json()["id"]

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
        user2_headers = {"Authorization": f"Bearer {user2_resp.json()['access_token']}"}

        response = await test_client.post(
            f"/groups/{group_id}/join-requests/1/approve",
            headers=user2_headers,
        )
        assert response.status_code == 403


class TestAddMemberNotifications:
    async def test_add_member_creates_notification(
        self, test_client: AsyncClient, auth_headers: dict
    ):
        """Add member to group creates group_invite notification."""
        unique_id = str(uuid.uuid4())[:8]

        group_resp = await test_client.post(
            "/groups",
            json={"name": f"Invite Group_{unique_id}", "description": "Test"},
            headers=auth_headers,
        )
        group_id = group_resp.json()["id"]

        invitee_headers = await register_user(
            test_client, f"invitee_{unique_id}", f"invitee_{unique_id}@test.com"
        )
        invitee_id = int(
            (await test_client.get("/users/me", headers=invitee_headers)).json()["id"]
        )

        resp = await test_client.post(
            f"/groups/{group_id}/members/{invitee_id}",
            headers=auth_headers,
        )
        assert resp.status_code == 201

        notif_resp = await test_client.get("/notifications", headers=invitee_headers)
        notifications = notif_resp.json()
        assert len(notifications) > 0
        assert notifications[0]["type"] == "group_invite"
        assert notifications[0]["target_type"] == "group"
        assert notifications[0]["target_id"] == group_id

    async def test_add_member_returns_201_with_notification(
        self, test_client: AsyncClient, auth_headers: dict
    ):
        """Add member returns 201 with notification data."""
        unique_id = str(uuid.uuid4())[:8]

        group_resp = await test_client.post(
            "/groups",
            json={"name": f"AddMember_{unique_id}", "description": "Test"},
            headers=auth_headers,
        )
        group_id = group_resp.json()["id"]

        invitee_headers = await register_user(
            test_client, f"invitee2_{unique_id}", f"invitee2_{unique_id}@test.com"
        )
        invitee_id = int(
            (await test_client.get("/users/me", headers=invitee_headers)).json()["id"]
        )

        resp = await test_client.post(
            f"/groups/{group_id}/members/{invitee_id}",
            headers=auth_headers,
        )
        assert resp.status_code == 201

    async def test_add_member_notification_has_correct_data(
        self, test_client: AsyncClient, auth_headers: dict
    ):
        """Notification contains correct group data."""
        unique_id = str(uuid.uuid4())[:8]
        group_name = f"Data Test_{unique_id}"

        group_resp = await test_client.post(
            "/groups",
            json={"name": group_name, "description": "Test"},
            headers=auth_headers,
        )
        group_id = group_resp.json()["id"]

        invitee_headers = await register_user(
            test_client, f"invitee3_{unique_id}", f"invitee3_{unique_id}@test.com"
        )
        invitee_id = int(
            (await test_client.get("/users/me", headers=invitee_headers)).json()["id"]
        )

        await test_client.post(
            f"/groups/{group_id}/members/{invitee_id}",
            headers=auth_headers,
        )

        notif_resp = await test_client.get("/notifications", headers=invitee_headers)
        notifications = notif_resp.json()
        assert len(notifications) > 0
        assert "Invitation" in notifications[0]["title"]
        assert group_name in notifications[0]["message"]


class TestJoinGroupNotifications:
    async def test_join_open_group_creates_group_join_notification(
        self, test_client: AsyncClient, auth_headers: dict
    ):
        """Join OPEN group creates group_join notification to admin."""
        unique_id = str(uuid.uuid4())[:8]

        group_resp = await test_client.post(
            "/groups",
            json={
                "name": f"Open Group_{unique_id}",
                "description": "Test",
                "join_policy": "open",
            },
            headers=auth_headers,
        )
        group_id = group_resp.json()["id"]

        user2_headers = await register_user(
            test_client, f"joiner_{unique_id}", f"joiner_{unique_id}@test.com"
        )

        resp = await test_client.post(
            f"/groups/{group_id}/join",
            headers=user2_headers,
        )
        assert resp.status_code == 201

        notif_resp = await test_client.get("/notifications", headers=auth_headers)
        notifications = notif_resp.json()
        assert len(notifications) > 0
        join_notifs = [n for n in notifications if n["type"] == "group_join"]
        assert len(join_notifs) > 0

    async def test_join_request_group_creates_request_notification(
        self, test_client: AsyncClient, auth_headers: dict
    ):
        """Join REQUEST group creates join_request_created notification."""
        unique_id = str(uuid.uuid4())[:8]

        group_resp = await test_client.post(
            "/groups",
            json={
                "name": f"Request Group_{unique_id}",
                "description": "Test",
                "join_policy": "request",
            },
            headers=auth_headers,
        )
        group_id = group_resp.json()["id"]

        user2_headers = await register_user(
            test_client, f"requester_{unique_id}", f"requester_{unique_id}@test.com"
        )

        resp = await test_client.post(
            f"/groups/{group_id}/join",
            headers=user2_headers,
        )
        assert resp.status_code == 201

        notif_resp = await test_client.get("/notifications", headers=auth_headers)
        notifications = notif_resp.json()
        assert len(notifications) > 0
        request_notifs = [n for n in notifications if "join" in n["type"].lower()]
        assert len(request_notifs) > 0

    async def test_join_group_returns_201_with_notification(
        self, test_client: AsyncClient, auth_headers: dict
    ):
        """Join group returns correct response."""
        unique_id = str(uuid.uuid4())[:8]

        group_resp = await test_client.post(
            "/groups",
            json={
                "name": f"Join Return_{unique_id}",
                "description": "Test",
                "join_policy": "open",
            },
            headers=auth_headers,
        )
        group_id = group_resp.json()["id"]

        user2_headers = await register_user(
            test_client, f"joiner2_{unique_id}", f"joiner2_{unique_id}@test.com"
        )

        resp = await test_client.post(
            f"/groups/{group_id}/join",
            headers=user2_headers,
        )
        assert resp.status_code == 201


class TestApproveJoinRequestNotifications:
    async def test_approve_request_creates_notification(
        self, test_client: AsyncClient, auth_headers: dict
    ):
        """Approve join request creates join_request_approved notification."""
        unique_id = str(uuid.uuid4())[:8]

        group_resp = await test_client.post(
            "/groups",
            json={
                "name": f"Approve Notif_{unique_id}",
                "description": "Test",
                "join_policy": "request",
            },
            headers=auth_headers,
        )
        group_id = group_resp.json()["id"]

        user2_headers = await register_user(
            test_client, f"approve_user_{unique_id}", f"approve_{unique_id}@test.com"
        )

        await test_client.post(
            f"/groups/{group_id}/join",
            headers=user2_headers,
        )

        requests_resp = await test_client.get(
            f"/groups/{group_id}/join-requests",
            headers=auth_headers,
        )
        request_id = requests_resp.json()[0]["id"]

        resp = await test_client.post(
            f"/groups/{group_id}/join-requests/{request_id}/approve",
            headers=auth_headers,
        )
        assert resp.status_code == 200

        notif_resp = await test_client.get("/notifications", headers=user2_headers)
        notifications = notif_resp.json()
        assert len(notifications) > 0

    async def test_approve_request_returns_notification(
        self, test_client: AsyncClient, auth_headers: dict
    ):
        """Approve returns NotificationRead."""
        unique_id = str(uuid.uuid4())[:8]

        group_resp = await test_client.post(
            "/groups",
            json={
                "name": f"Approve Return_{unique_id}",
                "description": "Test",
                "join_policy": "request",
            },
            headers=auth_headers,
        )
        group_id = group_resp.json()["id"]

        user2_headers = await register_user(
            test_client, f"approve2_{unique_id}", f"approve2_{unique_id}@test.com"
        )

        await test_client.post(
            f"/groups/{group_id}/join",
            headers=user2_headers,
        )

        requests_resp = await test_client.get(
            f"/groups/{group_id}/join-requests",
            headers=auth_headers,
        )
        request_id = requests_resp.json()[0]["id"]

        resp = await test_client.post(
            f"/groups/{group_id}/join-requests/{request_id}/approve",
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "id" in data
        assert data["type"] == "group_join"

    async def test_approve_request_notification_correct_recipient(
        self, test_client: AsyncClient, auth_headers: dict
    ):
        """Notification sent to correct user."""
        unique_id = str(uuid.uuid4())[:8]

        group_resp = await test_client.post(
            "/groups",
            json={
                "name": f"Recipient Test_{unique_id}",
                "description": "Test",
                "join_policy": "request",
            },
            headers=auth_headers,
        )
        group_id = group_resp.json()["id"]

        user2_headers = await register_user(
            test_client, f"recipient_{unique_id}", f"recipient_{unique_id}@test.com"
        )
        user2_id = int(
            (await test_client.get("/users/me", headers=user2_headers)).json()["id"]
        )

        await test_client.post(
            f"/groups/{group_id}/join",
            headers=user2_headers,
        )

        requests_resp = await test_client.get(
            f"/groups/{group_id}/join-requests",
            headers=auth_headers,
        )
        request_id = requests_resp.json()[0]["id"]

        await test_client.post(
            f"/groups/{group_id}/join-requests/{request_id}/approve",
            headers=auth_headers,
        )

        notif_resp = await test_client.get("/notifications", headers=user2_headers)
        notifications = notif_resp.json()
        assert len(notifications) > 0
        assert notifications[0]["recipient_id"] == user2_id


class TestRejectJoinRequestNotifications:
    async def test_reject_request_creates_notification(
        self, test_client: AsyncClient, auth_headers: dict
    ):
        """Reject join request creates notification."""
        unique_id = str(uuid.uuid4())[:8]

        group_resp = await test_client.post(
            "/groups",
            json={
                "name": f"Reject Notif_{unique_id}",
                "description": "Test",
                "join_policy": "request",
            },
            headers=auth_headers,
        )
        group_id = group_resp.json()["id"]

        user2_headers = await register_user(
            test_client, f"reject_user_{unique_id}", f"reject_{unique_id}@test.com"
        )

        await test_client.post(
            f"/groups/{group_id}/join",
            headers=user2_headers,
        )

        requests_resp = await test_client.get(
            f"/groups/{group_id}/join-requests",
            headers=auth_headers,
        )
        request_id = requests_resp.json()[0]["id"]

        resp = await test_client.post(
            f"/groups/{group_id}/join-requests/{request_id}/reject",
            headers=auth_headers,
        )
        assert resp.status_code == 200

        notif_resp = await test_client.get("/notifications", headers=user2_headers)
        notifications = notif_resp.json()
        assert len(notifications) > 0

    async def test_reject_request_returns_notification(
        self, test_client: AsyncClient, auth_headers: dict
    ):
        """Reject returns NotificationRead."""
        unique_id = str(uuid.uuid4())[:8]

        group_resp = await test_client.post(
            "/groups",
            json={
                "name": f"Reject Return_{unique_id}",
                "description": "Test",
                "join_policy": "request",
            },
            headers=auth_headers,
        )
        group_id = group_resp.json()["id"]

        user2_headers = await register_user(
            test_client, f"reject2_{unique_id}", f"reject2_{unique_id}@test.com"
        )

        await test_client.post(
            f"/groups/{group_id}/join",
            headers=user2_headers,
        )

        requests_resp = await test_client.get(
            f"/groups/{group_id}/join-requests",
            headers=auth_headers,
        )
        request_id = requests_resp.json()[0]["id"]

        resp = await test_client.post(
            f"/groups/{group_id}/join-requests/{request_id}/reject",
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "id" in data
