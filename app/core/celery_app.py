"""Celery application configuration."""

from celery import Celery
from celery.signals import (
    task_failure,
    task_postrun,
    task_prerun,
    task_success,
)

from app.config import get_settings

settings = get_settings()

# Create Celery app
celery_app = Celery(
    "tasker",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=[
        "app.tasks.sum_task",
        "app.tasks.chatgpt_task",
        "app.tasks.weather_task",
    ],
)

# Celery configuration
celery_app.conf.update(
    # Task settings
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    # Task execution settings
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    task_time_limit=300,  # 5 minutes hard limit
    task_soft_time_limit=240,  # 4 minutes soft limit
    # Worker settings
    worker_prefetch_multiplier=1,
    worker_concurrency=4,
    # Result backend settings
    result_expires=3600,  # 1 hour
    result_extended=True,
    # Task routing
    task_routes={
        "app.tasks.sum_task.*": {"queue": "default"},
        "app.tasks.chatgpt_task.*": {"queue": "external_api"},
        "app.tasks.weather_task.*": {"queue": "external_api"},
    },
    task_default_queue="default",
    # Retry settings
    task_default_retry_delay=60,  # 1 minute
    task_max_retries=3,
)


# Signal handlers for logging and metrics
@task_prerun.connect
def task_prerun_handler(task_id: str, task: Celery, *args, **kwargs) -> None:
    """Handle task pre-run signal."""
    # Import here to avoid circular imports
    import structlog

    logger = structlog.get_logger()
    logger.info(
        "task_started",
        task_id=task_id,
        task_name=task.name,
    )


@task_postrun.connect
def task_postrun_handler(
    task_id: str,
    task: Celery,
    retval: any,
    state: str,
    *args,
    **kwargs,
) -> None:
    """Handle task post-run signal."""
    import structlog

    logger = structlog.get_logger()
    logger.info(
        "task_completed",
        task_id=task_id,
        task_name=task.name,
        state=state,
    )


@task_success.connect
def task_success_handler(sender: Celery, result: any, **kwargs) -> None:
    """Handle task success signal."""
    from app.core.metrics import task_execution_counter

    task_execution_counter.labels(
        task_name=sender.name,
        status="success",
    ).inc()


@task_failure.connect
def task_failure_handler(
    sender: Celery,
    task_id: str,
    exception: Exception,
    traceback: any,
    **kwargs,
) -> None:
    """Handle task failure signal."""
    import structlog

    from app.core.metrics import task_execution_counter

    logger = structlog.get_logger()
    logger.error(
        "task_failed",
        task_id=task_id,
        task_name=sender.name,
        error=str(exception),
    )

    task_execution_counter.labels(
        task_name=sender.name,
        status="failure",
    ).inc()

