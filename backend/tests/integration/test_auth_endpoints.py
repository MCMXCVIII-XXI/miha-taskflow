from httpx import AsyncClient


class TestRegister:
    async def test_register_returns_200(self, test_client: AsyncClient):
        resp = await test_client.post(
            "/auth",
            json={
                "username": "reguser",
                "email": "reg@test.com",
                "password": "Password123",
                "first_name": "Reg",
                "last_name": "User",
            },
        )
        assert resp.status_code == 201
        assert "access_token" in resp.json()
        assert "refresh_token" in resp.json()

    async def test_register_duplicate_email_returns_409(self, test_client: AsyncClient):
        payload1 = {
            "username": "dupemail1",
            "email": "dupemail@test.com",
            "password": "Password123",
            "first_name": "Dup",
            "last_name": "Email",
        }
        payload2 = {
            "username": "dupemail2",
            "email": "dupemail@test.com",
            "password": "Password123",
            "first_name": "Dup",
            "last_name": "Email",
        }
        await test_client.post("/auth", json=payload1)
        resp = await test_client.post("/auth", json=payload2)
        assert resp.status_code == 409

    async def test_register_duplicate_username_returns_409(
        self, test_client: AsyncClient
    ):
        payload1 = {
            "username": "dupuser",
            "email": "dupuser1@test.com",
            "password": "Password123",
            "first_name": "Dup",
            "last_name": "User",
        }
        payload2 = {
            "username": "dupuser",
            "email": "dupuser2@test.com",
            "password": "Password123",
            "first_name": "Dup",
            "last_name": "User",
        }
        await test_client.post("/auth", json=payload1)
        resp = await test_client.post("/auth", json=payload2)
        assert resp.status_code == 409

    async def test_register_short_password_returns_422(self, test_client: AsyncClient):
        resp = await test_client.post(
            "/auth",
            json={
                "username": "shortpw",
                "email": "shortpw@test.com",
                "password": "Short1",
                "first_name": "Short",
                "last_name": "Password",
            },
        )
        assert resp.status_code == 422

    async def test_register_short_username_returns_422(self, test_client: AsyncClient):
        resp = await test_client.post(
            "/auth",
            json={
                "username": "ab",
                "email": "shortun@test.com",
                "password": "Password123",
                "first_name": "Short",
                "last_name": "Username",
            },
        )
        assert resp.status_code == 422

    async def test_register_missing_fields_returns_422(self, test_client: AsyncClient):
        resp = await test_client.post(
            "/auth",
            json={
                "username": "missing",
            },
        )
        assert resp.status_code == 422

    async def test_register_invalid_email_returns_422(self, test_client: AsyncClient):
        resp = await test_client.post(
            "/auth",
            json={
                "username": "bademail",
                "email": "not-an-email",
                "password": "Password123",
                "first_name": "Bad",
                "last_name": "Email",
            },
        )
        assert resp.status_code == 422

    async def test_register_empty_username_returns_422(self, test_client: AsyncClient):
        resp = await test_client.post(
            "/auth",
            json={
                "username": "",
                "email": "empty@test.com",
                "password": "Password123",
                "first_name": "Empty",
                "last_name": "User",
            },
        )
        assert resp.status_code == 422

    async def test_register_empty_password_returns_422(self, test_client: AsyncClient):
        resp = await test_client.post(
            "/auth",
            json={
                "username": "emptypw",
                "email": "emptypw@test.com",
                "password": "",
                "first_name": "Empty",
                "last_name": "Pw",
            },
        )
        assert resp.status_code == 422

    async def test_register_weak_password_returns_422(self, test_client: AsyncClient):
        resp = await test_client.post(
            "/auth",
            json={
                "username": "weakpw",
                "email": "weakpw@test.com",
                "password": "123",
                "first_name": "Weak",
                "last_name": "Pw",
            },
        )
        assert resp.status_code == 422


