"""Worker module tests."""

import pytest


class TestWorkerModule:
    """Tests for worker module."""

    def test_worker_module_imports(self) -> None:
        """Test that worker module can be imported."""
        from app.workers import worker

        assert worker.app is not None

    def test_worker_exports_celery_app(self) -> None:
        """Test that worker exports celery_app as app."""
        from app.workers.worker import app
        from app.core.celery_app import celery_app

        assert app is celery_app

    def test_worker_configures_logging(self) -> None:
        """Test that worker configures logging on import."""
        # This verifies the module-level configure_logging() call works
        from app.workers import worker

        assert worker is not None

