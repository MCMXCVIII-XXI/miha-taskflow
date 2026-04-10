from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Permission, Role, RolePermission

from .role_permissions import (
    ADMIN_PERMISSIONS,
    ASSIGNEE_PERMISSIONS,
    GROUP_ADMIN_PERMISSIONS,
    MEMBER_PERMISSIONS,
    USER_PERMISSIONS,
)


class SetupRolePermissions:
    """
    Setup role permissions

    Details:
        This class is responsible for setting up permissions for roles in the database.
        It includes methods for setting up member.

    Attributes:
        db (AsyncSession): Database session
        user_perms (list[str]): List of user permissions
        member_perms (list[str]): List of member permissions
        group_admin_perms (list[str]): List of group admin permissions
        task_leader_perms (list[str]): List of task leader permissions
        all_perms (list[str]): List of all permissions

    Methods:
        setup_user: Set up user permissions
        setup_member: Set up member permissions
        setup_assignee: Set up assignee permissions
        setup_group_admin: Set up group admin permissions
        setup_admin: Set up admin permissions
        setup_all: Set up all permissions
    """

    def __init__(self, db: AsyncSession) -> None:
        """
        db (AsyncSession): Database session
        user_perms (list[str]): List of user permissions
        member_perms (list[str]): List of member permissions
        assignee_perms (list[str]): List of assignee permissions
        group_admin_perms (list[str]): List of group admin permissions
        all_perms (list[str]): List of all permissions
        """
        self.db = db
        self.user_perms = USER_PERMISSIONS
        self.member_perms = MEMBER_PERMISSIONS
        self.assignee_perms = ASSIGNEE_PERMISSIONS
        self.group_admin_perms = GROUP_ADMIN_PERMISSIONS
        self.admin_perms = ADMIN_PERMISSIONS

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
        self,
        role: Role | None,
        perm_names: set[str] | Sequence[Permission],
    ) -> None:
        """
        Add role permission
        """
        for perm_name in perm_names:
            name = perm_name.name if isinstance(perm_name, Permission) else perm_name
            perm = await self.__get_permission(name)
            if perm and role:
                rp = RolePermission(role_id=role.id, permission_id=perm.id)
                self.db.add(rp)

    # A pyramid of roles is organized here ##########################################
    async def setup_user(self) -> None:
        role = await self.__get_role(name_role="USER")
        await self.__add_role_permission(role=role, perm_names=self.user_perms)

    async def setup_member(self) -> None:
        all_perms = self.user_perms | self.member_perms
        role = await self.__get_role(name_role="MEMBER")
        await self.__add_role_permission(role=role, perm_names=all_perms)

    async def setup_assignee(self) -> None:
        all_perms = self.user_perms | self.assignee_perms
        role = await self.__get_role(name_role="ASSIGNEE")
        await self.__add_role_permission(role=role, perm_names=all_perms)

    async def setup_group_admin(self) -> None:
        all_perms = self.user_perms | self.member_perms | self.group_admin_perms
        role = await self.__get_role(name_role="GROUP_ADMIN")
        await self.__add_role_permission(role=role, perm_names=all_perms)

    async def setup_admin(self) -> None:
        role = await self.__get_role(name_role="ADMIN")
        await self.__add_role_permission(role=role, perm_names=self.admin_perms)

    #################################################################################

    async def setup_all(self) -> None:
        await self.setup_user()
        await self.setup_member()
        await self.setup_assignee()
        await self.setup_group_admin()
        await self.setup_admin()

        await self.db.commit()
