from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.task_models import Task
from app.schemas.task_schemas import TaskBase, TaskCreate, TaskUpdate


async def get_tasks(db: AsyncSession, skip: int = 0, limit: int = 100) -> Sequence[TaskBase]:
    result = await db.scalars(select(Task).where(Task.is_active).offset(skip).limit(limit))
    tasks = result.all()
    return [TaskBase.model_validate(task) for task in tasks]


async def get_task(db: AsyncSession, task_id: int) -> TaskBase | None:
    return await db.get(TaskBase, task_id)


async def create_task(db: AsyncSession, task_in: TaskCreate) -> TaskBase:
    task = TaskBase(**task_in.model_dump())
    db.add(task)
    await db.commit()
    await db.refresh(task)
    return task


async def update_task(db: AsyncSession, task_id: int, task_in: TaskUpdate) -> TaskBase | None:
    task = await db.get(TaskBase, task_id)
    if not task:
        return None
    update_data = task_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(task, field, value)
    await db.commit()
    await db.refresh(task)
    return task


async def delete_task(db: AsyncSession, task_id: int) -> bool:
    task = await db.get(TaskBase, task_id)
    if not task:
        return False
    await db.delete(task)
    await db.commit()
    return True
