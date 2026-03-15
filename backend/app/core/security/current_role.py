from fastapi import Depends

from app.models import User
from app.schemas.user_schemas import UserRole

from ..exceptions import security_exc
from .auth import get_current_user


class RoleCurrentUser:
    """Roles for current user."""

    def __init__(self):
        self.EXCEPTION = security_exc.SecurityNotAuthorized

    def member(self, current_user: User = Depends(get_current_user)) -> User:
        if current_user.role != UserRole.MEMBER:
            raise self.EXCEPTION
        return current_user

    def admin_groups(
        self,
        current_user: User = Depends(get_current_user),
    ) -> User:
        if current_user.role != UserRole.GROUP_ADMIN:
            raise self.EXCEPTION
        return current_user

    def task_leader(self, current_user: User = Depends(get_current_user)) -> User:
        if current_user.role != UserRole.TASK_LEADER:
            raise self.EXCEPTION
        return current_user

    def admin(self, current_user: User = Depends(get_current_user)) -> User:
        if current_user.role != UserRole.ADMIN:
            raise self.EXCEPTION
        return current_user
