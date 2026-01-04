"""API endpoint tests."""

from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.task import Task, TaskStatus


class TestHealthEndpoint:
    """Tests for health check endpoint."""

    @pytest.mark.asyncio
    async def test_health_check_returns_healthy(self, client: AsyncClient) -> None:
        """Test that health check returns healthy status."""
        response = await client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "version" in data


class TestRunTaskEndpoint:
    """Tests for POST /run-task endpoint."""

    @pytest.mark.asyncio
    async def test_run_sum_task_success(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
    ) -> None:
        """Test successful sum task submission."""
        with patch("app.api.routes.get_celery_task") as mock_get_task:
            mock_task = MagicMock()
            mock_task.delay = MagicMock()
            mock_get_task.return_value = mock_task

            response = await client.post(
                "/run-task",
                json={
                    "task_name": "sum",
                    "task_parameters": {"a": 5, "b": 3},
                },
            )

        assert response.status_code == 202
        data = response.json()
        assert "task_uuid" in data
        assert data["message"] == "Task submitted successfully"
        mock_task.delay.assert_called_once()

    @pytest.mark.asyncio
    async def test_run_chatgpt_task_success(
        self,
        client: AsyncClient,
    ) -> None:
        """Test successful chatgpt task submission."""
        with patch("app.api.routes.get_celery_task") as mock_get_task:
            mock_task = MagicMock()
            mock_task.delay = MagicMock()
            mock_get_task.return_value = mock_task

            response = await client.post(
                "/run-task",
                json={
                    "task_name": "chatgpt",
                    "task_parameters": {"prompt": "What is Python?"},
                },
            )

        assert response.status_code == 202
        data = response.json()
        assert "task_uuid" in data

    @pytest.mark.asyncio
    async def test_run_weather_task_success(
        self,
        client: AsyncClient,
    ) -> None:
        """Test successful weather task submission."""
        with patch("app.api.routes.get_celery_task") as mock_get_task:
            mock_task = MagicMock()
            mock_task.delay = MagicMock()
            mock_get_task.return_value = mock_task

            response = await client.post(
                "/run-task",
                json={
                    "task_name": "weather",
                    "task_parameters": {"city": "London"},
                },
            )

        assert response.status_code == 202
        data = response.json()
        assert "task_uuid" in data

    @pytest.mark.asyncio
    async def test_run_task_invalid_task_name(
        self,
        client: AsyncClient,
    ) -> None:
        """Test task submission with invalid task name."""
        response = await client.post(
            "/run-task",
            json={
                "task_name": "invalid_task",
                "task_parameters": {},
            },
        )

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_run_sum_task_missing_parameter_a(
        self,
        client: AsyncClient,
    ) -> None:
        """Test sum task with missing parameter 'a'."""
        with patch("app.api.routes.get_celery_task") as mock_get_task:
            mock_task = MagicMock()
            mock_get_task.return_value = mock_task

            response = await client.post(
                "/run-task",
                json={
                    "task_name": "sum",
                    "task_parameters": {"b": 3},
                },
            )

        assert response.status_code == 400
        assert "Parameter 'a' is required" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_run_sum_task_missing_parameter_b(
        self,
        client: AsyncClient,
    ) -> None:
        """Test sum task with missing parameter 'b'."""
        with patch("app.api.routes.get_celery_task") as mock_get_task:
            mock_task = MagicMock()
            mock_get_task.return_value = mock_task

            response = await client.post(
                "/run-task",
                json={
                    "task_name": "sum",
                    "task_parameters": {"a": 5},
                },
            )

        assert response.status_code == 400
        assert "Parameter 'b' is required" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_run_sum_task_invalid_parameter_type(
        self,
        client: AsyncClient,
    ) -> None:
        """Test sum task with invalid parameter type."""
        with patch("app.api.routes.get_celery_task") as mock_get_task:
            mock_task = MagicMock()
            mock_get_task.return_value = mock_task

            response = await client.post(
                "/run-task",
                json={
                    "task_name": "sum",
                    "task_parameters": {"a": "not_a_number", "b": 3},
                },
            )

        assert response.status_code == 400
        assert "must be a number" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_run_sum_task_invalid_parameter_type_b(
        self,
        client: AsyncClient,
    ) -> None:
        """Test sum task with invalid parameter type for b."""
        with patch("app.api.routes.get_celery_task") as mock_get_task:
            mock_task = MagicMock()
            mock_get_task.return_value = mock_task

            response = await client.post(
                "/run-task",
                json={
                    "task_name": "sum",
                    "task_parameters": {"a": 5, "b": "not_a_number"},
                },
            )

        assert response.status_code == 400
        assert "must be a number" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_run_chatgpt_task_missing_prompt(
        self,
        client: AsyncClient,
    ) -> None:
        """Test chatgpt task with missing prompt."""
        with patch("app.api.routes.get_celery_task") as mock_get_task:
            mock_task = MagicMock()
            mock_get_task.return_value = mock_task

            response = await client.post(
                "/run-task",
                json={
                    "task_name": "chatgpt",
                    "task_parameters": {},
                },
            )

        assert response.status_code == 400
        assert "Parameter 'prompt' is required" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_run_chatgpt_task_empty_prompt(
        self,
        client: AsyncClient,
    ) -> None:
        """Test chatgpt task with empty prompt."""
        with patch("app.api.routes.get_celery_task") as mock_get_task:
            mock_task = MagicMock()
            mock_get_task.return_value = mock_task

            response = await client.post(
                "/run-task",
                json={
                    "task_name": "chatgpt",
                    "task_parameters": {"prompt": "   "},
                },
            )

        assert response.status_code == 400
        assert "must be a non-empty string" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_run_weather_task_missing_city(
        self,
        client: AsyncClient,
    ) -> None:
        """Test weather task with missing city."""
        with patch("app.api.routes.get_celery_task") as mock_get_task:
            mock_task = MagicMock()
            mock_get_task.return_value = mock_task

            response = await client.post(
                "/run-task",
                json={
                    "task_name": "weather",
                    "task_parameters": {},
                },
            )

        assert response.status_code == 400
        assert "Parameter 'city' is required" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_run_weather_task_empty_city(
        self,
        client: AsyncClient,
    ) -> None:
        """Test weather task with empty city."""
        with patch("app.api.routes.get_celery_task") as mock_get_task:
            mock_task = MagicMock()
            mock_get_task.return_value = mock_task

            response = await client.post(
                "/run-task",
                json={
                    "task_name": "weather",
                    "task_parameters": {"city": "   "},
                },
            )

        assert response.status_code == 400
        assert "must be a non-empty string" in response.json()["detail"]


