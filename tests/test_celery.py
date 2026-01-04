"""Celery app tests."""

from unittest.mock import MagicMock, patch

import pytest

from app.core.celery_app import (
    celery_app,
    task_failure_handler,
    task_postrun_handler,
    task_prerun_handler,
    task_success_handler,
)


class TestCeleryAppConfiguration:
    """Tests for Celery app configuration."""

    def test_celery_app_exists(self) -> None:
        """Test that celery app is created."""
        assert celery_app is not None

    def test_celery_app_name(self) -> None:
        """Test celery app name."""
        assert celery_app.main == "tasker"

    def test_celery_app_includes_tasks(self) -> None:
        """Test that celery app includes task modules."""
        includes = celery_app.conf.include
        assert "app.tasks.sum_task" in includes
        assert "app.tasks.chatgpt_task" in includes
        assert "app.tasks.weather_task" in includes

    def test_celery_app_serializer(self) -> None:
        """Test celery app uses JSON serializer."""
        assert celery_app.conf.task_serializer == "json"
        assert celery_app.conf.result_serializer == "json"

    def test_celery_app_timezone(self) -> None:
        """Test celery app uses UTC timezone."""
        assert celery_app.conf.timezone == "UTC"
        assert celery_app.conf.enable_utc is True


class TestCelerySignalHandlers:
    """Tests for Celery signal handlers."""

    def test_task_prerun_handler(self) -> None:
        """Test task prerun signal handler."""
        mock_task = MagicMock()
        mock_task.name = "test_task"

        # Should not raise
        task_prerun_handler(task_id="123", task=mock_task)

    def test_task_postrun_handler(self) -> None:
        """Test task postrun signal handler."""
        mock_task = MagicMock()
        mock_task.name = "test_task"

        # Should not raise
        task_postrun_handler(
            task_id="123",
            task=mock_task,
            retval={"result": "success"},
            state="SUCCESS",
        )

    def test_task_success_handler(self) -> None:
        """Test task success signal handler."""
        mock_sender = MagicMock()
        mock_sender.name = "test_task"

        # Should not raise
        task_success_handler(sender=mock_sender, result={"data": "test"})

    def test_task_failure_handler(self) -> None:
        """Test task failure signal handler."""
        mock_sender = MagicMock()
        mock_sender.name = "test_task"

        # Should not raise
        task_failure_handler(
            sender=mock_sender,
            task_id="123",
            exception=ValueError("Test error"),
            traceback=None,
        )