class TestLogin:
    async def test_login_returns_200(self, test_client: AsyncClient):
        await test_client.post(
            "/auth",
            json={
                "username": "loginuser",
                "email": "login@test.com",
                "password": "Password123",
                "first_name": "Login",
                "last_name": "User",
            },
        )
        resp = await test_client.post(
            "/auth/token",
            data={
                "username": "loginuser",
                "password": "Password123",
            },
        )
        assert resp.status_code == 200
        assert "access_token" in resp.json()

    async def test_login_by_email_returns_200(self, test_client: AsyncClient):
        await test_client.post(
            "/auth",
            json={
                "username": "loginemail",
                "email": "loginemail@test.com",
                "password": "Password123",
                "first_name": "Login",
                "last_name": "Email",
            },
        )
        resp = await test_client.post(
            "/auth/token",
            data={
                "username": "loginemail@test.com",
                "password": "Password123",
            },
        )
        assert resp.status_code == 200

    async def test_login_wrong_password_returns_401(self, test_client: AsyncClient):
        await test_client.post(
            "/auth",
            json={
                "username": "wrongpw",
                "email": "wrongpw@test.com",
                "password": "Password123",
                "first_name": "Wrong",
                "last_name": "Pw",
            },
        )
        resp = await test_client.post(
            "/auth/token",
            data={
                "username": "wrongpw",
                "password": "WrongPassword",
            },
        )
        assert resp.status_code == 401

    async def test_login_nonexistent_user_returns_404(self, test_client: AsyncClient):
        resp = await test_client.post(
            "/auth/token",
            data={
                "username": "nouser",
                "password": "Password123",
            },
        )
        assert resp.status_code == 404

    async def test_login_empty_username_returns_422(self, test_client: AsyncClient):
        resp = await test_client.post(
            "/auth/token",
            data={
                "username": "",
                "password": "Password123",
            },
        )
        assert resp.status_code == 422

    async def test_login_empty_password_returns_422(self, test_client: AsyncClient):
        resp = await test_client.post(
            "/auth/token",
            data={
                "username": "testuser",
                "password": "",
            },
        )
        assert resp.status_code == 422


class TestAccessToken:
    async def test_access_token_returns_200(self, test_client: AsyncClient):
        """Get new access token from refresh token — returns 200."""
        reg = await test_client.post(
            "/auth",
            json={
                "username": "accesstoken",
                "email": "accesstoken@test.com",
                "password": "Password123",
                "first_name": "Access",
                "last_name": "Token",
            },
        )
        refresh = reg.json()["refresh_token"]

        resp = await test_client.post(
            "/auth/access-token",
            json={"refresh_token": refresh},
        )
        assert resp.status_code == 200
        assert "access_token" in resp.json()

    async def test_access_token_invalid_returns_401(self, test_client: AsyncClient):
        resp = await test_client.post(
            "/auth/access-token",
            json={"refresh_token": "invalid.token.here"},
        )
        assert resp.status_code == 401


class TestRefreshToken:
    async def test_refresh_token_returns_200(self, test_client: AsyncClient):
        """Refresh token rotation — returns 200 with new tokens."""
        reg = await test_client.post(
            "/auth",
            json={
                "username": "refreshtoken",
                "email": "refreshtoken@test.com",
                "password": "Password123",
                "first_name": "Refresh",
                "last_name": "Token",
            },
        )
        refresh = reg.json()["refresh_token"]

        resp = await test_client.post(
            "/auth/refresh-token",
            json={"refresh_token": refresh},
        )
        assert resp.status_code == 200
        assert "access_token" in resp.json()
        assert "refresh_token" in resp.json()

    async def test_refresh_token_invalid_returns_401(self, test_client: AsyncClient):
        resp = await test_client.post(
            "/auth/refresh-token",
            json={"refresh_token": "invalid.token.here"},
        )
        assert resp.status_code == 401
