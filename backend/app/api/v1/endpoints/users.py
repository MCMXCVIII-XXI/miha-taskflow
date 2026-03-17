from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio.session import AsyncSession

from app.core.security.current_role import RoleCurrentUser
from app.crud.user_logic import create_user as create_user_logic
from app.crud.user_logic import create_user_group as create_user_group_logic
from app.crud.user_logic import delete_user as delete_user_logic
from app.crud.user_logic import get_group_users as get_group_users_logic
from app.crud.user_logic import get_user as get_user_logic
from app.crud.user_logic import get_user_groups as get_user_groups_logic
from app.crud.user_logic import get_users as get_users_logic
from app.crud.user_logic import set_user_role as set_user_role_logic
from app.crud.user_logic import update_user as update_user_logic
from app.db import db_helper
from app.models import User
from app.schemas.group_schemas import UserGroup as UserGroupSchemas
from app.schemas.group_schemas import UserGroupCreate
from app.schemas.user_schemas import User as UserSchemas
from app.schemas.user_schemas import UserCreate, UserRole, UserUpdate

router = APIRouter()


@router.post("/", response_model=UserSchemas, status_code=status.HTTP_201_CREATED)
async def create_user(
    user: UserCreate,
    db: AsyncSession = Depends(db_helper.get_session),
) -> UserSchemas:
    result = await create_user_logic(user, db)
    return UserSchemas.model_validate(result)


@router.get("/", response_model=list[UserSchemas], status_code=status.HTTP_200_OK)
async def get_users(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(db_helper.get_session),
) -> list[UserSchemas]:
    result = await get_users_logic(db, skip, limit)
    return [UserSchemas.model_validate(user) for user in result]


@router.get("/{user_id}", response_model=UserSchemas, status_code=status.HTTP_200_OK)
async def get_user(
    user_id: int,
    db: AsyncSession = Depends(db_helper.get_session),
) -> UserSchemas:
    user = await get_user_logic(user_id, db)
    return UserSchemas.model_validate(user)


@router.put("/{user_id}", response_model=UserSchemas, status_code=status.HTTP_200_OK)
async def update_user(
    user_id: int, user_in: UserUpdate, db: AsyncSession = Depends(db_helper.get_session)
) -> UserSchemas:
    user = await update_user_logic(user_id, user_in, db)
    return UserSchemas.model_validate(user)


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: int, db: AsyncSession = Depends(db_helper.get_session)
) -> None:
    await delete_user_logic(user_id, db)


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
) -> list[UserSchemas]:
    users = await get_group_users_logic(group_id, db, skip, limit)
    return [UserSchemas.model_validate(user) for user in users]


@router.post(
    "{user_id}/role",
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
    return UserSchemas.model_validate(user)


@router.post("/me", response_model=UserGroupSchemas, status_code=status.HTTP_200_OK)
async def create_user_group(
    user_id: int,
    user_group_in: UserGroupCreate,
    current_user: User = Depends(),
    db: AsyncSession = Depends(db_helper.get_session),
) -> UserGroupSchemas:
    user_group = await create_user_group_logic(user_id, user_group_in, db)
    return UserGroupSchemas.model_validate(user_group)


@router.get(
    "/me/groups", response_model=list[UserGroupSchemas], status_code=status.HTTP_200_OK
)
async def get_me_groups(
    current_user: User = Depends(RoleCurrentUser.member),
    db: AsyncSession = Depends(db_helper.get_session),
) -> list[UserGroupSchemas]:
    groups = await get_user_groups_logic(current_user.id, db)
    return [UserGroupSchemas.model_validate(group) for group in groups]


@router.post(
    "/me/groups/{group_id}/users",
    response_model=UserGroupSchemas,
    status_code=status.HTTP_200_OK,
)
async def add_user_to_group(
    group_id: int,
    user_id: int,
    current_user: User = Depends(RoleCurrentUser.admin_groups),
    db: AsyncSession = Depends(db_helper.get_session),
) -> UserGroupSchemas:
    user_group = await add_user_to_group_logic(group_id, user_id, db)
    return UserGroupSchemas.model_validate(user_group)
