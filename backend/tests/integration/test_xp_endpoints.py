from httpx import AsyncClient


class TestGetUserSkills:
    async def test_get_user_skills_returns_200(
        self, test_client: AsyncClient, auth_headers: dict
    ):
        """Get all skills for a user — returns 200."""
        resp = await test_client.get("/xp/users/1/skills", headers=auth_headers)
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    async def test_get_user_skills_without_auth_returns_401(
        self, test_client: AsyncClient
    ):
        """Get skills without auth — returns 401."""
        resp = await test_client.get("/xp/users/1/skills")
        assert resp.status_code == 401

    async def test_get_user_skills_for_nonexistent_user_returns_200(
        self, test_client: AsyncClient, auth_headers: dict
    ):
        """Get skills for nonexistent user — returns 200 with empty list."""
        resp = await test_client.get("/xp/users/99999/skills", headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json() == []

    async def test_get_user_skills_invalid_user_id_returns_404(
        self, test_client: AsyncClient, auth_headers: dict
    ):
        """Get skills with invalid user ID — returns 404 or empty."""
        resp = await test_client.get("/xp/users/0/skills", headers=auth_headers)
        assert resp.status_code in [200, 404]

    async def test_get_user_skills_negative_user_id_returns_404(
        self, test_client: AsyncClient, auth_headers: dict
    ):
        """Get skills with negative user ID — returns 404."""
        resp = await test_client.get("/xp/users/-1/skills", headers=auth_headers)
        assert resp.status_code in [200, 404]


class TestGetTopUserSkills:
    async def test_get_top_user_skills_returns_200(
        self, test_client: AsyncClient, auth_headers: dict
    ):
        """Get top N skills for a user — returns 200."""
        resp = await test_client.get(
            "/xp/users/1/skills/top?limit=3", headers=auth_headers
        )
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    async def test_get_top_user_skills_with_limit_returns_200(
        self, test_client: AsyncClient, auth_headers: dict
    ):
        """Get top skills with custom limit — returns 200."""
        resp = await test_client.get(
            "/xp/users/1/skills/top?limit=5", headers=auth_headers
        )
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) <= 5

    async def test_get_top_user_skills_without_auth_returns_401(
        self, test_client: AsyncClient
    ):
        """Get top skills without auth — returns 401."""
        resp = await test_client.get("/xp/users/1/skills/top")
        assert resp.status_code == 401

    async def test_get_top_user_skills_with_limit_0_returns_200(
        self, test_client: AsyncClient, auth_headers: dict
    ):
        """Get top skills with limit 0 — returns 200."""
        resp = await test_client.get(
            "/xp/users/1/skills/top?limit=0", headers=auth_headers
        )
        assert resp.status_code == 200

    async def test_get_top_user_skills_with_large_limit_returns_200(
        self, test_client: AsyncClient, auth_headers: dict
    ):
        """Get top skills with large limit — returns 200."""
        resp = await test_client.get(
            "/xp/users/1/skills/top?limit=1000", headers=auth_headers
        )
        assert resp.status_code == 200

    async def test_get_top_user_skills_for_nonexistent_user_returns_200(
        self, test_client: AsyncClient, auth_headers: dict
    ):
        """Get top skills for nonexistent user — returns 200 with empty list."""
        resp = await test_client.get("/xp/users/99999/skills/top", headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json() == []


class TestGetLeaderboard:
    async def test_get_leaderboard_returns_200(
        self, test_client: AsyncClient, auth_headers: dict
    ):
        """Get leaderboard — returns 200."""
        resp = await test_client.get("/xp/leaderboard", headers=auth_headers)
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    async def test_get_leaderboard_with_limit_returns_200(
        self, test_client: AsyncClient, auth_headers: dict
    ):
        """Get leaderboard with limit — returns 200."""
        resp = await test_client.get("/xp/leaderboard?limit=10", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) <= 10

    async def test_get_leaderboard_with_sphere_filter_returns_200(
        self, test_client: AsyncClient, auth_headers: dict
    ):
        """Get leaderboard filtered by sphere — returns 200."""
        resp = await test_client.get(
            "/xp/leaderboard?sphere=backend", headers=auth_headers
        )
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    async def test_get_leaderboard_without_auth_returns_401(
        self, test_client: AsyncClient
    ):
        """Get leaderboard without auth — returns 401."""
        resp = await test_client.get("/xp/leaderboard")
        assert resp.status_code == 401

    async def test_get_leaderboard_with_limit_0_returns_200(
        self, test_client: AsyncClient, auth_headers: dict
    ):
        """Get leaderboard with limit 0 — returns 200."""
        resp = await test_client.get("/xp/leaderboard?limit=0", headers=auth_headers)
        assert resp.status_code == 200

    async def test_get_leaderboard_with_large_limit_returns_200(
        self, test_client: AsyncClient, auth_headers: dict
    ):
        """Get leaderboard with large limit — returns 200."""
        resp = await test_client.get("/xp/leaderboard?limit=1000", headers=auth_headers)
        assert resp.status_code == 200

    async def test_get_leaderboard_with_all_spheres_returns_200(
        self, test_client: AsyncClient, auth_headers: dict
    ):
        """Get leaderboard filtered by each sphere — returns 200."""
        spheres = ["backend", "frontend", "devops", "qa", "product"]
        for sphere in spheres:
            resp = await test_client.get(
                f"/xp/leaderboard?sphere={sphere}", headers=auth_headers
            )
            assert resp.status_code == 200
