from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

import sentry_sdk
from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from prometheus_client import generate_latest
from sentry_sdk.integrations.fastapi import FastApiIntegration
from slowapi import Limiter
from slowapi.util import get_remote_address

from app.api.v1 import api_router
from app.cache import init_cache
from app.core.exceptions.rbac_exc import BaseRBACError
from app.core.exceptions.security_exc import BaseSecurityError
from app.core.log import get_logger, setup_logging
from app.core.middleware import http_logging_middleware
from app.core.permission import init_rbac
from app.db import db_helper
from app.service.exceptions.group_exc import BaseGroupError
from app.service.exceptions.group_membership_exc import BaseGroupMembershipError
from app.service.exceptions.notifi_exc import BaseNotificationError
from app.service.exceptions.search_exc import BaseSearchError
from app.service.exceptions.task_exc import BaseTaskError
from app.service.exceptions.user_exc import BaseUserError

# Initialize logging on startup
setup_logging()
logger = get_logger(__name__)

# Rate limiter
limiter = Limiter(key_func=get_remote_address)

# Sentry
sentry_sdk.init(
    dsn="",
    integrations=[FastApiIntegration()],
    traces_sample_rate=0.1,
)


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

# Add rate limiter
app.state.limiter = limiter

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "https://taskflow.ru"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
)

# Add HTTP logging middleware
app.middleware("http")(http_logging_middleware)


# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint for production."""
    logger.info("Health check requested")
    return {"status": "ok", "version": "1.0.0"}


# Prometheus metrics endpoint
@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint."""
    return Response(content=generate_latest(), media_type="text/plain")


# Include API router
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


@app.exception_handler(BaseNotificationError)
def notification_exception_handler(
    request: Request, exc: BaseNotificationError
) -> JSONResponse:
    logger.error(
        "Notification error: {message} | {method} {url}",
        message=exc.message,
        method=request.method,
        url=str(request.url),
    )
    return JSONResponse(
        status_code=exc.code,
        content={"detail": exc.message},
    )