class TestGetTaskOutputEndpoint:
    """Tests for GET /get-task-output endpoint."""

    @pytest.mark.asyncio
    async def test_get_task_output_not_found(
        self,
        client: AsyncClient,
    ) -> None:
        """Test getting output for non-existent task."""
        task_uuid = str(uuid4())
        response = await client.get(f"/get-task-output?task_uuid={task_uuid}")

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_get_task_output_pending(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
    ) -> None:
        """Test getting output for pending task."""
        # Create a pending task
        task = Task(
            task_name="sum",
            task_parameters={"a": 5, "b": 3},
            status=TaskStatus.PENDING.value,
        )
        db_session.add(task)
        await db_session.commit()
        await db_session.refresh(task)

        response = await client.get(f"/get-task-output?task_uuid={task.id}")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "pending"
        assert data["task_output"] is None

    @pytest.mark.asyncio
    async def test_get_task_output_completed(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
    ) -> None:
        """Test getting output for completed task."""
        # Create a completed task
        task = Task(
            task_name="sum",
            task_parameters={"a": 5, "b": 3},
            status=TaskStatus.COMPLETED.value,
            result={"operation": "sum", "a": 5, "b": 3, "result": 8},
        )
        db_session.add(task)
        await db_session.commit()
        await db_session.refresh(task)

        response = await client.get(f"/get-task-output?task_uuid={task.id}")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "completed"
        assert data["task_output"]["result"] == 8

    @pytest.mark.asyncio
    async def test_get_task_output_completed_caches_result(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
    ) -> None:
        """Test that completed task output is cached."""
        # Create a completed task
        task = Task(
            task_name="sum",
            task_parameters={"a": 5, "b": 3},
            status=TaskStatus.COMPLETED.value,
            result={"operation": "sum", "a": 5, "b": 3, "result": 8},
        )
        db_session.add(task)
        await db_session.commit()
        await db_session.refresh(task)

        # First request should hit DB and cache
        response = await client.get(f"/get-task-output?task_uuid={task.id}")
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_get_task_output_failed(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
    ) -> None:
        """Test getting output for failed task."""
        # Create a failed task
        task = Task(
            task_name="chatgpt",
            task_parameters={"prompt": "test"},
            status=TaskStatus.FAILED.value,
            error_message="API key invalid",
        )
        db_session.add(task)
        await db_session.commit()
        await db_session.refresh(task)

        response = await client.get(f"/get-task-output?task_uuid={task.id}")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "failed"
        assert data["error_message"] == "API key invalid"

    @pytest.mark.asyncio
    async def test_get_task_output_running(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
    ) -> None:
        """Test getting output for running task."""
        task = Task(
            task_name="weather",
            task_parameters={"city": "Paris"},
            status=TaskStatus.RUNNING.value,
        )
        db_session.add(task)
        await db_session.commit()
        await db_session.refresh(task)

        response = await client.get(f"/get-task-output?task_uuid={task.id}")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "running"
        assert data["task_output"] is None

    @pytest.mark.asyncio
    async def test_get_task_output_invalid_uuid(
        self,
        client: AsyncClient,
    ) -> None:
        """Test getting output with invalid UUID format."""
        response = await client.get("/get-task-output?task_uuid=not-a-uuid")

        assert response.status_code == 422


