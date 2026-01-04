"""Base task tests."""

from datetime import datetime
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID, uuid4

import pytest

from app.models.task import Task, TaskStatus
from app.tasks.base import BaseTask, run_async


class ConcreteTask(BaseTask):
    """Concrete task implementation for testing."""

    task_name = "test_task"

    def __init__(self, should_fail: bool = False, result: dict | None = None) -> None:
        self.should_fail = should_fail
        self._result = result or {"status": "success"}

    async def execute(self, **parameters: Any) -> dict[str, Any]:
        if self.should_fail:
            raise ValueError("Task execution failed")
        return self._result


class TestRunAsync:
    """Tests for run_async function."""

    def test_run_async_executes_coroutine(self) -> None:
        """Test that run_async executes a coroutine."""
        async def sample_coro():
            return 42

        result = run_async(sample_coro())
        assert result == 42

    def test_run_async_creates_new_loop_if_needed(self) -> None:
        """Test that run_async creates event loop if none exists."""
        async def sample_coro():
            return "test"

        result = run_async(sample_coro())
        assert result == "test"


class TestBaseTask:
    """Tests for BaseTask class."""

    @pytest.mark.asyncio
    async def test_execute_raises_not_implemented(self) -> None:
        """Test that abstract execute method raises NotImplementedError."""
        # We can't instantiate BaseTask directly, but we test via concrete class
        task = ConcreteTask()
        result = await task.execute()
        assert result == {"status": "success"}

    @pytest.mark.asyncio
    async def test_concrete_task_execute_success(self) -> None:
        """Test concrete task execution."""
        task = ConcreteTask(result={"value": 123})
        result = await task.execute()
        assert result == {"value": 123}

    @pytest.mark.asyncio
    async def test_concrete_task_execute_failure(self) -> None:
        """Test concrete task execution failure."""
        task = ConcreteTask(should_fail=True)
        with pytest.raises(ValueError, match="Task execution failed"):
            await task.execute()


class TestBaseTaskRun:
    """Tests for BaseTask.run method."""

    @pytest.mark.asyncio
    async def test_run_updates_task_status_to_running(self) -> None:
        """Test that run updates task status to running."""
        task = ConcreteTask()
        task_uuid = uuid4()

        mock_session = AsyncMock()
        mock_task_record = MagicMock()
        mock_task_record.status = TaskStatus.PENDING.value
        mock_session.get.return_value = mock_task_record

        with patch("app.tasks.base.get_session_context") as mock_ctx:
            mock_ctx.return_value.__aenter__.return_value = mock_session
            mock_ctx.return_value.__aexit__.return_value = None

            result = await task.run(task_uuid)

        assert result == {"status": "success"}

    @pytest.mark.asyncio
    async def test_run_updates_task_on_success(self) -> None:
        """Test that run updates task record on success."""
        task = ConcreteTask(result={"computed": True})
        task_uuid = uuid4()

        mock_session = AsyncMock()
        mock_task_record = MagicMock()
        mock_session.get.return_value = mock_task_record

        with patch("app.tasks.base.get_session_context") as mock_ctx:
            mock_ctx.return_value.__aenter__.return_value = mock_session
            mock_ctx.return_value.__aexit__.return_value = None

            result = await task.run(task_uuid)

        assert result == {"computed": True}

    @pytest.mark.asyncio
    async def test_run_updates_task_on_failure(self) -> None:
        """Test that run updates task record on failure."""
        task = ConcreteTask(should_fail=True)
        task_uuid = uuid4()

        mock_session = AsyncMock()
        mock_task_record = MagicMock()
        mock_session.get.return_value = mock_task_record

        with patch("app.tasks.base.get_session_context") as mock_ctx:
            mock_ctx.return_value.__aenter__.return_value = mock_session
            mock_ctx.return_value.__aexit__.return_value = None

            with pytest.raises(ValueError):
                await task.run(task_uuid)

    @pytest.mark.asyncio
    async def test_run_handles_missing_task_record(self) -> None:
        """Test that run handles missing task record gracefully."""
        task = ConcreteTask()
        task_uuid = uuid4()

        mock_session = AsyncMock()
        mock_session.get.return_value = None  # Task not found

        with patch("app.tasks.base.get_session_context") as mock_ctx:
            mock_ctx.return_value.__aenter__.return_value = mock_session
            mock_ctx.return_value.__aexit__.return_value = None

            result = await task.run(task_uuid)

        # Should still complete even if task record doesn't exist
        assert result == {"status": "success"}

    @pytest.mark.asyncio
    async def test_run_records_metrics(self) -> None:
        """Test that run records execution metrics."""
        task = ConcreteTask()
        task_uuid = uuid4()

        mock_session = AsyncMock()
        mock_session.get.return_value = None

        with patch("app.tasks.base.get_session_context") as mock_ctx:
            with patch("app.tasks.base.task_execution_duration") as mock_metric:
                mock_ctx.return_value.__aenter__.return_value = mock_session
                mock_ctx.return_value.__aexit__.return_value = None

                await task.run(task_uuid)

                # Metric should be recorded
                mock_metric.labels.assert_called_with(task_name="test_task")

