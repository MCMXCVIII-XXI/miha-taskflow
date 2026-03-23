from datetime import UTC, datetime, timedelta

import jwt

from app.core.config import token_settings


def create_access_token(data: dict[str, str | datetime]) -> str:
    to_encode = data.copy()
    expire = datetime.now(UTC) + timedelta(
        minutes=token_settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )
    to_encode.update({"exp": expire, "token_type": "access"})
    return jwt.encode(
        to_encode, token_settings.SECRET_KEY, algorithm=token_settings.ALGORITHM
    )


def create_refresh_token(data: dict[str, str | datetime]) -> str:
    to_encode = data.copy()

    expire = datetime.now(UTC) + timedelta(
        days=token_settings.REFRESH_TOKEN_EXPIRE_DAYS
    )
    to_encode.update({"exp": expire, "token_type": "refresh"})
    return jwt.encode(
        to_encode, token_settings.SECRET_KEY, algorithm=token_settings.ALGORITHM
    )


def decode_token(token: str) -> dict[str, str | datetime]:
    try:
        payload = jwt.decode(
            token, token_settings.SECRET_KEY, algorithms=[token_settings.ALGORITHM]
        )
        date = payload.get("exp")
        if date and datetime.fromtimestamp(date, tz=UTC) < datetime.now(UTC):
            raise jwt.ExpiredSignatureError
        return payload
    except jwt.PyJWTError as e:
        raise e
