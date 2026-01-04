"""Base task class with common functionality."""

import asyncio
import time
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any
from uuid import UUID

import structlog

from app.config import get_settings
from app.core.database import get_session_context
from app.core.metrics import task_execution_duration, tasks_by_status
from app.models.task import Task, TaskStatus

settings = get_settings()
logger = structlog.get_logger()


class BaseTask(ABC):
    """Base class for all async tasks."""

    task_name: str = "base"

    @abstractmethod
    async def execute(self, **parameters: Any) -> dict[str, Any]:
        """Execute the task logic.

        Args:
            **parameters: Task-specific parameters

        Returns:
            Task result as a dictionary
        """
        raise NotImplementedError

    async def run(self, task_uuid: UUID, **parameters: Any) -> dict[str, Any]:
        """Run the task with logging and metrics.

        Args:
            task_uuid: UUID of the task record
            **parameters: Task-specific parameters

        Returns:
            Task result
        """
        start_time = time.time()

        logger.info(
            "task_execution_started",
            task_uuid=str(task_uuid),
            task_name=self.task_name,
            parameters=parameters,
        )

        async with get_session_context() as session:
            # Update task status to running
            task = await session.get(Task, task_uuid)
            if task:
                task.status = TaskStatus.RUNNING.value
                await session.commit()
                # Update status gauges: pending → running
                tasks_by_status.labels(status="pending").dec()
                tasks_by_status.labels(status="running").inc()

        try:
            result = await self.execute(**parameters)

            # Update task with result
            async with get_session_context() as session:
                task = await session.get(Task, task_uuid)
                if task:
                    task.status = TaskStatus.COMPLETED.value
                    task.result = result
                    task.completed_at = datetime.utcnow()
                    await session.commit()
                    # Update status gauges: running → completed
                    tasks_by_status.labels(status="running").dec()
                    tasks_by_status.labels(status="completed").inc()

            duration = time.time() - start_time
            task_execution_duration.labels(task_name=self.task_name).observe(duration)

            logger.info(
                "task_execution_completed",
                task_uuid=str(task_uuid),
                task_name=self.task_name,
                duration_seconds=duration,
            )

            return result

        except Exception as e:
            # Update task with error
            async with get_session_context() as session:
                task = await session.get(Task, task_uuid)
                if task:
                    task.status = TaskStatus.FAILED.value
                    task.error_message = str(e)
                    task.completed_at = datetime.utcnow()
                    await session.commit()
                    # Update status gauges: running → failed
                    tasks_by_status.labels(status="running").dec()
                    tasks_by_status.labels(status="failed").inc()

            duration = time.time() - start_time
            task_execution_duration.labels(task_name=self.task_name).observe(duration)

            logger.error(
                "task_execution_failed",
                task_uuid=str(task_uuid),
                task_name=self.task_name,
                error=str(e),
                duration_seconds=duration,
            )
            raise


def run_async(coro):
    """Run async coroutine in sync context (for Celery)."""
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    return loop.run_until_complete(coro)

