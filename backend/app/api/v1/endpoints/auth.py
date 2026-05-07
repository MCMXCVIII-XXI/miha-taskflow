from fastapi import APIRouter, Depends, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio.session import AsyncSession

from app.db import db_helper
from app.examples.auth_examples import AuthExamples
from app.schemas import RefreshTokenRequest, TokenResponse, UserCreate
from app.service import AuthenticationService, get_authentication_service

router = APIRouter(tags=["auth"])


@router.post(
    "",
    response_model=TokenResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register new user",
    description="""
    Register a new user account and generate initial authentication tokens.

    **No authentication required.**

    **Request body:**
    - `username` (required, 3-50 chars): Unique username
    - `email` (required, valid email): User's email address
    - `password` (required, min 8 chars): Account password
    - `first_name` (required, max 50 chars): User's first name
    - `last_name` (required, max 50 chars): User's last name

    **Returns:** Access and refresh tokens with 30-day expiry.

    **Rate limit:** 5 registrations per IP per hour.
    """,
    responses={
        201: {
            "description": "User registered successfully",
            "content": {"application/json": {"example": AuthExamples.REGISTER_SUCCESS}},
        },
        400: {
            "description": "User already exists",
            "content": {"application/json": {"example": AuthExamples.DUPLICATE_EMAIL}},
        },
        422: {
            "description": "Validation error",
            "content": {"application/json": {"example": AuthExamples.VALIDATION_ERROR}},
        },
    },
)
async def register(
    user_in: UserCreate,
    db: AsyncSession = Depends(db_helper.get_session),
    svc: AuthenticationService = Depends(get_authentication_service),
) -> TokenResponse:
    """Register new user account and generate initial authentication tokens."""
    return await svc.register(user_in)


@router.post(
    "/token",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    summary="Login",
    description="""
    Authenticate user using username and password.

    **No authentication required.**

    **Request body (OAuth2 form):**
    - `username`: User's username or email
    - `password`: User's password

    **Returns:** Access and refresh tokens with 30-day expiry.

    **Note:** Uses OAuth2PasswordRequestForm for proper OAuth2 compatibility.
    """,
    responses={
        200: {
            "description": "Login successful",
            "content": {"application/json": {"example": AuthExamples.LOGIN_SUCCESS}},
        },
        401: {
            "description": "Invalid credentials",
            "content": {
                "application/json": {"example": AuthExamples.INVALID_CREDENTIALS}
            },
        },
    },
)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(db_helper.get_session),
    svc: AuthenticationService = Depends(get_authentication_service),
) -> TokenResponse:
    """Authenticate user and generate access/refresh tokens."""
    return await svc.login(form_data)


@router.post(
    "/access-token",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    summary="Get access token",
    description="""
    Generate new access token using a valid refresh token.

    **Authentication required.**

    **Request body:**
    - `refresh_token` (required): Valid refresh token

    **Returns:** New access token only (refresh token unchanged).

    **Use case:** When access token expired but refresh token is still valid.
    """,
    responses={
        200: {
            "description": "Access token generated",
            "content": {"application/json": {"example": AuthExamples.REFRESH_SUCCESS}},
        },
        401: {
            "description": "Invalid or expired refresh token",
            "content": {"application/json": {"example": AuthExamples.INVALID_TOKEN}},
        },
    },
)
async def access_token(
    body: RefreshTokenRequest,
    db: AsyncSession = Depends(db_helper.get_session),
    svc: AuthenticationService = Depends(get_authentication_service),
) -> TokenResponse:
    """Generate new access token using a valid refresh token."""
    return await svc.access_token(body)


@router.post(
    "/refresh-token",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    summary="Refresh tokens",
    description="""
    Generate new access and refresh tokens using a valid refresh token.

    **Authentication required.**

    **Request body:**
    - `refresh_token` (required): Valid refresh token

    **Returns:** New access AND refresh tokens.

    **Use case:** Full token refresh, typically done periodically.
    """,
    responses={
        200: {
            "description": "Tokens refreshed successfully",
            "content": {
                "application/json": {"example": AuthExamples.REFRESH_TOKEN_SUCCESS}
            },
        },
        401: {
            "description": "Invalid or expired refresh token",
            "content": {"application/json": {"example": AuthExamples.INVALID_TOKEN}},
        },
    },
)
async def refresh_token(
    body: RefreshTokenRequest,
    db: AsyncSession = Depends(db_helper.get_session),
    svc: AuthenticationService = Depends(get_authentication_service),
) -> TokenResponse:
    """Generate new access and refresh tokens using a valid refresh token."""
    return await svc.refresh_token(body)
