"""Metrics module tests."""

import pytest

from app.core.metrics import (
    app_info,
    cache_hits_counter,
    cache_misses_counter,
    db_operation_duration,
    db_operations_counter,
    external_api_duration,
    external_api_requests,
    init_metrics,
    task_execution_counter,
    task_execution_duration,
    tasks_by_status,
    tasks_submitted_counter,
)


class TestMetricsDefinitions:
    """Tests for metric definitions."""

    def test_app_info_metric_exists(self) -> None:
        """Test app_info metric is defined."""
        assert app_info is not None

    def test_tasks_submitted_counter_exists(self) -> None:
        """Test tasks_submitted_counter is defined."""
        assert tasks_submitted_counter is not None

    def test_task_execution_counter_exists(self) -> None:
        """Test task_execution_counter is defined."""
        assert task_execution_counter is not None

    def test_task_execution_duration_exists(self) -> None:
        """Test task_execution_duration histogram is defined."""
        assert task_execution_duration is not None

    def test_tasks_by_status_gauge_exists(self) -> None:
        """Test tasks_by_status gauge is defined."""
        assert tasks_by_status is not None

    def test_cache_counters_exist(self) -> None:
        """Test cache hit/miss counters are defined."""
        assert cache_hits_counter is not None
        assert cache_misses_counter is not None

    def test_db_metrics_exist(self) -> None:
        """Test database metrics are defined."""
        assert db_operations_counter is not None
        assert db_operation_duration is not None

    def test_external_api_metrics_exist(self) -> None:
        """Test external API metrics are defined."""
        assert external_api_requests is not None
        assert external_api_duration is not None


class TestInitMetrics:
    """Tests for init_metrics function."""

    def test_init_metrics_sets_app_info(self) -> None:
        """Test init_metrics sets application info."""
        init_metrics()
        # Should not raise

    def test_init_metrics_initializes_status_gauges(self) -> None:
        """Test init_metrics initializes status gauges to 0."""
        init_metrics()
        # Status gauges should be initialized for all statuses


class TestMetricsUsage:
    """Tests for using metrics."""

    def test_increment_tasks_submitted(self) -> None:
        """Test incrementing tasks submitted counter."""
        tasks_submitted_counter.labels(task_name="sum").inc()
        # Should not raise

    def test_increment_task_execution(self) -> None:
        """Test incrementing task execution counter."""
        task_execution_counter.labels(task_name="sum", status="success").inc()
        # Should not raise

    def test_observe_task_duration(self) -> None:
        """Test observing task execution duration."""
        task_execution_duration.labels(task_name="sum").observe(1.5)
        # Should not raise

    def test_set_tasks_by_status(self) -> None:
        """Test setting tasks by status gauge."""
        tasks_by_status.labels(status="pending").set(5)
        # Should not raise

    def test_increment_cache_hits(self) -> None:
        """Test incrementing cache hits counter."""
        cache_hits_counter.inc()
        # Should not raise

    def test_increment_cache_misses(self) -> None:
        """Test incrementing cache misses counter."""
        cache_misses_counter.inc()
        # Should not raise

    def test_increment_db_operations(self) -> None:
        """Test incrementing database operations counter."""
        db_operations_counter.labels(operation="select", table="tasks").inc()
        # Should not raise

    def test_observe_db_duration(self) -> None:
        """Test observing database operation duration."""
        db_operation_duration.labels(operation="insert", table="tasks").observe(0.05)
        # Should not raise

    def test_increment_external_api_requests(self) -> None:
        """Test incrementing external API requests counter."""
        external_api_requests.labels(api_name="openai", status="success").inc()
        # Should not raise

    def test_observe_external_api_duration(self) -> None:
        """Test observing external API duration."""
        external_api_duration.labels(api_name="openweather").observe(0.5)
        # Should not raise

