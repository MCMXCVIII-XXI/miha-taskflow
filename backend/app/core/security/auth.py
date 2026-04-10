"""Authentication utilities for JWT-based user verification.

This module provides functions for validating JWT tokens and retrieving
authenticated user information from the database. It implements the
core authentication logic for the TaskFlow application.
"""

import jwt
from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import db_helper
from app.models import User as UserModel

from ..exceptions import security_exc
from .token import decode_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token")


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(db_helper.get_session),
) -> UserModel:
    """Get current authenticated user from JWT token.

    Validates the provided JWT token and retrieves the corresponding
    user from the database. Ensures the user account is active.

    Args:
        token (str): JWT token from Authorization header (via OAuth2 scheme)
        db (AsyncSession): Database session for user lookup

    Returns:
        UserModel: Authenticated user instance

    Raises:
        security_exc.SecurityExpired: When token has expired
        security_exc.SecurityCouldNotVerify: When token is invalid or user not found
    """
    try:
        payload = decode_token(token)
        sub = payload.get("sub")
        email = payload.get("email")
        if not sub:
            raise security_exc.SecurityCouldNotVerify(
                message="Invalid token", headers={"WWW-Authenticate": "Bearer"}
            )
        if not isinstance(sub, str) or not sub.isdigit():
            raise security_exc.SecurityCouldNotVerify(
                message="Invalid user ID format", headers={"WWW-Authenticate": "Bearer"}
            )
        user_id = int(sub)

    except jwt.ExpiredSignatureError as e:
        raise security_exc.SecurityExpired(
            message="Token expired", headers={"WWW-Authenticate": "Bearer"}
        ) from e
    except jwt.PyJWTError as e:
        raise security_exc.SecurityCouldNotVerify(
            message="Invalid token", headers={"WWW-Authenticate": "Bearer"}
        ) from e
    result = await db.scalars(
        select(UserModel).where(UserModel.id == user_id, UserModel.is_active)
    )
    user = result.first()
    if user is None:
        raise security_exc.SecurityCouldNotVerify(
            message="User not found", headers={"WWW-Authenticate": "Bearer"}
        )
    if user.email != email:
        raise security_exc.SecurityCouldNotVerify(
            message="Email does not match", headers={"WWW-Authenticate": "Bearer"}
        )
    return user
