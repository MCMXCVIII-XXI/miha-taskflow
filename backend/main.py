"""Main application module for TaskFlow.

This module initializes the FastAPI application and configures all
core components including database, caching, authentication, and routing.
It also sets up exception handling, middleware, and application lifecycle
management through lifespan events.

The application follows a layered architecture with clear separation
of concerns between presentation, business logic, and data layers.
"""

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
from app.core.metrics import METRICS
from app.core.middleware import http_logging_middleware
from app.core.permission import init_rbac
from app.core.sse import sse_manager
from app.db import db_helper
from app.es import es_helper
from app.service.exceptions.comment_exc import BaseCommentError
from app.service.exceptions.group_exc import BaseGroupError
from app.service.exceptions.group_membership_exc import BaseGroupMembershipError
from app.service.exceptions.notifi_exc import BaseNotificationError
from app.service.exceptions.rating_exc import BaseRatingError
from app.service.exceptions.search_exc import BaseSearchError
from app.service.exceptions.task_exc import BaseTaskError
from app.service.exceptions.user_exc import BaseUserError

# Initialize logging on startup
setup_logging()
logger = get_logger(__name__)

# Rate limiter for API request throttling
limiter = Limiter(key_func=get_remote_address)

# Sentry integration for error tracking and monitoring
sentry_sdk.init(
    dsn="",
    integrations=[FastApiIntegration()],
    traces_sample_rate=0.1,
)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan manager for startup and shutdown events.

    This async context manager handles application initialization and cleanup,
    ensuring all services are properly started and stopped with the application.

    Startup sequence:
    1. Initialize logging system
    2. Initialize Redis cache
    3. Initialize Role-Based Access Control (RBAC) system
    4. Start Server-Sent Events (SSE) manager
    5. Initialize Elasticsearch client

    Shutdown sequence:
    1. Stop SSE manager
    2. Close Elasticsearch connections
    3. Close database connections
    """
    # Startup sequence
    logger.info("Starting TaskFlow application")

    # Initialize Redis cache for performance optimization
    await init_cache()
    logger.info("Cache initialized")

    # Initialize Role-Based Access Control system
    await init_rbac()
    logger.info("RBAC initialized")

    # Start Server-Sent Events manager for real-time notifications
    await sse_manager.start()
    logger.info("SSE Manager initialized")

    # Initialize Elasticsearch client for search functionality
    await es_helper._get_client()
    logger.info("Elasticsearch initialized")

    yield

    # Shutdown sequence
    logger.info("Shutting down TaskFlow application")

    # Stop SSE manager gracefully
    await sse_manager.stop()

    # Close Elasticsearch connections
    await es_helper.dispose()

    # Close database connections
    await db_helper.dispose()
    logger.info("Database connections closed")


app = FastAPI(
    title="TaskFlow",
    version="1.0.0",
    lifespan=lifespan,
    description="TaskFlow - Advanced task management system with \
        groups, XP, and notifications",
)

# Add rate limiter to prevent abuse and ensure fair usage
app.state.limiter = limiter

# CORS middleware for cross-origin resource sharing
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "https://taskflow.ru"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Authorization", "Content-Type"],
)

# Add HTTP logging middleware for request/response tracking
app.middleware("http")(http_logging_middleware)


# Health check endpoint for monitoring and deployment health checks
@app.get("/health", tags=["health"])
async def health_check():
    """Health check endpoint for production monitoring.

    Returns application status and version information for
    infrastructure monitoring and deployment health checks.

    Returns:
        dict: Status information with version
    """
    logger.info("Health check requested")
    return {"status": "ok", "version": "1.0.0"}


# Prometheus metrics endpoint for application monitoring
@app.get("/metrics", tags=["monitoring"])
async def metrics():
    """Prometheus metrics endpoint for application monitoring.

    Exposes application metrics in Prometheus format for monitoring
    and alerting purposes. Includes request rates, error rates,
    and performance metrics.

    Returns:
        Response: Plain text metrics in Prometheus format
    """
    return Response(content=generate_latest(), media_type="text/plain")


# Include API router with all version 1 endpoints
app.include_router(api_router)


# Exception handlers for domain-specific errors ###################################
@app.exception_handler(BaseRatingError)
def rating_exception_handler(request: Request, exc: BaseRatingError) -> JSONResponse:
    """Handle rating-related exceptions with appropriate logging and response."""
    METRICS.SOCIAL_ACTIONS_TOTAL.labels(
        type="rating", action="operation", status="error"
    ).inc()
    logger.error(
        "Rating error: {message} | {method} {url}",
        message=exc.message,
        method=request.method,
        url=str(request.url),
    )
    return JSONResponse(
        status_code=exc.code,
        content={"detail": exc.message},
    )


@app.exception_handler(BaseCommentError)
def comment_exception_handler(request: Request, exc: BaseCommentError) -> JSONResponse:
    """Handle comment-related exceptions with appropriate logging and response."""
    METRICS.SOCIAL_ACTIONS_TOTAL.labels(
        type="comment", action="operation", status="error"
    ).inc()
    logger.error(
        "Comment error: {message} | {method} {url}",
        message=exc.message,
        method=request.method,
        url=str(request.url),
    )
    return JSONResponse(
        status_code=exc.code,
        content={"detail": exc.message},
    )


@app.exception_handler(BaseSearchError)
def search_exception_handler(request: Request, exc: BaseSearchError) -> JSONResponse:
    """Handle search-related exceptions with appropriate logging and response."""
    METRICS.SEARCH_QUERIES_TOTAL.labels(entity="search", status="error").inc()
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
    """Handle Role-Based Access Control exceptions with warning level logging."""
    METRICS.USER_ACTIONS_TOTAL.labels(
        action="rbac_check", role="unknown", status="error"
    ).inc()
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
    """Handle security-related exceptions with warning level logging."""
    METRICS.USER_ACTIONS_TOTAL.labels(
        action="security_check", role="unknown", status="error"
    ).inc()
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
    """Handle group-related exceptions with error level logging."""
    METRICS.GROUP_ACTIONS_TOTAL.labels(action="group_operation", status="error").inc()
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
    """Handle group membership exceptions with warning level logging."""
    METRICS.GROUP_ACTIONS_TOTAL.labels(
        action="membership_operation", status="error"
    ).inc()
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
    """Handle task-related exceptions with error level logging."""
    METRICS.TASKS_TOTAL.labels(
        action="task_operation", status="error", sphere="general"
    ).inc()
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
    """Handle user-related exceptions with error level logging."""
    METRICS.USER_ACTIONS_TOTAL.labels(
        action="user_operation", role="user", status="error"
    ).inc()
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
    """Handle notification-related exceptions with error level logging."""
    METRICS.NOTIFICATION_SENT_TOTAL.labels(
        type="notification_failure", status="error"
    ).inc()
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
