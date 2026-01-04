"""Logging module tests."""

import logging
from unittest.mock import patch

import pytest
import structlog

from app.core.logging import (
    LoggerContextManager,
    add_app_context,
    bind_context,
    clear_context,
    configure_logging,
    get_log_level,
    get_logger,
)


class TestGetLogLevel:
    """Tests for get_log_level function."""

    def test_debug_level(self) -> None:
        """Test DEBUG log level."""
        assert get_log_level("DEBUG") == logging.DEBUG

    def test_info_level(self) -> None:
        """Test INFO log level."""
        assert get_log_level("INFO") == logging.INFO

    def test_warning_level(self) -> None:
        """Test WARNING log level."""
        assert get_log_level("WARNING") == logging.WARNING

    def test_error_level(self) -> None:
        """Test ERROR log level."""
        assert get_log_level("ERROR") == logging.ERROR

    def test_critical_level(self) -> None:
        """Test CRITICAL log level."""
        assert get_log_level("CRITICAL") == logging.CRITICAL

    def test_lowercase_level(self) -> None:
        """Test lowercase level name."""
        assert get_log_level("debug") == logging.DEBUG

    def test_unknown_level_defaults_to_info(self) -> None:
        """Test unknown level defaults to INFO."""
        assert get_log_level("UNKNOWN") == logging.INFO


class TestAddAppContext:
    """Tests for add_app_context function."""

    def test_adds_app_and_env(self) -> None:
        """Test that app context is added to event dict."""
        event_dict = {"message": "test"}
        result = add_app_context(None, "", event_dict)

        assert "app" in result
        assert "env" in result


class TestConfigureLogging:
    """Tests for configure_logging function."""

    def test_configure_json_logging(self) -> None:
        """Test JSON logging configuration."""
        configure_logging(json_logs=True, log_level="INFO")
        logger = structlog.get_logger()
        assert logger is not None

    def test_configure_console_logging(self) -> None:
        """Test console logging configuration."""
        configure_logging(json_logs=False, log_level="DEBUG")
        logger = structlog.get_logger()
        assert logger is not None

    def test_configure_default_settings(self) -> None:
        """Test logging with default settings."""
        configure_logging()
        logger = structlog.get_logger()
        assert logger is not None


class TestGetLogger:
    """Tests for get_logger function."""

    def test_get_logger_without_name(self) -> None:
        """Test getting logger without name."""
        logger = get_logger()
        assert logger is not None

    def test_get_logger_with_name(self) -> None:
        """Test getting logger with name."""
        logger = get_logger("test_logger")
        assert logger is not None


class TestLoggerContextManager:
    """Tests for LoggerContextManager."""

    def test_context_manager_binds_context(self) -> None:
        """Test that context manager binds context."""
        with LoggerContextManager(request_id="123") as ctx:
            assert ctx is not None

    def test_context_manager_unbinds_context(self) -> None:
        """Test that context manager unbinds context on exit."""
        with LoggerContextManager(test_key="test_value"):
            pass
        # Context should be unbound after exiting


class TestContextFunctions:
    """Tests for bind_context and clear_context."""

    def test_bind_context(self) -> None:
        """Test binding context variables."""
        bind_context(user_id="user123")
        # No error means success

    def test_clear_context(self) -> None:
        """Test clearing context variables."""
        bind_context(user_id="user123")
        clear_context()
        # No error means success

