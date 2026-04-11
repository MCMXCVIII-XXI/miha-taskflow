from sqlalchemy import Select, select

from app.models import Role


class RoleQueries:
    """
    Query builders for Role-related operations.

    Provides reusable Select[tuple[Role]] and Select[tuple[int]] builders
    for filtering roles by ID or name. All filters are combined with AND.
    """

    @staticmethod
    def _build_role_query(
        base: Select[tuple[Role]],
        id: int | None = None,
        name: str | None = None,
    ) -> Select[tuple[Role]]:
        """
        Builds filters for a Role query.

        Args:
            base: Base role query (e.g. `select(Role)`).
            id: Filter by role ID.
            name: Filter by role name.

        Returns:
            Select[tuple[Role]] with applied filters.
        """
        if id is not None:
            base = base.where(Role.id == id)
        if name is not None:
            base = base.where(Role.name == name)
        return base

    @staticmethod
    def _build_role_id_query(
        base: Select[tuple[int]],
        id: int | None = None,
        name: str | None = None,
    ) -> Select[tuple[int]]:
        """
        Builds filters for a Role ID-only query.

        Args:
            base: Base role.id query (e.g. `select(Role.id)`).
            id: Filter by role ID.
            name: Filter by role name.

        Returns:
            Select[tuple[int]] with applied filters.
        """
        if id is not None:
            base = base.where(Role.id == id)
        if name is not None:
            base = base.where(Role.name == name)
        return base

    @staticmethod
    def get_role(
        id: int | None = None,
        name: str | None = None,
    ) -> Select[tuple[Role]]:
        """
        Builds a query to retrieve roles by filters.

        Args:
            id: Filter by role ID.
            name: Filter by role name.

        Returns:
            Select[tuple[Role]] for matching roles.
        """
        base = select(Role)
        return RoleQueries._build_role_query(base, id=id, name=name)

    @staticmethod
    def get_role_id(
        id: int | None = None,
        name: str | None = None,
    ) -> Select[tuple[int]]:
        """
        Builds a query to retrieve only role IDs by filters.

        Args:
            id: Filter by role ID.
            name: Filter by role name.

        Returns:
            Select[tuple[int]] for IDs of matching roles.
        """
        base = select(Role.id)
        return RoleQueries._build_role_id_query(base, id=id, name=name)
