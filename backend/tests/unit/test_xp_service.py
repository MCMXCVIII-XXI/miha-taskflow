from unittest.mock import AsyncMock

from app.schemas.enum import TaskSphere
from app.service.xp import XPService


class TestCalculateBaseXP:
    def test_easy_returns_10(self):
        mock_db = AsyncMock()
        svc = XPService(mock_db)
        result = svc._calculate_base_xp(story_points=1)
        assert result == 10

    def test_medium_returns_30(self):
        mock_db = AsyncMock()
        svc = XPService(mock_db)
        result = svc._calculate_base_xp(story_points=3)
        assert result == 30

    def test_hard_returns_50(self):
        mock_db = AsyncMock()
        svc = XPService(mock_db)
        result = svc._calculate_base_xp(story_points=5)
        assert result == 50


class TestCalculateTimeBonus:
    def test_early_completion_returns_bonus(self):
        mock_db = AsyncMock()
        svc = XPService(mock_db)
        result = svc._calculate_time_bonus(deadline_days=7, actual_days=3)
        assert result > 1.0

    def test_late_completion_returns_min(self):
        mock_db = AsyncMock()
        svc = XPService(mock_db)
        result = svc._calculate_time_bonus(deadline_days=7, actual_days=14)
        assert result == 0.5

    def test_on_time_returns_1(self):
        mock_db = AsyncMock()
        svc = XPService(mock_db)
        result = svc._calculate_time_bonus(deadline_days=7, actual_days=7)
        assert result == 1.0

    def test_zero_deadline_returns_1(self):
        mock_db = AsyncMock()
        svc = XPService(mock_db)
        result = svc._calculate_time_bonus(deadline_days=0, actual_days=5)
        assert result == 1.0


class TestCalculateStreakBonus:
    def test_no_streak_returns_1(self):
        mock_db = AsyncMock()
        svc = XPService(mock_db)
        result = svc._calculate_streak_bonus(streak=0)
        assert result == 1.0

    def test_3_day_streak_returns_1(self):
        mock_db = AsyncMock()
        svc = XPService(mock_db)
        result = svc._calculate_streak_bonus(streak=3)
        assert result == 1.0

    def test_5_day_streak_returns_1_2(self):
        mock_db = AsyncMock()
        svc = XPService(mock_db)
        result = svc._calculate_streak_bonus(streak=5)
        assert result == 1.2

    def test_10_day_streak_returns_1_5(self):
        mock_db = AsyncMock()
        svc = XPService(mock_db)
        result = svc._calculate_streak_bonus(streak=10)
        assert result == 1.5


class TestDistributeXP:
    def test_single_sphere_full_xp(self):
        mock_db = AsyncMock()
        svc = XPService(mock_db)
        spheres = [{"sphere": "BACKEND", "weight": 1.0}]
        result = svc._distribute_xp(spheres, base_xp=100, multiplier=1.0)
        assert result["BACKEND"] == 100

    def test_multiple_spheres_distributed(self):
        mock_db = AsyncMock()
        svc = XPService(mock_db)
        spheres = [
            {"sphere": "BACKEND", "weight": 0.7},
            {"sphere": "FRONTEND", "weight": 0.3},
        ]
        result = svc._distribute_xp(spheres, base_xp=100, multiplier=1.0)
        assert result["BACKEND"] == 70
        assert result["FRONTEND"] == 30


class TestCalculateTaskXP:
    def test_calculate_with_all_factors(self):
        mock_db = AsyncMock()
        svc = XPService(mock_db)
        spheres = [{"sphere": "BACKEND", "weight": 1.0}]
        result = svc.calculate_task_xp(
            spheres=spheres,
            story_points=3,
            deadline_days=7,
            actual_days=5,
            streak=0,
        )
        assert "BACKEND" in result
        assert result["BACKEND"] > 0


class TestGetLevelFromXP:
    def test_low_xp_returns_level_1(self):
        mock_db = AsyncMock()
        svc = XPService(mock_db)
        result = svc.get_level_from_xp(xp=0)
        assert result == 1

    def test_high_xp_returns_higher_level(self):
        mock_db = AsyncMock()
        svc = XPService(mock_db)
        result = svc.get_level_from_xp(xp=5000)
        assert result > 1


class TestGetTitle:
    def test_get_title_returns_string(self):
        mock_db = AsyncMock()
        svc = XPService(mock_db)
        result = svc.get_title(TaskSphere.BACKEND, level=1)
        assert isinstance(result, str)


class TestGetXPNextLevel:
    def test_get_xp_to_next_level(self):
        mock_db = AsyncMock()
        svc = XPService(mock_db)
        result = svc.get_xp_to_next_level(xp=100, level=1)
        assert isinstance(result, int)
        assert result >= 0


class TestGetProgressPercent:
    def test_progress_percent_returns_int(self):
        mock_db = AsyncMock()
        svc = XPService(mock_db)
        result = svc.get_progress_percent(xp=50, level=1)
        assert isinstance(result, int)
        assert 0 <= result <= 100
