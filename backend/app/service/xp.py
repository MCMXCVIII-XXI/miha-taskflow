from collections.abc import Sequence
from datetime import UTC, datetime
from typing import Any

from fastapi import Depends
from sqlalchemy import ScalarResult
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.log import logging
from app.db import db_helper
from app.models import UserSkill
from app.schemas import UserSkillWithTitle
from app.schemas.enum import TaskSphere

from .base import XPBaseService

logger = logging.get_logger(__name__)


class XPService(XPBaseService):
    """Experience Points (XP) service for user leveling and skill tracking.

    This service implements the XP calculation and leveling system for users.
    It tracks user progress in different skill spheres and calculates XP
    based on task completion, difficulty, and timing.

    XP Calculation Formula:
    1. Base XP = story_points * 10
    2. Time Bonus = 0.5x - 2x (based on deadline adherence)
    3. Streak Bonus = 1.2x (5+ consecutive days) or 1.5x (10+ consecutive days)

    Attributes:
        _db (AsyncSession): SQLAlchemy async database session
        _spheres (TaskSphere): Available task spheres enumeration
        _base_rank (BaseRank): Base ranking system
        _xp_thresholds (XPThreshold): XP thresholds for level progression
        _task_difficulty (TaskDifficulty): Task difficulty levels
        _max_daily_xp (int): Maximum XP that can be earned per day (500)
        _frozen_days (int): Number of days skills remain frozen (60)
    """

    def __init__(
        self,
        db: AsyncSession,
    ) -> None:
        super().__init__(db)

    def _calculate_base_xp(self, story_points: int) -> int:
        """Base XP from story points (10 XP per point)."""
        return story_points * 10

    def _calculate_time_bonus(self, deadline_days: int, actual_days: int) -> float:
        """Time bonus: faster completion = more XP (0.5x - 2x)."""
        if deadline_days <= 0:
            return 1.0
        bonus = 1 + (deadline_days - actual_days) / deadline_days
        return max(0.5, min(bonus, 2.0))

    def _calculate_streak_bonus(self, streak: int) -> float:
        """Streak multiplier: 5+ days = 1.2x, 10+ days = 1.5x."""
        if streak >= 10:
            return 1.5
        if streak >= 5:
            return 1.2
        return 1.0

    def _distribute_xp(
        self, spheres: list[dict[str, Any]], base_xp: int, multiplier: float
    ) -> dict[str, int]:
        """Distribute total XP across spheres by weight."""
        result = {}
        for sphere_data in spheres:
            sphere_str = sphere_data.get("sphere", "BACKEND").upper()
            weight = sphere_data.get("weight", 1.0)
            xp = int(base_xp * weight * multiplier)
            result[sphere_str] = xp
        return result

    def calculate_task_xp(
        self,
        spheres: list[dict[str, Any]],  # [{"sphere": "BACKEND", "weight": 0.7}]
        story_points: int = 1,
        deadline_days: int = 7,
        actual_days: int = 7,
        streak: int = 0,
    ) -> dict[str, int]:
        """Calculate XP distribution across spheres."""
        base_xp = self._calculate_base_xp(story_points)
        time_bonus = self._calculate_time_bonus(deadline_days, actual_days)
        streak_bonus = self._calculate_streak_bonus(streak)

        multiplier = time_bonus * streak_bonus
        return self._distribute_xp(spheres, base_xp, multiplier)

    def get_level_from_xp(self, xp: int) -> int:
        """Level by XP dynamic thresholds"""
        xp_thresholds = self._get_xp_thresholds()
        level = 1
        for lvl, threshold in sorted(xp_thresholds.items(), key=lambda x: -x[1]):
            if xp >= threshold:
                level = lvl
                break
        return level

    async def _get_leaderboard(
        self, skills: list[UserSkill], limit: int
    ) -> list[dict[str, Any]]:
        if not skills:
            return []

        user_ids = [skill.user_id for skill in skills]

        users_result = await self._db.scalars(
            self._user_queries.get_user(id__in=user_ids, is_active=True)
        )
        users_map = {user.id: user for user in users_result}

        leaderboard = []
        for skill in skills:
            user = users_map.get(skill.user_id)
            title = self.get_title(skill.sphere, skill.level)
            leaderboard.append(
                {
                    "user_id": skill.user_id,
                    "username": user.username if user else "Unknown",
                    "sphere": skill.sphere.value,
                    "xp_total": skill.xp_total,
                    "level": skill.level,
                    "title": title,
                }
            )
        return leaderboard

    async def get_leaderboard(
        self, sphere: str | None, limit: int = 10
    ) -> list[dict[str, Any]]:
        if sphere:
            task_sphere = TaskSphere(sphere)
            result: ScalarResult[UserSkill] = await self._db.scalars(
                self._user_skill_queries.get_user_skill(sphere=task_sphere).limit(limit)
            )
            skills: list[UserSkill] = list(result)
            leaderboard = await self._get_leaderboard(skills, limit)
            return leaderboard
        return []

    def get_title(self, sphere: TaskSphere, level: int) -> str:
        """Dynamic title from _get_sphere_titles()"""
        sphere_titles = self._get_sphere_titles()
        titles = sphere_titles.get(sphere.value, {})
        return titles.get(level, f"Level {level}")

    def get_xp_to_next_level(self, xp: int, level: int) -> int:
        """Get the XP required to reach the next level."""
        xp_thresholds = self._get_xp_thresholds()
        next_level = min(level + 1, 10)
        next_threshold = xp_thresholds.get(next_level, 15000)
        return max(0, next_threshold - xp)

    def get_progress_percent(self, xp: int, level: int) -> int:
        """Get the progress percentage towards the next level."""
        xp_thresholds = self._get_xp_thresholds()
        current = xp_thresholds.get(level, 0)
        next_threshold = xp_thresholds.get(min(level + 1, 10), 15000)
        level_xp = xp - current
        level_range = next_threshold - current
        return min(100, int((level_xp / level_range * 100) if level_range > 0 else 100))

    async def get_or_create_skill(self, user_id: int, sphere: TaskSphere) -> UserSkill:
        """Get or create user skill."""
        skill = await self._db.scalar(
            self._user_skill_queries.get_user_skill(sphere=sphere, user_id=user_id)
        )

        if not skill:
            skill = UserSkill(user_id=user_id, sphere=sphere)
            self._db.add(skill)
            await self._db.commit()
            await self._db.refresh(skill)

        return skill

    async def _check_daily_cap(self, skill: UserSkill, xp_to_add: int) -> int:
        """Check and enforce daily XP cap.

        Args:
            skill: User skill to check.
            xp_to_add: Amount of XP trying to add.

        Returns:
            Actual XP that can be added (may be less than requested due to cap).
        """
        today = datetime.now(UTC).date()
        if skill.last_xp_date and skill.last_xp_date.date() == today:
            remaining = self._max_daily_xp - skill.xp_today
            if remaining <= 0:
                return 0
            return min(xp_to_add, remaining)
        return xp_to_add

    def _reset_daily_xp(self, skill: UserSkill) -> None:
        """Reset daily XP counter if new day."""
        today = datetime.now(UTC).date()
        if not skill.last_xp_date or skill.last_xp_date.date() != today:
            skill.xp_today = 0

    def _update_xp(self, skill: UserSkill, xp: int) -> None:
        """Update XP total with daily cap."""
        skill._old_level = skill.level  # type: ignore[attr-defined]
        old_xp = skill.xp_total
        skill.xp_total = old_xp + min(xp, self._max_daily_xp)
        skill.last_xp_date = datetime.now(UTC)

    def _update_level(self, skill: UserSkill) -> None:
        """Recalculate level from current XP."""
        new_level = self.get_level_from_xp(skill.xp_total)
        skill.level = new_level

    def _update_streak(self, skill: UserSkill) -> None:
        """Update daily streak counter."""
        if skill.last_xp_date:
            days_diff = (datetime.now(UTC) - skill.last_xp_date).days
            if days_diff == 1:
                skill.streak += 1
            elif days_diff > 1:
                skill.streak = 1

    async def add_sphere_xp(
        self, user_id: int, sphere: TaskSphere, xp: int
    ) -> tuple[bool, int]:
        """Add XP to user sphere and handle leveling/streaks."""
        skill = await self.get_or_create_skill(user_id, sphere)

        if skill.is_frozen:
            return False, skill.level

        self._reset_daily_xp(skill)
        xp_allowed = await self._check_daily_cap(skill, xp)
        if xp_allowed == 0:
            return False, skill.level

        self._update_xp(skill, xp_allowed)
        self._update_level(skill)
        self._update_streak(skill)

        await self._db.commit()

        leveled_up = skill.level > skill._old_level  # type: ignore[attr-defined]
        return leveled_up, skill.level

    async def _get_user_skills_raw(self, user_id: int) -> Sequence[UserSkill]:
        """Fetch raw UserSkill records from DB."""
        result = await self._db.scalars(
            self._user_skill_queries.get_user_skill(user_id=user_id)
        )
        return result.all()

    def _enrich_skill_with_progress(self, skill: UserSkill) -> UserSkillWithTitle:
        """Add title, progress, and XP to next level."""
        title = self.get_title(skill.sphere, skill.level)
        xp_to_next = self.get_xp_to_next_level(skill.xp_total, skill.level)
        progress = self.get_progress_percent(skill.xp_total, skill.level)

        return UserSkillWithTitle(
            id=skill.id,
            user_id=skill.user_id,
            sphere=skill.sphere,
            xp_total=skill.xp_total,
            level=skill.level,
            streak=skill.streak,
            is_frozen=skill.is_frozen,
            title=title,
            xp_to_next_level=xp_to_next,
            progress_percent=progress,
        )

    async def get_user_skills(self, user_id: int) -> list[UserSkillWithTitle]:
        """Get all user skills with progress and titles."""
        skills = await self._get_user_skills_raw(user_id)
        return [self._enrich_skill_with_progress(skill) for skill in skills]

    async def get_top_skills(
        self, user_id: int, limit: int = 3
    ) -> list[UserSkillWithTitle]:
        """Get top N skills for a user."""
        skills = await self.get_user_skills(user_id)
        return sorted(skills, key=lambda s: s.xp_total, reverse=True)[:limit]


def get_xp_service(db: AsyncSession = Depends(db_helper.get_session)) -> XPService:
    return XPService(
        db=db,
    )
