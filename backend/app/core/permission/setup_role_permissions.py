from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Permission, Role, RolePermission


class SetupRolePermissions:
    """
    Setup role permissions

    Details:
        This class is responsible for setting up permissions for roles in the database.
        It includes methods for setting up member.


    """

    def __init__(self, db: AsyncSession) -> None:
        """
        db (AsyncSession): Database session
        member_perms (list[str]): List of member permissions
        group_admin_perms (list[str]): List of group admin permissions
        task_leader_perms (list[str]): List of task leader permissions
        all_perms (list[str]): List of all permissions
        """
        self.db = db
        self.member_perms = ["user:view", "group:view", "task:view", "task:create"]
        self.group_admin_perms = [
            "user:create",
            "user:update",
            "user:delete",
            "group:manage",
            "group:create",
            "group:delete",
            "task:update",
        ]
        self.task_leader_perms = ["task:delete"]
        self.all_perms = None

    async def __get_role(self, name_role: str) -> Role | None:
        """
        Get role by name
        """
        result = await self.db.scalars(select(Role).where(Role.name == name_role))
        return result.first()

    async def __get_permission(self, name_perm: str) -> Permission | None:
        """
        Get permission by name
        """
        result = await self.db.scalars(
            select(Permission).where(Permission.name == name_perm)
        )
        return result.first()

    async def __add_role_permission(
        self, role: Role | None, perm_names: Sequence[str]
    ) -> None:
        """
        Add role permission
        """
        for perm_name in perm_names:
            perm = await self.__get_permission(perm_name)
            if perm and role:
                rp = RolePermission(role_id=role.id, permission_id=perm.id)
                self.db.add(rp)

    # A pyramid of roles is organized here ##########################################
    async def setup_member(self) -> None:
        role = await self.__get_role(name_role="MEMBER")
        await self.__add_role_permission(role=role, perm_names=self.member_perms)

    async def setup_group_admin(self) -> None:
        all_perms = self.member_perms + self.group_admin_perms
        role = await self.__get_role(name_role="GROUP_ADMIN")
        await self.__add_role_permission(role=role, perm_names=all_perms)

    async def setup_task_leader(self) -> None:
        all_perms = self.member_perms + self.task_leader_perms
        role = await self.__get_role(name_role="TASK_LEADER")
        await self.__add_role_permission(role=role, perm_names=all_perms)

    async def setup_admin(self) -> None:
        result = await self.db.scalars(select(Permission.name))
        all_perms = result.all()
        role = await self.__get_role(name_role="ADMIN")
        await self.__add_role_permission(role=role, perm_names=all_perms)

    #################################################################################

    async def setup_all(self) -> None:
        await self.setup_member()
        await self.setup_group_admin()
        await self.setup_task_leader()
        await self.setup_admin()

        await self.db.commit()
