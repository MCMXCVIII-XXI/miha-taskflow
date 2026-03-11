from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Task as TaskModel
from app.models import User as UserModel
from app.models import UserGroup as UserGroupModel
from app.schemas.task_schemas import TaskCreate, TaskUpdate

from .crud_result import CrudResultTask


async def get_tasks(
    db: AsyncSession, skip: int = 0, limit: int = 100
) -> Sequence[TaskModel]:
    tasks = await db.scalars(
        select(TaskModel)
        .order_by(TaskModel.id)
        .where(TaskModel.is_active)
        .offset(skip)
        .limit(limit)
    )
    return tasks.all()


async def get_task(task_id: int, db: AsyncSession) -> TaskModel | CrudResultTask:
    result = await db.scalars(
        select(TaskModel).where(TaskModel.id == task_id, TaskModel.is_active)
    )
    task = result.first()

    if not task:
        return CrudResultTask.NOT_FOUND

    return task


async def create_task(
    task_in: TaskCreate, db: AsyncSession
) -> TaskModel | CrudResultTask:
    result = await db.scalars(
        select(TaskModel).where(
            (TaskModel.title == task_in.title),
            (TaskModel.group_id == task_in.group_id),
            TaskModel.is_active,
        )
    )

    check = result.first()

    if check:
        return CrudResultTask.TITLE_CONFLICT

    task = TaskModel(**task_in.model_dump())
    db.add(task)
    await db.commit()
    await db.refresh(task)
    return task


async def update_task(
    task_id: int, task_in: TaskUpdate, db: AsyncSession
) -> TaskModel | CrudResultTask:
    task = await get_task(task_id, db)

    if task == CrudResultTask.NOT_FOUND:
        return CrudResultTask.NOT_FOUND

    update_data = task_in.model_dump(exclude_unset=True)

    # Check if task with this title or group already exists
    ###########################################################################
    result = await db.scalars(
        select(TaskModel).where(
            (TaskModel.title == update_data["title"]),
            (TaskModel.group_id == update_data["group_id"]),
            TaskModel.id != task_id,
            TaskModel.is_active,
        )
    )
    check = result.first()
    if check:
        return CrudResultTask.TITLE_CONFLICT
    ###########################################################################

    for field, value in update_data.items():
        setattr(task, field, value)

    await db.commit()
    await db.refresh(task)
    return task


async def delete_task(task_id: int, db: AsyncSession) -> bool | CrudResultTask:
    result = await get_task(task_id, db)

    if isinstance(result, CrudResultTask):
        return CrudResultTask.NOT_FOUND

    result.is_active = False
    await db.commit()
    return True


async def get_user_tasks(
    user: UserModel, db: AsyncSession, skip: int = 0, limit: int = 100
) -> Sequence[TaskModel]:
    tasks = await db.scalars(
        select(TaskModel)
        .join(UserModel, UserModel.id == TaskModel.owner_id)
        .where(UserModel.id == user.id, TaskModel.is_active)
        .order_by(TaskModel.id)
        .offset(skip)
        .limit(limit)
    )
    return tasks.all()


async def get_group_tasks(
    group_id: int, db: AsyncSession, skip: int = 0, limit: int = 100
) -> Sequence[TaskModel]:
    tasks = await db.scalars(
        select(TaskModel)
        .join(UserGroupModel, UserGroupModel.id == TaskModel.group_id)
        .where(UserGroupModel.id == group_id, TaskModel.is_active)
        .order_by(TaskModel.id)
        .offset(skip)
        .limit(limit)
    )
    return tasks.all()
