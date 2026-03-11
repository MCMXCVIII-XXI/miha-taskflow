from enum import Enum


class SecurityResultAuth(Enum):
    COULD_NOT_VERIFY = "Could not verify credentials"
    REFRESH_TOKEN_ERROR = "Could not validate refresh token"  # noqa: S105
    ACCESS_TOKEN_ERROR = "Could not validate access token"  # noqa: S105
    EXPIRED = "Token has expired"
    NOT_AUTHORIZED = "You cannot perform this action."
