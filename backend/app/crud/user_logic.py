from collections.abc import Sequence

import jwt
from fastapi import Depends
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security.hash import get_password_hash
from app.db import db_helper
from app.models import User as UserModel
from app.models import UserGroupMembership as UserGroupMembershipModel
from app.schemas.token_schemas import (
    AccessTokenRequest,
    RefreshTokenRequest,
    TokenResponse,
)
from app.schemas.user_schemas import UserCreate, UserRole, UserUpdate

from .exceptions import user_exc


async def get_users(
    db: AsyncSession, skip: int = 0, limit: int = 100
) -> Sequence[UserModel]:
    users = await db.scalars(
        select(UserModel)
        .order_by(UserModel.id)
        .where(UserModel.is_active)
        .offset(skip)
        .limit(limit)
    )
    return users.all()


async def get_user(user_id: int, db: AsyncSession) -> UserModel:
    result = await db.scalars(
        select(UserModel).where(UserModel.id == user_id, UserModel.is_active)
    )
    user = result.first()

    if not user:
        raise user_exc.UserNotFound()

    return user


async def create_user(user_in: UserCreate, db: AsyncSession) -> UserModel:
    result = await db.scalars(
        select(UserModel).where(
            (UserModel.email == user_in.email)
            | (UserModel.username == user_in.username),
            UserModel.is_active,
        )
    )
    check = result.first()
    if check:
        if check.username == user_in.username:
            raise user_exc.UserUsernameConflict()
        elif check.email == user_in.email:
            raise user_exc.UserEmailConflict()

    user = UserModel(
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


async def update_user(user_id: int, user_in: UserUpdate, db: AsyncSession) -> UserModel:
    try:
        user = await get_user(user_id, db)
    except user_exc.UserNotFound as e:
        raise e

    if not user:
        raise user_exc.UserNotFound()

    update_data = user_in.model_dump(exclude_unset=True)

    # Check if user with this email or username already exists
    ###########################################################################
    result = await db.scalars(
        select(UserModel).where(
            (UserModel.email == update_data["email"])
            | (UserModel.username == update_data["username"]),
            UserModel.id != user_id,
            UserModel.is_active,
        )
    )
    check = result.first()
    if check:
        if check.email == update_data["email"]:
            raise user_exc.UserEmailConflict()
        elif check.username == update_data["username"]:
            raise user_exc.UserUsernameConflict()
    ###########################################################################

    for field, value in update_data.items():
        setattr(user, field, value)

    await db.commit()
    await db.refresh(user)
    return user


async def delete_user(user_id: int, db: AsyncSession) -> bool:
    try:
        user = await get_user(user_id, db)
    except user_exc.UserNotFound as e:
        raise e

    user.is_active = False
    await db.commit()
    return True


async def login(
    from_data: OAuth2PasswordRequestForm,
    db: AsyncSession,
) -> TokenResponse | SecurityResultAuth | CrudResultUser:
    result = await db.scalars(
        select(UserModel).where(
            (UserModel.email == from_data.username),
            UserModel.is_active,
        )
    )
    user = result.first()
    if not user:
        return CrudResultUser.NOT_FOUND
    if not verify_password(from_data.password, user.hashed_password):
        return SecurityResultAuth.COULD_NOT_VERIFY

    access_token = create_access_token(
        data={
            "sub": str(user.id),
            "username": user.username,
            "email": user.email,
            "role": str(user.role),
        }
    )
    refresh_token = create_refresh_token(
        data={
            "sub": str(user.id),
            "email": user.email,
            "username": user.username,
            "role": str(user.role),
        }
    )
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
    )


async def access_token(
    body: AccessTokenRequest,
    db: AsyncSession,
) -> TokenResponse | SecurityResultAuth:
    access_token = body.access_token

    try:
        payload = decode_token(access_token)
        user_id = payload.get("sub")
        email = payload.get("email")
        token_type = payload.get("token_type")

        if user_id is None or token_type != "access":  # noqa: S105
            return SecurityResultAuth.ACCESS_TOKEN_ERROR

    except jwt.ExpiredSignatureError:
        return SecurityResultAuth.EXPIRED
    except jwt.PyJWTError:
        return SecurityResultAuth.ACCESS_TOKEN_ERROR

    result = await db.scalars(
        select(UserModel).where(UserModel.id == user_id, UserModel.is_active)
    )
    user = result.first()

    if user is None:
        return SecurityResultAuth.REFRESH_TOKEN_ERROR
    if user.email != email:
        return SecurityResultAuth.REFRESH_TOKEN_ERROR

    access_token = create_access_token(
        data={
            "sub": str(user.id),
            "username": user.username,
            "email": user.email,
            "role": str(user.role),
        }
    )

    return TokenResponse(access_token=access_token)


async def refresh_token(
    body: RefreshTokenRequest,
    db: AsyncSession,
) -> TokenResponse | SecurityResultAuth:
    old_refresh_token = body.refresh_token

    try:
        payload = decode_token(old_refresh_token)
        user_id = payload.get("sub")
        email = payload.get("email")
        token_type = payload.get("token_type")

        if user_id is None or token_type != "refresh":  # noqa: S105
            return SecurityResultAuth.REFRESH_TOKEN_ERROR

    except jwt.ExpiredSignatureError:
        return SecurityResultAuth.EXPIRED
    except jwt.PyJWTError:
        return SecurityResultAuth.REFRESH_TOKEN_ERROR

    result = await db.scalars(
        select(UserModel).where(UserModel.id == user_id, UserModel.is_active)
    )
    user = result.first()

    if user is None:
        return SecurityResultAuth.REFRESH_TOKEN_ERROR
    if user.email != email:
        return SecurityResultAuth.REFRESH_TOKEN_ERROR

    new_refresh_token = create_refresh_token(
        data={
            "sub": str(user.id),
            "username": user.username,
            "email": user.email,
            "role": str(user.role),
        }
    )

    return TokenResponse(
        refresh_token=new_refresh_token,
    )


async def get_group_users(
    group_id: int, db: AsyncSession, skip: int = 0, limit: int = 100
) -> Sequence[UserModel]:
    users = await db.scalars(
        select(UserModel)
        .join(
            UserGroupMembershipModel, UserModel.id == UserGroupMembershipModel.user_id
        )
        .where(UserGroupMembershipModel.group_id == group_id)
        .where(UserModel.is_active)
        .order_by(UserModel.id)
        .offset(skip)
        .limit(limit)
    )
    return users.all()


async def get_group_user(group_id: int, user: UserModel, db: AsyncSession) -> UserModel:
    result = await db.scalars(
        select(UserModel)
        .join(
            UserGroupMembershipModel, UserModel.id == UserGroupMembershipModel.user_id
        )
        .where(UserModel.is_active)
    )
    users = result.first()

    if not users:
        raise user_exc.UserNotFound()

    return users


async def set_user_role(
    user_id: int,
    role: UserRole,
    db: AsyncSession = Depends(db_helper.get_session),
) -> UserModel:
    try:
        result = await get_user(user_id, db)
    except user_exc.UserNotFound as e:
        raise e

    result.role = role
    await db.commit()
    await db.refresh(result)
    return result
