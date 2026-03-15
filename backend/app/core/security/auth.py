import jwt
from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db import db_helper
from app.models import User

from ..exceptions import security_exc
from .token import decode_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/v1/users/token")


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(db_helper.get_session),
) -> User:
    try:
        payload = decode_token(token)
        user_id = payload.get("sub")
        email = payload.get("mail")
        if not user_id:
            raise security_exc.SecurityCouldNotVerify(
                headers={"WWW-Authenticate": "Bearer"}
            )
    except jwt.ExpiredSignatureError as e:
        raise security_exc.SecurityExpired(
            headers={"WWW-Authenticate": "Bearer"}
        ) from e
    except jwt.PyJWTError as e:
        raise security_exc.SecurityCouldNotVerify(
            headers={"WWW-Authenticate": "Bearer"}
        ) from e
    result = await db.scalars(select(User).where(User.id == user_id, User.is_active))
    user = result.first()
    if user is None:
        raise security_exc.SecurityCouldNotVerify(
            headers={"WWW-Authenticate": "Bearer"}
        )
    if user.email != email:
        raise security_exc.SecurityCouldNotVerify(
            headers={"WWW-Authenticate": "Bearer"}
        )
    return user
