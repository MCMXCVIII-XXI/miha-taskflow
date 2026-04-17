"""
Celery Beat periodic tasks configuration for Outbox Pattern.

Automatically schedules background jobs for reliable ES synchronization.

SCHEDULE:
├── process-outbox-every-30-seconds (30s)
│   └── Scans outbox table → indexes to ES
│   └── Keeps ES eventually consistent with PostgreSQL
│
└── retry-failed-every-5-minutes (5min)
    └── Retries failed indexing operations
    └── max_retries=3 by default → DLQ after 3 attempts

Why these intervals:
- 30s: Balance between freshness and ES load (100 docs/batch)
- 5min: Retries shouldn't spam but shouldn't linger forever

Production scaling:
- soil-1 worker: 1 job/30s = 120 jobs/hour
- soil-4 workers: 480 jobs/hour capacity
"""

from .celery import celery_app

celery_app.conf.beat_schedule = {
    "process-outbox-every-30-seconds": {
        "task": "app.outbox_processor",
        "schedule": 30.0,
    },
    "retry-failed-every-5-minutes": {
        "task": "app.outbox_retry_failed",
        "schedule": 300.0,
    },
}
