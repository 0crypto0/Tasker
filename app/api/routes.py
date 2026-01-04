"""API route definitions."""

from uuid import UUID

import structlog
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app import __version__
from app.api.schemas import (
    ErrorResponse,
    HealthResponse,
    RunTaskRequest,
    RunTaskResponse,
    TaskName,
    TaskOutputResponse,
    TaskStatusResponse,
)
from app.core.cache import CacheService, get_cache
from app.core.database import get_session
from app.core.metrics import tasks_by_status, tasks_submitted_counter
from app.models.task import Task, TaskStatus

logger = structlog.get_logger()

router = APIRouter()


def get_celery_task(task_name: TaskName):
    """Get the Celery task function for the given task name."""
    from app.tasks.chatgpt_task import query_chatgpt
    from app.tasks.sum_task import sum_numbers
    from app.tasks.weather_task import fetch_weather

    task_map = {
        TaskName.SUM: sum_numbers,
        TaskName.CHATGPT: query_chatgpt,
        TaskName.WEATHER: fetch_weather,
    }
    return task_map.get(task_name)


@router.post(
    "/run-task",
    response_model=RunTaskResponse,
    status_code=status.HTTP_202_ACCEPTED,
    responses={
        400: {"model": ErrorResponse, "description": "Invalid request"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
    summary="Submit a task for execution",
    description="Submit a new task and receive a UUID immediately. The task runs asynchronously.",
)
async def run_task(
    request: RunTaskRequest,
    session: AsyncSession = Depends(get_session),
) -> RunTaskResponse:
    """Submit a new task for asynchronous execution.

    Returns immediately with a task UUID.
    """
    logger.info(
        "task_submission_received",
        task_name=request.task_name.value,
        parameters=request.task_parameters,
    )

    # Get the Celery task
    celery_task = get_celery_task(request.task_name)
    if not celery_task:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unknown task: {request.task_name}",
        )

    # Validate task-specific parameters
    try:
        _validate_task_parameters(request.task_name, request.task_parameters)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )

    # Create task record in database
    task = Task(
        task_name=request.task_name.value,
        task_parameters=request.task_parameters,
        status=TaskStatus.PENDING.value,
    )
    session.add(task)
    await session.commit()
    await session.refresh(task)

    # Update metrics
    tasks_submitted_counter.labels(task_name=request.task_name.value).inc()
    tasks_by_status.labels(status="pending").inc()

    # Submit to Celery (fire and forget)
    celery_task.delay(str(task.id), **request.task_parameters)

    logger.info(
        "task_submitted",
        task_uuid=str(task.id),
        task_name=request.task_name.value,
    )

    return RunTaskResponse(
        task_uuid=task.id,
        message="Task submitted successfully",
    )


