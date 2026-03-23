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
            Role(name="USER", description="Basic user"),
            Role(name="MEMBER", description="Member"),
            Role(name="GROUP_ADMIN", description="Group admin"),
            Role(name="TASK_LEADER", description="Task leader"),
            Role(name="ADMIN", description="Admin app"),
        ]
        self.permissions = [
            Permission.create(resource="user", action="view", description="View user"),
            Permission.create(
                resource="user", action="create", description="Create user"
            ),
            Permission.create(
                resource="user", action="update", description="Update user"
            ),
            Permission.create(
                resource="user", action="delete", description="Delete user"
            ),
            Permission.create(
                resource="group", action="view", description="View group"
            ),
            Permission.create(
                resource="group", action="manage", description="Manage group"
            ),
            Permission.create(
                resource="group", action="create", description="Create group"
            ),
            Permission.create(
                resource="group", action="delete", description="Delete group"
            ),
            Permission.create(resource="task", action="view", description="View task"),
            Permission.create(
                resource="task", action="create", description="Create task"
            ),
            Permission.create(
                resource="task", action="update", description="Update task"
            ),
            Permission.create(
                resource="task", action="delete", description="Delete task"
            ),
        ]

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
