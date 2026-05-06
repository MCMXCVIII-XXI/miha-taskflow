"""Unit tests for XPService calculation logic.

Tests the core XP calculation methods:
- _calculate_base_xp: Base XP from story points
- _calculate_time_bonus: Time bonus for early/late completion
- _calculate_streak_bonus: Streak bonus for consecutive days
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.service.xp import XPService


@pytest.fixture
def mock_db():
    return MagicMock()


@pytest.fixture
def mock_xp_transaction():
    tx = MagicMock()
    tx.get_or_create_skill = AsyncMock()
    tx.add_sphere_xp = AsyncMock()
    return tx


@pytest.fixture
def xp_service(mock_db, mock_xp_transaction):
    """Create XPService with mocked dependencies."""
    with patch.object(XPService, "__init__", return_value=None):
        svc = XPService(db=mock_db, xp_transaction=mock_xp_transaction)
        return svc


class TestCalculateBaseXP:
    """Tests for _calculate_base_xp method."""

    def test_easy_returns_10(self, xp_service):
        """EASY difficulty (1 story point) returns 10 XP."""
        result = xp_service._calculate_base_xp(story_points=1)
        assert result == 10

    def test_medium_returns_30(self, xp_service):
        """MEDIUM difficulty (3 story points) returns 30 XP."""
        result = xp_service._calculate_base_xp(story_points=3)
        assert result == 30

    def test_hard_returns_50(self, xp_service):
        """HARD difficulty (5 story points) returns 50 XP."""
        result = xp_service._calculate_base_xp(story_points=5)
        assert result == 50

    def test_zero_story_points(self, xp_service):
        """Zero story points returns 0 XP."""
        result = xp_service._calculate_base_xp(story_points=0)
        assert result == 0

    def test_custom_story_points(self, xp_service):
        """Custom story points return correct XP."""
        result = xp_service._calculate_base_xp(story_points=7)
        assert result == 70


class TestCalculateTimeBonus:
    """Tests for _calculate_time_bonus method."""

    def test_on_time_returns_1(self, xp_service):
        """On-time completion returns 1.0x multiplier."""
        result = xp_service._calculate_time_bonus(deadline_days=7, actual_days=7)
        assert result == 1.0

    def test_early_completion_returns_bonus(self, xp_service):
        """Early completion returns bonus > 1.0."""
        result = xp_service._calculate_time_bonus(deadline_days=7, actual_days=3)
        assert result > 1.0
        assert result <= 2.0

    def test_late_completion_returns_min(self, xp_service):
        """Late completion returns minimum 0.5x."""
        result = xp_service._calculate_time_bonus(deadline_days=7, actual_days=14)
        assert result == 0.5

    def test_zero_deadline_returns_1(self, xp_service):
        """Zero deadline returns 1.0x (no time bonus)."""
        result = xp_service._calculate_time_bonus(deadline_days=0, actual_days=7)
        assert result == 1.0

    def test_negative_deadline_returns_1(self, xp_service):
        """Negative deadline returns 1.0x."""
        result = xp_service._calculate_time_bonus(deadline_days=-1, actual_days=7)
        assert result == 1.0

    def test_exactly_on_time(self, xp_service):
        """Exactly on time returns 1.0."""
        result = xp_service._calculate_time_bonus(deadline_days=5, actual_days=5)
        assert result == 1.0

    def test_max_early_bonus(self, xp_service):
        """Maximum early completion returns 2.0x."""
        result = xp_service._calculate_time_bonus(deadline_days=7, actual_days=0)
        assert result == 2.0

    def test_max_late_bonus(self, xp_service):
        """Maximum late completion returns 0.5x."""
        result = xp_service._calculate_time_bonus(deadline_days=1, actual_days=100)
        assert result == 0.5


class TestCalculateStreakBonus:
    """Tests for _calculate_streak_bonus method."""

    def test_zero_streak_returns_1(self, xp_service):
        """Zero streak returns 1.0x."""
        result = xp_service._calculate_streak_bonus(streak=0)
        assert result == 1.0

    def test_one_day_streak_returns_1(self, xp_service):
        """1 day streak returns 1.0x."""
        result = xp_service._calculate_streak_bonus(streak=1)
        assert result == 1.0

    def test_four_day_streak_returns_1(self, xp_service):
        """4 day streak returns 1.0x (below threshold)."""
        result = xp_service._calculate_streak_bonus(streak=4)
        assert result == 1.0

    def test_five_day_streak_returns_1_2(self, xp_service):
        """5 day streak returns 1.2x."""
        result = xp_service._calculate_streak_bonus(streak=5)
        assert result == 1.2

    def test_seven_day_streak_returns_1_2(self, xp_service):
        """7 day streak returns 1.2x."""
        result = xp_service._calculate_streak_bonus(streak=7)
        assert result == 1.2

    def test_nine_day_streak_returns_1_2(self, xp_service):
        """9 day streak returns 1.2x."""
        result = xp_service._calculate_streak_bonus(streak=9)
        assert result == 1.2

    def test_ten_day_streak_returns_1_5(self, xp_service):
        """10 day streak returns 1.5x."""
        result = xp_service._calculate_streak_bonus(streak=10)
        assert result == 1.5

    def test_fifteen_day_streak_returns_1_5(self, xp_service):
        """15 day streak returns 1.5x."""
        result = xp_service._calculate_streak_bonus(streak=15)
        assert result == 1.5

    def test_negative_streak_returns_1(self, xp_service):
        """Negative streak returns 1.0x."""
        result = xp_service._calculate_streak_bonus(streak=-1)
        assert result == 1.0


class TestXPIntegrationScenarios:
    """Integration scenarios testing multiple calculation methods together."""

    def test_easy_on_time_no_streak(self, xp_service):
        """EASY task, on time, no streak: 10 * 1.0 * 1.0 = 10"""
        base = xp_service._calculate_base_xp(story_points=1)
        time_bonus = xp_service._calculate_time_bonus(deadline_days=7, actual_days=7)
        streak_bonus = xp_service._calculate_streak_bonus(streak=0)

        total = base * time_bonus * streak_bonus
        assert total == 10

    def test_hard_early_high_streak(self, xp_service):
        """HARD task, early, high streak: 50 * 1.571... * 1.5 = ~117"""
        base = xp_service._calculate_base_xp(story_points=5)
        time_bonus = xp_service._calculate_time_bonus(deadline_days=7, actual_days=3)
        streak_bonus = xp_service._calculate_streak_bonus(streak=10)

        total = base * time_bonus * streak_bonus
        assert 110 < total < 125

    def test_medium_late_medium_streak(self, xp_service):
        """MEDIUM task, late, medium streak: 30 * 0.5 * 1.2 = 18"""
        base = xp_service._calculate_base_xp(story_points=3)
        time_bonus = xp_service._calculate_time_bonus(deadline_days=7, actual_days=14)
        streak_bonus = xp_service._calculate_streak_bonus(streak=5)

        total = base * time_bonus * streak_bonus
        assert total == 18

    def test_max_xp_scenario(self, xp_service):
        """Maximum XP: HARD (5pts) + max time bonus (2x) + max streak (1.5x) = 150"""
        base = xp_service._calculate_base_xp(story_points=5)
        time_bonus = xp_service._calculate_time_bonus(deadline_days=7, actual_days=0)
        streak_bonus = xp_service._calculate_streak_bonus(streak=15)

        total = base * time_bonus * streak_bonus
        assert total == 150

    def test_min_xp_scenario(self, xp_service):
        """Minimum XP: EASY (1pt) + min time (0.5x) + no streak = 5"""
        base = xp_service._calculate_base_xp(story_points=1)
        time_bonus = xp_service._calculate_time_bonus(deadline_days=1, actual_days=100)
        streak_bonus = xp_service._calculate_streak_bonus(streak=0)

        total = base * time_bonus * streak_bonus
        assert total == 5
