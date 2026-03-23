from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Permission, Role


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
        self.roles = [
            Role(name="MEMBER", description="Basic user"),
            Role(name="GROUP_ADMIN", description="Group admin"),
            Role(name="TASK_LEADER", description="Task leader"),
            Role(name="ADMIN", description="Admin app"),
        ]
        self.permissions = [
            # User ####################################################################
            Permission(name="user:view", resource="user", action="view"),
            Permission(name="user:create", resource="user", action="create"),
            Permission(name="user:update", resource="user", action="update"),
            Permission(name="user:delete", resource="user", action="delete"),
            # Group ###################################################################
            Permission(name="group:view", resource="group", action="view"),
            Permission(name="group:manage", resource="group", action="manage"),
            Permission(name="group:create", resource="group", action="create"),
            Permission(name="group:delete", resource="group", action="delete"),
            # Task ####################################################################
            Permission(name="task:view", resource="task", action="view"),
            Permission(name="task:create", resource="task", action="create"),
            Permission(name="task:update", resource="task", action="update"),
            Permission(name="task:delete", resource="task", action="delete"),
            ############################################################################
        ]

    async def seed(self) -> None:
        """
        Add roles and permissions to the database
        """
        for obj in self.roles + self.permissions:
            result = await self.db.scalars(
                select(type(obj)).where(type(obj).name == obj.name)
            )
            if not result.first():
                self.db.add(obj)

        await self.db.commit()
