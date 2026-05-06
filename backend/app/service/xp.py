"""XP (Experience Points) service for user leveling and skill tracking.

This module provides the XPService class for managing user experience points,
skill spheres, and leveling progression.

**Key Components:**
* `XPService`: Main service class for XP operations;
* `get_xp_service`: FastAPI dependency injection factory.

**Dependencies:**
* `TaskRepository`: Task data access layer (via BaseService);
* `UserSkillRepository`: User skills data access layer;
* `UserRepository`: User data access layer.

**Usage Example:**
    ```python
    from app.service.xp import get_xp_service

    @router.post("/users/{user_id}/xp")
    async def add_xp(
        user_id: int,
        sphere: TaskSphere,
        xp: int,
        xp_svc: XPService = Depends(get_xp_service)
    ):
        return await xp_svc.add_sphere_xp(user_id, sphere, xp)
    ```

**Notes:**
- XP is earned by completing tasks with different difficulty levels;
- Daily XP cap of 500 points applies;
- Streak bonuses for consecutive days (5+ days = 1.2x, 10+ days = 1.5x);
- Time bonuses for early completion (0.5x - 2x multiplier);
- Skills can be frozen after 60 days of inactivity.
"""

from collections.abc import Sequence
from datetime import UTC, datetime
from typing import Any

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.log import logging
from app.core.metrics import METRICS
from app.db import db_helper
from app.models import UserSkill
from app.schemas import UserSkillWithTitle
from app.schemas.enum import TaskSphere

