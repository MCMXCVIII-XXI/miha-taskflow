from unittest.mock import AsyncMock, MagicMock

import pytest

from app.service import AuthenticationService
from app.service.exceptions import user_exc


class TestRegister:
    async def test_register_returns_tokens(self, mock_db: AsyncMock):
        mock_result = MagicMock()
        mock_result.first.return_value = None
        mock_db.scalars.return_value = mock_result
        user_in = MagicMock()
        user_in.username = "unituser"
        user_in.email = "unit@test.com"
        user_in.first_name = "Unit"
        user_in.last_name = "Test"
        user_in.patronymic = None
        user_in.hashed_password.get_secret_value.return_value = "Password123"
        mock_indexer = MagicMock()
        mock_indexer.index_user = AsyncMock()
        svc = AuthenticationService(mock_db, mock_indexer)
        result = await svc.register(user_in)
        assert hasattr(result, "access_token")
        assert hasattr(result, "refresh_token")
        mock_db.add.assert_called_once()
        mock_db.commit.assert_awaited_once()

    async def test_register_duplicate_raises(self, mock_db: AsyncMock):
        mock_result = MagicMock()
        mock_result.first.return_value = MagicMock()
        mock_db.scalars.return_value = mock_result
        user_in = MagicMock()
        user_in.email = "dup@test.com"
        user_in.username = "dup"
        mock_indexer = MagicMock()
        svc = AuthenticationService(mock_db, mock_indexer)
        with pytest.raises(user_exc.UserAlreadyExists):
            await svc.register(user_in)
