from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.v1 import api_router
from app.core.exceptions.security_exc import BaseSecurityError
from app.core.permission import init_rbac
from app.crud.exceptions.group_exc import BaseGroupError
from app.crud.exceptions.group_membership_exc import BaseGroupMembershipError
from app.crud.exceptions.task_exc import BaseTaskError
from app.crud.exceptions.user_exc import BaseUserError
from app.db import db_helper


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    # startup
    yield
    # shutdown
    await db_helper.dispose()


app = FastAPI(title="TaskFlow", version="1.0.0", lifespan=lifespan)
app.include_router(api_router)


# Exception handlers ##################################################################
@app.exception_handler(BaseSecurityError)
def security_exception_handler(
    request: Request, exc: BaseSecurityError
) -> JSONResponse:
    return JSONResponse(
        status_code=exc.code,
        content={"detail": exc.message},
    )


@app.exception_handler(BaseGroupError)
def group_exception_handler(request: Request, exc: BaseGroupError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.code,
        content={"detail": exc.message},
    )


@app.exception_handler(BaseGroupMembershipError)
def group_membership_exception_handler(
    request: Request, exc: BaseGroupMembershipError
) -> JSONResponse:
    return JSONResponse(
        status_code=exc.code,
        content={"detail": exc.message},
    )


@app.exception_handler(BaseTaskError)
def task_exception_handler(request: Request, exc: BaseTaskError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.code,
        content={"detail": exc.message},
    )


@app.exception_handler(BaseUserError)
def user_exception_handler(request: Request, exc: BaseUserError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.code,
        content={"detail": exc.message},
    )


########################################################################################