class TestGetTaskStatusEndpoint:
    """Tests for GET /tasks/{uuid}/status endpoint."""

    @pytest.mark.asyncio
    async def test_get_task_status_success(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
    ) -> None:
        """Test getting task status."""
        task = Task(
            task_name="sum",
            task_parameters={"a": 5, "b": 3},
            status=TaskStatus.RUNNING.value,
        )
        db_session.add(task)
        await db_session.commit()
        await db_session.refresh(task)

        response = await client.get(f"/tasks/{task.id}/status")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "running"

    @pytest.mark.asyncio
    async def test_get_task_status_not_found(
        self,
        client: AsyncClient,
    ) -> None:
        """Test getting status for non-existent task."""
        task_uuid = str(uuid4())
        response = await client.get(f"/tasks/{task_uuid}/status")

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_get_task_status_pending(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
    ) -> None:
        """Test getting pending task status."""
        task = Task(
            task_name="chatgpt",
            task_parameters={"prompt": "test"},
            status=TaskStatus.PENDING.value,
        )
        db_session.add(task)
        await db_session.commit()
        await db_session.refresh(task)

        response = await client.get(f"/tasks/{task.id}/status")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "pending"

    @pytest.mark.asyncio
    async def test_get_task_status_completed(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
    ) -> None:
        """Test getting completed task status."""
        task = Task(
            task_name="weather",
            task_parameters={"city": "London"},
            status=TaskStatus.COMPLETED.value,
            result={"city": "London", "temperature": {"current": 15}},
        )
        db_session.add(task)
        await db_session.commit()
        await db_session.refresh(task)

        response = await client.get(f"/tasks/{task.id}/status")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "completed"

    @pytest.mark.asyncio
    async def test_get_task_status_failed(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
    ) -> None:
        """Test getting failed task status."""
        task = Task(
            task_name="chatgpt",
            task_parameters={"prompt": "test"},
            status=TaskStatus.FAILED.value,
            error_message="Connection timeout",
        )
        db_session.add(task)
        await db_session.commit()
        await db_session.refresh(task)

        response = await client.get(f"/tasks/{task.id}/status")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "failed"


