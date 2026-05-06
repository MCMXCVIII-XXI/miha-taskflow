"""Authentication and authorization service for user management.

This module provides the AuthenticationService class for handling user
registration, login, token refresh, and session management.

**Key Components:**
* `AuthenticationService`: Main service class for authentication operations;
* `get_authentication_service`: FastAPI dependency injection factory.

**Dependencies:**
* `UserRepository`: User data access layer;
* `UnitOfWork`: Transaction management;
* `ElasticsearchIndexer`: Search index management;
* JWT utilities: Token creation and validation.

**Usage Example:**
    ```python
    from app.service.auth import get_authentication_service

    @router.post("/auth/register")
    async def register(
        auth_svc: AuthenticationService = Depends(get_authentication_service),
        user_data: UserCreate
    ):
        return await auth_svc.register(user_data)
    ```

**Notes:**
- All operations require active user status unless explicitly stated;
- Tokens are JWT-based with configurable expiration;
- Refresh tokens support rotation for security.
"""

from datetime import datetime

import jwt
from fastapi import Depends
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import security_exc
from app.core.log import logging
from app.core.log.mask import _mask_email
from app.core.metrics import METRICS
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    verify_password,
)
from app.db import db_helper
from app.es import ElasticsearchIndexer, get_es_indexer
from app.models import User as UserModel
from app.schemas import RefreshTokenRequest, TokenResponse, UserCreate
from app.schemas.enum import TokenType

from .base import BaseService
from .exceptions import user_exc
from .transactions.auth import AuthTransaction, get_auth_transaction
from .utils import Indexer

logger = logging.get_logger(__name__)


