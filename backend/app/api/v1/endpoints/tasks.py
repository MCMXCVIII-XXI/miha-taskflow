from collections.abc import Sequence

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio.session import AsyncSession

from app.crud.task_logic import (
    create_task,
    delete_task,
    get_task,
    get_tasks,
    update_task,
)
from app.db.session import async_session
from app.schemas.task_schemas import TaskBase, TaskCreate, TaskUpdate

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.post("/", response_model=TaskBase, status_code=status.HTTP_201_CREATED)
async def create_new_task(
    task_in: TaskCreate, db: AsyncSession = Depends(async_session)
) -> TaskBase:
    return await create_task(db, task_in)


@router.get("/", response_model=list[TaskBase], status_code=status.HTTP_200_OK)
async def read_tasks(
    skip: int = 0, limit: int = 100, db: AsyncSession = Depends(async_session)
) -> Sequence[TaskBase]:
    return await get_tasks(db, skip, limit)


@router.get("/{task_id}", response_model=TaskBase, status_code=status.HTTP_200_OK)
async def read_task(task_id: int, db: AsyncSession = Depends(async_session)) -> TaskBase:
    task = await get_task(db, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@router.put("/{task_id}", response_model=TaskBase, status_code=status.HTTP_200_OK)
async def update_task_endpoint(
    task_id: int, task_in: TaskUpdate, db: AsyncSession = Depends(async_session)
) -> TaskBase:
    task = await update_task(db, task_id, task_in)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task_endpoint(task_id: int, db: AsyncSession = Depends(async_session)) -> None:
    result = await delete_task(db, task_id)
    if not result:
        raise HTTPException(status_code=404, detail="Task not found")
