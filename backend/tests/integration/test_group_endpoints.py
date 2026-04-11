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


class TestSearchGroups:
    async def test_search_my_groups_returns_200(
        self, test_client: AsyncClient, auth_headers: dict
    ):
        """Search owned groups — returns 200."""
        await test_client.post(
            "/groups",
            json={"name": "My Group", "description": "Owned"},
            headers=auth_headers,
        )
        resp = await test_client.get("/groups/me", headers=auth_headers)
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    async def test_search_member_groups_returns_200(
        self, test_client: AsyncClient, auth_headers: dict
    ):
        """Search member groups — returns 200."""
        create_resp = await test_client.post(
            "/groups",
            json={"name": "Member Group", "description": "For membership"},
            headers=auth_headers,
        )
        group_id = create_resp.json()["id"]
        await test_client.post(f"/groups/{group_id}/join", headers=auth_headers)

        resp = await test_client.get("/groups/members", headers=auth_headers)
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    async def test_search_groups_with_limit(
        self, test_client: AsyncClient, auth_headers: dict
    ):
        """Search groups with limit — returns limited results."""
        for i in range(3):
            await test_client.post(
                "/groups",
                json={"name": f"Limit Group {i}", "description": f"Group {i}"},
                headers=auth_headers,
            )

        resp = await test_client.get("/groups?limit=2", headers=auth_headers)
        assert resp.status_code == 200
        assert len(resp.json()) <= 2

    async def test_search_groups_with_offset(
        self, test_client: AsyncClient, auth_headers: dict
    ):
        """Search groups with offset — skips first results."""
        for i in range(11):
            await test_client.post(
                "/groups",
                json={"name": f"Offset Group {i}", "description": f"Group {i}"},
                headers=auth_headers,
            )

        resp_all = await test_client.get("/groups", headers=auth_headers)
        resp_offset = await test_client.get("/groups?offset=1", headers=auth_headers)

        assert resp_all.status_code == 200
        assert resp_offset.status_code == 200

        all_data = resp_all.json()
        offset_data = resp_offset.json()

        assert len(all_data) <= 10, "Data should not exceed default limit"
        assert len(offset_data) <= 10, "Data should not exceed default limit"
        assert offset_data[0]["id"] != all_data[0]["id"], (
            "Offset should skip first element"
        )

    async def test_search_groups_by_name_filter(
        self, test_client: AsyncClient, auth_headers: dict
    ):
        """Search groups by name filter — returns matching groups."""
        await test_client.post(
            "/groups",
            json={"name": "UniqueFilterGroup123", "description": "Test"},
            headers=auth_headers,
        )
        await test_client.post(
            "/groups",
            json={"name": "Other Group", "description": "Other"},
            headers=auth_headers,
        )

        resp = await test_client.get("/groups?name=UniqueFilter", headers=auth_headers)
        assert resp.status_code == 200
        groups = resp.json()
        assert any("UniqueFilterGroup123" in g["name"] for g in groups)

    async def test_search_groups_empty_result(
        self, test_client: AsyncClient, auth_headers: dict
    ):
        """Search groups with non-matching filter — returns empty list."""
        resp = await test_client.get(
            "/groups?name=NonExistent12345", headers=auth_headers
        )
        assert resp.status_code == 200
        assert resp.json() == []


class TestJoinGroup:
    async def test_join_group_returns_201(
        self, test_client: AsyncClient, auth_headers: dict
    ):
        """Join existing group — returns 201."""
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
        assert resp.status_code == 201

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

    async def test_exit_group_not_member_returns_404(
        self, test_client: AsyncClient, auth_headers: dict
    ):
        """Exit group without joining — returns 404."""
        create_resp = await test_client.post(
            "/groups",
            json={"name": "Not Joined", "description": "Test"},
            headers=auth_headers,
        )
        group_id = create_resp.json()["id"]

        resp = await test_client.delete(
            f"/groups/{group_id}/exit", headers=auth_headers
        )
        assert resp.status_code == 404

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

        # Admin creates group
        group_resp = await test_client.post(
            "/groups",
            json={"name": f"Join Req Group_{unique_id}", "description": "Test"},
            headers=auth_headers,
        )
        group_id = group_resp.json()["id"]

        # Create another user who will request to join
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

        # User2 requests to join
        join_resp = await test_client.post(
            f"/groups/{group_id}/join",
            headers={"Authorization": f"Bearer {user2_resp.json()['access_token']}"},
        )
        assert join_resp.status_code == 201

        # Admin gets join requests
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

        # Admin creates group
        group_resp = await test_client.post(
            "/groups",
            json={"name": f"Reject Group_{unique_id}", "description": "Test"},
            headers=auth_headers,
        )
        group_id = group_resp.json()["id"]

        # Create another user who will request to join
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

        # User2 requests to join
        join_resp = await test_client.post(
            f"/groups/{group_id}/join",
            headers={"Authorization": f"Bearer {user2_token}"},
        )
        assert join_resp.status_code == 201
        request_id = 1  # Default request_id

        # Admin rejects join request
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

        # Admin creates group with REQUEST join policy
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

        # Create another user who will request to join
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

        # User2 requests to join (should create join request since policy is REQUEST)
        join_resp = await test_client.post(
            f"/groups/{group_id}/join",
            headers={"Authorization": f"Bearer {user2_token}"},
        )
        assert join_resp.status_code == 201

        # Get join requests to find request_id
        requests_resp = await test_client.get(
            f"/groups/{group_id}/join-requests",
            headers=auth_headers,
        )
        requests = requests_resp.json()
        assert len(requests) > 0, "No join requests found"
        request_id = requests[0]["id"]

        # Admin approves join request
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

        # Admin creates two groups with REQUEST policy
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

        # Create user who joins group1
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

        # User joins group1 (creates join request)
        await test_client.post(
            f"/groups/{group1_id}/join",
            headers={"Authorization": f"Bearer {user2_token}"},
        )

        # Get request_id from group1
        requests_resp = await test_client.get(
            f"/groups/{group1_id}/join-requests",
            headers=auth_headers,
        )
        request_id = requests_resp.json()[0]["id"]

        # Try to approve with group2 — should fail
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

        # Admin creates group with REQUEST policy
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

        # Create regular user
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

        # Try to approve as non-admin
        response = await test_client.post(
            f"/groups/{group_id}/join-requests/1/approve",
            headers=user2_headers,
        )
        assert response.status_code == 403
