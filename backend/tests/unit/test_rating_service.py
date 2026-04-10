from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.schemas.enum import RatingTarget, TaskStatus
from app.service.exceptions.rating_exc import (
    RatingAlreadyExists,
    RatingForbiddenError,
    RatingNotFound,
)
from app.service.rating import RatingService


class TestCreateRating:
    async def test_create_rating_for_completed_task(self, mock_db: AsyncMock):
        mock_task = MagicMock()
        mock_task.id = 1
        mock_task.status = TaskStatus.DONE

        mock_db.scalar = AsyncMock(side_effect=[mock_task, None])
        mock_db.add = MagicMock()
        mock_db.commit = AsyncMock()

        mock_user = MagicMock()
        mock_user.id = 1

        with patch("app.service.rating.RatingRead") as MockRatingRead:
            mock_read = MagicMock()
            mock_read.id = 1
            mock_read.score = 8
            MockRatingRead.model_validate.return_value = mock_read

            svc = RatingService(mock_db)
            await svc.create_rating(
                target_id=1,
                target_type=RatingTarget.TASK,
                score=8,
                current_user=mock_user,
            )

            mock_db.add.assert_called_once()
            mock_db.commit.assert_awaited_once()

    async def test_create_duplicate_rating_raises(self, mock_db: AsyncMock):
        mock_task = MagicMock()
        mock_task.id = 1
        mock_task.status = TaskStatus.DONE

        mock_existing = MagicMock()
        mock_existing.id = 1

        mock_db.scalar = AsyncMock(side_effect=[mock_task, mock_existing])

        mock_user = MagicMock()
        mock_user.id = 1

        svc = RatingService(mock_db)
        with pytest.raises(RatingAlreadyExists):
            await svc.create_rating(
                target_id=1,
                target_type=RatingTarget.TASK,
                score=8,
                current_user=mock_user,
            )

    async def test_create_rating_for_group(self, mock_db: AsyncMock):
        mock_group = MagicMock()
        mock_group.id = 1

        call_count = [0]

        async def mock_scalar(query):
            call_count[0] += 1
            # First call: check group existence (should return group)
            # Second call: check existing rating (should return None)
            if call_count[0] == 1:
                return mock_group
            return None

        mock_db.scalar = AsyncMock(side_effect=mock_scalar)
        mock_db.add = MagicMock()
        mock_db.commit = AsyncMock()

        mock_user = MagicMock()
        mock_user.id = 1

        with patch("app.service.rating.RatingRead") as MockRatingRead:
            mock_read = MagicMock()
            mock_read.id = 1
            MockRatingRead.model_validate.return_value = mock_read

            svc = RatingService(mock_db)
            await svc.create_rating(
                target_id=1,
                target_type=RatingTarget.GROUP,
                score=10,
                current_user=mock_user,
            )

            mock_db.add.assert_called_once()


class TestDeleteRating:
    async def test_delete_own_rating(self, mock_db: AsyncMock):
        mock_rating = MagicMock()
        mock_rating.id = 1
        mock_rating.user_id = 1

        mock_db.scalar = AsyncMock(return_value=mock_rating)
        mock_db.delete = AsyncMock()
        mock_db.commit = AsyncMock()

        mock_user = MagicMock()
        mock_user.id = 1

        svc = RatingService(mock_db)
        await svc.delete_rating(1, mock_user)

        mock_db.delete.assert_called_once_with(mock_rating)
        mock_db.commit.assert_awaited_once()

    async def test_delete_others_rating_raises(self, mock_db: AsyncMock):
        mock_rating = MagicMock()
        mock_rating.id = 1
        mock_rating.user_id = 1

        mock_db.scalar = AsyncMock(return_value=mock_rating)

        mock_user = MagicMock()
        mock_user.id = 2

        svc = RatingService(mock_db)
        with pytest.raises(RatingForbiddenError):
            await svc.delete_rating(1, mock_user)

    async def test_delete_nonexistent_rating_raises(self, mock_db: AsyncMock):
        mock_db.scalar = AsyncMock(return_value=None)

        mock_user = MagicMock()
        mock_user.id = 1

        svc = RatingService(mock_db)
        with pytest.raises(RatingNotFound):
            await svc.delete_rating(999, mock_user)
