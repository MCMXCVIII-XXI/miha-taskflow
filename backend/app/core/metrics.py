"""TaskFlow business metrics for Prometheus.

Follows Prometheus naming: app_unit_type_suffix (taskflow_tasks_total).
No HTTP (middleware covers). Only TaskFlow domain."""

from prometheus_client import Counter, Gauge, Histogram

http_requests_total = Counter(
    "http_requests_total", "Total HTTP requests", ["method", "endpoint", "status_code"]
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
    ["action", "role"],
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
    ["type", "action"],
)

XP_CHANGES_TOTAL = Counter(
    "taskflow_xp_changes_total",
    "XP changes",
    ["direction"],
)

XP_TOTAL = Gauge(
    "taskflow_xp_total",
    "Total XP in system",
)

NOTIFICATION_SENT_TOTAL = Counter(
    "taskflow_notification_sent_total",
    "Notifications sent",
    ["type"],
)

SEARCH_QUERIES_TOTAL = Counter(
    "taskflow_search_queries_total",
    "Search queries",
    ["entity", "status"],
)

SEARCH_LATENCY_SECONDS = Histogram(
    "taskflow_search_latency_seconds",
    "Search latency",
    ["entity"],
)

CELERY_TASKS_TOTAL = Counter(
    "taskflow_celery_tasks_total",
    "Celery tasks",
    ["task_name", "status"],
)
