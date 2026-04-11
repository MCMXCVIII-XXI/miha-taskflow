from sqlalchemy import Select, select

from app.models import UserSkill
from app.schemas.enum import TaskSphere


class UserSkillQueries:
    """
    Provides query builders for UserSkill-related operations.

    All methods return SQLAlchemy Select[tuple[UserSkill]] objects
    that can be executed by services; no results are fetched directly.
    Filtering is optional and combined via AND logic.
    """

    @staticmethod
    def get_user_skill(
        id: int | None = None,
        user_id: int | None = None,
        sphere: TaskSphere | None = None,
        xp_total: int | None = None,
        level: int | None = None,
        streak: int | None = None,
        is_frozen: bool | None = None,
    ) -> Select[tuple[UserSkill]]:
        """
        Builds a query to filter UserSkill records by multiple optional criteria.

        All filters are combined with AND. If a parameter is None, it is ignored.

        Args:
            id: Filter by skill ID.
            user_id: Filter by user ID.
            sphere: Filter by task sphere (enum value).
            xp_total: Filter by total XP.
            level: Filter by level.
            streak: Filter by daily streak.
            is_frozen: Filter by frozen state.

        Returns:
            Select[tuple[UserSkill]] query for matching UserSkill rows.
        """
        base = select(UserSkill)

        if id is not None:
            base = base.where(UserSkill.id == id)
        if user_id is not None:
            base = base.where(UserSkill.user_id == user_id)
        if sphere is not None:
            base = base.where(UserSkill.sphere == sphere)
        if xp_total is not None:
            base = base.where(UserSkill.xp_total == xp_total)
        if level is not None:
            base = base.where(UserSkill.level == level)
        if streak is not None:
            base = base.where(UserSkill.streak == streak)
        if is_frozen is not None:
            base = base.where(UserSkill.is_frozen == is_frozen)

        return base

    @staticmethod
    def by_user(user_id: int) -> Select[tuple[UserSkill]]:
        """
        Convenience method to get all skills for a given user.

        Args:
            user_id: ID of the user.

        Returns:
            Select[tuple[UserSkill]] query for all user skills.
        """
        return select(UserSkill).where(UserSkill.user_id == user_id)

    @staticmethod
    def by_sphere(user_id: int, sphere: TaskSphere) -> Select[tuple[UserSkill]]:
        """
        Convenience method to get a specific skill by user and sphere.

        Args:
            user_id: ID of the user.
            sphere: Skill sphere (enum).

        Returns:
            Select[tuple[UserSkill]] query for the requested skill; may be empty.
        """
        return (
            select(UserSkill)
            .where(UserSkill.user_id == user_id)
            .where(UserSkill.sphere == sphere)
        )
