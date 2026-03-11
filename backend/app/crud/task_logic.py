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
) -> Sequence[Task]:
    tasks = await db.scalars(
        select(Task).order_by(Task.id).where(Task.is_active).offset(skip).limit(limit)
    )
    return tasks.all()


async def get_task(task_id: int, db: AsyncSession) -> Task | CrudResultTask:
    result = await db.scalars(select(Task).where(Task.id == task_id, Task.is_active))
    task = result.first()

    if not task:
        return CrudResultTask.NOT_FOUND

    return task


async def create_task(task_in: TaskCreate, db: AsyncSession) -> Task | CrudResultTask:
    result = await db.scalars(
        select(Task).where(
            (Task.title == task_in.title),
            (Task.group_id == task_in.group_id),
            Task.is_active,
        )
    )

    check = result.first()

    if check:
        return CrudResultTask.TITLE_CONFLICT

    task = Task(**task_in.model_dump())
    db.add(task)
    await db.commit()
    await db.refresh(task)
    return task


async def update_task(
    task_id: int, task_in: TaskUpdate, db: AsyncSession
) -> Task | CrudResultTask:
    result = await db.scalars(select(Task).where(Task.id == task_id, Task.is_active))
    task = result.first()

    if not task:
        return CrudResultTask.NOT_FOUND

    update_data = task_in.model_dump(exclude_unset=True)

    # Check if task with this title or group already exists
    ###########################################################################
    result = await db.scalars(
        select(Task).where(
            (Task.title == update_data["title"]),
            (Task.group_id == update_data["group_id"]),
            Task.id != task_id,
            Task.is_active,
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
    result = await db.scalars(select(Task).where(Task.id == task_id, Task.is_active))
    task = result.first()

    if not task:
        return CrudResultTask.NOT_FOUND

    task.is_active = False
    await db.commit()
    return True
