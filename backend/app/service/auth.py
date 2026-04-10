from datetime import datetime

import jwt
from fastapi import Depends
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import security_exc
from app.core.log import get_logger
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    get_password_hash,
    verify_password,
)
from app.db import db_helper
from app.models import User as UserModel
from app.schemas import RefreshTokenRequest, TokenResponse, UserCreate
from app.schemas.enum import TokenType

from .base import BaseService
from .exceptions import user_exc

logger = get_logger("service.auth")


def _mask_email(email: str) -> str:
    """Mask email for logging: user@example.com -> u***@example.com"""
    if not email or "@" not in email:
        return "***"
    local, domain = email.split("@", 1)
    return f"{local[0]}***@{domain}" if len(local) > 1 else "***@{domain}"


class AuthenticationService(BaseService):
    """Authentication service implementing JWT-based authentication flow.

    This service handles user registration, authentication, and token management
    using JSON Web Tokens (JWT). It supports both access and refresh tokens
    with automatic rotation and validation.

    Features:
    - User registration with password hashing
    - Username/email authentication
    - Access and refresh token generation
    - Token validation with expiration checks
    - Token refresh and rotation mechanisms

    Attributes:
        _db (AsyncSession): SQLAlchemy async database session

    Raises:
        user_exc.UserAlreadyExists: When trying to register with existing email/username
        user_exc.UserNotFound: When user credentials are invalid
        security_exc.SecurityCouldNotVerify: When authentication fails
        security_exc.SecurityExpired: When token has expired
        security_exc.SecurityRefreshTokenError: When refresh token is invalid
    """

    REFRESH_TOKEN_TYPE = TokenType.REFRESH.value
    ACCESS_TOKEN_TYPE = TokenType.ACCESS.value
    BOTH_TOKEN_TYPE = TokenType.BOTH.value

    def __init__(self, db: AsyncSession) -> None:
        super().__init__(db)

    def _create_token_response(
        self,
        user: UserModel,
        options: str = BOTH_TOKEN_TYPE,
    ) -> TokenResponse:
        """
        Create TokenResponse with access/refresh tokens.

        Details:
            Builds JWT payload from user data (id, username, email, role).
            Supports access/refresh/both token generation.

        Arguments:
            user (UserModel): Authenticated user
            options (TokenType): Token type

        Returns:
            TokenResponse: Token(s) response

        Example Usage:
            tokens = self._create_token_response(user, TokenType.BOTH)
        """
        data: dict[str, str | datetime] = {
            "sub": str(user.id),
            "username": user.username,
            "email": user.email,
            "role": str(user.role),
        }

        if options == "access":
            return TokenResponse(access_token=create_access_token(data))
        elif options == "refresh":
            return TokenResponse(refresh_token=create_refresh_token(data))
        elif options == "both":
            return TokenResponse(
                access_token=create_access_token(data),
                refresh_token=create_refresh_token(data),
            )
        else:
            raise security_exc.SecurityInvalidTokenType(
                message=f"Invalid token type: {options}",
            )

    async def register(
        self,
        user_in: UserCreate,
    ) -> TokenResponse:
        """
        Register new user with immediate token issuance.

        Details:
            Email/username conflict check + password hashing.
            Creates user + returns both access/refresh tokens.

        Arguments:
            user_in (UserCreate): Registration data

        Returns:
            TokenResponse: Access + refresh tokens

        Raises:
            user_exc.UserAlreadyExists: Email/username collision

        Example Usage:
            tokens = await auth_svc.register(UserCreate(username="john", ...))
        """
        result = await self._db.scalars(
            select(UserModel).where(
                (UserModel.email == user_in.email)
                | (UserModel.username == user_in.username),
            )
        )
        user = result.first()
        if user:
            logger.warning(
                "Registration failed: duplicate email {email} or username {username}",
                email=_mask_email(user_in.email),
                username=user_in.username,
            )
            raise user_exc.UserAlreadyExists(
                message="User with this email or username already exists"
            )
        user = UserModel(
            username=user_in.username,
            email=user_in.email,
            first_name=user_in.first_name,
            last_name=user_in.last_name,
            patronymic=user_in.patronymic,
            hashed_password=get_password_hash(
                user_in.hashed_password.get_secret_value()
            ),
        )
        self._db.add(user)
        await self._db.commit()
        await self._db.refresh(user)

        logger.info(
            "User registered: user_id={user_id}, username={username}, email={email}",
            user_id=user.id,
            username=user.username,
            email=_mask_email(user.email),
        )

        return self._create_token_response(user)

    async def login(
        self,
        form_data: OAuth2PasswordRequestForm,
    ) -> TokenResponse:
        """
        Authenticate user by email/username + password.

        Details:
            Dual-field lookup (email OR username) + password verification.
            Returns both access/refresh tokens on success.

        Arguments:
            form_data (OAuth2PasswordRequestForm): Login credentials

        Returns:
            TokenResponse: Access + refresh tokens

        Raises:
            user_exc.UserNotFound: User inactive/not found
            security_exc.SecurityCouldNotVerify: Invalid password

        Example Usage:
            tokens = await auth_svc.login(OAuth2PasswordRequestForm(...))
        """
        result = await self._db.scalars(
            select(UserModel).where(
                (UserModel.email == form_data.username)
                | (UserModel.username == form_data.username),
                UserModel.is_active,
            )
        )
        user = result.first()
        if not user:
            logger.warning(
                "Login failed: user not found or inactive: {username}",
                username=form_data.username,
            )
            raise user_exc.UserNotFound(message="User not found or inactive")
        if not verify_password(form_data.password, user.hashed_password):
            logger.warning(
                "Login failed: invalid password for user {user_id} ({username})",
                user_id=user.id,
                username=form_data.username,
            )
            raise security_exc.SecurityCouldNotVerify(
                message="Could not verify credentials"
            )

        logger.info(
            "User logged in: user_id={user_id}, username={username}",
            user_id=user.id,
            username=user.username,
        )

        return self._create_token_response(user)

    async def _get_user_from_refresh_token(self, refresh_token: str) -> UserModel:
        """
        Validate refresh token + return bound active user.

        Details:
            4-step validation: JWT decode → payload check → DB lookup → email match.
            Ensures token-user consistency + activity.

        Arguments:
            refresh_token (str): Client refresh token

        Returns:
            UserModel: Validated active user

        Raises:
            security_exc.SecurityExpired: Token expired
            security_exc.SecurityRefreshTokenError: Invalid payload/DB mismatch

        Example Usage:
            user = await self._get_user_from_refresh_token(token)
        """
        try:
            payload = decode_token(refresh_token)
        except jwt.ExpiredSignatureError as e:
            raise security_exc.SecurityExpired(message="Token has expired") from e
        except jwt.PyJWTError as e:
            raise security_exc.SecurityRefreshTokenError(
                message="Could not validate refresh token"
            ) from e

        user_id_str = payload.get("sub")
        email = payload.get("email")
        token_type = payload.get("token_type")

        # Bandit S105: JWT standard token_type validation
        if user_id_str is None or token_type != self.REFRESH_TOKEN_TYPE:
            raise security_exc.SecurityRefreshTokenError(
                message="Could not validate refresh token"
            )

        # Convert user_id to integer for database query
        if not isinstance(user_id_str, (str, int)):
            raise security_exc.SecurityRefreshTokenError(
                message="Invalid user_id type in token"
            )

        try:
            user_id = int(user_id_str)
        except (ValueError, TypeError) as e:
            raise security_exc.SecurityRefreshTokenError(
                message="Could not validate refresh token"
            ) from e

        result = await self._db.scalars(
            select(UserModel).where(UserModel.id == user_id, UserModel.is_active)
        )
        user = result.first()

        if user is None or user.email != email:
            raise security_exc.SecurityRefreshTokenError(
                message="Could not validate refresh token"
            )

        return user

    async def access_token(self, body: RefreshTokenRequest) -> TokenResponse:
        """
        Issue new access token from valid refresh token.

        Details:
            Refresh → access token rotation (refresh stays valid).

        Arguments:
            body (RefreshTokenRequest): Refresh token payload

        Returns:
            TokenResponse: New access token

        Raises:
            security_exc.SecurityRefreshTokenError: Invalid/expired refresh

        Example Usage:
            new_access = await auth_svc.access_token({"refresh_token": token})
        """
        user = await self._get_user_from_refresh_token(body.refresh_token)
        return self._create_token_response(user, options=self.ACCESS_TOKEN_TYPE)

    async def refresh_token(
        self,
        body: RefreshTokenRequest,
    ) -> TokenResponse:
        """
        Rotate refresh token (security best practice).

        Details:
            Refresh → new refresh token (old becomes invalid).

        Arguments:
            body (RefreshTokenRequest): Old refresh token

        Returns:
            TokenResponse: New refresh token

        Raises:
            security_exc.SecurityRefreshTokenError: Invalid/expired refresh

        Example Usage:
            new_refresh = await auth_svc.refresh_token({"refresh_token": token})
        """
        user = await self._get_user_from_refresh_token(body.refresh_token)
        return self._create_token_response(user, options=self.REFRESH_TOKEN_TYPE)


def get_authentication_service(
    db: AsyncSession = Depends(db_helper.get_session),
) -> AuthenticationService:
    """
    FastAPI dependency factory for AuthenticationService.

    Details:
        Creates AuthenticationService with DB session.
        Used in auth routes (register/login/refresh).

    Arguments:
        db (AsyncSession): Database session

    Returns:
        AuthenticationService: Fresh auth service instance

    Example Usage:
        @router.post("/register")
        async def register(
            auth_svc: AuthenticationService = Depends(get_authentication_service)
        ):
            return await auth_svc.register(user_in)
    """
    return AuthenticationService(db)
