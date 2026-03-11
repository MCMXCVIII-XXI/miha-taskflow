from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio.session import AsyncSession

from app.core.security.current_role import RoleCurrentUser
from app.crud.crud_result import CrudResultUser
from app.crud.user_logic import access_token as access_token_logic
from app.crud.user_logic import create_user as create_user_logic
from app.crud.user_logic import delete_user as delete_user_logic
from app.crud.user_logic import get_group_users as get_group_users_logic
from app.crud.user_logic import get_user as get_user_logic
from app.crud.user_logic import get_users as get_users_logic
from app.crud.user_logic import login as login_logic
from app.crud.user_logic import refresh_token as refresh_token_logic
from app.crud.user_logic import set_user_role as set_user_role_logic
from app.crud.user_logic import update_user as update_user_logic
from app.db import db_helper
from app.models import User
from app.schemas.token_schemas import (
    AccessTokenRequest,
    RefreshTokenRequest,
    TokenResponse,
)
from app.schemas.user_schemas import User as UserSchemas
from app.schemas.user_schemas import UserCreate, UserRole, UserUpdate

router = APIRouter(prefix="", tags=["users"])


@router.post("/", response_model=UserSchemas, status_code=status.HTTP_201_CREATED)
async def create_user(
    user: UserCreate,
    db: AsyncSession = Depends(db_helper.get_session),
) -> UserSchemas:
    result = await create_user_logic(user, db)
    if result == CrudResultUser.USERNAME_CONFLICT:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=CrudResultUser.USERNAME_CONFLICT.value,
        )
    elif result == CrudResultUser.EMAIL_CONFLICT:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=CrudResultUser.EMAIL_CONFLICT.value,
        )

    return UserSchemas.model_validate(result)


@router.get("/", response_model=list[UserSchemas], status_code=status.HTTP_200_OK)
async def get_users(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(db_helper.get_session),
    current_user: User = Depends(RoleCurrentUser.admin),
) -> list[UserSchemas]:
    result = await get_users_logic(db, skip, limit)
    return [UserSchemas.model_validate(user) for user in result]


@router.get("/{user_id}", response_model=UserSchemas, status_code=status.HTTP_200_OK)
async def get_user(
    user_id: int,
    db: AsyncSession = Depends(db_helper.get_session),
) -> UserSchemas:
    user = await get_user_logic(user_id, db)
    if user == CrudResultUser.NOT_FOUND:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=CrudResultUser.NOT_FOUND.value
        )
    return UserSchemas.model_validate(user)


@router.put("/{user_id}", response_model=UserSchemas, status_code=status.HTTP_200_OK)
async def update_user(
    user_id: int, user_in: UserUpdate, db: AsyncSession = Depends(db_helper.get_session)
) -> UserSchemas:
    user = await update_user_logic(user_id, user_in, db)
    if user == CrudResultUser.NOT_FOUND:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=CrudResultUser.NOT_FOUND.value
        )
    if user == CrudResultUser.USERNAME_CONFLICT:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=CrudResultUser.USERNAME_CONFLICT.value,
        )
    elif user == CrudResultUser.EMAIL_CONFLICT:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=CrudResultUser.EMAIL_CONFLICT.value,
        )
    return UserSchemas.model_validate(user)


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: int, db: AsyncSession = Depends(db_helper.get_session)
) -> None:
    result = await delete_user_logic(user_id, db)
    if result == CrudResultUser.NOT_FOUND:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=CrudResultUser.NOT_FOUND.value
        )


@router.post("/token", response_model=dict[str, str], status_code=status.HTTP_200_OK)
async def login(
    from_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(db_helper.get_session),
) -> TokenResponse:
    result = await login_logic(from_data, db)

    if isinstance(result, TokenResponse):
        return result

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Incorrect username or password",
        headers={"WWW-Authenticate": "Bearer"},
    )


@router.post(
    "/access-token", response_model=TokenResponse, status_code=status.HTTP_200_OK
)
async def access_token(
    body: AccessTokenRequest,
    db: AsyncSession = Depends(db_helper.get_session),
) -> TokenResponse:
    result = await access_token_logic(body, db)

    if isinstance(result, TokenResponse):
        return result

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid token",
        headers={"WWW-Authenticate": "Bearer"},
    )


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

    if isinstance(result, TokenResponse):
        return result

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid token",
        headers={"WWW-Authenticate": "Bearer"},
    )


@router.get("/me", response_model=UserSchemas, status_code=status.HTTP_200_OK)
async def get_me(
    current_user: User = Depends(RoleCurrentUser.member),
    db: AsyncSession = Depends(db_helper.get_session),
) -> UserSchemas:
    return UserSchemas.model_validate(current_user)


@router.get(
    "/group/{group_id}",
    response_model=list[UserSchemas],
    status_code=status.HTTP_200_OK,
)
async def get_group_users(
    group_id: int,
    db: AsyncSession = Depends(db_helper.get_session),
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(RoleCurrentUser.admin_groups),
) -> list[UserSchemas]:
    users = await get_group_users_logic(group_id, db, skip, limit)
    return [UserSchemas.model_validate(user) for user in users]


@router.post(
    "/group/{group_id}/role",
    response_model=UserSchemas,
    status_code=status.HTTP_200_OK,
)
async def set_user_role(
    user_id: int,
    role: UserRole,
    db: AsyncSession = Depends(db_helper.get_session),
    current_user: User = Depends(RoleCurrentUser.admin_groups),
) -> UserSchemas:
    user = await set_user_role_logic(user_id, role, db)

    if user == CrudResultUser.NOT_FOUND:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=CrudResultUser.NOT_FOUND.value,
        )

    return UserSchemas.model_validate(user)
