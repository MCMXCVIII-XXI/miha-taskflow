from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.service import AuthenticationService
from app.service.exceptions import user_exc


@pytest.fixture
def mock_auth_transaction():
    mock = MagicMock()
    mock.register = AsyncMock()
    mock.login = AsyncMock()
    return mock


@pytest.fixture
def mock_indexer():
    return MagicMock()


class TestRegister:
    async def test_register_returns_tokens(
        self, mock_db: AsyncMock, mock_indexer, mock_auth_transaction
    ):
        mock_user = MagicMock()
        mock_user.id = 1
        mock_user.username = "unituser"
        mock_user.email = "unit@test.com"

        mock_tokens = MagicMock()
        # ruff: noqa: S105
        mock_tokens.access_token = "access"
        mock_tokens.refresh_token = "refresh"

        mock_auth_transaction.register = AsyncMock(return_value=mock_user)
        mock_auth_transaction.login = AsyncMock(return_value=mock_tokens)

        mock_user_in = MagicMock()
        mock_user_in.username = "unituser"
        mock_user_in.email = "unit@test.com"
        mock_user_in.first_name = "Unit"
        mock_user_in.last_name = "Test"
        mock_user_in.hashed_password.get_secret_value.return_value = "Password123"

        svc = AuthenticationService(
            mock_db, mock_indexer, auth_transaction=mock_auth_transaction
        )
        mock_indexer.index = AsyncMock()
        with patch.object(svc, "_indexer", mock_indexer):
            result = await svc.register(mock_user_in)

        mock_auth_transaction.register.assert_called_once()
        assert hasattr(result, "access_token")

    async def test_register_duplicate_raises(
        self, mock_db: AsyncMock, mock_indexer, mock_auth_transaction
    ):
        mock_auth_transaction.register = AsyncMock(
            side_effect=user_exc.UserAlreadyExists(message="User exists")
        )

        mock_user_in = MagicMock()
        mock_user_in.email = "dup@test.com"
        mock_user_in.username = "dup"

        svc = AuthenticationService(
            mock_db, mock_indexer, auth_transaction=mock_auth_transaction
        )
        with pytest.raises(user_exc.UserAlreadyExists):
            await svc.register(mock_user_in)
