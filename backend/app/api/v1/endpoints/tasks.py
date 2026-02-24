from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from backend.app.db.session import async_session
from backend.app.crud.task import (
    get_tasks,
    create_task,
    get_task,
    update_task,
    delete_task,
)
from backend.app.models.task import Task, TaskCreate

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.post("/", response_model=Task, status_code=status.HTTP_201_CREATED)
async def create_new_task(
    task_in: TaskCreate, db: AsyncSession = Depends(async_session)
) -> Task:
    return await create_task(db, task_in)


@router.get("/", response_model=List[Task], status_code=status.HTTP_200_OK)
async def read_tasks(
    skip: int = 0, limit: int = 100, db: AsyncSession = Depends(async_session)
) -> List[Task]:
    return await get_tasks(db, skip, limit)


@router.get("/{task_id}", response_model=Task, status_code=status.HTTP_200_OK)
async def read_task(task_id: int, db: AsyncSession = Depends(async_session)) -> Task:
    task = await get_task(db, task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@router.put("/{task_id}", response_model=Task, status_code=status.HTTP_200_OK)
async def update_task_endpoint(
    task_id: int, task_in: TaskCreate, db: AsyncSession = Depends(async_session)
) -> Task:
    task = await update_task(db, task_id, task_in)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task_endpoint(
    task_id: int, db: AsyncSession = Depends(async_session)
) -> None:
    result = await delete_task(db, task_id)
    if not result:
        raise HTTPException(status_code=404, detail="Task not found")
