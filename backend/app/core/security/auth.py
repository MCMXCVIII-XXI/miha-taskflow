import jwt
from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import db_helper
from app.models import UserModel

from ..exceptions import security_exc
from .token import decode_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token")


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(db_helper.get_session),
) -> UserModel:
    try:
        payload = decode_token(token)
        user_id = payload.get("sub")
        email = payload.get("mail")
        if not user_id:
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
