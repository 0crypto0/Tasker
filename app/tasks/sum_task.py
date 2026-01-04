"""Sum two numbers task implementation."""

from typing import Any
from uuid import UUID

import structlog

from app.core.celery_app import celery_app
from app.tasks.base import BaseTask, run_async

logger = structlog.get_logger()


class SumTask(BaseTask):
    """Task to sum two numbers."""

    task_name = "sum"

    async def execute(self, a: float, b: float, **kwargs: Any) -> dict[str, Any]:
        """Execute the sum operation.

        Args:
            a: First number
            b: Second number

        Returns:
            Dictionary with the sum result
        """
        # Validate inputs are numeric
        if not isinstance(a, (int, float)):
            raise ValueError(f"Parameter 'a' must be numeric, got {type(a).__name__}")
        if not isinstance(b, (int, float)):
            raise ValueError(f"Parameter 'b' must be numeric, got {type(b).__name__}")

        result = a + b

        logger.debug(
            "sum_calculated",
            a=a,
            b=b,
            result=result,
        )

        return {
            "operation": "sum",
            "a": a,
            "b": b,
            "result": result,
        }


@celery_app.task(
    name="app.tasks.sum_task.sum_numbers",
    bind=True,
    max_retries=3,
    default_retry_delay=60,
)
def sum_numbers(self, task_uuid: str, a: float, b: float) -> dict[str, Any]:
    """Celery task to sum two numbers.

    Args:
        task_uuid: UUID of the task record
        a: First number
        b: Second number

    Returns:
        Task result
    """
    task = SumTask()
    try:
        return run_async(task.run(UUID(task_uuid), a=a, b=b))
    except Exception as exc:
        logger.error(
            "sum_task_failed",
            task_uuid=task_uuid,
            error=str(exc),
        )
        # Don't retry on validation errors - they won't succeed on retry
        if isinstance(exc, ValueError):
            raise
        raise self.retry(exc=exc)

