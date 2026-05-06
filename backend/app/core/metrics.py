"""TaskFlow business metrics for Prometheus.

Follows Prometheus naming: app_unit_type_suffix (taskflow_tasks_total).
No HTTP (middleware covers). Only TaskFlow domain."""

from prometheus_client import Counter, Gauge, Histogram

http_requests_total = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "status_code", "status"],
)

http_request_duration_seconds = Histogram(
    "http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["method", "endpoint"],
)


TASKS_TOTAL = Counter(
    "taskflow_tasks_total",
    "Tasks processed",
    ["action", "status", "sphere"],
)

TASK_DURATION = Histogram(
    "taskflow_task_duration_seconds",
    "Task execution time",
    ["action", "sphere"],
    buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0],
)

ACTIVE_TASKS = Gauge(
    "taskflow_active_tasks",
    "Active tasks",
    ["sphere"],
)

USER_ACTIONS_TOTAL = Counter(
    "taskflow_user_actions_total",
    "User actions",
    ["action", "role", "status"],
)

ACTIVE_USERS = Gauge(
    "taskflow_active_users",
    "Active users",
    ["role"],
)

GROUP_ACTIONS_TOTAL = Counter(
    "taskflow_group_actions_total",
    "Group actions",
    ["action", "status"],
)

SOCIAL_ACTIONS_TOTAL = Counter(
    "taskflow_social_actions_total",
    "Comments/ratings",
    ["type", "action", "status"],
)

XP_CHANGES_TOTAL = Counter(
    "taskflow_xp_changes_total",
    "XP changes",
    ["direction", "status", "sphere"],
)

XP_TOTAL = Gauge(
    "taskflow_xp_total",
    "Total XP in system",
)

NOTIFICATION_SENT_TOTAL = Counter(
    "taskflow_notification_sent_total",
    "Notifications sent",
    ["type", "status"],
)

SEARCH_QUERIES_TOTAL = Counter(
    "taskflow_search_queries_total",
    "Search queries",
    ["entity", "status"],
)

SEARCH_LATENCY_SECONDS = Histogram(
    "taskflow_search_latency_seconds",
    "Search latency",
    ["entity", "status"],
)

CELERY_TASKS_TOTAL = Counter(
    "taskflow_celery_tasks_total",
    "Celery tasks",
    ["task_name", "status"],
)

CACHE_INVALIDATIONS_TOTAL = Counter(
    "taskflow_cache_invalidations_total", "Count of cache invalidations", ["namespace"]
)

SERVICE_INIT_TOTAL = Counter(
    "taskflow_service_init_total", "Number of service initializations", ["service_name"]
)

BULK_INDEX_TOTAL = Counter(
    "taskflow_bulk_index_total", "Bulk items indexed", ["entity_type", "status"]
)

BULK_INDEX_DURATION = Histogram(
    "taskflow_bulk_index_seconds", "Bulk indexing time", ["entity_type"]
)

OUTBOX_EVENTS_TOTAL = Counter(
    "taskflow_outbox_events_total",
    "Processed outbox events",
    ["entity_type", "event_type", "status"],
)

OUTBOX_PROCESS_DURATION = Histogram(
    "taskflow_outbox_process_seconds", "Time to process outbox event", ["entity_type"]
)


class METRICS:
    """TaskFlow business metrics for Prometheus.

    Follows Prometheus naming: app_unit_type_suffix (taskflow_tasks_total).
    No HTTP (middleware covers). Only TaskFlow domain."""

    http_requests_total = http_requests_total
    http_request_duration_seconds = http_request_duration_seconds

    TASKS_TOTAL = TASKS_TOTAL
    TASK_DURATION = TASK_DURATION
    ACTIVE_TASKS = ACTIVE_TASKS
    USER_ACTIONS_TOTAL = USER_ACTIONS_TOTAL
    ACTIVE_USERS = ACTIVE_USERS
    GROUP_ACTIONS_TOTAL = GROUP_ACTIONS_TOTAL
    SOCIAL_ACTIONS_TOTAL = SOCIAL_ACTIONS_TOTAL
    XP_CHANGES_TOTAL = XP_CHANGES_TOTAL
    XP_TOTAL = XP_TOTAL
    NOTIFICATION_SENT_TOTAL = NOTIFICATION_SENT_TOTAL
    SEARCH_QUERIES_TOTAL = SEARCH_QUERIES_TOTAL
    SEARCH_LATENCY_SECONDS = SEARCH_LATENCY_SECONDS
    CELERY_TASKS_TOTAL = CELERY_TASKS_TOTAL
    CACHE_INVALIDATIONS_TOTAL = CACHE_INVALIDATIONS_TOTAL
    SERVICE_INIT_TOTAL = SERVICE_INIT_TOTAL
    BULK_INDEX_TOTAL = BULK_INDEX_TOTAL
    BULK_INDEX_DURATION = BULK_INDEX_DURATION
    OUTBOX_EVENTS_TOTAL = OUTBOX_EVENTS_TOTAL
    OUTBOX_PROCESS_DURATION = OUTBOX_PROCESS_DURATION
