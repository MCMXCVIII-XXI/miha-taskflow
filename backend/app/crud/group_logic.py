from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import UserGroup as UserGroupModel
from app.schemas.group_schemas import UserGroupCreate, UserGroupUpdate

from .exceptions import group_exc


async def get_groups(
    db: AsyncSession, skip: int = 0, limit: int = 100
) -> Sequence[UserGroupModel]:
    groups = await db.scalars(
        select(UserGroupModel)
        .order_by(UserGroupModel.id)
        .where(UserGroupModel.is_active)
        .offset(skip)
        .limit(limit)
    )
    return groups.all()


async def get_group(group_id: int, db: AsyncSession) -> UserGroupModel:
    result = await db.scalars(
        select(UserGroupModel).where(
            UserGroupModel.id == group_id, UserGroupModel.is_active
        )
    )
    group = result.first()

    if not group:
        raise group_exc.GroupNotFound()

    return group


async def create_group(group_in: UserGroupCreate, db: AsyncSession) -> UserGroupModel:
    result = await db.scalars(
        select(UserGroupModel).where(
            UserGroupModel.name == group_in.name, UserGroupModel.is_active
        )
    )

    check = result.first()

    if check:
        raise group_exc.GroupNameConflict()

    group = UserGroupModel(**group_in.model_dump())
    db.add(group)
    await db.commit()
    await db.refresh(group)
    return group


async def update_group(
    group_id: int, group_in: UserGroupUpdate, db: AsyncSession
) -> UserGroupModel:
    try:
        group = await get_group(group_id, db)
    except group_exc.GroupNotFound as e:
        raise e

    # Check if group with this name already exists
    ###########################################################################
    result = await db.scalars(
        select(UserGroupModel).where(
            (UserGroupModel.name == group_in.name),
            UserGroupModel.is_active,
        )
    )
    check = result.first()
    if check:
        raise group_exc.GroupNameConflict()
    ###########################################################################

    group.name = group_in.name
    await db.commit()
    await db.refresh(group)
    return group


async def delete_group(group_id: int, db: AsyncSession) -> bool:
    try:
        group = await get_group(group_id, db)
    except group_exc.GroupNotFound as e:
        raise e

    group.is_active = False
    await db.commit()
    return True
