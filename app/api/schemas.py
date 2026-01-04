"""Pydantic schemas for API request/response validation."""

from datetime import datetime
from enum import Enum
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class TaskName(str, Enum):
    """Supported task names."""

    SUM = "sum"
    CHATGPT = "chatgpt"
    WEATHER = "weather"


class TaskStatus(str, Enum):
    """Task status values."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


# Request schemas
class RunTaskRequest(BaseModel):
    """Request schema for running a task."""

    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "task_name": "sum",
                    "task_parameters": {"a": 5, "b": 3},
                },
                {
                    "task_name": "chatgpt",
                    "task_parameters": {"prompt": "What is Python?"},
                },
                {
                    "task_name": "weather",
                    "task_parameters": {"city": "London"},
                },
            ]
        }
    )

    task_name: TaskName = Field(
        ...,
        description="Name of the task to run",
    )
    task_parameters: dict[str, Any] = Field(
        ...,
        description="Parameters required for the task",
    )


# Response schemas
class RunTaskResponse(BaseModel):
    """Response schema for task submission."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "task_uuid": "550e8400-e29b-41d4-a716-446655440000",
                "message": "Task submitted successfully",
            }
        }
    )

    task_uuid: UUID = Field(
        ...,
        description="Unique identifier for the submitted task",
    )
    message: str = Field(
        default="Task submitted successfully",
        description="Status message",
    )


class TaskOutputResponse(BaseModel):
    """Response schema for task output retrieval."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "task_uuid": "550e8400-e29b-41d4-a716-446655440000",
                "task_name": "sum",
                "status": "completed",
                "task_output": {"operation": "sum", "a": 5, "b": 3, "result": 8},
                "error_message": None,
                "created_at": "2026-01-04T10:30:00Z",
                "completed_at": "2026-01-04T10:30:01Z",
            }
        }
    )

    task_uuid: UUID = Field(
        ...,
        description="Task UUID",
    )
    task_name: str = Field(
        ...,
        description="Name of the task",
    )
    status: TaskStatus = Field(
        ...,
        description="Current status of the task",
    )
    task_output: dict[str, Any] | None = Field(
        default=None,
        description="Task output (available when completed)",
    )
    error_message: str | None = Field(
        default=None,
        description="Error message (available when failed)",
    )
    created_at: datetime = Field(
        ...,
        description="Task creation timestamp",
    )
    completed_at: datetime | None = Field(
        default=None,
        description="Task completion timestamp",
    )


class TaskStatusResponse(BaseModel):
    """Response schema for task status check."""

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "task_uuid": "550e8400-e29b-41d4-a716-446655440000",
                "status": "running",
            }
        }
    )

    task_uuid: UUID = Field(
        ...,
        description="Task UUID",
    )
    status: TaskStatus = Field(
        ...,
        description="Current status of the task",
    )


class HealthResponse(BaseModel):
    """Response schema for health check."""

    status: str = Field(
        default="healthy",
        description="Health status",
    )
    version: str = Field(
        ...,
        description="Application version",
    )


class ErrorResponse(BaseModel):
    """Response schema for errors."""

    detail: str = Field(
        ...,
        description="Error detail message",
    )
    error_code: str | None = Field(
        default=None,
        description="Error code for programmatic handling",
    )

