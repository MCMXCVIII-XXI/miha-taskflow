from fastapi import APIRouter, Depends, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio.session import AsyncSession

from app.db import db_helper
from app.schemas import RefreshTokenRequest, TokenResponse, UserCreate
from app.service import AuthenticationService, get_authentication_service

router = APIRouter()


@router.post("/token", response_model=TokenResponse, status_code=status.HTTP_200_OK)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(db_helper.get_session),
    svc: AuthenticationService = Depends(get_authentication_service),
) -> TokenResponse:
    """Endpoint for user login"""
    return await svc.login(form_data)


@router.post("", response_model=TokenResponse, status_code=status.HTTP_200_OK)
async def register(
    user_in: UserCreate,
    db: AsyncSession = Depends(db_helper.get_session),
    svc: AuthenticationService = Depends(get_authentication_service),
) -> TokenResponse:
    """Endpoint for user registration"""
    return await svc.register(user_in)


@router.post(
    "/access-token", response_model=TokenResponse, status_code=status.HTTP_200_OK
)
async def access_token(
    body: RefreshTokenRequest,
    db: AsyncSession = Depends(db_helper.get_session),
    svc: AuthenticationService = Depends(get_authentication_service),
) -> TokenResponse:
    """Endpoint for accessing a new access token using a refresh token"""
    return await svc.access_token(body)


@router.post(
    "/refresh-token",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
)
async def refresh_token(
    body: RefreshTokenRequest,
    db: AsyncSession = Depends(db_helper.get_session),
    svc: AuthenticationService = Depends(get_authentication_service),
) -> TokenResponse:
    """Endpoint for refreshing a token using a refresh token"""
    return await svc.refresh_token(body)
