from fastapi import APIRouter, Response
from prometheus_client import generate_latest

router = APIRouter(tags=["main"])


@router.get(
    "/health",
    summary="Health check",
    response_model=dict[str, str],
    description="""
    Simple health check endpoint.

    Returns:
    - status: Application status (always "ok")
    - version: Application version
    """,
    responses={
        200: {
            "description": "Service is healthy",
            "content": {
                "application/json": {
                    "example": {
                        "status": "ok",
                        "version": "1.0.0",
                    }
                }
            },
        },
    },
)
async def health_check():
    return {
        "status": "ok",
        "version": "1.0.0",
    }


@router.get(
    "/metrics",
    summary="Prometheus metrics",
    description="""
    Prometheus metrics endpoint for application monitoring.

    Returns: Metrics in Prometheus format (text/plain)

    Included metrics:
    - HTTP request duration (histogram)
    - HTTP requests total (counter)
    - HTTP requests in progress (gauge)
    - Application errors (counter)
    - Custom business metrics (social actions, XP, ratings)

    Usage:
    Add this endpoint to Prometheus config:
    ```yaml
    scrape_configs:
      - job_name: 'taskflow'
        static_configs:
          - targets: ['host:port']
    ```
    """,
    response_class=Response,
    responses={
        200: {
            "description": "Prometheus metrics",
            "content": {
                "text/plain": {
                    "example": (
                        "# HELP http_requests_total Total HTTP requests\n"
                        "# TYPE http_requests_total counter\n"
                        'http_requests_total{method="GET",status="200"} 1234.0\n'
                    )
                }
            },
        },
    },
)
async def metrics() -> Response:
    return Response(content=generate_latest(), media_type="text/plain")
