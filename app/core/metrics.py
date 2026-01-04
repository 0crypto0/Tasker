"""Prometheus metrics configuration."""

from prometheus_client import Counter, Gauge, Histogram, Info

# Application info metric
app_info = Info(
    "tasker_app",
    "Tasker application information",
)

# Task submission metrics
tasks_submitted_counter = Counter(
    "tasker_tasks_submitted_total",
    "Total number of tasks submitted",
    ["task_name"],
)

# Task execution metrics
task_execution_counter = Counter(
    "tasker_task_executions_total",
    "Total number of task executions",
    ["task_name", "status"],
)

task_execution_duration = Histogram(
    "tasker_task_execution_duration_seconds",
    "Task execution duration in seconds",
    ["task_name"],
    buckets=(0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0, 120.0, 300.0),
)

# Task status gauge
tasks_by_status = Gauge(
    "tasker_tasks_by_status",
    "Current number of tasks by status",
    ["status"],
)

# Cache metrics
cache_hits_counter = Counter(
    "tasker_cache_hits_total",
    "Total number of cache hits",
)

cache_misses_counter = Counter(
    "tasker_cache_misses_total",
    "Total number of cache misses",
)

# Database metrics
db_operations_counter = Counter(
    "tasker_db_operations_total",
    "Total number of database operations",
    ["operation", "table"],
)

db_operation_duration = Histogram(
    "tasker_db_operation_duration_seconds",
    "Database operation duration in seconds",
    ["operation", "table"],
    buckets=(0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0),
)

# External API metrics
external_api_requests = Counter(
    "tasker_external_api_requests_total",
    "Total number of external API requests",
    ["api_name", "status"],
)

external_api_duration = Histogram(
    "tasker_external_api_duration_seconds",
    "External API request duration in seconds",
    ["api_name"],
    buckets=(0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0),
)


def init_metrics() -> None:
    """Initialize application metrics."""
    app_info.info({
        "version": "1.0.0",
        "environment": "production",
    })

    # Initialize status gauges to 0
    for status in ["pending", "running", "completed", "failed"]:
        tasks_by_status.labels(status=status).set(0)