def _validate_task_parameters(task_name: TaskName, parameters: dict) -> None:
    """Validate task-specific parameters.

    Args:
        task_name: The task name
        parameters: The task parameters

    Raises:
        ValueError: If parameters are invalid
    """
    from app.config import get_settings
    
    settings = get_settings()
    
    if task_name == TaskName.SUM:
        if "a" not in parameters:
            raise ValueError("Parameter 'a' is required for sum task")
        if "b" not in parameters:
            raise ValueError("Parameter 'b' is required for sum task")
        if not isinstance(parameters["a"], (int, float)):
            raise ValueError("Parameter 'a' must be a number")
        if not isinstance(parameters["b"], (int, float)):
            raise ValueError("Parameter 'b' must be a number")
        # Prevent overflow attacks
        if abs(parameters["a"]) > settings.max_number_value:
            raise ValueError(f"Parameter 'a' exceeds maximum allowed value of {settings.max_number_value}")
        if abs(parameters["b"]) > settings.max_number_value:
            raise ValueError(f"Parameter 'b' exceeds maximum allowed value of {settings.max_number_value}")
        # Check for special float values
        import math
        if math.isnan(parameters["a"]) or math.isinf(parameters["a"]):
            raise ValueError("Parameter 'a' must be a finite number")
        if math.isnan(parameters["b"]) or math.isinf(parameters["b"]):
            raise ValueError("Parameter 'b' must be a finite number")

    elif task_name == TaskName.CHATGPT:
        if "prompt" not in parameters:
            raise ValueError("Parameter 'prompt' is required for chatgpt task")
        if not isinstance(parameters["prompt"], str):
            raise ValueError("Parameter 'prompt' must be a string")
        prompt = parameters["prompt"].strip()
        if not prompt:
            raise ValueError("Parameter 'prompt' must be a non-empty string")
        if len(prompt) > settings.max_prompt_length:
            raise ValueError(f"Parameter 'prompt' exceeds maximum length of {settings.max_prompt_length} characters")
        # Validate optional parameters
        if "max_tokens" in parameters:
            if not isinstance(parameters["max_tokens"], int) or parameters["max_tokens"] <= 0:
                raise ValueError("Parameter 'max_tokens' must be a positive integer")
            if parameters["max_tokens"] > 4000:
                raise ValueError("Parameter 'max_tokens' cannot exceed 4000")
        if "temperature" in parameters:
            if not isinstance(parameters["temperature"], (int, float)):
                raise ValueError("Parameter 'temperature' must be a number")
            if not (0 <= parameters["temperature"] <= 2):
                raise ValueError("Parameter 'temperature' must be between 0 and 2")

    elif task_name == TaskName.WEATHER:
        if "city" not in parameters:
            raise ValueError("Parameter 'city' is required for weather task")
        if not isinstance(parameters["city"], str):
            raise ValueError("Parameter 'city' must be a string")
        city = parameters["city"].strip()
        if not city:
            raise ValueError("Parameter 'city' must be a non-empty string")
        if len(city) > settings.max_city_length:
            raise ValueError(f"Parameter 'city' exceeds maximum length of {settings.max_city_length} characters")
        # Basic sanitization - only allow alphanumeric, spaces, and common punctuation
        import re
        if not re.match(r"^[\w\s\-\.,\']+$", city, re.UNICODE):
            raise ValueError("Parameter 'city' contains invalid characters")
        # Validate optional units parameter
        if "units" in parameters:
            if parameters["units"] not in ("metric", "imperial", "kelvin"):
                raise ValueError("Parameter 'units' must be 'metric', 'imperial', or 'kelvin'")


@router.get(
    "/get-task-output",
    response_model=TaskOutputResponse,
    responses={
        404: {"model": ErrorResponse, "description": "Task not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"},
    },
    summary="Get task output",
    description="Retrieve the output of a completed task by its UUID.",
)
async def get_task_output(
    task_uuid: UUID = Query(..., description="The UUID of the task"),
    session: AsyncSession = Depends(get_session),
    cache: CacheService = Depends(get_cache),
) -> TaskOutputResponse:
    """Get the output of a task by UUID.

    Checks cache first, then falls back to database.
    """
    logger.debug(
        "task_output_requested",
        task_uuid=str(task_uuid),
    )

    # Try to get from cache first
    cached_output = await cache.get_task_output(str(task_uuid))
    if cached_output:
        logger.debug(
            "task_output_cache_hit",
            task_uuid=str(task_uuid),
        )
        return TaskOutputResponse(**cached_output)

    # Query database
    task = await session.get(Task, task_uuid)

    if not task:
        logger.warning(
            "task_not_found",
            task_uuid=str(task_uuid),
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task with UUID {task_uuid} not found",
        )

    response = TaskOutputResponse(
        task_uuid=task.id,
        task_name=task.task_name,
        status=task.status,
        task_output=task.result,
        error_message=task.error_message,
        created_at=task.created_at,
        completed_at=task.completed_at,
    )

    # Cache completed tasks
    if task.status in (TaskStatus.COMPLETED.value, TaskStatus.FAILED.value):
        await cache.set_task_output(str(task_uuid), response.model_dump(mode="json"))

    return response


@router.get(
    "/tasks/{task_uuid}/status",
    response_model=TaskStatusResponse,
    responses={
        404: {"model": ErrorResponse, "description": "Task not found"},
    },
    summary="Get task status",
    description="Get the current status of a task.",
)
async def get_task_status(
    task_uuid: UUID,
    session: AsyncSession = Depends(get_session),
) -> TaskStatusResponse:
    """Get the status of a task by UUID."""
    task = await session.get(Task, task_uuid)

    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task with UUID {task_uuid} not found",
        )

    return TaskStatusResponse(
        task_uuid=task.id,
        status=task.status,
    )


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Health check",
    description="Check if the service is healthy.",
)
async def health_check() -> HealthResponse:
    """Health check endpoint for load balancers."""
    return HealthResponse(
        status="healthy",
        version=__version__,
    )

