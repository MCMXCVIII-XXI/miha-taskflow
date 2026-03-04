from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio.session import AsyncSession

from app.crud.crud_result import CrudResultTask
from app.crud.task_logic import create_task as create
from app.crud.task_logic import (
    delete_task as delete,
)
from app.crud.task_logic import (
    get_task,
    get_tasks,
)
from app.crud.task_logic import (
    update_task as update,
)
from app.db import db_helper
from app.schemas.task_schemas import TaskBase, TaskCreate, TaskUpdate

router = APIRouter(prefix="", tags=["tasks"])


@router.post("/", response_model=TaskBase, status_code=status.HTTP_201_CREATED)
async def create_task(
    task_in: TaskCreate, db: AsyncSession = Depends(db_helper.get_session)
) -> TaskBase:
    task = await create(task_in, db)

    if task == CrudResultTask.TITLE_CONFLICT:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Task already exists"
        )

    return TaskBase.model_validate(task)


@router.get("/", response_model=list[TaskBase], status_code=status.HTTP_200_OK)
async def read_tasks(
    skip: int = 0, limit: int = 100, db: AsyncSession = Depends(db_helper.get_session)
) -> list[TaskBase]:
    tasks = await get_tasks(db, skip, limit)
    return [TaskBase.model_validate(task) for task in tasks]


@router.get("/{task_id}", response_model=TaskBase, status_code=status.HTTP_200_OK)
async def read_task(
    task_id: int, db: AsyncSession = Depends(db_helper.get_session)
) -> TaskBase:
    task = await get_task(task_id, db)

    if task == CrudResultTask.NOT_FOUND:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Task not found"
        )

    return TaskBase.model_validate(task)


@router.put("/{task_id}", response_model=TaskBase, status_code=status.HTTP_200_OK)
async def update_task_endpoint(
    task_id: int, task_in: TaskUpdate, db: AsyncSession = Depends(db_helper.get_session)
) -> TaskBase:
    task = await update(task_id, task_in, db)

    if task == CrudResultTask.NOT_FOUND:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Task not found"
        )
    if task == CrudResultTask.TITLE_CONFLICT:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Task already exists"
        )

    return TaskBase.model_validate(task)


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task_endpoint(
    task_id: int, db: AsyncSession = Depends(db_helper.get_session)
) -> None:
    result = await delete(task_id, db)
    if result == CrudResultTask.NOT_FOUND:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Task not found"
        )