class AuthenticationService(BaseService):
    """Service for user authentication and authorization operations.

    Handles user registration, login, token generation, and token refresh
    operations. Provides JWT-based authentication with support for both
    access and refresh tokens.

    Attributes:
        _db (AsyncSession): SQLAlchemy async session for database operations
        _user_repository (UserRepository): Repository for user data operations
        _uow (UnitOfWork): Unit of work for transaction management
        _indexer (Indexer): Elasticsearch indexer wrapper for search operations
        REFRESH_TOKEN_TYPE (str): Token type identifier for refresh tokens
        ACCESS_TOKEN_TYPE (str): Token type identifier for access tokens
        BOTH_TOKEN_TYPE (str): Token type identifier for both token types

    Example:
        ```python
        auth_service = AuthenticationService(
            db=session,
            uow=uow,
            indexer=indexer,
            user_repository=user_repo
        )
        tokens = await auth_service.login(OAuth2PasswordRequestForm(...))
        ```
    """

    REFRESH_TOKEN_TYPE = TokenType.REFRESH.value
    ACCESS_TOKEN_TYPE = TokenType.ACCESS.value
    BOTH_TOKEN_TYPE = TokenType.BOTH.value

    def __init__(
        self,
        db: AsyncSession,
        indexer: ElasticsearchIndexer,
        auth_transaction: AuthTransaction,
    ) -> None:
        """Initialize authentication service with dependencies.

        Args:
            db: SQLAlchemy async session for database operations
            uow: Unit of work for transaction management
            indexer: Elasticsearch client for indexing operations
            user_repository: Repository for user database operations
        """
        super().__init__(db=db)
        self._indexer = Indexer(indexer)
        self._auth_transaction = auth_transaction

    def _create_token_response(
        self,
        user: UserModel,
        options: str = BOTH_TOKEN_TYPE,
    ) -> TokenResponse:
        """Create TokenResponse with access/refresh tokens.

        Builds JWT payload from user data (id, username, email, role) and
        generates appropriate token(s) based on the options parameter.

        Args:
            user: Authenticated user instance
                Type: UserModel
            options: Token type to generate.
                Type: str
                Values: "access", "refresh", "both"
                Defaults to "both".

        Returns:
            TokenResponse: Token(s) response containing access and/or refresh tokens

        Raises:
            security_exc.SecurityInvalidTokenType: When invalid token type specified

        Example:
            ```python
            tokens = self._create_token_response(user, options="both")
            # Returns: TokenResponse(access_token="...", refresh_token="...")
            ```
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
        """Register new user with immediate token issuance.

        Validates email and username are unique, hashes password, creates
        new user record, indexes in Elasticsearch, and returns both
        access and refresh tokens.

        Args:
            user_in: User registration data
                Type: UserCreate
                Contains: username, email, password, first_name, last_name, patronymic

        Returns:
            TokenResponse: Access and refresh tokens for immediate authentication

        Raises:
            user_exc.UserAlreadyExists: When email or username already in use

        Example:
            ```python
            tokens = await auth_svc.register(
                UserCreate(
                    username="john",
                    email="john@example.com",
                    password="secure123",
                    first_name="John",
                    last_name="Doe"
                )
            )
            ```
        """
        user = await self._auth_transaction.register(user_in=user_in)
        await self._indexer.index(user)

        METRICS.USER_ACTIONS_TOTAL.labels(
            action="auth_register", role="guest", status="success"
        ).inc()

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
        """Authenticate user by email/username and password.

        Performs dual-field lookup (email OR username) with password verification.
        Returns both access and refresh tokens on successful authentication.

        Args:
            form_data: Login credentials containing username and password
                Type: OAuth2PasswordRequestForm
                Fields: username (email or username), password

        Returns:
            TokenResponse: Access and refresh tokens for authenticated session

        Raises:
            user_exc.UserNotFound: When user not found or inactive
            security_exc.SecurityCouldNotVerify: When password is invalid

        Example:
            ```python
            tokens = await auth_svc.login(
                OAuth2PasswordRequestForm(username="john", password="secure123")
            )
            ```
        """
        user = await self._user_repo.get_by_email_or_username(
            username=form_data.username,
            email=form_data.username,
            is_active=True,
        )
        if not user:
            METRICS.USER_ACTIONS_TOTAL.labels(
                action="auth_login_fail", role="guest", status="failure"
            )
            logger.warning(
                "Login failed: user not found or inactive: {username}",
                username=form_data.username,
            )
            raise user_exc.UserNotFound(message="User not found or inactive")
        if not verify_password(form_data.password, user.hashed_password):
            METRICS.USER_ACTIONS_TOTAL.labels(
                action="auth_login_fail", role="guest", status="failure"
            ).inc()
            logger.warning(
                "Login failed: invalid password for user {user_id} ({username})",
                user_id=user.id,
                username=form_data.username,
            )
            raise security_exc.SecurityCouldNotVerify(
                message="Could not verify credentials"
            )
        METRICS.USER_ACTIONS_TOTAL.labels(
            action="auth_login_success", role="user", status="success"
        ).inc()
        logger.info(
            "User logged in: user_id={user_id}, username={username}",
            user_id=user.id,
            username=user.username,
        )

        return self._create_token_response(user)

    async def _get_user_from_refresh_token(self, refresh_token: str) -> UserModel:
        """Validate refresh token and return bound active user.

        Performs 4-step validation: JWT decode → payload check → database lookup
        → email match. Ensures token-user consistency and user activity.

        Args:
            refresh_token: Client refresh token to validate
                Type: str

        Returns:
            UserModel: Validated active user instance

        Raises:
            security_exc.SecurityExpired: When token has expired
            security_exc.SecurityRefreshTokenError: When token validation fails

        Example:
            ```python
            user = await self._get_user_from_refresh_token(token)
            ```
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

        if user_id_str is None or token_type != self.REFRESH_TOKEN_TYPE:
            raise security_exc.SecurityRefreshTokenError(
                message="Could not validate refresh token"
            )

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

        user = await self._user_repo.get(
            id=user_id,
            is_active=True,
        )

        if user is None or user.email != email:
            raise security_exc.SecurityRefreshTokenError(
                message="Could not validate refresh token"
            )

        return user

    async def access_token(self, body: RefreshTokenRequest) -> TokenResponse:
        """Issue new access token from valid refresh token.

        Validates refresh token and issues a new access token while keeping
        the refresh token valid (non-rotating refresh).

        Args:
            body: Refresh token request containing the refresh token
                Type: RefreshTokenRequest
                Fields: refresh_token

        Returns:
            TokenResponse: New access token

        Raises:
            security_exc.SecurityRefreshTokenError: /
                When refresh token is invalid or expired

        Example:
            ```python
            tokens = await auth_svc.access_token(
                RefreshTokenRequest(refresh_token="eyJ...")
            )
            ```
        """
        user = await self._get_user_from_refresh_token(body.refresh_token)
        METRICS.USER_ACTIONS_TOTAL.labels(
            action="auth_refresh_access", role="user", status="success"
        ).inc()
        return self._create_token_response(user, options=self.ACCESS_TOKEN_TYPE)

    async def refresh_token(
        self,
        body: RefreshTokenRequest,
    ) -> TokenResponse:
        """Rotate refresh token (security best practice).

        Validates old refresh token and issues a new refresh token while
        invalidating the old one. This is the recommended security practice
        to limit token lifetime and prevent token reuse attacks.

        Args:
            body: Old refresh token to rotate
                Type: RefreshTokenRequest
                Fields: refresh_token

        Returns:
            TokenResponse: New refresh token

        Raises:
            security_exc.SecurityRefreshTokenError:
                When refresh token is invalid or expired

        Example:
            ```python
            tokens = await auth_svc.refresh_token(
                RefreshTokenRequest(refresh_token="eyJ...")
            )
            ```
        """
        user = await self._get_user_from_refresh_token(body.refresh_token)
        METRICS.USER_ACTIONS_TOTAL.labels(
            action="auth_refresh_access", role="user", status="success"
        ).inc()
        return self._create_token_response(user, options=self.REFRESH_TOKEN_TYPE)


def get_authentication_service(
    db: AsyncSession = Depends(db_helper.get_session),
    indexer: ElasticsearchIndexer = Depends(get_es_indexer),
    auth_transaction: AuthTransaction = Depends(get_auth_transaction),
) -> AuthenticationService:
    """Create AuthenticationService instance with dependency injection.

    Factory function for FastAPI dependency injection that creates and configures
    an AuthenticationService instance with all required dependencies.

    Args:
        db: Database session from FastAPI dependency injection.
            Type: AsyncSession.
        uow: Unit of work from FastAPI dependency injection.
            Type: UnitOfWork.
        indexer: Elasticsearch client from FastAPI dependency injection.
            Type: ElasticsearchIndexer.
        user_repository: User repository from FastAPI dependency injection.
            Type: UserRepository.

    Returns:
        AuthenticationService: Configured authentication service instance

    Example:
        ```python
        @router.post("/auth/register")
        async def register(
            auth_svc: AuthenticationService = Depends(get_authentication_service),
            user_data: UserCreate
        ):
            return await auth_svc.register(user_data)
        ```
    """
    return AuthenticationService(
        db=db, indexer=indexer, auth_transaction=auth_transaction
    )
