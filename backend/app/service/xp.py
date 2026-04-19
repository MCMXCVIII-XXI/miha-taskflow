from collections.abc import Sequence
from datetime import UTC, datetime
from typing import Any

from fastapi import Depends
from sqlalchemy import ScalarResult
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.log import logging
from app.core.metrics import SEARCH_QUERIES_TOTAL, XP_CHANGES_TOTAL
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
        logger.debug("Initializing XPService with db session", db_session_id=id(db))
        super().__init__(db)

    def _calculate_base_xp(self, story_points: int) -> int:
        """
        Calculate the base XP from story points.
        """
        logger.debug("Calculating base XP from story points", story_points=story_points)
        return story_points * 10

    def _calculate_time_bonus(self, deadline_days: int, actual_days: int) -> float:
        """
        Calculate the time bonus based on the deadline and actual days completed.
        """
        logger.debug(
            "Calculating time bonus",
            deadline_days=deadline_days,
            actual_days=actual_days,
        )
        if deadline_days <= 0:
            return 1.0
        bonus = 1 + (deadline_days - actual_days) / deadline_days
        return max(0.5, min(bonus, 2.0))

    def _calculate_streak_bonus(self, streak: int) -> float:
        """
        Calculate the streak bonus based on the number of consecutive days completed.
        """
        logger.debug("Calculating streak bonus", streak=streak)
        if streak >= 10:
            return 1.5
        if streak >= 5:
            return 1.2
        return 1.0

    def _distribute_xp(
        self, spheres: list[dict[str, Any]], base_xp: int, multiplier: float
    ) -> dict[str, int]:
        """
        Distribute the base XP across the given spheres with a multiplier.
        """
        logger.debug(
            "Starting XP distribution across spheres",
            base_xp=base_xp,
            multiplier=multiplier,
        )
        result = {}
        for sphere_data in spheres:
            sphere_str = sphere_data.get("sphere", "BACKEND").upper()
            weight = sphere_data.get("weight", 1.0)
            xp = int(base_xp * weight * multiplier)
            result[sphere_str] = xp
        logger.debug("XP distribution finished", xp_per_sphere=result)
        return result

    def calculate_task_xp(
        self,
        spheres: list[dict[str, Any]],  # [{"sphere": "BACKEND", "weight": 0.7}]
        story_points: int = 1,
        deadline_days: int = 7,
        actual_days: int = 7,
        streak: int = 0,
    ) -> dict[str, int]:
        """
        Calculate the XP for a task based on story \
            points, deadline, actual days, and streak.
        """
        logger.debug(
            "Starting task XP calculation",
            story_points=story_points,
            deadline_days=deadline_days,
            actual_days=actual_days,
            streak=streak,
            spheres=spheres,
        )
        base_xp = self._calculate_base_xp(story_points)
        time_bonus = self._calculate_time_bonus(deadline_days, actual_days)
        streak_bonus = self._calculate_streak_bonus(streak)

        multiplier = time_bonus * streak_bonus
        result = self._distribute_xp(spheres, base_xp, multiplier)
        logger.debug("Task XP calculation finished", xp_per_sphere=result)
        return result

    def get_level_from_xp(self, xp: int) -> int:
        """
        Calculate the level from the given XP.
        """
        logger.debug("Calculating level from XP", xp=xp)
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
        """
        Internal method to fetch the leaderboard from a list of skills.
        """
        if not skills:
            logger.debug("No skills, returning empty leaderboard", limit=limit)
            return []

        user_ids = [skill.user_id for skill in skills]

        logger.debug("Fetching leaderboard users", user_ids=user_ids, limit=limit)
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
        logger.debug("Leaderboard constructed", count=len(leaderboard), limit=limit)
        return leaderboard

    async def get_leaderboard(
        self, sphere: str | None, limit: int = 10
    ) -> list[dict[str, Any]]:
        """
        Fetch the leaderboard for a given sphere, sorted by XP total.
        """
        logger.info("Starting leaderboard fetch", sphere=sphere, limit=limit)
        SEARCH_QUERIES_TOTAL.labels(entity="xp_leaderboard", status="success").inc()
        if sphere:
            task_sphere = TaskSphere(sphere)
            logger.debug(
                "Querying skills for specific sphere", sphere=sphere, limit=limit
            )
            result: ScalarResult[UserSkill] = await self._db.scalars(
                self._user_skill_queries.get_user_skill(sphere=task_sphere).limit(limit)
            )
            skills: list[UserSkill] = list(result)
            leaderboard = await self._get_leaderboard(skills, limit)
            logger.info(
                "Leaderboard fetched for sphere", sphere=sphere, count=len(leaderboard)
            )
            return leaderboard
        logger.debug("No sphere, returning empty leaderboard", limit=limit)
        return []

    def get_title(self, sphere: TaskSphere, level: int) -> str:
        """Get the title for a given sphere and level."""
        logger.debug("Getting title for sphere and level", sphere=sphere, level=level)
        sphere_titles = self._get_sphere_titles()
        titles = sphere_titles.get(sphere.value, {})
        return titles.get(level, f"Level {level}")

    def get_xp_to_next_level(self, xp: int, level: int) -> int:
        """
        Calculate the XP required to reach the next level based on current XP and level.
        """
        logger.debug("Calculating XP to next level", xp=xp, level=level)
        xp_thresholds = self._get_xp_thresholds()
        next_level = min(level + 1, 10)
        next_threshold = xp_thresholds.get(next_level, 15000)
        return max(0, next_threshold - xp)

    def get_progress_percent(self, xp: int, level: int) -> int:
        """
        Calculate the progress percent to the next level based \
            on current XP and level.
        """
        logger.debug("Calculating progress percent to next level", xp=xp, level=level)
        xp_thresholds = self._get_xp_thresholds()
        current = xp_thresholds.get(level, 0)
        next_threshold = xp_thresholds.get(min(level + 1, 10), 15000)
        level_xp = xp - current
        level_range = next_threshold - current
        return min(100, int((level_xp / level_range * 100) if level_range > 0 else 100))

    async def get_or_create_skill(self, user_id: int, sphere: TaskSphere) -> UserSkill:
        """Fetch an existing user skill or create a new one if not found."""
        logger.debug("Fetching or creating user skill", user_id=user_id, sphere=sphere)
        skill = await self._db.scalar(
            self._user_skill_queries.get_user_skill(sphere=sphere, user_id=user_id)
        )

        if not skill:
            logger.info(
                "User skill not found, creating new one", user_id=user_id, sphere=sphere
            )
            skill = UserSkill(user_id=user_id, sphere=sphere)
            self._db.add(skill)
            await self._db.commit()
            XP_CHANGES_TOTAL.labels(direction="skill_create").inc()
            await self._db.refresh(skill)
            logger.info(
                "New user skill created",
                user_id=user_id,
                skill_id=skill.id,
                sphere=sphere,
            )

        logger.debug(
            "User skill retrieved", user_id=user_id, skill_id=skill.id, sphere=sphere
        )
        return skill

    async def _check_daily_cap(self, skill: UserSkill, xp_to_add: int) -> int:
        """Check if the daily XP cap has been reached and return the XP to add."""
        logger.debug(
            "Checking daily XP cap",
            user_id=skill.user_id,
            sphere=skill.sphere,
            xp_to_add=xp_to_add,
        )
        today = datetime.now(UTC).date()
        if skill.last_xp_date and skill.last_xp_date.date() == today:
            remaining = self._max_daily_xp - skill.xp_today
            if remaining <= 0:
                logger.warning(
                    "Daily XP cap reached",
                    user_id=skill.user_id,
                    sphere=skill.sphere,
                    remaining=remaining,
                )
                return 0
            logger.debug(
                "Daily XP cap allows more XP", remaining=remaining, xp_to_add=xp_to_add
            )
            return min(xp_to_add, remaining)
        logger.debug(
            "Current date differs from last XP date, allowing full XP",
            today=today,
            last_date=skill.last_xp_date,
        )
        return xp_to_add

    def _reset_daily_xp(self, skill: UserSkill) -> None:
        """
        Reset the daily XP counter if the current date differs \
            from the last XP date.
        """
        logger.debug(
            "Resetting daily XP counter if new day",
            user_id=skill.user_id,
            sphere=skill.sphere,
        )
        today = datetime.now(UTC).date()
        if not skill.last_xp_date or skill.last_xp_date.date() != today:
            logger.debug(
                "Resetting daily XP counter", user_id=skill.user_id, sphere=skill.sphere
            )
            skill.xp_today = 0

    def _update_xp(self, skill: UserSkill, xp: int) -> None:
        """Update the XP total with daily cap and record the last XP date."""
        logger.debug(
            "Updating XP total with daily cap",
            user_id=skill.user_id,
            sphere=skill.sphere,
            xp=xp,
        )
        skill._old_level = skill.level  # type: ignore[attr-defined]
        old_xp = skill.xp_total
        skill.xp_total = old_xp + min(xp, self._max_daily_xp)
        skill.last_xp_date = datetime.now(UTC)

    def _update_level(self, skill: UserSkill) -> None:
        """Recalculate the level from the current XP total and update the skill."""
        logger.debug(
            "Recalculating level from current XP",
            user_id=skill.user_id,
            sphere=skill.sphere,
            xp_total=skill.xp_total,
        )
        new_level = self.get_level_from_xp(skill.xp_total)
        logger.debug(
            "Level updated",
            user_id=skill.user_id,
            sphere=skill.sphere,
            old_level=skill.level,
            new_level=new_level,
        )
        skill.level = new_level

    def _update_streak(self, skill: UserSkill) -> None:
        """Update the daily streak counter for a skill."""
        logger.debug(
            "Updating daily streak counter",
            user_id=skill.user_id,
            sphere=skill.sphere,
            streak=skill.streak,
        )
        if skill.last_xp_date:
            days_diff = (datetime.now(UTC) - skill.last_xp_date).days
            if days_diff == 1:
                logger.debug(
                    "Streak increased by 1 day",
                    user_id=skill.user_id,
                    sphere=skill.sphere,
                    days_diff=days_diff,
                    streak=skill.streak,
                )
                skill.streak += 1
            elif days_diff > 1:
                logger.debug(
                    "Streak reset after gap",
                    user_id=skill.user_id,
                    sphere=skill.sphere,
                    days_diff=days_diff,
                    streak=skill.streak,
                )
                skill.streak = 1

    async def add_sphere_xp(
        self, user_id: int, sphere: TaskSphere, xp: int
    ) -> tuple[bool, int]:
        """Add XP to a user's sphere and return the result along with the new level."""
        logger.info("Adding XP to user sphere", user_id=user_id, sphere=sphere, xp=xp)
        skill = await self.get_or_create_skill(user_id, sphere)

        if skill.is_frozen:
            logger.info(
                "User skill is frozen, skipping XP addition",
                user_id=user_id,
                sphere=sphere,
                xp=xp,
            )
            return False, skill.level

        self._reset_daily_xp(skill)
        xp_allowed = await self._check_daily_cap(skill, xp)
        if xp_allowed == 0:
            logger.info(
                "Daily XP cap reached, no XP added",
                user_id=user_id,
                sphere=sphere,
                requested_xp=xp,
                allowed_xp=0,
            )
            return False, skill.level

        self._update_xp(skill, xp_allowed)
        self._update_level(skill)
        self._update_streak(skill)

        logger.debug(
            "Committing XP changes to DB",
            user_id=user_id,
            skill_id=skill.id,
            sphere=sphere,
            xp_allowed=xp_allowed,
        )
        await self._db.commit()
        XP_CHANGES_TOTAL.labels(direction="gain").inc()

        leveled_up = skill.level > skill._old_level  # type: ignore[attr-defined]
        logger.info(
            "XP added to user skill",
            user_id=user_id,
            sphere=sphere,
            old_level=skill._old_level,  # type: ignore[attr-defined]
            new_level=skill.level,
            xp=xp_allowed,
            leveled_up=leveled_up,
        )
        return leveled_up, skill.level

    async def _get_user_skills_raw(self, user_id: int) -> Sequence[UserSkill]:
        """Fetch raw user skills from the database without any enrichment."""
        logger.debug("Fetching raw user skills from DB", user_id=user_id)
        result = await self._db.scalars(
            self._user_skill_queries.get_user_skill(user_id=user_id)
        )
        skills = result.all()
        logger.debug("Raw user skills fetched", user_id=user_id, count=len(skills))
        return skills

    def _enrich_skill_with_progress(self, skill: UserSkill) -> UserSkillWithTitle:
        """Enrich a UserSkill with progress information and title."""
        logger.debug(
            "Enriching user skill with progress and title",
            user_id=skill.user_id,
            sphere=skill.sphere,
        )
        title = self.get_title(skill.sphere, skill.level)
        xp_to_next = self.get_xp_to_next_level(skill.xp_total, skill.level)
        progress = self.get_progress_percent(skill.xp_total, skill.level)

        enriched = UserSkillWithTitle(
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
        logger.debug(
            "Skill enriched with progress",
            user_id=skill.user_id,
            sphere=skill.sphere,
            level=skill.level,
            progress=progress,
        )
        return enriched

    async def get_user_skills(self, user_id: int) -> list[UserSkillWithTitle]:
        """Get all skills for a user, enriched with progress information."""
        SEARCH_QUERIES_TOTAL.labels(entity="user_skills", status="success").inc()
        logger.info("Starting fetch of user skills", user_id=user_id)
        skills = await self._get_user_skills_raw(user_id)
        enriched = [self._enrich_skill_with_progress(skill) for skill in skills]
        logger.info(
            "User skills fetched and enriched", user_id=user_id, count=len(enriched)
        )
        return enriched

    async def get_top_skills(
        self, user_id: int, limit: int = 3
    ) -> list[UserSkillWithTitle]:
        """Get the top skills for a user based on their XP total."""
        SEARCH_QUERIES_TOTAL.labels(entity="top_skills", status="success").inc()
        logger.info("Fetching top skills for user", user_id=user_id, limit=limit)
        skills = await self.get_user_skills(user_id)
        top_skills = sorted(skills, key=lambda s: s.xp_total, reverse=True)[:limit]
        logger.info(
            "Top skills calculated", user_id=user_id, limit=limit, count=len(top_skills)
        )
        return top_skills


def get_xp_service(db: AsyncSession = Depends(db_helper.get_session)) -> XPService:
    """Dependency function to provide XPService instance."""
    logger.debug("Dependency get_xp_service creating XPService instance")
    return XPService(
        db=db,
    )
