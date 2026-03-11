from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.crud_result import CrudResultGroup
from app.models import UserGroup as UserGroupModel
from app.schemas.group_schemas import UserGroupCreate, UserGroupUpdate


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


async def get_group(
    group_id: int, db: AsyncSession
) -> UserGroupModel | CrudResultGroup:
    result = await db.scalars(
        select(UserGroupModel).where(
            UserGroupModel.id == group_id, UserGroupModel.is_active
        )
    )
    group = result.first()

    if not group:
        return CrudResultGroup.NOT_FOUND

    return group


async def create_group(
    group_in: UserGroupCreate, db: AsyncSession
) -> UserGroupModel | CrudResultGroup:
    result = await db.scalars(
        select(UserGroupModel).where(
            UserGroupModel.name == group_in.name, UserGroupModel.is_active
        )
    )

    check = result.first()

    if check:
        return CrudResultGroup.NAME_CONFLICT

    group = UserGroupModel(**group_in.model_dump())
    db.add(group)
    await db.commit()
    await db.refresh(group)
    return group


async def update_group(
    group_id: int, group_in: UserGroupUpdate, db: AsyncSession
) -> UserGroupModel | CrudResultGroup:
    group = await get_group(group_id, db)

    if isinstance(group, CrudResultGroup):
        return group

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
        return CrudResultGroup.NAME_CONFLICT
    ###########################################################################

    group.name = group_in.name
    await db.commit()
    await db.refresh(group)
    return group


async def delete_group(group_id: int, db: AsyncSession) -> bool | CrudResultGroup:
    result = await get_group(group_id, db)

    if isinstance(result, CrudResultGroup):
        return result

    result.is_active = False
    await db.commit()
    return True
