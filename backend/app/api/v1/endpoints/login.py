from fastapi import APIRouter, Depends, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio.session import AsyncSession

from app.crud.login_logic import access_token as access_token_logic
from app.crud.login_logic import login as login_logic
from app.crud.login_logic import refresh_token as refresh_token_logic
from app.db import db_helper
from app.schemas.token_schemas import (
    AccessTokenRequest,
    RefreshTokenRequest,
    TokenResponse,
)

router = APIRouter()


@router.post("/token", response_model=dict[str, str], status_code=status.HTTP_200_OK)
async def login(
    from_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(db_helper.get_session),
) -> TokenResponse:
    result = await login_logic(from_data, db)
    return result


@router.post(
    "/access-token", response_model=TokenResponse, status_code=status.HTTP_200_OK
)
async def access_token(
    body: AccessTokenRequest,
    db: AsyncSession = Depends(db_helper.get_session),
) -> TokenResponse:
    result = await access_token_logic(body, db)
    return result


@router.post(
    "/refresh-token",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
)
async def refresh_token(
    body: RefreshTokenRequest,
    db: AsyncSession = Depends(db_helper.get_session),
) -> TokenResponse:
    result = await refresh_token_logic(body, db)
    return result