from .base import XPBaseService
from .transactions.xp import XPTransaction, get_xp_transaction

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
        _task_repo: Repository for task data operations
        _user_repo: Repository for user data operations
        _user_skill_repo: Repository for user skills operations
        _spheres (TaskSphere): Available task spheres enumeration
        _base_rank (BaseRank): Base ranking system
        _xp_thresholds (XPThreshold): XP thresholds for level progression
        _task_difficulty (TaskDifficulty): Task difficulty levels
        _max_daily_xp (int): Maximum XP that can be earned per day (500)
        _frozen_days (int): Number of days skills remain frozen (60)

    Example:
        ```python
        xp_service = XPService(db_session)
        leveled_up, new_level = await xp_service.add_sphere_xp(
            user_id=123,
            sphere=TaskSphere.BACKEND,
            xp=100
        )
        ```
    """

    def __init__(
        self,
        db: AsyncSession,
        xp_transaction: XPTransaction,
    ) -> None:
        """Initialize XPService with database session.

        Args:
            db: SQLAlchemy async database session
        """
        super().__init__(db)
        self._xp_transaction = xp_transaction

    def _calculate_base_xp(self, story_points: int) -> int:
        """Calculate base XP from story points (10 XP per point).

        Args:
            story_points: Number of story points for the task
                Type: int

        Returns:
            int: Base XP (story_points * 10)
        """
        logger.debug("Calculating base XP from story points", story_points=story_points)
        return story_points * 10

    def _calculate_time_bonus(self, deadline_days: int, actual_days: int) -> float:
        """Calculate time bonus multiplier based on deadline adherence.

        Faster completion results in higher bonus (0.5x - 2x range).

        Args:
            deadline_days: Days allocated for the task
                Type: int
            actual_days: Days actually taken to complete
                Type: int

        Returns:
            float: Multiplier between 0.5 and 2.0
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
        """Calculate streak bonus multiplier based on consecutive days.

        5+ days = 1.2x, 10+ days = 1.5x.

        Args:
            streak: Number of consecutive days
                Type: int

        Returns:
            float: Multiplier (1.0, 1.2, or 1.5)
        """
        logger.debug("Calculating streak bonus", streak=streak)

        if streak >= 10:
            return 1.5
        if streak >= 5:
            return 1.2
        return 1.0

    async def get_or_create_skill(self, user_id: int, sphere: TaskSphere) -> UserSkill:
        """Get or create user skill."""
        logger.info(
            "User skill not found, creating new one", user_id=user_id, sphere=sphere
        )
        skill = await self._xp_transaction.get_or_create_skill(
            user_id=user_id, sphere=sphere
        )
        logger.debug(
            "User skill retrieved", user_id=user_id, skill_id=skill.id, sphere=sphere
        )
        return skill

    def _distribute_xp(
        self, spheres: list[dict[str, Any]], base_xp: int, multiplier: float
    ) -> dict[str, int]:
        """Distribute total XP across spheres by weight.

        Args:
            spheres: List of sphere configurations with weights
                Type: list[dict[str, Any]]
                Example: [{"sphere": "BACKEND", "weight": 0.7}]
            base_xp: Base XP before distribution
                Type: int
            multiplier: Overall multiplier
                Type: float

        Returns:
            dict[str, int]: Dictionary mapping sphere names to XP amounts

        Example:
            ```python
            xp_dist = self._distribute_xp(
                [{"sphere": "BACKEND", "weight": 0.5},
                 {"sphere": "FRONTEND", "weight": 0.5}],
                100,
                1.2
            )
            # Returns: {"BACKEND": 60, "FRONTEND": 60}
            ```
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
        spheres: list[dict[str, Any]],
        story_points: int = 1,
        deadline_days: int = 7,
        actual_days: int = 7,
        streak: int = 0,
    ) -> dict[str, int]:
        """Calculate XP distribution across spheres for a task.

        Combines base XP, time bonus, and streak bonus to calculate
        final XP distribution across multiple spheres.

        Args:
            spheres: List of sphere configurations with weights
                Type: list[dict[str, Any]]
                Example: [{"sphere": "BACKEND", "weight": 0.7}]
            story_points: Number of story points for the task
                Type: int
                Defaults to 1
            deadline_days: Days allocated for the task
                Type: int
                Defaults to 7
            actual_days: Days actually taken to complete
                Type: int
                Defaults to 7
            streak: Number of consecutive days
                Type: int
                Defaults to 0

        Returns:
            dict[str, int]: Dictionary mapping sphere names to XP amounts

        Example:
            ```python
            xp_dist = await xp_svc.calculate_task_xp(
                [{"sphere": "BACKEND", "weight": 1.0}],
                story_points=3,
                deadline_days=7,
                actual_days=5,
                streak=3
            )
            # Returns: {"BACKEND": 36}
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
        """Calculate level from total XP using dynamic thresholds.

        Args:
            xp: Total XP amount
                Type: int

        Returns:
            int: Current level (1-10)

        Example:
            ```python
            level = xp_service.get_level_from_xp(500)
            # Returns: 3 (or appropriate level based on thresholds)
            ```
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
        """Build leaderboard data from user skills.

        Args:
            skills: List of UserSkill records
                Type: list[UserSkill]
            limit: Maximum number of entries
                Type: int

        Returns:
            list[dict[str, Any]]: Leaderboard entries with user data

        Example:
            ```python
            leaderboard = await self._get_leaderboard(skills, 10)
            ```
        """
        if not skills:
            logger.debug("No skills, returning empty leaderboard", limit=limit)
            return []

        user_ids = [skill.user_id for skill in skills]

        logger.debug("Fetching leaderboard users", user_ids=user_ids, limit=limit)
        users_result = await self._user_repo.find_many(id_in=user_ids, is_active=True)
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
        """Get leaderboard for a specific sphere or all spheres.

        Args:
            sphere: Optional sphere name to filter by
                Type: str | None
                Defaults to None (all spheres)
            limit: Maximum number of entries
                Type: int
                Defaults to 10

        Returns:
            list[dict[str, Any]]: Leaderboard entries sorted by XP

        Raises:
            None

        Example:
            ```python
            leaderboard = await xp_svc.get_leaderboard("BACKEND", 10)
            ```
        """
        logger.info("Starting leaderboard fetch", sphere=sphere, limit=limit)
        METRICS.SEARCH_QUERIES_TOTAL.labels(
            entity="xp_leaderboard", status="success"
        ).inc()
        if sphere:
            task_sphere = TaskSphere(sphere)
            result = await self._user_skill_repo.get_user_skill_select(
                sphere=task_sphere, limit=limit
            )
            skills = list(result)
            leaderboard = await self._get_leaderboard(skills, limit)

            logger.info(
                "Leaderboard retrieved: sphere={sphere}, count={count}",
                sphere=sphere,
                count=len(leaderboard),
            )

            return leaderboard
        logger.debug("No sphere, returning empty leaderboard", limit=limit)
        return []

    def get_title(self, sphere: TaskSphere, level: int) -> str:
        """Get dynamic title for a sphere at a given level.

        Args:
            sphere: The task sphere
                Type: TaskSphere
            level: Current level
                Type: int

        Returns:
            str: Title string or "Level {level}" if no title defined

        Example:
            ```python
            title = xp_service.get_title(TaskSphere.BACKEND, 5)
            # Returns: "Senior Developer" or similar
        """
        logger.debug("Getting title for sphere and level", sphere=sphere, level=level)
        sphere_titles = self._get_sphere_titles()
        titles = sphere_titles.get(sphere.value, {})
        return titles.get(level, f"Level {level}")

    def get_xp_to_next_level(self, xp: int, level: int) -> int:
        """Get the XP required to reach the next level.

        Args:
            xp: Current XP amount
                Type: int
            level: Current level
                Type: int

        Returns:
            int: XP needed for next level (0 if at max level)

        Example:
            ```python
            needed = xp_service.get_xp_to_next_level(500, 3)
            # Returns: 150 (or appropriate threshold difference)
        """
        logger.debug("Calculating XP to next level", xp=xp, level=level)
        xp_thresholds = self._get_xp_thresholds()
        next_level = min(level + 1, 10)
        next_threshold = xp_thresholds.get(next_level, 15000)
        return max(0, next_threshold - xp)

    def get_progress_percent(self, xp: int, level: int) -> int:
        """Get the progress percentage towards the next level.

        Args:
            xp: Current XP amount
                Type: int
            level: Current level
                Type: int

        Returns:
            int: Progress percentage (0-100)

        Example:
            ```python
            progress = xp_service.get_progress_percent(500, 3)
            # Returns: 75 (75% towards next level)
        """
        logger.debug("Calculating progress percent to next level", xp=xp, level=level)
        xp_thresholds = self._get_xp_thresholds()
        current = xp_thresholds.get(level, 0)
        next_threshold = xp_thresholds.get(min(level + 1, 10), 15000)
        level_xp = xp - current
        level_range = next_threshold - current
        return min(100, int((level_xp / level_range * 100) if level_range > 0 else 100))

    async def _check_daily_cap(self, skill: UserSkill, xp_to_add: int) -> int:
        """Check and enforce daily XP cap.

        Args:
            skill: User skill to check.
                Type: UserSkill
            xp_to_add: Amount of XP trying to add.
                Type: int

        Returns:
            int: Actual XP that can be added (may be less than requested due to cap).
        """
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
        """Reset daily XP counter if new day.

        Args:
            skill: User skill to reset.
                Type: UserSkill
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
        """Update XP total with daily cap.

        Args:
            skill: User skill to update.
                Type: UserSkill
            xp: XP amount to add.
                Type: int
        """
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
        """Recalculate level from current XP.

        Args:
            skill: User skill to update.
                Type: UserSkill
        """
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
        """Update daily streak counter.

        Args:
            skill: User skill to update.
                Type: UserSkill
        """
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
        """Add XP to user sphere and handle leveling/streaks.

        Applies XP to the user's skill in the specified sphere,
        handling streak updates, level recalculations, and daily caps.

        Args:
            user_id: ID of the user
                Type: int
            sphere: The sphere to add XP to
                Type: TaskSphere
            xp: Amount of XP to add
                Type: int

        Returns:
            tuple[bool, int]: Tuple of (leveled_up boolean, new_level int)
        """
        logger.info("Adding XP to user sphere", user_id=user_id, sphere=sphere, xp=xp)

        skill = await self.get_or_create_skill(user_id, sphere)

        if skill.is_frozen:
            logger.info("User skill is frozen, skipping XP addition", ...)
            return False, skill.level

        self._reset_daily_xp(skill)
        xp_allowed = await self._check_daily_cap(skill, xp)
        if xp_allowed == 0:
            logger.info("Daily XP cap reached, no XP added", ...)
            return False, skill.level

        logger.debug("Committing XP changes to DB", ...)

        _, new_level = await self._xp_transaction.add_sphere_xp(
            user_id=user_id,
            sphere=sphere,
            xp=xp_allowed,
        )

        self._reset_daily_xp(skill)
        xp_allowed = await self._check_daily_cap(skill=skill, xp_to_add=xp)
        if xp_allowed == 0:
            METRICS.XP_CHANGES_TOTAL.labels(
                direction="add", status="failure", sphere=sphere
            ).inc()
            return False, skill.level

        self._update_xp(skill, xp_allowed)
        self._update_level(skill)
        self._update_streak(skill)

        leveled_up = new_level > skill.level
        logger.info(
            "XP added: user_id={user_id}, sphere={sphere}, \
                xp={xp}, new_level={level}, leveled_up={leveled_up}",
            user_id=user_id,
            sphere=sphere.value,
            xp=xp,
            level=new_level,
            leveled_up=leveled_up,
        )
        METRICS.XP_CHANGES_TOTAL.labels(
            direction="add", status="success", sphere=sphere.value
        ).inc()
        return leveled_up, new_level

    async def _get_user_skills_raw(self, user_id: int) -> Sequence[UserSkill]:
        """Fetch raw UserSkill records from DB.

        Args:
            user_id: ID of the user
                Type: int

        Returns:
            Sequence[UserSkill]: User skill records
        """
        logger.debug("Raw user skills fetched", user_id=user_id)
        return await self._user_skill_repo.by_user(user_id=user_id)

    def _enrich_skill_with_progress(self, skill: UserSkill) -> UserSkillWithTitle:
        """Add title, progress, and XP to next level.

        Args:
            skill: User skill to enrich
                Type: UserSkill

        Returns:
            UserSkillWithTitle: Enriched skill with additional fields
        """
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
        """Get all user skills with progress and titles.

        Args:
            user_id: ID of the user
                Type: int

        Returns:
            list[UserSkillWithTitle]: User skills with enriched data

        Example:
            ```python
            skills = await xp_svc.get_user_skills(123)
            ```
        """
        METRICS.SEARCH_QUERIES_TOTAL.labels(
            entity="user_skills", status="success"
        ).inc()
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
        """Get top N skills for a user by XP.

        Args:
            user_id: ID of the user
                Type: int
            limit: Maximum number of skills to return
                Type: int
                Defaults to 3

        Returns:
            list[UserSkillWithTitle]: Top skills sorted by XP

        Example:
            ```python
            top_skills = await xp_svc.get_top_skills(123, 5)
            ```
        """
        METRICS.SEARCH_QUERIES_TOTAL.labels(entity="top_skills", status="success").inc()
        logger.info("Fetching top skills for user", user_id=user_id, limit=limit)
        skills = await self.get_user_skills(user_id)
        top_skills = sorted(skills, key=lambda s: s.xp_total, reverse=True)[:limit]
        logger.info(
            "Top skills calculated", user_id=user_id, limit=limit, count=len(top_skills)
        )
        return top_skills


def get_xp_service(
    db: AsyncSession = Depends(db_helper.get_session),
    xp_transaction: XPTransaction = Depends(get_xp_transaction),
) -> XPService:
    """Create XPService instance with dependency injection.

    Factory function for FastAPI dependency injection that creates and configures
    an XPService instance with all required dependencies.

    Args:
        db: Database session from FastAPI dependency injection.
            Type: AsyncSession.

    Returns:
        XPService: Configured XP service instance

    Example:
        ```python
        @router.post("/users/{user_id}/xp")
        async def add_xp(
            user_id: int,
            sphere: TaskSphere,
            xp: int,
            xp_svc: XPService = Depends(get_xp_service)
        ):
            return await xp_svc.add_sphere_xp(user_id, sphere, xp)
        ```
    """
    return XPService(
        db=db,
        xp_transaction=xp_transaction,
    )
