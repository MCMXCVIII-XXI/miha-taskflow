import jwt
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import security_exc
from app.core.security.hash import verify_password
from app.core.security.token import (
    create_access_token,
    create_refresh_token,
    decode_token,
)
from app.models import User as UserModel
from app.schemas.token_schemas import (
    AccessTokenRequest,
    RefreshTokenRequest,
    TokenResponse,
)

from .exceptions import user_exc


async def login(
    from_data: OAuth2PasswordRequestForm,
    db: AsyncSession,
) -> TokenResponse:
    result = await db.scalars(
        select(UserModel).where(
            (UserModel.email == from_data.username)
            | (UserModel.username == from_data.username),
            UserModel.is_active,
        )
    )
    user = result.first()
    if not user:
        raise user_exc.UserNotFound()
    if not verify_password(from_data.password, user.hashed_password):
        raise security_exc.SecurityCouldNotVerify()

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
) -> TokenResponse:
    access_token = body.access_token

    try:
        payload = decode_token(access_token)
        user_id = payload.get("sub")
        email = payload.get("email")
        token_type = payload.get("token_type")

        if user_id is None or token_type != "access":  # noqa: S105
            raise security_exc.SecurityAccessTokenError()

    except jwt.ExpiredSignatureError as e:
        raise security_exc.SecurityExpired() from e
    except jwt.PyJWTError as e:
        raise security_exc.SecurityAccessTokenError() from e

    result = await db.scalars(
        select(UserModel).where(UserModel.id == user_id, UserModel.is_active)
    )
    user = result.first()

    if user is None or user.email != email:
        raise security_exc.SecurityRefreshTokenError()

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
) -> TokenResponse:
    old_refresh_token = body.refresh_token

    try:
        payload = decode_token(old_refresh_token)
        user_id = payload.get("sub")
        email = payload.get("email")
        token_type = payload.get("token_type")

        if user_id is None or token_type != "refresh":  # noqa: S105
            raise security_exc.SecurityRefreshTokenError()

    except jwt.ExpiredSignatureError as e:
        raise security_exc.SecurityExpired() from e
    except jwt.PyJWTError as e:
        raise security_exc.SecurityRefreshTokenError() from e

    result = await db.scalars(
        select(UserModel).where(UserModel.id == user_id, UserModel.is_active)
    )
    user = result.first()

    if user is None or user.email != email:
        raise security_exc.SecurityRefreshTokenError()

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
