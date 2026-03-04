from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security.hash import get_password_hash
from app.models import User
from app.schemas.user_schemas import UserCreate, UserUpdate

from .crud_result import CrudResultUser


async def get_users(
    db: AsyncSession, skip: int = 0, limit: int = 100
) -> Sequence[User]:
    users = await db.scalars(
        select(User).order_by(User.id).where(User.is_active).offset(skip).limit(limit)
    )
    return users.all()


async def get_user(user_id: int, db: AsyncSession) -> User | CrudResultUser:
    result = await db.scalars(select(User).where(User.id == user_id, User.is_active))
    user = result.first()

    if not user:
        return CrudResultUser.NOT_FOUND

    return user


async def create_user(user_in: UserCreate, db: AsyncSession) -> User | CrudResultUser:
    result = await db.scalars(
        select(User).where(
            (User.email == user_in.email) | (User.username == user_in.username),
            User.is_active,
        )
    )
    check = result.first()
    if check:
        if check.username == user_in.username:
            return CrudResultUser.USERNAME_CONFLICT
        elif check.email == user_in.email:
            return CrudResultUser.EMAIL_CONFLICT

    user = User(
        username=user_in.username,
        email=user_in.email,
        first_name=user_in.first_name,
        last_name=user_in.last_name,
        patronymic=user_in.patronymic,
        hashed_password=get_password_hash(user_in.hashed_password.get_secret_value()),
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def update_user(
    user_id: int, user_in: UserUpdate, db: AsyncSession
) -> User | CrudResultUser:
    result = await db.scalars(select(User).where(User.id == user_id, User.is_active))
    user = result.first()

    if not user:
        return CrudResultUser.NOT_FOUND

    update_data = user_in.model_dump(exclude_unset=True)

    # Check if user with this email or username already exists
    ###########################################################################
    result = await db.scalars(
        select(User).where(
            (User.email == update_data["email"])
            | (User.username == update_data["username"]),
            User.id != user_id,
            User.is_active,
        )
    )
    check = result.first()
    if check:
        if check.email == update_data["email"]:
            return CrudResultUser.EMAIL_CONFLICT
        elif check.username == update_data["username"]:
            return CrudResultUser.USERNAME_CONFLICT
    ###########################################################################

    for field, value in update_data.items():
        setattr(user, field, value)

    await db.commit()
    await db.refresh(user)
    return user


async def delete_user(user_id: int, db: AsyncSession) -> bool | CrudResultUser:
    result = await db.scalars(select(User).where(User.id == user_id, User.is_active))
    user = result.first()

    if not user:
        return CrudResultUser.NOT_FOUND

    user.is_active = False
    await db.commit()
    return True
