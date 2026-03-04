from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio.session import AsyncSession

from app.crud.crud_result import CrudResultUser
from app.crud.user_logic import (
    create_user as create,
)
from app.crud.user_logic import (
    delete_user as delete,
)
from app.crud.user_logic import (
    get_user,
    get_users,
)
from app.crud.user_logic import (
    update_user as update,
)
from app.db import db_helper
from app.schemas.user_schemas import UserBase, UserCreate, UserUpdate

router = APIRouter(prefix="", tags=["users"])


@router.post("/", response_model=UserBase, status_code=status.HTTP_201_CREATED)
async def create_user(
    user: UserCreate, db: AsyncSession = Depends(db_helper.get_session)
) -> UserBase:
    result = await create(user, db)
    if result == CrudResultUser.USERNAME_CONFLICT:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Username already exists"
        )
    elif result == CrudResultUser.EMAIL_CONFLICT:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Email already exists"
        )

    return UserBase.model_validate(result)


@router.get("/", response_model=list[UserBase], status_code=status.HTTP_200_OK)
async def read_users(
    skip: int = 0, limit: int = 100, db: AsyncSession = Depends(db_helper.get_session)
) -> list[UserBase]:
    result = await get_users(db, skip, limit)
    return [UserBase.model_validate(user) for user in result]


@router.get("/{user_id}", response_model=UserBase, status_code=status.HTTP_200_OK)
async def read_user(
    user_id: int, db: AsyncSession = Depends(db_helper.get_session)
) -> UserBase:
    user = await get_user(user_id, db)
    if user == CrudResultUser.NOT_FOUND:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )
    return UserBase.model_validate(user)


@router.put("/{user_id}", response_model=UserBase, status_code=status.HTTP_200_OK)
async def update_user_endpoint(
    user_id: int, user_in: UserUpdate, db: AsyncSession = Depends(db_helper.get_session)
) -> UserBase:
    user = await update(user_id, user_in, db)
    if user == CrudResultUser.NOT_FOUND:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )
    if user == CrudResultUser.USERNAME_CONFLICT:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Username already exists"
        )
    elif user == CrudResultUser.EMAIL_CONFLICT:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Email already exists"
        )
    return UserBase.model_validate(user)


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user_endpoint(
    user_id: int, db: AsyncSession = Depends(db_helper.get_session)
) -> None:
    result = await delete(user_id, db)
    if result == CrudResultUser.NOT_FOUND:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )
