from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio.session import AsyncSession

from app.crud.crud_result import CrudResultGroup, CrudResultGroupMembership
from app.crud.group_logic import create_group as create_group_logic
from app.crud.group_logic import delete_group as delete_group_logic
from app.crud.group_logic import get_group as get_group_logic
from app.crud.group_logic import get_groups as get_groups_logic
from app.crud.group_logic import update_group as update_group_logic
from app.crud.groups_memberships_logic import add_to_group as add_to_group_logic
from app.crud.groups_memberships_logic import (
    delete_group_membership as delete_group_membership_logic,
)
from app.crud.groups_memberships_logic import (
    get_group_memberships as get_group_memberships_logic,
)
from app.db import db_helper
from app.schemas.group_schemas import UserGroup as UserGroupSchema
from app.schemas.group_schemas import (
    UserGroupCreate,
    UserGroupMembershipCreate,
    UserGroupUpdate,
)
from app.schemas.group_schemas import (
    UserGroupMembership as UserGroupMembershipSchema,
)

router = APIRouter()


@router.get(
    "/",
    response_model=list[UserGroupSchema],
    status_code=status.HTTP_200_OK,
)
async def get_groups(
    db: AsyncSession = Depends(db_helper.get_session),
    skip: int = 0,
    limit: int = 100,
) -> list[UserGroupSchema]:
    result = await get_groups_logic(db, skip, limit)
    return [UserGroupSchema.model_validate(group) for group in result]


@router.post(
    "/",
    response_model=list[UserGroupSchema],
    status_code=status.HTTP_201_CREATED,
)
async def create_group(
    group_in: UserGroupCreate,
    db: AsyncSession = Depends(db_helper.get_session),
) -> UserGroupSchema:
    result = await create_group_logic(group_in, db)

    if result == CrudResultGroup.NAME_CONFLICT:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=CrudResultGroup.NAME_CONFLICT.value,
        )

    return UserGroupSchema.model_validate(result)


@router.get(
    "/{group_id}",
    response_model=UserGroupSchema,
    status_code=status.HTTP_200_OK,
)
async def get_group(
    group_id: int,
    db: AsyncSession = Depends(db_helper.get_session),
) -> UserGroupSchema:
    result = await get_group_logic(group_id, db)

    if result == CrudResultGroup.NOT_FOUND:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=CrudResultGroup.NOT_FOUND.value,
        )

    return UserGroupSchema.model_validate(result)


@router.put(
    "/{group_id}",
    response_model=UserGroupSchema,
    status_code=status.HTTP_200_OK,
)
async def update_group(
    group_id: int,
    group_in: UserGroupUpdate,
    db: AsyncSession = Depends(db_helper.get_session),
) -> UserGroupSchema:
    result = await update_group_logic(group_id, group_in, db)

    if result == CrudResultGroup.NOT_FOUND:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=CrudResultGroup.NOT_FOUND.value,
        )
    elif result == CrudResultGroup.NAME_CONFLICT:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=CrudResultGroup.NAME_CONFLICT.value,
        )

    return UserGroupSchema.model_validate(result)


@router.delete(
    "/{group_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_group(
    group_id: int,
    db: AsyncSession = Depends(db_helper.get_session),
) -> None:
    result = await delete_group_logic(group_id, db)

    if result == CrudResultGroup.NOT_FOUND:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=CrudResultGroup.NOT_FOUND.value,
        )


@router.get(
    "/{group_id}/memberships",
    response_model=list[UserGroupMembershipSchema],
    status_code=status.HTTP_200_OK,
)
async def get_group_memberships(
    group_id: int,
    db: AsyncSession = Depends(db_helper.get_session),
    skip: int = 0,
    limit: int = 100,
) -> list[UserGroupMembershipSchema]:
    result = await get_group_memberships_logic(group_id, db, skip, limit)
    return [
        UserGroupMembershipSchema.model_validate(membership) for membership in result
    ]


@router.post(
    "/{group_id}/memberships",
    response_model=UserGroupMembershipSchema,
    status_code=status.HTTP_200_OK,
)
async def add_to_group(
    group_id: int,
    membership_in: UserGroupMembershipCreate,
    db: AsyncSession = Depends(db_helper.get_session),
) -> UserGroupMembershipSchema:
    result = await add_to_group_logic(group_id, membership_in, db)

    if result == CrudResultGroupMembership.MEMBER_CONFLICT:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=CrudResultGroupMembership.MEMBER_CONFLICT.value,
        )

    return UserGroupMembershipSchema.model_validate(result)


@router.delete(
    "/{membership_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_group_membership(
    membership_id: int,
    db: AsyncSession = Depends(db_helper.get_session),
) -> None:
    result = await delete_group_membership_logic(membership_id, db)

    if result == CrudResultGroupMembership.NOT_FOUND:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=CrudResultGroupMembership.NOT_FOUND.value,
        )
