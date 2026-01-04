"""Pytest configuration and fixtures."""

import asyncio
from collections.abc import AsyncGenerator, Generator
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from httpx import ASGITransport, AsyncClient
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.config import Settings, get_settings
from app.core.cache import CacheService, cache_service
from app.core.database import Base, get_session
from app.main import app


# Test settings
def get_test_settings() -> Settings:
    """Get test settings."""
    return Settings(
        app_env="testing",
        database_url="sqlite+aiosqlite:///:memory:",
        redis_url="redis://localhost:6379/15",
        celery_broker_url="redis://localhost:6379/14",
        celery_result_backend="redis://localhost:6379/13",
        openai_api_key="test-key",
        openweather_api_key="test-key",
        log_json=False,
        log_level="DEBUG",
        cors_origins=["http://localhost:3000"],
        rate_limit_enabled=False,
        max_prompt_length=10000,
        max_city_length=100,
        max_number_value=1e15,
    )


# Override settings
app.dependency_overrides[get_settings] = get_test_settings


# Async engine for testing
test_engine = create_async_engine(
    "sqlite+aiosqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
    echo=False,
)

TestAsyncSessionLocal = async_sessionmaker(
    test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create an instance of the default event loop for each test case."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="function")
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Create a fresh database session for each test."""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with TestAsyncSessionLocal() as session:
        yield session

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture(scope="function")
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Create a test client with database override."""

    async def override_get_session() -> AsyncGenerator[AsyncSession, None]:
        yield db_session

    app.dependency_overrides[get_session] = override_get_session

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as ac:
        yield ac

    app.dependency_overrides.pop(get_session, None)


@pytest.fixture
def sync_client() -> Generator[TestClient, None, None]:
    """Create a synchronous test client."""
    with TestClient(app) as client:
        yield client


@pytest.fixture
def mock_cache() -> Generator[MagicMock, None, None]:
    """Create a mock cache service."""
    mock = MagicMock(spec=CacheService)
    mock.get = AsyncMock(return_value=None)
    mock.set = AsyncMock(return_value=True)
    mock.delete = AsyncMock(return_value=True)
    mock.get_task_output = AsyncMock(return_value=None)
    mock.set_task_output = AsyncMock(return_value=True)

    with patch.object(cache_service, "get", mock.get):
        with patch.object(cache_service, "set", mock.set):
            with patch.object(cache_service, "delete", mock.delete):
                with patch.object(cache_service, "get_task_output", mock.get_task_output):
                    with patch.object(cache_service, "set_task_output", mock.set_task_output):
                        yield mock


@pytest.fixture
def mock_celery_task() -> Generator[MagicMock, None, None]:
    """Create a mock Celery task."""
    mock = MagicMock()
    mock.delay = MagicMock(return_value=MagicMock(id=str(uuid4())))
    yield mock


@pytest.fixture
def sample_task_data() -> dict[str, Any]:
    """Sample task data for testing."""
    return {
        "sum": {
            "task_name": "sum",
            "task_parameters": {"a": 5, "b": 3},
        },
        "chatgpt": {
            "task_name": "chatgpt",
            "task_parameters": {"prompt": "What is Python?"},
        },
        "weather": {
            "task_name": "weather",
            "task_parameters": {"city": "London"},
        },
    }

