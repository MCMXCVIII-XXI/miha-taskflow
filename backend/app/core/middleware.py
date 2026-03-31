import time
from typing import Any

from fastapi import Request

from app.core.log import get_logger
from app.core.metrics import http_request_duration_seconds, http_requests_total

logger = get_logger("http")

SLOW_QUERY_THRESHOLD = 1.0  # seconds


async def http_logging_middleware(request: Request, call_next: Any) -> Any:
    """
    Middleware for logging HTTP requests.

    Logs:
    - Method, URL, status code
    - Request processing time
    - Client IP
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
