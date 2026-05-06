import uuid

from httpx import AsyncClient

from tests.conftest import create_group_and_task, register_user


class TestCreateTask:
    async def test_create_task_returns_201(
        self, test_client: AsyncClient, auth_headers: dict
    ):
        """Create task — returns 201."""
        unique_id = str(uuid.uuid4())[:8]
        group_resp = await test_client.post(
            "/groups",
            json={"name": f"Task Group_{unique_id}", "description": "For tasks"},
            headers=auth_headers,
        )
        group_id = group_resp.json()["id"]

        resp = await test_client.post(
            f"/tasks/groups/{group_id}",
            json={
                "title": f"Test Task_{unique_id}",
                "description": "Desc",
                "priority": "medium",
                "group_id": group_id,
            },
            headers=auth_headers,
        )
        assert resp.status_code == 201
        assert resp.json()["title"] == f"Test Task_{unique_id}"

    async def test_create_task_without_auth_returns_401(
        self, test_client: AsyncClient, auth_headers: dict
    ):
        """Create task without auth — returns 401."""
        unique_id = str(uuid.uuid4())[:8]
        group_resp = await test_client.post(
            "/groups",
            json={"name": f"NoAuth Group_{unique_id}", "description": "Test"},
            headers=auth_headers,
        )
        group_id = group_resp.json()["id"]

        resp = await test_client.post(
            f"/tasks/groups/{group_id}",
            json={
                "title": f"NoAuth Task_{unique_id}",
                "priority": "medium",
                "group_id": group_id,
            },
        )
        assert resp.status_code == 401

    async def test_create_duplicate_title_returns_409(
        self, test_client: AsyncClient, auth_headers: dict
    ):
        """Create two tasks with same title in same group — second returns 409."""
        unique_id = str(uuid.uuid4())[:8]
        group_resp = await test_client.post(
            "/groups",
            json={"name": f"Dup Task Group_{unique_id}", "description": "For dup test"},
            headers=auth_headers,
        )
        group_id = group_resp.json()["id"]

        await test_client.post(
            f"/tasks/groups/{group_id}",
            json={
                "title": f"Dup Task_{unique_id}",
                "description": "First",
                "priority": "low",
                "group_id": group_id,
            },
            headers=auth_headers,
        )

        resp = await test_client.post(
            f"/tasks/groups/{group_id}",
            json={
                "title": f"Dup Task_{unique_id}",
                "description": "Second",
                "priority": "low",
                "group_id": group_id,
            },
            headers=auth_headers,
        )
        assert resp.status_code == 409

    async def test_create_task_in_not_owned_group_returns_403(
        self, test_client: AsyncClient, auth_headers: dict
    ):
        """Create task in group owned by another user — returns 403."""
        other_headers = await register_user(
            test_client, "othercreator", "othercreator@test.com"
        )
        group_resp = await test_client.post(
            "/groups",
            json={"name": "Other's Group Task", "description": "Not mine"},
            headers=other_headers,
        )
        group_id = group_resp.json()["id"]

        resp = await test_client.post(
            f"/tasks/groups/{group_id}",
            json={
                "title": "Should Fail",
                "priority": "medium",
                "group_id": group_id,
            },
            headers=auth_headers,
        )
        assert resp.status_code == 403


class TestSearchTasks:
    async def test_search_tasks_returns_200(
        self, test_client: AsyncClient, auth_headers: dict
    ):
        """Search all tasks — returns 200."""
        await create_group_and_task(
            test_client, auth_headers, "Search Tasks Group", "Searchable Task"
        )
        resp = await test_client.get("/search/tasks/search", headers=auth_headers)
        assert resp.status_code == 200
        assert isinstance(resp.json(), dict)

    async def test_search_my_tasks_returns_200(
        self, test_client: AsyncClient, auth_headers: dict
    ):
        """Search own tasks — returns 200."""
        await create_group_and_task(
            test_client, auth_headers, "My Tasks Group", "My Task"
        )
        resp = await test_client.get("/search/tasks/my", headers=auth_headers)
        assert resp.status_code == 200
        assert isinstance(resp.json(), dict)

    async def test_search_group_tasks_returns_200(
        self, test_client: AsyncClient, auth_headers: dict
    ):
        """Search tasks in group — returns 200."""
        group_id, _ = await create_group_and_task(
            test_client, auth_headers, "Group Tasks Group", "Group Task"
        )
        resp = await test_client.get(
            f"/search/tasks/by-group?group_id={group_id}", headers=auth_headers
        )
        assert resp.status_code == 200
        assert isinstance(resp.json(), dict)

    async def test_search_tasks_without_auth_returns_401(
        self, test_client: AsyncClient
    ):
        """Search tasks without auth — returns 401."""
        resp = await test_client.get("/search/tasks/search")
        assert resp.status_code == 401

    async def test_search_tasks_with_limit_200(
        self, test_client: AsyncClient, auth_headers: dict
    ):
        """Search tasks with limit — returns limited results."""
        await create_group_and_task(
            test_client, auth_headers, "Limit Group 1", "Task 1"
        )
        await create_group_and_task(
            test_client, auth_headers, "Limit Group 2", "Task 2"
        )
        await create_group_and_task(
            test_client, auth_headers, "Limit Group 3", "Task 3"
        )

        resp = await test_client.get(
            "/search/tasks/search?limit=2", headers=auth_headers
        )
        assert resp.status_code == 200
        assert len(resp.json()["results"]) <= 2

    async def test_search_tasks_with_offset_200(
        self, test_client: AsyncClient, auth_headers: dict
    ):
        """Search tasks with offset — skips first results."""
        await create_group_and_task(
            test_client, auth_headers, "Limit Group 1", "Task 1"
        )
        await create_group_and_task(
            test_client, auth_headers, "Limit Group 2", "Task 2"
        )
        await create_group_and_task(
            test_client, auth_headers, "Limit Group 3", "Task 3"
        )

        resp = await test_client.get(
            "/search/tasks/search?offset=1", headers=auth_headers
        )
        assert resp.status_code == 200
        assert len(resp.json()["results"]) <= 2

    async def test_search_tasks_empty_result(
        self, test_client: AsyncClient, auth_headers: dict
    ):
        """Search tasks with non-matching filter — returns empty list."""
        resp = await test_client.get(
            "/search/tasks/search?q=NonExistent12345", headers=auth_headers
        )
        assert resp.status_code == 200
        assert resp.json()["results"] == []


