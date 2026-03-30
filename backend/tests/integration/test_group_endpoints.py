from httpx import AsyncClient


async def _register_user(client: AsyncClient, username: str, email: str) -> dict:
    """Register user (or login if exists) and return auth headers."""
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
    return {"Authorization": f"Bearer {token}"}


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
        other_headers = await _register_user(
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
        other_headers = await _register_user(
            test_client, "otherupdate", "otherupdate@test.com"
        )
        create_resp = await test_client.post(
            "/groups",
            json={"name": "Other's Group", "description": "Not mine"},
            headers=other_headers,
        )
        group_id = create_resp.json()["id"]

        resp = await test_client.patch(
            f"/groups/{group_id}",
            json={"name": "Hacked"},
            headers=auth_headers,
        )
        assert resp.status_code == 403


class TestDeleteGroup:
    async def test_delete_group_returns_204(
        self, test_client: AsyncClient, auth_headers: dict
    ):
        """Delete owned group — returns 204."""
        create_resp = await test_client.post(
            "/groups",
            json={"name": "Deletable", "description": "Will be deleted"},
            headers=auth_headers,
        )
        group_id = create_resp.json()["id"]

        resp = await test_client.delete(f"/groups/{group_id}", headers=auth_headers)
        assert resp.status_code == 204

    async def test_deleted_group_not_in_search(
        self, test_client: AsyncClient, auth_headers: dict
    ):
        """Deleted group should not appear in search results."""
        create_resp = await test_client.post(
            "/groups",
            json={"name": "Will Disappear", "description": "Gone"},
            headers=auth_headers,
        )
        group_id = create_resp.json()["id"]
        await test_client.delete(f"/groups/{group_id}", headers=auth_headers)

        groups_resp = await test_client.get("/groups", headers=auth_headers)
        group_ids = [g["id"] for g in groups_resp.json()]
        assert group_id not in group_ids

    async def test_delete_not_owned_group_returns_403(
        self, test_client: AsyncClient, auth_headers: dict
    ):
        """Delete group owned by another user — returns 403."""
        other_headers = await _register_user(
            test_client, "otherdelete", "otherdelete@test.com"
        )
        create_resp = await test_client.post(
            "/groups",
            json={"name": "Protected Group", "description": "Cannot delete"},
            headers=other_headers,
        )
        group_id = create_resp.json()["id"]

        resp = await test_client.delete(f"/groups/{group_id}", headers=auth_headers)
        assert resp.status_code == 403


class TestMemberManagement:
    async def test_add_member_returns_201(
        self, test_client: AsyncClient, auth_headers: dict
    ):
        """Add member to group — returns 201."""
        create_resp = await test_client.post(
            "/groups",
            json={"name": "Add Member Group", "description": "For add test"},
            headers=auth_headers,
        )
        group_id = create_resp.json()["id"]

        await test_client.post(
            "/auth",
            json={
                "username": "member1",
                "email": "member1@test.com",
                "password": "Password123",
                "first_name": "Member",
                "last_name": "One",
            },
        )
        users_resp = await test_client.get(
            "/users?username=member1", headers=auth_headers
        )
        member_id = users_resp.json()[0]["id"]

        resp = await test_client.post(
            f"/groups/{group_id}/members/{member_id}",
            headers=auth_headers,
        )
        assert resp.status_code == 201

    async def test_remove_member_returns_204(
        self, test_client: AsyncClient, auth_headers: dict
    ):
        """Remove member from group — returns 204."""
        create_resp = await test_client.post(
            "/groups",
            json={"name": "Remove Member Group", "description": "For remove test"},
            headers=auth_headers,
        )
        group_id = create_resp.json()["id"]

        await test_client.post(
            "/auth",
            json={
                "username": "member2",
                "email": "member2@test.com",
                "password": "Password123",
                "first_name": "Member",
                "last_name": "Two",
            },
        )
        users_resp = await test_client.get(
            "/users?username=member2", headers=auth_headers
        )
        member_id = users_resp.json()[0]["id"]

        await test_client.post(
            f"/groups/{group_id}/members/{member_id}",
            headers=auth_headers,
        )

        resp = await test_client.delete(
            f"/groups/{group_id}/members/{member_id}",
            headers=auth_headers,
        )
        assert resp.status_code == 204

    async def test_add_member_to_not_owned_group_returns_403(
        self, test_client: AsyncClient, auth_headers: dict
    ):
        """Add member to group owned by another user — returns 403."""
        other_headers = await _register_user(
            test_client, "othermember", "othermember@test.com"
        )
        create_resp = await test_client.post(
            "/groups",
            json={"name": "Protected Members", "description": "Not mine"},
            headers=other_headers,
        )
        group_id = create_resp.json()["id"]

        await test_client.post(
            "/auth",
            json={
                "username": "newmember",
                "email": "newmember@test.com",
                "password": "Password123",
                "first_name": "New",
                "last_name": "Member",
            },
        )
        users_resp = await test_client.get(
            "/users?username=newmember", headers=auth_headers
        )
        member_id = users_resp.json()[0]["id"]

        resp = await test_client.post(
            f"/groups/{group_id}/members/{member_id}",
            headers=auth_headers,
        )
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
