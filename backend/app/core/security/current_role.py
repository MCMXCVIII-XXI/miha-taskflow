from fastapi import Depends, HTTPException, status

from app.models import User
from app.schemas.user_schemas import UserRole

from .auth import get_current_user


class RoleCurrentUser:
    """Roles for current user."""

    EXCEPTION = HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Only admins can perform this action",
    )

    def guest(self, current_user: User = Depends(get_current_user)) -> User:
        if current_user.role != UserRole.GUEST:
            raise self.EXCEPTION
        return current_user

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

    def lead(self, current_user: User = Depends(get_current_user)) -> User:
        if current_user.role != UserRole.LEAD:
            raise self.EXCEPTION
        return current_user

    def manager(self, current_user: User = Depends(get_current_user)) -> User:
        if current_user.role != UserRole.MANAGER:
            raise self.EXCEPTION
        return current_user

    def admin(self, current_user: User = Depends(get_current_user)) -> User:
        if current_user.role != UserRole.ADMIN:
            raise self.EXCEPTION
        return current_user