class TestInputValidation:
    """Tests for enhanced input validation."""

    @pytest.mark.asyncio
    async def test_sum_task_rejects_negative_infinity(
        self,
        client: AsyncClient,
    ) -> None:
        """Test sum task rejects negative large values that could cause overflow."""
        with patch("app.api.routes.get_celery_task") as mock_get_task:
            mock_task = MagicMock()
            mock_get_task.return_value = mock_task

            # Note: JSON doesn't support infinity, so we test with very large negative numbers
            response = await client.post(
                "/run-task",
                json={
                    "task_name": "sum",
                    "task_parameters": {"a": -1e16, "b": 1},
                },
            )

        assert response.status_code == 400
        assert "exceeds maximum" in response.json()["detail"]

    def test_validate_sum_rejects_infinity_directly(self) -> None:
        """Test validation function rejects infinity values."""
        import math
        from app.api.routes import _validate_task_parameters
        from app.api.schemas import TaskName
        
        # Infinity is caught by the "exceeds maximum" check since inf > max_value
        with pytest.raises(ValueError) as exc_info:
            _validate_task_parameters(TaskName.SUM, {"a": math.inf, "b": 1})
        
        assert "exceeds maximum" in str(exc_info.value)

    def test_validate_sum_rejects_nan_directly(self) -> None:
        """Test validation function rejects NaN values."""
        import math
        from app.api.routes import _validate_task_parameters
        from app.api.schemas import TaskName
        
        with pytest.raises(ValueError) as exc_info:
            _validate_task_parameters(TaskName.SUM, {"a": math.nan, "b": 1})
        
        assert "finite number" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_sum_task_rejects_nan(
        self,
        client: AsyncClient,
    ) -> None:
        """Test sum task rejects NaN values (via None in JSON)."""
        with patch("app.api.routes.get_celery_task") as mock_get_task:
            mock_task = MagicMock()
            mock_get_task.return_value = mock_task

            # NaN becomes null in JSON, so we send None which fails type check
            response = await client.post(
                "/run-task",
                json={
                    "task_name": "sum",
                    "task_parameters": {"a": None, "b": 1},
                },
            )

        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_sum_task_rejects_large_numbers(
        self,
        client: AsyncClient,
    ) -> None:
        """Test sum task rejects numbers exceeding max value."""
        with patch("app.api.routes.get_celery_task") as mock_get_task:
            mock_task = MagicMock()
            mock_get_task.return_value = mock_task

            response = await client.post(
                "/run-task",
                json={
                    "task_name": "sum",
                    "task_parameters": {"a": 1e16, "b": 1},
                },
            )

        assert response.status_code == 400
        assert "exceeds maximum" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_chatgpt_task_rejects_long_prompt(
        self,
        client: AsyncClient,
    ) -> None:
        """Test chatgpt task rejects prompts exceeding max length."""
        with patch("app.api.routes.get_celery_task") as mock_get_task:
            mock_task = MagicMock()
            mock_get_task.return_value = mock_task

            response = await client.post(
                "/run-task",
                json={
                    "task_name": "chatgpt",
                    "task_parameters": {"prompt": "x" * 10001},
                },
            )

        assert response.status_code == 400
        assert "exceeds maximum length" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_chatgpt_task_validates_max_tokens(
        self,
        client: AsyncClient,
    ) -> None:
        """Test chatgpt task validates max_tokens parameter."""
        with patch("app.api.routes.get_celery_task") as mock_get_task:
            mock_task = MagicMock()
            mock_get_task.return_value = mock_task

            response = await client.post(
                "/run-task",
                json={
                    "task_name": "chatgpt",
                    "task_parameters": {"prompt": "test", "max_tokens": 5000},
                },
            )

        assert response.status_code == 400
        assert "cannot exceed 4000" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_chatgpt_task_validates_temperature(
        self,
        client: AsyncClient,
    ) -> None:
        """Test chatgpt task validates temperature parameter."""
        with patch("app.api.routes.get_celery_task") as mock_get_task:
            mock_task = MagicMock()
            mock_get_task.return_value = mock_task

            response = await client.post(
                "/run-task",
                json={
                    "task_name": "chatgpt",
                    "task_parameters": {"prompt": "test", "temperature": 3.0},
                },
            )

        assert response.status_code == 400
        assert "between 0 and 2" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_weather_task_rejects_long_city(
        self,
        client: AsyncClient,
    ) -> None:
        """Test weather task rejects city names exceeding max length."""
        with patch("app.api.routes.get_celery_task") as mock_get_task:
            mock_task = MagicMock()
            mock_get_task.return_value = mock_task

            response = await client.post(
                "/run-task",
                json={
                    "task_name": "weather",
                    "task_parameters": {"city": "x" * 101},
                },
            )

        assert response.status_code == 400
        assert "exceeds maximum length" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_weather_task_rejects_invalid_characters(
        self,
        client: AsyncClient,
    ) -> None:
        """Test weather task rejects city names with invalid characters."""
        with patch("app.api.routes.get_celery_task") as mock_get_task:
            mock_task = MagicMock()
            mock_get_task.return_value = mock_task

            response = await client.post(
                "/run-task",
                json={
                    "task_name": "weather",
                    "task_parameters": {"city": "London<script>"},
                },
            )

        assert response.status_code == 400
        assert "invalid characters" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_weather_task_validates_units(
        self,
        client: AsyncClient,
    ) -> None:
        """Test weather task validates units parameter."""
        with patch("app.api.routes.get_celery_task") as mock_get_task:
            mock_task = MagicMock()
            mock_get_task.return_value = mock_task

            response = await client.post(
                "/run-task",
                json={
                    "task_name": "weather",
                    "task_parameters": {"city": "London", "units": "invalid"},
                },
            )

        assert response.status_code == 400
        assert "'metric', 'imperial', or 'kelvin'" in response.json()["detail"]


