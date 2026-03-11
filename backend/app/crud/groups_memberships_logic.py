from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.crud_result import CrudResultGroupMembership
from app.models import UserGroupMembership as UserGroupMembershipModel
from app.schemas.group_schemas import UserGroupMembershipCreate


async def get_group_memberships(
    group_id: int, db: AsyncSession, skip: int = 0, limit: int = 100
) -> Sequence[UserGroupMembershipModel]:
    memberships = await db.scalars(
        select(UserGroupMembershipModel)
        .where(
            UserGroupMembershipModel.group_id == group_id,
            UserGroupMembershipModel.is_active,
        )
        .order_by(UserGroupMembershipModel.id)
        .offset(skip)
        .limit(limit)
    )
    return memberships.all()


async def add_to_group(
    group_id: int, membership_in: UserGroupMembershipCreate, db: AsyncSession
) -> UserGroupMembershipModel | CrudResultGroupMembership:
    result = await db.scalars(
        select(UserGroupMembershipModel).where(
            (UserGroupMembershipModel.user_id == membership_in.user_id),
            (UserGroupMembershipModel.group_id == membership_in.group_id),
            UserGroupMembershipModel.is_active,
        )
    )

    check = result.first()

    if check:
        return CrudResultGroupMembership.MEMBER_CONFLICT

    membership = UserGroupMembershipModel(**membership_in.model_dump())
    db.add(membership)
    await db.commit()
    await db.refresh(membership)
    return membership


async def delete_group_membership(
    membership_id: int, db: AsyncSession
) -> bool | CrudResultGroupMembership:
    result = await db.scalars(
        select(UserGroupMembershipModel).where(
            UserGroupMembershipModel.id == membership_id,
            UserGroupMembershipModel.is_active,
        )
    )
    membership = result.first()

    if not membership:
        return CrudResultGroupMembership.NOT_FOUND

    membership.is_active = False
    await db.commit()
    return True
