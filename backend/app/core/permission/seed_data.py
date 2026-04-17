from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Permission, Role

from .permissions import PERMISSIONS, ROLES


class SeedData:
    """
    Seed data for RBAC

    Attribute:
        db (AsyncSession): The database session.
        roles (list[Role]): The list of roles to seed.
        permissions (list[Permission]): The list of permissions to seed.

    Details:
        This class provides methods to seed roles and permissions into the database.
        It uses the `roles` and `permissions` attributes to insert data into database.
        The `seed` method is used to seed the database with the roles and permissions.
        Permissions template: {resource}:{action}[:context]
    """

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.roles = ROLES
        self.permissions = PERMISSIONS

    async def seed(self) -> None:
        """Seed roles and permissions into the database."""
        for role in self.roles:
            result = await self.db.scalars(select(Role).where(Role.name == role.name))
            if not result.first():
                self.db.add(role)

        for permission in self.permissions:
            if not await self._permission_exists(
                permission.resource,
                permission.action,
                permission.context,
                permission.description,
            ):
                self.db.add(permission)

        await self.db.flush()
        await self.db.commit()

    async def _permission_exists(
        self,
        resource: str,
        action: str,
        context: str | None,
        description: str | None = None,
    ) -> bool:
        """Check if a permission exists by resource+action+context"""
        query = select(Permission).where(
            Permission.resource == resource,
            Permission.action == action,
            Permission.context == context if context else Permission.context.is_(None),
        )
        result = await self.db.scalars(query)
        return result.first() is not None
