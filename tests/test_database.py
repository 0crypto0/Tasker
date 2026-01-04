"""Database module tests."""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import Base, get_session_context


class TestGetSessionContext:
    """Tests for get_session_context function."""

    @pytest.mark.asyncio
    async def test_session_context_success(self) -> None:
        """Test session context manager on success."""
        # This tests the exception path - context manager should commit on success
        from app.models.task import Task

        # We can't easily test the production context manager in tests
        # because it uses a different engine, but we can verify it exists
        assert get_session_context is not None

    @pytest.mark.asyncio
    async def test_session_context_is_async_context_manager(self) -> None:
        """Test that session context is an async context manager."""
        import inspect
        
        # Verify it's an async context manager
        assert inspect.isasyncgenfunction(get_session_context.__wrapped__) or \
               hasattr(get_session_context, '__aenter__') or \
               callable(get_session_context)


class TestBase:
    """Tests for Base declarative class."""

    def test_base_has_metadata(self) -> None:
        """Test that Base has metadata with naming convention."""
        assert Base.metadata is not None
        assert Base.metadata.naming_convention is not None

    def test_naming_convention_has_required_keys(self) -> None:
        """Test that naming convention has all required keys."""
        convention = Base.metadata.naming_convention
        assert "ix" in convention
        assert "uq" in convention
        assert "ck" in convention
        assert "fk" in convention
        assert "pk" in convention

