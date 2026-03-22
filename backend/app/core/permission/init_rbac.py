from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import Base, db_helper
from app.models import Permission, Role, RolePermission, UserRole

from .seed_data import SeedData
from .setup_role_permissions import SetupRolePermissions


class RBAC:
    """
    Class for working with RBAC

    Details:
        This class is responsible for working with RBAC.
        It includes methods for checking if tables exist,
        adding data, clearing tables, and binding roles and permissions.

        Init should be done after migrations.

        seed: instance of class SeedData
        setup: instance of class SetupRolePermissions

    Args:
        db (AsyncSession): Database session
        models (tuple[type[Base], ...]): Models for RBAC
        seed (SeedData): Seed data for RBAC
        setup (SetupRolePermissions): Setup role permissions
    """

    def __init__(
        self,
        db: AsyncSession,
        models: tuple[type[Base], ...],
        seed: SeedData,
        setup: SetupRolePermissions,
    ) -> None:
        self.db = db
        self.models = models
        self._seed = seed
        self._setup = setup

    async def __clear(self) -> None:
        """Clear RBAC tables and binds"""
        # Role↔Permission
        await self.db.scalars(delete(RolePermission))
        # Only RBAC tables
        await self.db.scalars(delete(Permission))
        await self.db.scalars(delete(Role))

    async def init(self) -> None:
        """
        Initial seeding of RBAC
        """
        async with self.db.begin():
            # Clear tables and binds ###########
            await self.__clear()
            # Adding data ######################
            await self._seed.seed()
            # Binds role and permissions #######
            await self._setup.setup_all()


async def init_rbac() -> RBAC:
    """
    Get RBAC
    """
    # Models for RBAC
    # First models this binds "many to many"
    MODELS = (RolePermission, UserRole, Role, Permission)

    # Get RBAC for initial seeding and setup
    async with db_helper.get_session_ctx() as db:
        rbac = RBAC(
            db=db, models=MODELS, seed=SeedData(db), setup=SetupRolePermissions(db)
        )
        await rbac.init()