class TestGetCeleryTask:
    """Tests for get_celery_task function."""

    def test_get_celery_task_sum(self) -> None:
        """Test getting sum task."""
        from app.api.routes import get_celery_task
        from app.api.schemas import TaskName

        task = get_celery_task(TaskName.SUM)
        assert task is not None
        assert task.name == "app.tasks.sum_task.sum_numbers"

    def test_get_celery_task_chatgpt(self) -> None:
        """Test getting chatgpt task."""
        from app.api.routes import get_celery_task
        from app.api.schemas import TaskName

        task = get_celery_task(TaskName.CHATGPT)
        assert task is not None
        assert task.name == "app.tasks.chatgpt_task.query_chatgpt"

    def test_get_celery_task_weather(self) -> None:
        """Test getting weather task."""
        from app.api.routes import get_celery_task
        from app.api.schemas import TaskName

        task = get_celery_task(TaskName.WEATHER)
        assert task is not None
        assert task.name == "app.tasks.weather_task.fetch_weather"


class TestTaskModel:
    """Tests for Task model."""

    @pytest.mark.asyncio
    async def test_task_repr(
        self,
        db_session: AsyncSession,
    ) -> None:
        """Test task string representation."""
        task = Task(
            task_name="sum",
            task_parameters={"a": 1, "b": 2},
            status=TaskStatus.PENDING.value,
        )
        db_session.add(task)
        await db_session.commit()
        await db_session.refresh(task)

        repr_str = repr(task)
        assert "Task" in repr_str
        assert "sum" in repr_str
        assert "pending" in repr_str

    @pytest.mark.asyncio
    async def test_task_to_dict(
        self,
        db_session: AsyncSession,
    ) -> None:
        """Test task to_dict method."""
        task = Task(
            task_name="weather",
            task_parameters={"city": "Tokyo"},
            status=TaskStatus.COMPLETED.value,
            result={"city": "Tokyo", "temperature": {"current": 20}},
        )
        db_session.add(task)
        await db_session.commit()
        await db_session.refresh(task)

        task_dict = task.to_dict()

        assert task_dict["task_name"] == "weather"
        assert task_dict["task_parameters"] == {"city": "Tokyo"}
        assert task_dict["status"] == "completed"
        assert task_dict["result"] == {"city": "Tokyo", "temperature": {"current": 20}}
        assert "id" in task_dict
        assert "created_at" in task_dict
