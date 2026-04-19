"""HTTP request logging and monitoring middleware.

This module implements middleware for logging HTTP requests and responses,
monitoring performance metrics, and tracking slow queries for debugging
and performance optimization purposes.

The middleware tracks:
- Request/response logging with timing information
- Prometheus metrics for request rates and durations
- Slow query detection and logging
"""

import time
from typing import Any

from fastapi import Request

from app.core.log import get_logger
from app.core.metrics import http_request_duration_seconds, http_requests_total

logger = get_logger("http")

SLOW_QUERY_THRESHOLD = 1.0


async def http_logging_middleware(request: Request, call_next: Any) -> Any:
    """Logs HTTP requests and monitors performance with metrics collection.

    Records incoming HTTP requests and outgoing responses with processing time
    tracking. Collects Prometheus metrics for monitoring and logs slow queries
    that exceed the configured threshold for performance analysis.

    Args:
        request (Request): Incoming HTTP request object
        call_next (Any): Next middleware or endpoint handler function

    Returns:
        Any: HTTP response from the next handler in the chain
    """
    start_time = time.time()

    # Log request
    logger.info(
        "HTTP Request: {method} {url}",
        method=request.method,
        url=str(request.url),
        client_ip=request.client.host if request.client else None,
    )

    # Process request
    response = await call_next(request)

    # Calculate processing time
    process_time = time.time() - start_time

    # Log response
    logger.info(
        "HTTP Response: {method} {url} - {status_code} ({time:.3f}s)",
        method=request.method,
        url=str(request.url),
        status_code=response.status_code,
        time=process_time,
    )

    # Log slow queries
    if process_time > SLOW_QUERY_THRESHOLD:
        logger.warning(
            "Slow request: {method} {url} took {time:.3f}s",
            method=request.method,
            url=str(request.url),
            time=process_time,
        )

    # Prometheus metrics
    endpoint = request.url.path
    http_requests_total.labels(
        method=request.method,
        endpoint=endpoint,
        status_code=response.status_code,
    ).inc()
    http_request_duration_seconds.labels(
        method=request.method,
        endpoint=endpoint,
    ).observe(process_time)

    return response
