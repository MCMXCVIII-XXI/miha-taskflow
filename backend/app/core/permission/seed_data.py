from sqlalchemy.dialects.postgresql import insert
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
        if self.roles:
            stmt = insert(Role).values(
                [{"name": r.name, "description": r.description} for r in self.roles]
            )
            await self.db.execute(stmt.on_conflict_do_nothing(index_elements=["name"]))

        if self.permissions:
            stmt = insert(Permission).values(
                [
                    {
                        "name": p.name,
                        "resource": p.resource,
                        "action": p.action,
                        "context": p.context,
                        "description": p.description,
                    }
                    for p in self.permissions
                ]
            )
            await self.db.execute(stmt.on_conflict_do_nothing(index_elements=["name"]))
        await self.db.commit()
