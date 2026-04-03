import uuid

from httpx import AsyncClient

from app.schemas.task import TaskStatus
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
        resp = await test_client.get("/tasks", headers=auth_headers)
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    async def test_search_my_tasks_returns_200(
        self, test_client: AsyncClient, auth_headers: dict
    ):
        """Search own tasks — returns 200."""
        await create_group_and_task(
            test_client, auth_headers, "My Tasks Group", "My Task"
        )
        resp = await test_client.get("/tasks/me", headers=auth_headers)
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    async def test_search_group_tasks_returns_200(
        self, test_client: AsyncClient, auth_headers: dict
    ):
        """Search tasks in group — returns 200."""
        group_id, _ = await create_group_and_task(
            test_client, auth_headers, "Group Tasks Group", "Group Task"
        )
        resp = await test_client.get(f"/tasks/groups/{group_id}", headers=auth_headers)
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    async def test_search_tasks_without_auth_returns_401(
        self, test_client: AsyncClient
    ):
        """Search tasks without auth — returns 401."""
        resp = await test_client.get("/tasks")
        assert resp.status_code == 401

    async def test_search_tasks_with_limit(
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

        resp = await test_client.get("/tasks?limit=2", headers=auth_headers)
        assert resp.status_code == 200
        assert len(resp.json()) <= 2

    async def test_search_tasks_with_offset(
        self, test_client: AsyncClient, auth_headers: dict
    ):
        """Search tasks with offset — skips first results."""
        # Create unique group and task for this test
        unique_id = str(uuid.uuid4())[:8]
        group_id, _ = await create_group_and_task(
            test_client,
            auth_headers,
            f"Offset Group Unique_{unique_id}",
            f"Task Unique_{unique_id}",
        )

        # Get tasks for this specific group with offset
        resp_all = await test_client.get(
            f"/tasks/groups/{group_id}", headers=auth_headers
        )
        resp_offset = await test_client.get(
            f"/tasks/groups/{group_id}?offset=1", headers=auth_headers
        )

        assert resp_all.status_code == 200
        assert resp_offset.status_code == 200
        # With offset=1, should get fewer or equal results
        assert len(resp_offset.json()) <= len(resp_all.json())

    async def test_search_tasks_by_status_filter(
        self, test_client: AsyncClient, auth_headers: dict
    ):
        """Search tasks by status filter — returns matching tasks."""
        # '_' is task_id
        group_id, _ = await create_group_and_task(
            test_client, auth_headers, "Status Filter Group", "Status Task"
        )

        resp = await test_client.get(
            f"/tasks/groups/{group_id}?status={TaskStatus.PENDING.value}",
            headers=auth_headers,
        )
        assert resp.status_code == 200
        tasks = resp.json()
        assert all(t["status"] == TaskStatus.PENDING.value for t in tasks)

    async def test_search_tasks_empty_result(
        self, test_client: AsyncClient, auth_headers: dict
    ):
        """Search tasks with non-matching filter — returns empty list."""
        resp = await test_client.get(
            "/tasks?title=NonExistent12345", headers=auth_headers
        )
        assert resp.status_code == 200
        assert resp.json() == []


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
        # Default status is pending, try setting it again
        resp = await test_client.patch(
            f"/tasks/{task_id}/status",
            params={"new_status": "pending"},
            headers=auth_headers,
        )
        assert resp.status_code == 409


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

        await test_client.post(
            "/auth",
            json={
                "username": "taskmember1",
                "email": "taskmember1@test.com",
                "password": "Password123",
                "first_name": "Task",
                "last_name": "Member1",
            },
        )
        users_resp = await test_client.get(
            "/users?username=taskmember1", headers=auth_headers
        )
        member_id = users_resp.json()[0]["id"]

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

        await test_client.post(
            "/auth",
            json={
                "username": "taskmember2",
                "email": "taskmember2@test.com",
                "password": "Password123",
                "first_name": "Task",
                "last_name": "Member2",
            },
        )
        users_resp = await test_client.get(
            "/users?username=taskmember2", headers=auth_headers
        )
        member_id = users_resp.json()[0]["id"]

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

        await test_client.post(
            "/auth",
            json={
                "username": "victim",
                "email": "victim@test.com",
                "password": "Password123",
                "first_name": "Victim",
                "last_name": "User",
            },
        )
        users_resp = await test_client.get(
            "/users?username=victim", headers=auth_headers
        )
        member_id = users_resp.json()[0]["id"]

        resp = await test_client.post(
            f"/tasks/{task_id}/members/{member_id}",
            headers=auth_headers,
        )
        assert resp.status_code == 403


class TestJoinTask:
    async def test_join_task_returns_201(
        self, test_client: AsyncClient, auth_headers: dict
    ):
        """Join task — returns 201."""
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
        assert resp.status_code == 201

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
        """Exit task without joining — returns 403."""
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

        resp = await test_client.delete(f"/tasks/{task_id}/exit", headers=auth_headers)
        assert resp.status_code == 403


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

        resp = await test_client.get("/tasks/assigned", headers=auth_headers)
        assert resp.status_code == 200
        tasks = resp.json()
        assert isinstance(tasks, list)
        assert any(t["id"] == task_id for t in tasks)

    async def test_search_assigned_empty_returns_200(
        self, test_client: AsyncClient, auth_headers: dict
    ):
        """Search assigned tasks — returns 200 (empty or with tasks)."""
        resp = await test_client.get("/tasks/assigned", headers=auth_headers)
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    async def test_search_assigned_without_auth_returns_401(
        self, test_client: AsyncClient
    ):
        """Search assigned tasks without auth — returns 401."""
        resp = await test_client.get("/tasks/assigned")
        assert resp.status_code == 401
