from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.api.v1 import api_router
from app.cache import init_cache
from app.core.exceptions.rbac_exc import BaseRBACError
from app.core.exceptions.security_exc import BaseSecurityError
from app.core.logging import get_logger, setup_logging
from app.core.middleware import http_logging_middleware
from app.core.permission import init_rbac
from app.db import db_helper
from app.service.exceptions.group_exc import BaseGroupError
from app.service.exceptions.group_membership_exc import BaseGroupMembershipError
from app.service.exceptions.search_exc import BaseSearchError
from app.service.exceptions.task_exc import BaseTaskError
from app.service.exceptions.user_exc import BaseUserError

# Initialize logging on startup
setup_logging()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    # startup
    logger.info("Starting TaskFlow application")

    # Initialize cache Redis
    await init_cache()
    logger.info("Cache initialized")

    # Adding values to the RBAC tables
    await init_rbac()
    logger.info("RBAC initialized")

    yield

    # shutdown
    logger.info("Shutting down TaskFlow application")
    # Closing the database connection
    await db_helper.dispose()
    logger.info("Database connections closed")


app = FastAPI(title="TaskFlow", version="1.0.0", lifespan=lifespan)

# Add HTTP logging middleware
app.middleware("http")(http_logging_middleware)
app.include_router(api_router)


# Exception handlers ##################################################################
@app.exception_handler(BaseSearchError)
def search_exception_handler(request: Request, exc: BaseSearchError) -> JSONResponse:
    logger.error(
        "Search error: {message} | {method} {url}",
        message=exc.message,
        method=request.method,
        url=str(request.url),
    )
    return JSONResponse(
        status_code=exc.code,
        content={"detail": exc.message},
    )


@app.exception_handler(BaseRBACError)
def rbac_exception_handler(request: Request, exc: BaseRBACError) -> JSONResponse:
    logger.warning(
        "RBAC error: {message} | {method} {url}",
        message=exc.message,
        method=request.method,
        url=str(request.url),
    )
    return JSONResponse(
        status_code=exc.code,
        content={"detail": exc.message},
    )


@app.exception_handler(BaseSecurityError)
def security_exception_handler(
    request: Request, exc: BaseSecurityError
) -> JSONResponse:
    logger.warning(
        "Security error: {message} | {method} {url}",
        message=exc.message,
        method=request.method,
        url=str(request.url),
    )
    return JSONResponse(
        status_code=exc.code,
        content={"detail": exc.message},
    )


@app.exception_handler(BaseGroupError)
def group_exception_handler(request: Request, exc: BaseGroupError) -> JSONResponse:
    logger.error(
        "Group error: {message} | {method} {url}",
        message=exc.message,
        method=request.method,
        url=str(request.url),
    )
    return JSONResponse(
        status_code=exc.code,
        content={"detail": exc.message},
    )


@app.exception_handler(BaseGroupMembershipError)
def group_membership_exception_handler(
    request: Request, exc: BaseGroupMembershipError
) -> JSONResponse:
    logger.warning(
        "Group membership error: {message} | {method} {url}",
        message=exc.message,
        method=request.method,
        url=str(request.url),
    )
    return JSONResponse(
        status_code=exc.code,
        content={"detail": exc.message},
    )


@app.exception_handler(BaseTaskError)
def task_exception_handler(request: Request, exc: BaseTaskError) -> JSONResponse:
    logger.error(
        "Task error: {message} | {method} {url}",
        message=exc.message,
        method=request.method,
        url=str(request.url),
    )
    return JSONResponse(
        status_code=exc.code,
        content={"detail": exc.message},
    )


@app.exception_handler(BaseUserError)
def user_exception_handler(request: Request, exc: BaseUserError) -> JSONResponse:
    logger.error(
        "User error: {message} | {method} {url}",
        message=exc.message,
        method=request.method,
        url=str(request.url),
    )
    return JSONResponse(
        status_code=exc.code,
        content={"detail": exc.message},
    )


########################################################################################