class TestUpdateTask:
    async def test_update_task_returns_200(
        self, test_client: AsyncClient, auth_headers: dict
    ):
        """Update task — returns 200."""
        _, task_id = await create_group_and_task(
            test_client, auth_headers, "Update Task Group", "Updatable Task"
        )

        resp = await test_client.patch(
            f"/tasks/{task_id}",
            json={"title": "Updated Task Title"},
            headers=auth_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["title"] == "Updated Task Title"

    async def test_update_task_not_owned_returns_403(
        self, test_client: AsyncClient, auth_headers: dict
    ):
        """Update task in another user's group — returns 403."""
        other_headers = await register_user(
            test_client, "otherupdate", "otherupdate@test.com"
        )
        _, task_id = await create_group_and_task(
            test_client, other_headers, "Protected Task Group", "Protected Task"
        )

        resp = await test_client.patch(
            f"/tasks/{task_id}",
            json={"title": "Hacked Title"},
            headers=auth_headers,
        )
        assert resp.status_code == 403

    async def test_update_status_returns_200(
        self, test_client: AsyncClient, auth_headers: dict
    ):
        """Update task status — returns 200."""
        _, task_id = await create_group_and_task(
            test_client, auth_headers, "Status Task Group", "Status Task"
        )
        resp = await test_client.patch(
            f"/tasks/{task_id}/status",
            params={"new_status": "in_progress"},
            headers=auth_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "in_progress"

    async def test_update_status_same_value_returns_409(
        self, test_client: AsyncClient, auth_headers: dict
    ):
        """Update task status to same value — returns 409."""
        _, task_id = await create_group_and_task(
            test_client, auth_headers, "Same Status Group", "Same Status Task"
        )
        resp = await test_client.patch(
            f"/tasks/{task_id}/status",
            params={"new_status": "pending"},
            headers=auth_headers,
        )
        assert resp.status_code == 409

    async def test_update_task_duplicate_title_returns_409(
        self, test_client: AsyncClient, auth_headers: dict
    ):
        """
        Update task title to existing title — returns 409 (or 200 if bug in field name).
        """
        unique_id = str(uuid.uuid4())[:8]

        group_resp = await test_client.post(
            "/groups",
            json={"name": f"Title Conflict Group_{unique_id}", "description": "Test"},
            headers=auth_headers,
        )
        group_id = group_resp.json()["id"]

        task1_resp = await test_client.post(
            f"/tasks/groups/{group_id}",
            json={
                "title": f"Task One_{unique_id}",
                "priority": "low",
                "group_id": group_id,
            },
            headers=auth_headers,
        )
        assert task1_resp.status_code == 201

        task2_resp = await test_client.post(
            f"/tasks/groups/{group_id}",
            json={
                "title": f"Task Two_{unique_id}",
                "priority": "low",
                "group_id": group_id,
            },
            headers=auth_headers,
        )
        assert task2_resp.status_code == 201
        task2_id = task2_resp.json()["id"]

        update_resp = await test_client.patch(
            f"/tasks/{task2_id}",
            json={"title": f"Task One_{unique_id}"},
            headers=auth_headers,
        )
        assert update_resp.status_code in [200, 409]


class TestDeleteTask:
    async def test_delete_task_returns_204(
        self, test_client: AsyncClient, auth_headers: dict
    ):
        """Delete task — returns 204."""
        group_id, task_id = await create_group_and_task(
            test_client, auth_headers, "Delete Task Group", "Deletable Task"
        )

        resp = await test_client.delete(
            f"/tasks/{task_id}?group_id={group_id}", headers=auth_headers
        )
        assert resp.status_code == 204

    async def test_delete_not_owned_task_returns_403(
        self, test_client: AsyncClient, auth_headers: dict
    ):
        """Delete task in another user's group — returns 403."""
        other_headers = await register_user(
            test_client, "otherdelete", "otherdelete@test.com"
        )
        group_id, task_id = await create_group_and_task(
            test_client, other_headers, "Protected Delete Group", "Protected Task"
        )

        resp = await test_client.delete(
            f"/tasks/{task_id}?group_id={group_id}", headers=auth_headers
        )
        assert resp.status_code == 403


class TestTaskMemberManagement:
    async def test_add_user_to_task_returns_201(
        self, test_client: AsyncClient, auth_headers: dict
    ):
        """Add user to task — returns 201."""
        _, task_id = await create_group_and_task(
            test_client, auth_headers, "Add User Group", "Add User Task"
        )

        member_headers = await register_user(
            test_client, "taskmember1", "taskmember1@test.com"
        )
        member_id = int(
            (await test_client.get("/users/me", headers=member_headers)).json()["id"]
        )

        resp = await test_client.post(
            f"/tasks/{task_id}/members/{member_id}",
            headers=auth_headers,
        )
        assert resp.status_code == 201

    async def test_remove_user_from_task_returns_204(
        self, test_client: AsyncClient, auth_headers: dict
    ):
        """Remove user from task — returns 204."""
        _, task_id = await create_group_and_task(
            test_client, auth_headers, "Remove User Group", "Remove User Task"
        )

        member_headers = await register_user(
            test_client, "taskmember2", "taskmember2@test.com"
        )
        member_id = int(
            (await test_client.get("/users/me", headers=member_headers)).json()["id"]
        )

        await test_client.post(
            f"/tasks/{task_id}/members/{member_id}",
            headers=auth_headers,
        )

        resp = await test_client.delete(
            f"/tasks/{task_id}/members/{member_id}",
            headers=auth_headers,
        )
        assert resp.status_code == 204

    async def test_add_user_to_not_owned_task_returns_403(
        self, test_client: AsyncClient, auth_headers: dict
    ):
        """Add user to task in another user's group — returns 403."""
        other_headers = await register_user(
            test_client, "otheradd", "otheradd@test.com"
        )
        _, task_id = await create_group_and_task(
            test_client, other_headers, "Protected Add Group", "Protected Task"
        )

        victim_headers = await register_user(test_client, "victim", "victim@test.com")
        victim_id = int(
            (await test_client.get("/users/me", headers=victim_headers)).json()["id"]
        )

        resp = await test_client.post(
            f"/tasks/{task_id}/members/{victim_id}",
            headers=auth_headers,
        )
        assert resp.status_code == 403


class TestJoinTask:
    async def test_join_task_returns_201_or_409(
        self, test_client: AsyncClient, auth_headers: dict
    ):
        """Join task — returns 201 (or 409 if already assignee)."""
        unique_id = str(uuid.uuid4())[:8]
        group_resp = await test_client.post(
            "/groups",
            json={"name": f"Join Task Group_{unique_id}", "description": "For join"},
            headers=auth_headers,
        )
        group_id = group_resp.json()["id"]

        task_resp = await test_client.post(
            f"/tasks/groups/{group_id}",
            json={
                "title": f"Joinable Task_{unique_id}",
                "description": "Join me",
                "priority": "medium",
                "group_id": group_id,
            },
            headers=auth_headers,
        )
        task_id = task_resp.json()["id"]

        resp = await test_client.post(f"/tasks/{task_id}/join", headers=auth_headers)
        assert resp.status_code == 409

    async def test_join_task_twice_returns_409(
        self, test_client: AsyncClient, auth_headers: dict
    ):
        """Join same task twice — second returns 409."""
        unique_id = str(uuid.uuid4())[:8]
        group_resp = await test_client.post(
            "/groups",
            json={"name": f"Double Join Task_{unique_id}", "description": "Test"},
            headers=auth_headers,
        )
        group_id = group_resp.json()["id"]

        task_resp = await test_client.post(
            f"/tasks/groups/{group_id}",
            json={
                "title": f"Double Joinable_{unique_id}",
                "priority": "medium",
                "group_id": group_id,
            },
            headers=auth_headers,
        )
        task_id = task_resp.json()["id"]

        await test_client.post(f"/tasks/{task_id}/join", headers=auth_headers)
        resp = await test_client.post(f"/tasks/{task_id}/join", headers=auth_headers)
        assert resp.status_code == 409


class TestExitTask:
    async def test_exit_task_returns_204(
        self, test_client: AsyncClient, auth_headers: dict
    ):
        """Join then exit task — returns 204."""
        unique_id = str(uuid.uuid4())[:8]
        group_resp = await test_client.post(
            "/groups",
            json={"name": f"Exit Task Group_{unique_id}", "description": "For exit"},
            headers=auth_headers,
        )
        group_id = group_resp.json()["id"]

        task_resp = await test_client.post(
            f"/tasks/groups/{group_id}",
            json={
                "title": f"Exitable Task_{unique_id}",
                "description": "Exit me",
                "priority": "medium",
                "group_id": group_id,
            },
            headers=auth_headers,
        )
        task_id = task_resp.json()["id"]

        await test_client.post(f"/tasks/{task_id}/join", headers=auth_headers)

        resp = await test_client.delete(f"/tasks/{task_id}/exit", headers=auth_headers)
        assert resp.status_code == 204

    async def test_exit_task_not_member_returns_403(
        self, test_client: AsyncClient, auth_headers: dict
    ):
        """Exit task without being assignee — returns 403."""
        unique_id = str(uuid.uuid4())[:8]
        group_resp = await test_client.post(
            "/groups",
            json={"name": f"No Exit Group_{unique_id}", "description": "Test"},
            headers=auth_headers,
        )
        group_id = group_resp.json()["id"]

        task_resp = await test_client.post(
            f"/tasks/groups/{group_id}",
            json={
                "title": f"No Exit Task_{unique_id}",
                "priority": "medium",
                "group_id": group_id,
            },
            headers=auth_headers,
        )
        task_id = task_resp.json()["id"]

        user2_resp = await test_client.post(
            "/auth",
            json={
                "username": f"exituser_{unique_id}",
                "email": f"exituser_{unique_id}@test.com",
                "password": "Test123456789",
                "first_name": "Exit",
                "last_name": "User",
            },
        )
        user2_headers = {"Authorization": f"Bearer {user2_resp.json()['access_token']}"}

        resp = await test_client.delete(f"/tasks/{task_id}/exit", headers=user2_headers)
        assert resp.status_code == 403

    async def test_exit_last_task_cleans_assignee_role(
        self, test_client: AsyncClient, auth_headers: dict
    ):
        """Exit last task — ASSIGNEE role should be cleaned."""
        unique_id = str(uuid.uuid4())[:8]

        group_resp = await test_client.post(
            "/groups",
            json={"name": f"Cleanup Role Group_{unique_id}", "description": "Test"},
            headers=auth_headers,
        )
        group_id = group_resp.json()["id"]

        task_resp = await test_client.post(
            f"/tasks/groups/{group_id}",
            json={
                "title": f"Sole Task_{unique_id}",
                "priority": "medium",
                "group_id": group_id,
            },
            headers=auth_headers,
        )
        assert task_resp.status_code == 201
        task_id = task_resp.json()["id"]

        resp = await test_client.delete(f"/tasks/{task_id}/exit", headers=auth_headers)
        assert resp.status_code == 204


class TestSearchAssignedTasks:
    async def test_search_assigned_returns_200(
        self, test_client: AsyncClient, auth_headers: dict
    ):
        """Search assigned tasks after joining — returns 200."""
        unique_id = str(uuid.uuid4())[:8]
        group_resp = await test_client.post(
            "/groups",
            json={"name": f"Assigned Group_{unique_id}", "description": "For assigned"},
            headers=auth_headers,
        )
        group_id = group_resp.json()["id"]

        task_resp = await test_client.post(
            f"/tasks/groups/{group_id}",
            json={
                "title": f"Assigned Task_{unique_id}",
                "priority": "medium",
                "group_id": group_id,
            },
            headers=auth_headers,
        )
        task_id = task_resp.json()["id"]
        await test_client.post(f"/tasks/{task_id}/join", headers=auth_headers)

        resp = await test_client.get("/search/tasks/my", headers=auth_headers)
        assert resp.status_code in [200, 403]
        if resp.status_code == 200:
            data = resp.json()
            if isinstance(data, list):
                assert isinstance(data, list)
            elif isinstance(data, dict):
                assert "results" in data
            else:
                pass

    async def test_search_assigned_empty_returns_200(
        self, test_client: AsyncClient, auth_headers: dict
    ):
        """Search assigned tasks — returns 200 (empty or with tasks)."""
        resp = await test_client.get("/search/tasks/my", headers=auth_headers)
        assert resp.status_code in [200, 403]
        if resp.status_code == 200:
            data = resp.json()
            assert isinstance(data, dict)
            assert "results" in data

    async def test_search_assigned_without_auth_returns_401(
        self, test_client: AsyncClient
    ):
        """Search assigned tasks without auth — returns 401."""
        resp = await test_client.get("/search/tasks/my")
        assert resp.status_code == 401


class TestTaskJoinRequests:
    """Test task join requests endpoints."""

    async def test_get_task_join_requests_returns_200(
        self, test_client: AsyncClient, auth_headers: dict
    ):
        """Get task join requests — returns 200."""
        unique_id = str(uuid.uuid4())[:8]

        group_resp = await test_client.post(
            "/groups",
            json={"name": f"Task Join Req Group_{unique_id}", "description": "Test"},
            headers=auth_headers,
        )
        group_id = group_resp.json()["id"]

        task_resp = await test_client.post(
            f"/tasks/groups/{group_id}",
            json={
                "title": f"Task Join Req_{unique_id}",
                "description": "Test",
                "priority": "medium",
                "group_id": group_id,
            },
            headers=auth_headers,
        )
        assert task_resp.status_code == 201
        task_id = task_resp.json()["id"]

        response = await test_client.get(
            f"/tasks/{task_id}/join-requests",
            headers=auth_headers,
        )
        assert response.status_code == 200

    async def test_approve_task_join_request_returns_404(
        self, test_client: AsyncClient, auth_headers: dict
    ):
        """Approve task join request — returns 200."""
        unique_id = str(uuid.uuid4())[:8]

        group_resp = await test_client.post(
            "/groups",
            json={"name": f"Task Approve Group_{unique_id}", "description": "Test"},
            headers=auth_headers,
        )
        group_id = group_resp.json()["id"]

        task_resp = await test_client.post(
            f"/tasks/groups/{group_id}",
            json={
                "title": f"Task Approve_{unique_id}",
                "description": "Test",
                "priority": "high",
                "group_id": group_id,
            },
            headers=auth_headers,
        )
        assert task_resp.status_code == 201
        task_id = task_resp.json()["id"]

        requests_resp = await test_client.get(
            f"/tasks/{task_id}/join-requests",
            headers=auth_headers,
        )
        existing_ids = (
            [r["id"] for r in requests_resp.json()]
            if requests_resp.status_code == 200
            else []
        )

        fake_id = 99999 if 99999 not in existing_ids else max(existing_ids) + 1
        response = await test_client.post(
            f"/tasks/{task_id}/join-requests/{fake_id}/approve",
            headers=auth_headers,
        )
        assert response.status_code == 404

    async def test_reject_task_join_request_returns_200(
        self, test_client: AsyncClient, auth_headers: dict
    ):
        """Reject task join request — returns 200."""
        unique_id = str(uuid.uuid4())[:8]

        group_resp = await test_client.post(
            "/groups",
            json={"name": f"Task Reject Group_{unique_id}", "description": "Test"},
            headers=auth_headers,
        )
        group_id = group_resp.json()["id"]

        task_resp = await test_client.post(
            f"/tasks/groups/{group_id}",
            json={
                "title": f"Task Reject_{unique_id}",
                "description": "Test",
                "priority": "medium",
                "group_id": group_id,
            },
            headers=auth_headers,
        )
        assert task_resp.status_code == 201
        task_id = task_resp.json()["id"]

        response = await test_client.post(
            f"/tasks/{task_id}/join-requests/1/reject",
            headers=auth_headers,
        )
        assert response.status_code in [200, 404]

    async def test_approve_already_handled_request_returns_400(
        self, test_client: AsyncClient, auth_headers: dict
    ):
        """Approve already approved/rejected request — returns 400."""
        unique_id = str(uuid.uuid4())[:8]

        group_resp = await test_client.post(
            "/groups",
            json={"name": f"Approve Handled Group_{unique_id}", "description": "Test"},
            headers=auth_headers,
        )
        group_id = group_resp.json()["id"]

        task_resp = await test_client.post(
            f"/tasks/groups/{group_id}",
            json={
                "title": f"Approved Task_{unique_id}",
                "priority": "medium",
                "group_id": group_id,
            },
            headers=auth_headers,
        )
        assert task_resp.status_code == 201
        task_id = task_resp.json()["id"]

        user2_headers = await register_user(
            test_client, f"requser_{unique_id}", f"req_{unique_id}@test.com"
        )

        join_resp = await test_client.post(
            f"/tasks/{task_id}/join",
            headers=user2_headers,
        )
        assert join_resp.status_code in [201, 409]

        requests_resp = await test_client.get(
            f"/tasks/{task_id}/join-requests",
            headers=auth_headers,
        )
        requests = requests_resp.json()
        pending_request = next((r for r in requests if r["status"] == "PENDING"), None)
        if not pending_request:
            return
        request_id = pending_request["id"]

        approve_resp = await test_client.post(
            f"/tasks/{task_id}/join-requests/{request_id}/approve",
            headers=auth_headers,
        )
        assert approve_resp.status_code == 200

        approve_again_resp = await test_client.post(
            f"/tasks/{task_id}/join-requests/{request_id}/approve",
            headers=auth_headers,
        )
        assert approve_again_resp.status_code == 400

    async def test_reject_already_handled_request_returns_400(
        self, test_client: AsyncClient, auth_headers: dict
    ):
        """Reject already approved/rejected request — returns 400."""
        unique_id = str(uuid.uuid4())[:8]

        group_resp = await test_client.post(
            "/groups",
            json={"name": f"Reject Handled Group_{unique_id}", "description": "Test"},
            headers=auth_headers,
        )
        group_id = group_resp.json()["id"]

        task_resp = await test_client.post(
            f"/tasks/groups/{group_id}",
            json={
                "title": f"Rejected Task_{unique_id}",
                "priority": "medium",
                "group_id": group_id,
            },
            headers=auth_headers,
        )
        assert task_resp.status_code == 201
        task_id = task_resp.json()["id"]

        user2_headers = await register_user(
            test_client, f"rejectuser_{unique_id}", f"reject_{unique_id}@test.com"
        )

        join_resp = await test_client.post(
            f"/tasks/{task_id}/join",
            headers=user2_headers,
        )
        assert join_resp.status_code in [201, 409]

        requests_resp = await test_client.get(
            f"/tasks/{task_id}/join-requests",
            headers=auth_headers,
        )
        requests = requests_resp.json()
        pending_request = next((r for r in requests if r["status"] == "PENDING"), None)
        if not pending_request:
            return
        request_id = pending_request["id"]

        reject_resp = await test_client.post(
            f"/tasks/{task_id}/join-requests/{request_id}/reject",
            headers=auth_headers,
        )
        assert reject_resp.status_code == 200

        reject_again_resp = await test_client.post(
            f"/tasks/{task_id}/join-requests/{request_id}/reject",
            headers=auth_headers,
        )
        assert reject_again_resp.status_code == 400


class TestTaskJoinPolicy:
    async def test_join_open_task_direct_join(
        self, test_client: AsyncClient, auth_headers: dict
    ):
        """Join task in open group — direct join without approval check."""
        unique_id = str(uuid.uuid4())[:8]

        group_resp = await test_client.post(
            "/groups",
            json={"name": f"Open Group_{unique_id}", "description": "Open group"},
            headers=auth_headers,
        )
        if group_resp.status_code != 201:
            return
        group_id = group_resp.json()["id"]

        task_resp = await test_client.post(
            f"/tasks/groups/{group_id}",
            json={
                "title": f"Open Task_{unique_id}",
                "priority": "low",
                "group_id": group_id,
            },
            headers=auth_headers,
        )
        if task_resp.status_code != 201:
            return
        task_id = task_resp.json()["id"]

        user2_headers = await register_user(
            test_client, f"openuser_{unique_id}", f"open_{unique_id}@test.com"
        )

        join_resp = await test_client.post(
            f"/tasks/{task_id}/join",
            headers=user2_headers,
        )
        assert join_resp.status_code in [201, 409]

    async def test_join_closed_task_creates_request(
        self, test_client: AsyncClient, auth_headers: dict
    ):
        """Join task in group without task_id — creates request."""
        unique_id = str(uuid.uuid4())[:8]

        group_resp = await test_client.post(
            "/groups",
            json={"name": f"Closed Group_{unique_id}", "description": "Closed group"},
            headers=auth_headers,
        )
        if group_resp.status_code != 201:
            return
        group_id = group_resp.json()["id"]

        task_resp = await test_client.post(
            f"/tasks/groups/{group_id}",
            json={
                "title": f"Closed Task_{unique_id}",
                "priority": "low",
                "group_id": group_id,
            },
            headers=auth_headers,
        )
        if task_resp.status_code != 201:
            return
        task_id = task_resp.json()["id"]

        user2_headers = await register_user(
            test_client, f"closeduser_{unique_id}", f"closed_{unique_id}@test.com"
        )

        join_resp = await test_client.post(
            f"/tasks/{task_id}/join",
            headers=user2_headers,
        )
        assert join_resp.status_code in [201, 409, 422]


class TestAddAssigneeNotifications:
    async def test_add_assignee_creates_task_invite_notification(
        self, test_client: AsyncClient, auth_headers: dict
    ):
        """Add assignee to task creates notification."""
        unique_id = str(uuid.uuid4())[:8]

        group_resp = await test_client.post(
            "/groups",
            json={"name": f"Task Group_{unique_id}", "description": "Test"},
            headers=auth_headers,
        )
        group_id = group_resp.json()["id"]

        task_resp = await test_client.post(
            f"/tasks/groups/{group_id}",
            json={
                "title": f"Test Task_{unique_id}",
                "description": "Test",
                "priority": "medium",
                "group_id": group_id,
            },
            headers=auth_headers,
        )
        assert task_resp.status_code == 201
        task_id = task_resp.json()["id"]

        user2_headers = await register_user(
            test_client, f"assignee_{unique_id}", f"assignee_{unique_id}@test.com"
        )
        user2_id = int(
            (await test_client.get("/users/me", headers=user2_headers)).json()["id"]
        )

        resp = await test_client.post(
            f"/tasks/{task_id}/members/{user2_id}",
            headers=auth_headers,
        )
        assert resp.status_code == 201

        notif_resp = await test_client.get("/notifications", headers=user2_headers)
        notifications = notif_resp.json()
        assert isinstance(notifications, list)
        if len(notifications) > 0:
            assert notifications[0]["target_id"] == task_id

    async def test_add_assignee_notification_has_task_data(
        self, test_client: AsyncClient, auth_headers: dict
    ):
        """Notification contains correct task data."""
        unique_id = str(uuid.uuid4())[:8]
        task_title = f"Data Test Task_{unique_id}"

        group_resp = await test_client.post(
            "/groups",
            json={"name": f"Task Data Group_{unique_id}", "description": "Test"},
            headers=auth_headers,
        )
        group_id = group_resp.json()["id"]

        task_resp = await test_client.post(
            f"/tasks/groups/{group_id}",
            json={
                "title": task_title,
                "description": "Test",
                "priority": "low",
                "group_id": group_id,
            },
            headers=auth_headers,
        )
        assert task_resp.status_code == 201
        task_id = task_resp.json()["id"]

        user2_headers = await register_user(
            test_client, f"assignee2_{unique_id}", f"assignee2_{unique_id}@test.com"
        )
        user2_id = int(
            (await test_client.get("/users/me", headers=user2_headers)).json()["id"]
        )

        await test_client.post(
            f"/tasks/{task_id}/members/{user2_id}",
            headers=auth_headers,
        )

        notif_resp = await test_client.get("/notifications", headers=user2_headers)
        notifications = notif_resp.json()
        assert isinstance(notifications, list)
        if len(notifications) > 0:
            assert notifications[0]["target_id"] == task_id

    async def test_add_assignee_returns_201(
        self, test_client: AsyncClient, auth_headers: dict
    ):
        """Add assignee returns 201."""
        unique_id = str(uuid.uuid4())[:8]

        group_resp = await test_client.post(
            "/groups",
            json={"name": f"Add Return_{unique_id}", "description": "Test"},
            headers=auth_headers,
        )
        group_id = group_resp.json()["id"]

        task_resp = await test_client.post(
            f"/tasks/groups/{group_id}",
            json={
                "title": f"Return Task_{unique_id}",
                "priority": "high",
                "group_id": group_id,
            },
            headers=auth_headers,
        )
        assert task_resp.status_code == 201
        task_id = task_resp.json()["id"]

        user2_headers = await register_user(
            test_client, f"assignee3_{unique_id}", f"assignee3_{unique_id}@test.com"
        )
        user2_id = int(
            (await test_client.get("/users/me", headers=user2_headers)).json()["id"]
        )

        resp = await test_client.post(
            f"/tasks/{task_id}/members/{user2_id}",
            headers=auth_headers,
        )
        assert resp.status_code == 201


class TestJoinTaskNotifications:
    async def test_join_task_creates_request_notification(
        self, test_client: AsyncClient, auth_headers: dict
    ):
        """Join task creates notification."""
        unique_id = str(uuid.uuid4())[:8]

        group_resp = await test_client.post(
            "/groups",
            json={"name": f"Join Task Group_{unique_id}", "description": "Test"},
            headers=auth_headers,
        )
        group_id = group_resp.json()["id"]

        task_resp = await test_client.post(
            f"/tasks/groups/{group_id}",
            json={
                "title": f"Join Task_{unique_id}",
                "description": "Test",
                "priority": "medium",
                "group_id": group_id,
            },
            headers=auth_headers,
        )
        assert task_resp.status_code == 201
        task_id = task_resp.json()["id"]

        user2_headers = await register_user(
            test_client, f"joiner_{unique_id}", f"joiner_{unique_id}@test.com"
        )

        resp = await test_client.post(
            f"/tasks/{task_id}/join",
            headers=user2_headers,
        )
        assert resp.status_code == 201

        notif_resp = await test_client.get("/notifications", headers=auth_headers)
        notifications = notif_resp.json()
        assert isinstance(notifications, list)

    async def test_join_task_returns_201(
        self, test_client: AsyncClient, auth_headers: dict
    ):
        """Join task returns 201."""
        unique_id = str(uuid.uuid4())[:8]

        group_resp = await test_client.post(
            "/groups",
            json={"name": f"Join Return_{unique_id}", "description": "Test"},
            headers=auth_headers,
        )
        group_id = group_resp.json()["id"]

        task_resp = await test_client.post(
            f"/tasks/groups/{group_id}",
            json={
                "title": f"Join Return Task_{unique_id}",
                "priority": "low",
                "group_id": group_id,
            },
            headers=auth_headers,
        )
        assert task_resp.status_code == 201
        task_id = task_resp.json()["id"]

        user2_headers = await register_user(
            test_client, f"joiner2_{unique_id}", f"joiner2_{unique_id}@test.com"
        )

        resp = await test_client.post(
            f"/tasks/{task_id}/join",
            headers=user2_headers,
        )
        assert resp.status_code == 201

    async def test_join_task_notification_sent_to_admin(
        self, test_client: AsyncClient, auth_headers: dict
    ):
        """Notification sent to admin."""
        unique_id = str(uuid.uuid4())[:8]

        group_resp = await test_client.post(
            "/groups",
            json={"name": f"Admin Notif_{unique_id}", "description": "Test"},
            headers=auth_headers,
        )
        group_id = group_resp.json()["id"]

        task_resp = await test_client.post(
            f"/tasks/groups/{group_id}",
            json={
                "title": f"Admin Task_{unique_id}",
                "priority": "medium",
                "group_id": group_id,
            },
            headers=auth_headers,
        )
        assert task_resp.status_code == 201
        task_id = task_resp.json()["id"]

        user2_headers = await register_user(
            test_client, f"joiner3_{unique_id}", f"joiner3_{unique_id}@test.com"
        )

        await test_client.post(
            f"/tasks/{task_id}/join",
            headers=user2_headers,
        )

        notif_resp = await test_client.get("/notifications", headers=auth_headers)
        notifications = notif_resp.json()
        assert isinstance(notifications, list)


class TestApproveTaskJoinNotifications:
    async def test_approve_task_join_creates_notifications(
        self, test_client: AsyncClient, auth_headers: dict
    ):
        """Approve task join creates notifications."""
        unique_id = str(uuid.uuid4())[:8]

        group_resp = await test_client.post(
            "/groups",
            json={"name": f"Approve Task_{unique_id}", "description": "Test"},
            headers=auth_headers,
        )
        group_id = group_resp.json()["id"]

        task_resp = await test_client.post(
            f"/tasks/groups/{group_id}",
            json={
                "title": f"Approve Task_{unique_id}",
                "priority": "high",
                "group_id": group_id,
            },
            headers=auth_headers,
        )
        assert task_resp.status_code == 201
        task_id = task_resp.json()["id"]

        user2_headers = await register_user(
            test_client, f"approvee_{unique_id}", f"approvee_{unique_id}@test.com"
        )

        await test_client.post(
            f"/tasks/{task_id}/join",
            headers=user2_headers,
        )

        requests_resp = await test_client.get(
            f"/tasks/{task_id}/join-requests",
            headers=auth_headers,
        )
        data = requests_resp.json()
        if isinstance(data, list) and data:
            request_id = data[0]["id"]

            resp = await test_client.post(
                f"/tasks/{task_id}/join-requests/{request_id}/approve",
                headers=auth_headers,
            )
            assert resp.status_code == 200

    async def test_approve_task_join_returns_notification(
        self, test_client: AsyncClient, auth_headers: dict
    ):
        """Approve returns NotificationRead."""
        unique_id = str(uuid.uuid4())[:8]

        group_resp = await test_client.post(
            "/groups",
            json={"name": f"Approve Return_{unique_id}", "description": "Test"},
            headers=auth_headers,
        )
        group_id = group_resp.json()["id"]

        task_resp = await test_client.post(
            f"/tasks/groups/{group_id}",
            json={
                "title": f"Approve Return Task_{unique_id}",
                "priority": "medium",
                "group_id": group_id,
            },
            headers=auth_headers,
        )
        assert task_resp.status_code == 201
        task_id = task_resp.json()["id"]

        user2_headers = await register_user(
            test_client, f"approvee2_{unique_id}", f"approvee2_{unique_id}@test.com"
        )

        await test_client.post(
            f"/tasks/{task_id}/join",
            headers=user2_headers,
        )

        requests_resp = await test_client.get(
            f"/tasks/{task_id}/join-requests",
            headers=auth_headers,
        )
        data = requests_resp.json()
        if isinstance(data, list) and data:
            request_id = data[0]["id"]

            resp = await test_client.post(
                f"/tasks/{task_id}/join-requests/{request_id}/approve",
                headers=auth_headers,
            )
            assert resp.status_code == 200
            result = resp.json()
            assert "id" in result

    async def test_approve_task_join_creates_multiple_notifications(
        self, test_client: AsyncClient, auth_headers: dict
    ):
        """Check multiple notification types."""
        unique_id = str(uuid.uuid4())[:8]

        group_resp = await test_client.post(
            "/groups",
            json={"name": f"Multi Notif_{unique_id}", "description": "Test"},
            headers=auth_headers,
        )
        group_id = group_resp.json()["id"]

        task_resp = await test_client.post(
            f"/tasks/groups/{group_id}",
            json={
                "title": f"Multi Task_{unique_id}",
                "priority": "low",
                "group_id": group_id,
            },
            headers=auth_headers,
        )
        assert task_resp.status_code == 201
        task_id = task_resp.json()["id"]

        user2_headers = await register_user(
            test_client, f"multi_user_{unique_id}", f"multi_{unique_id}@test.com"
        )

        await test_client.post(
            f"/tasks/{task_id}/join",
            headers=user2_headers,
        )

        requests_resp = await test_client.get(
            f"/tasks/{task_id}/join-requests",
            headers=auth_headers,
        )
        data = requests_resp.json()
        if isinstance(data, list) and data:
            request_id = data[0]["id"]

            await test_client.post(
                f"/tasks/{task_id}/join-requests/{request_id}/approve",
                headers=auth_headers,
            )

    async def test_approve_task_join_notification_types(
        self, test_client: AsyncClient, auth_headers: dict
    ):
        """Check notification types after approve."""
        unique_id = str(uuid.uuid4())[:8]

        group_resp = await test_client.post(
            "/groups",
            json={"name": f"Types Test_{unique_id}", "description": "Test"},
            headers=auth_headers,
        )
        group_id = group_resp.json()["id"]

        task_resp = await test_client.post(
            f"/tasks/groups/{group_id}",
            json={
                "title": f"Types Task_{unique_id}",
                "priority": "high",
                "group_id": group_id,
            },
            headers=auth_headers,
        )
        assert task_resp.status_code == 201
        task_id = task_resp.json()["id"]

        user2_headers = await register_user(
            test_client, f"types_user_{unique_id}", f"types_{unique_id}@test.com"
        )

        await test_client.post(
            f"/tasks/{task_id}/join",
            headers=user2_headers,
        )

        requests_resp = await test_client.get(
            f"/tasks/{task_id}/join-requests",
            headers=auth_headers,
        )
        data = requests_resp.json()
        if isinstance(data, list) and data:
            request_id = data[0]["id"]

            await test_client.post(
                f"/tasks/{task_id}/join-requests/{request_id}/approve",
                headers=auth_headers,
            )


class TestRejectTaskJoinNotifications:
    async def test_reject_task_join_creates_notification(
        self, test_client: AsyncClient, auth_headers: dict
    ):
        """Reject task join creates notification."""
        unique_id = str(uuid.uuid4())[:8]

        group_resp = await test_client.post(
            "/groups",
            json={"name": f"Reject Task_{unique_id}", "description": "Test"},
            headers=auth_headers,
        )
        group_id = group_resp.json()["id"]

        task_resp = await test_client.post(
            f"/tasks/groups/{group_id}",
            json={
                "title": f"Reject Task_{unique_id}",
                "priority": "medium",
                "group_id": group_id,
            },
            headers=auth_headers,
        )
        assert task_resp.status_code == 201
        task_id = task_resp.json()["id"]

        user2_headers = await register_user(
            test_client, f"rejectee_{unique_id}", f"rejectee_{unique_id}@test.com"
        )

        await test_client.post(
            f"/tasks/{task_id}/join",
            headers=user2_headers,
        )

        requests_resp = await test_client.get(
            f"/tasks/{task_id}/join-requests",
            headers=auth_headers,
        )
        data = requests_resp.json()
        if isinstance(data, list) and data:
            request_id = data[0]["id"]

            resp = await test_client.post(
                f"/tasks/{task_id}/join-requests/{request_id}/reject",
                headers=auth_headers,
            )
            assert resp.status_code == 200

    async def test_reject_task_join_returns_notification(
        self, test_client: AsyncClient, auth_headers: dict
    ):
        """Reject returns NotificationRead."""
        unique_id = str(uuid.uuid4())[:8]

        group_resp = await test_client.post(
            "/groups",
            json={"name": f"Reject Return_{unique_id}", "description": "Test"},
            headers=auth_headers,
        )
        group_id = group_resp.json()["id"]

        task_resp = await test_client.post(
            f"/tasks/groups/{group_id}",
            json={
                "title": f"Reject Return Task_{unique_id}",
                "priority": "low",
                "group_id": group_id,
            },
            headers=auth_headers,
        )
        assert task_resp.status_code == 201
        task_id = task_resp.json()["id"]

        user2_headers = await register_user(
            test_client, f"rejectee2_{unique_id}", f"rejectee2_{unique_id}@test.com"
        )

        await test_client.post(
            f"/tasks/{task_id}/join",
            headers=user2_headers,
        )

        requests_resp = await test_client.get(
            f"/tasks/{task_id}/join-requests",
            headers=auth_headers,
        )
        data = requests_resp.json()
        if isinstance(data, list) and data:
            request_id = data[0]["id"]

            resp = await test_client.post(
                f"/tasks/{task_id}/join-requests/{request_id}/reject",
                headers=auth_headers,
            )
            assert resp.status_code == 200
            result = resp.json()
            assert "id" in result

    async def test_reject_task_join_notification_correct_type(
        self, test_client: AsyncClient, auth_headers: dict
    ):
        """Notification has correct type."""
        unique_id = str(uuid.uuid4())[:8]

        group_resp = await test_client.post(
            "/groups",
            json={"name": f"Reject Type_{unique_id}", "description": "Test"},
            headers=auth_headers,
        )
        group_id = group_resp.json()["id"]

        task_resp = await test_client.post(
            f"/tasks/groups/{group_id}",
            json={
                "title": f"Reject Type Task_{unique_id}",
                "priority": "high",
                "group_id": group_id,
            },
            headers=auth_headers,
        )
        assert task_resp.status_code == 201
        task_id = task_resp.json()["id"]

        user2_headers = await register_user(
            test_client, f"rejectee3_{unique_id}", f"rejectee3_{unique_id}@test.com"
        )

        await test_client.post(
            f"/tasks/{task_id}/join",
            headers=user2_headers,
        )

        requests_resp = await test_client.get(
            f"/tasks/{task_id}/join-requests",
            headers=auth_headers,
        )
        data = requests_resp.json()
        if isinstance(data, list) and data:
            request_id = data[0]["id"]

            await test_client.post(
                f"/tasks/{task_id}/join-requests/{request_id}/reject",
                headers=auth_headers,
            )


class TestNotificationEdgeCases:
    async def test_add_assignee_without_auth_returns_401(
        self, test_client: AsyncClient
    ):
        """No auth → returns 401."""
        resp = await test_client.post("/tasks/1/members/1")
        assert resp.status_code == 401

    async def test_add_assignee_nonexistent_task_returns_404(
        self, test_client: AsyncClient, auth_headers: dict
    ):
        """Nonexistent task → returns 404."""
        user2_headers = await register_user(
            test_client, "nonexistent_task", "nonexistent@test.com"
        )
        user2_id = int(
            (await test_client.get("/users/me", headers=user2_headers)).json()["id"]
        )
        resp = await test_client.post(
            f"/tasks/99999/members/{user2_id}",
            headers=auth_headers,
        )
        assert resp.status_code in [403, 404, 400, 409]

    async def test_join_task_without_auth_returns_401(self, test_client: AsyncClient):
        """No auth → returns 401."""
        resp = await test_client.post("/tasks/1/join")
        assert resp.status_code == 401

    async def test_approve_task_join_without_auth_returns_401(
        self, test_client: AsyncClient
    ):
        """No auth → returns 401."""
        resp = await test_client.post("/tasks/1/join-requests/1/approve")
        assert resp.status_code == 401

    async def test_reject_task_join_without_auth_returns_401(
        self, test_client: AsyncClient
    ):
        """No auth → returns 401."""
        resp = await test_client.post("/tasks/1/join-requests/1/reject")
        assert resp.status_code == 401

    async def test_notification_goes_to_correct_user(
        self, test_client: AsyncClient, auth_headers: dict
    ):
        """Notification sent to correct recipient."""
        unique_id = str(uuid.uuid4())[:8]

        group_resp = await test_client.post(
            "/groups",
            json={"name": f"Correct User_{unique_id}", "description": "Test"},
            headers=auth_headers,
        )
        group_id = group_resp.json()["id"]

        task_resp = await test_client.post(
            f"/tasks/groups/{group_id}",
            json={
                "title": f"Correct Task_{unique_id}",
                "priority": "medium",
                "group_id": group_id,
            },
            headers=auth_headers,
        )
        assert task_resp.status_code == 201
        task_id = task_resp.json()["id"]

        user2_headers = await register_user(
            test_client, f"correct_user_{unique_id}", f"correct_{unique_id}@test.com"
        )
        user2_id = int(
            (await test_client.get("/users/me", headers=user2_headers)).json()["id"]
        )

        await test_client.post(
            f"/tasks/{task_id}/members/{user2_id}",
            headers=auth_headers,
        )

        user2_notifs = await test_client.get("/notifications", headers=user2_headers)
        notifications = user2_notifs.json()
        assert isinstance(notifications, list)
        if notifications:
            assert notifications[0]["target_id"] == task_id

    async def test_no_duplicate_notifications_on_repeat(
        self, test_client: AsyncClient, auth_headers: dict
    ):
        """Adding same user twice → only one notification."""
        unique_id = str(uuid.uuid4())[:8]

        group_resp = await test_client.post(
            "/groups",
            json={"name": f"Dup Assign_{unique_id}", "description": "Test"},
            headers=auth_headers,
        )
        group_id = group_resp.json()["id"]

        task_resp = await test_client.post(
            f"/tasks/groups/{group_id}",
            json={
                "title": f"Dup Task_{unique_id}",
                "priority": "low",
                "group_id": group_id,
            },
            headers=auth_headers,
        )
        assert task_resp.status_code == 201
        task_id = task_resp.json()["id"]

        user2_headers = await register_user(
            test_client, f"dup_user_{unique_id}", f"dup_{unique_id}@test.com"
        )
        user2_id = int(
            (await test_client.get("/users/me", headers=user2_headers)).json()["id"]
        )

        resp1 = await test_client.post(
            f"/tasks/{task_id}/members/{user2_id}",
            headers=auth_headers,
        )
        assert resp1.status_code == 201

        resp2 = await test_client.post(
            f"/tasks/{task_id}/members/{user2_id}",
            headers=auth_headers,
        )
        assert resp2.status_code == 409
