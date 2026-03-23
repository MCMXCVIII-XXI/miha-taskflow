from sqlalchemy import delete
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
        await self.db.execute(delete(RolePermission))
        # Only RBAC tables
        await self.db.execute(delete(Permission))
        await self.db.execute(delete(Role))

    async def init(self) -> None:
        """
        Initial seeding of RBAC

        Details:
            Initial seeding of RBAC
            Adding roles and permissions
            Creating many to many relationship between roles and permissions
        """
        # Clear tables and binds ###########
        async with self.db.begin():
            await self.__clear()
        # Adding data ######################
        async with self.db.begin():
            await self._seed.seed()
        # Binds role and permissions #######
        async with self.db.begin():
            await self._setup.setup_all()


async def init_rbac() -> None:
    """
    Get RBAC
    """
    # Models for RBAC
    # First models this binds "many to many"
    MODELS = (RolePermission, UserRole, Role, Permission)

    # Get RBAC for initial seeding and setup
    async with db_helper.get_session_ctx() as db:  # type: AsyncSession
        rbac = RBAC(
            db=db, models=MODELS, seed=SeedData(db), setup=SetupRolePermissions(db)
        )
        await rbac.init()
