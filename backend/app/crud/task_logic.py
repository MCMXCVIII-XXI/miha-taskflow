from collections.abc import Sequence

from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models.task import Task, TaskCreate, TaskUpdate


async def get_tasks(db: AsyncSession, skip: int = 0, limit: int = 100) -> Sequence[Task]:
    result = await db.scalars(select(Task).offset(skip).limit(limit))
    return result.all()


async def get_task(db: AsyncSession, task_id: int) -> Task | None:
    return await db.get(Task, task_id)


async def create_task(db: AsyncSession, task_in: TaskCreate) -> Task:
    task = Task(**task_in.model_dump())
    db.add(task)
    await db.commit()
    await db.refresh(task)
    return task


async def update_task(db: AsyncSession, task_id: int, task_in: TaskUpdate) -> Task | None:
    task = await db.get(Task, task_id)
    if not task:
        return None
    update_data = task_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(task, field, value)
    await db.commit()
    await db.refresh(task)
    return task


async def delete_task(db: AsyncSession, task_id: int) -> bool:
    task = await db.get(Task, task_id)
    if not task:
        return False
    await db.delete(task)
    await db.commit()
    return True
