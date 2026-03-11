from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio.session import AsyncSession

from app.core.security.current_role import RoleCurrentUser
from app.crud.crud_result import CrudResultTask
from app.crud.task_logic import create_task as create
from app.crud.task_logic import delete_task as delete
from app.crud.task_logic import get_group_tasks as get_group_tasks_logic
from app.crud.task_logic import get_task, get_tasks, get_user_tasks
from app.crud.task_logic import update_task as update
from app.db import db_helper
from app.models import User as UserModel
from app.schemas.task_schemas import Task as TaskSchemas
from app.schemas.task_schemas import TaskCreate, TaskUpdate

router = APIRouter(prefix="", tags=["tasks"])


@router.post("/", response_model=TaskSchemas, status_code=status.HTTP_201_CREATED)
async def create_task(
    task_in: TaskCreate, db: AsyncSession = Depends(db_helper.get_session)
) -> TaskSchemas:
    task = await create(task_in, db)

    if task == CrudResultTask.TITLE_CONFLICT:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=CrudResultTask.TITLE_CONFLICT.value,
        )

    return TaskSchemas.model_validate(task)


@router.get("/", response_model=list[TaskSchemas], status_code=status.HTTP_200_OK)
async def read_tasks(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(db_helper.get_session),
) -> list[TaskSchemas]:
    tasks = await get_tasks(db, skip, limit)
    return [TaskSchemas.model_validate(task) for task in tasks]


@router.get("/{task_id}", response_model=TaskSchemas, status_code=status.HTTP_200_OK)
async def read_task(
    task_id: int,
    db: AsyncSession = Depends(db_helper.get_session),
    current_user: UserModel = Depends(RoleCurrentUser.admin),
) -> TaskSchemas:
    task = await get_task(task_id, db)

    if task == CrudResultTask.NOT_FOUND:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=CrudResultTask.NOT_FOUND.value
        )

    return TaskSchemas.model_validate(task)


@router.put("/{task_id}", response_model=TaskSchemas, status_code=status.HTTP_200_OK)
async def update_task_endpoint(
    task_id: int, task_in: TaskUpdate, db: AsyncSession = Depends(db_helper.get_session)
) -> TaskSchemas:
    task = await update(task_id, task_in, db)

    if task == CrudResultTask.NOT_FOUND:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=CrudResultTask.NOT_FOUND.value
        )
    if task == CrudResultTask.TITLE_CONFLICT:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=CrudResultTask.TITLE_CONFLICT.value,
        )

    return TaskSchemas.model_validate(task)


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task_endpoint(
    task_id: int, db: AsyncSession = Depends(db_helper.get_session)
) -> None:
    result = await delete(task_id, db)
    if result == CrudResultTask.NOT_FOUND:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=CrudResultTask.NOT_FOUND.value
        )


@router.get(
    "/me/tasks", response_model=list[TaskSchemas], status_code=status.HTTP_200_OK
)
async def get_me_tasks(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(db_helper.get_session),
    current_user: UserModel = Depends(RoleCurrentUser.member),
) -> list[TaskSchemas]:
    tasks = await get_user_tasks(current_user, db, skip, limit)
    return [TaskSchemas.model_validate(task) for task in tasks]


@router.get(
    "/group/{group_id}/tasks",
    response_model=list[TaskSchemas],
    status_code=status.HTTP_200_OK,
)
async def get_group_tasks(
    group_id: int,
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(db_helper.get_session),
    current_user: UserModel = Depends(RoleCurrentUser.admin_groups),
) -> list[TaskSchemas]:
    tasks = await get_group_tasks_logic(group_id, db, skip, limit)
    return [TaskSchemas.model_validate(task) for task in tasks]
