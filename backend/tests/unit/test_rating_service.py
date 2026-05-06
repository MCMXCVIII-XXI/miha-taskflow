from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.schemas.enum import RatingTarget
from app.service.exceptions.rating_exc import (
    RatingAlreadyExists,
    RatingForbiddenError,
    RatingNotFound,
)
from app.service.rating import RatingService


@pytest.fixture
def mock_rating_transaction():
    mock = MagicMock()
    mock.create_rating = AsyncMock()
    mock.delete_rating = AsyncMock()
    return mock


class TestCreateRating:
    async def test_create_rating_for_completed_task(
        self, mock_db: AsyncMock, mock_rating_transaction
    ):

        mock_rating = MagicMock()
        mock_rating.id = 1
        mock_rating.score = 8
        mock_rating.user_id = 1
        mock_rating.target_id = 1
        mock_rating.target_type = RatingTarget.TASK
        mock_rating.created_at = datetime.now(tz=UTC)

        mock_rating_transaction.create_rating = AsyncMock(return_value=mock_rating)

        mock_user = MagicMock()
        mock_user.id = 1

        svc = RatingService(mock_db, rating_transaction=mock_rating_transaction)
        result = await svc.create_rating(
            target_id=1,
            target_type=RatingTarget.TASK,
            score=8,
            current_user=mock_user,
        )

        mock_rating_transaction.create_rating.assert_called_once()
        assert result.id == 1

    async def test_create_duplicate_rating_raises(
        self, mock_db: AsyncMock, mock_rating_transaction
    ):
        mock_rating_transaction.create_rating = AsyncMock(
            side_effect=RatingAlreadyExists(message="Already rated")
        )

        mock_user = MagicMock()
        mock_user.id = 1

        svc = RatingService(mock_db, rating_transaction=mock_rating_transaction)
        with pytest.raises(RatingAlreadyExists):
            await svc.create_rating(
                target_id=1,
                target_type=RatingTarget.TASK,
                score=8,
                current_user=mock_user,
            )

    async def test_create_rating_for_group(
        self, mock_db: AsyncMock, mock_rating_transaction
    ):

        mock_rating = MagicMock()
        mock_rating.id = 1
        mock_rating.score = 10
        mock_rating.user_id = 1
        mock_rating.target_id = 1
        mock_rating.target_type = RatingTarget.GROUP
        mock_rating.created_at = datetime.now(tz=UTC)

        mock_rating_transaction.create_rating = AsyncMock(return_value=mock_rating)

        mock_user = MagicMock()
        mock_user.id = 1

        svc = RatingService(mock_db, rating_transaction=mock_rating_transaction)
        await svc.create_rating(
            target_id=1,
            target_type=RatingTarget.GROUP,
            score=10,
            current_user=mock_user,
        )

        mock_rating_transaction.create_rating.assert_called_once()


class TestDeleteRating:
    async def test_delete_own_rating(self, mock_db: AsyncMock, mock_rating_transaction):
        mock_user = MagicMock()
        mock_user.id = 1

        mock_rating_transaction.delete_rating = AsyncMock()

        svc = RatingService(mock_db, rating_transaction=mock_rating_transaction)
        await svc.delete_rating(1, mock_user)

        mock_rating_transaction.delete_rating.assert_called_once()

    async def test_delete_others_rating_raises(
        self, mock_db: AsyncMock, mock_rating_transaction
    ):
        mock_rating_transaction.delete_rating = AsyncMock(
            side_effect=RatingForbiddenError(message="Not your rating")
        )

        mock_user = MagicMock()
        mock_user.id = 1

        svc = RatingService(mock_db, rating_transaction=mock_rating_transaction)
        with pytest.raises(RatingForbiddenError):
            await svc.delete_rating(1, mock_user)

    async def test_delete_nonexistent_rating_raises(
        self, mock_db: AsyncMock, mock_rating_transaction
    ):
        mock_rating_transaction.delete_rating = AsyncMock(
            side_effect=RatingNotFound(message="Rating not found")
        )

        mock_user = MagicMock()
        mock_user.id = 1

        svc = RatingService(mock_db, rating_transaction=mock_rating_transaction)
        with pytest.raises(RatingNotFound):
            await svc.delete_rating(999, mock_user)
