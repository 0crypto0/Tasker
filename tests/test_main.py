"""Main app module tests."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


class TestMiddleware:
    """Tests for middleware functions."""

    @pytest.mark.asyncio
    async def test_request_id_middleware_adds_header(self) -> None:
        """Test that request ID middleware adds X-Request-ID header."""
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as client:
            response = await client.get("/health")

        assert "X-Request-ID" in response.headers

    @pytest.mark.asyncio
    async def test_request_id_middleware_uses_provided_id(self) -> None:
        """Test that middleware uses provided request ID."""
        custom_id = "custom-request-id-123"

        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as client:
            response = await client.get(
                "/health",
                headers={"X-Request-ID": custom_id},
            )

        assert response.headers["X-Request-ID"] == custom_id


class TestExceptionHandlers:
    """Tests for exception handlers."""

    @pytest.mark.asyncio
    async def test_validation_error_handler(self) -> None:
        """Test validation error handler returns 422."""
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as client:
            response = await client.post(
                "/run-task",
                json={
                    "task_name": "invalid",
                    "task_parameters": {},
                },
            )

        assert response.status_code == 422
        data = response.json()
        assert "detail" in data

    @pytest.mark.asyncio
    async def test_validation_error_on_invalid_uuid(self) -> None:
        """Test validation error on invalid UUID format."""
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as client:
            response = await client.get("/get-task-output?task_uuid=not-a-uuid")

        assert response.status_code == 422


class TestCORSMiddleware:
    """Tests for CORS middleware."""

    @pytest.mark.asyncio
    async def test_cors_headers_present(self) -> None:
        """Test that CORS headers are present in response."""
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as client:
            response = await client.options(
                "/health",
                headers={
                    "Origin": "http://localhost:3000",
                    "Access-Control-Request-Method": "GET",
                },
            )

        # CORS preflight should return 200
        assert response.status_code == 200


class TestAppConfiguration:
    """Tests for app configuration."""

    def test_app_title(self) -> None:
        """Test app title is set correctly."""
        assert app.title == "Tasker"

    def test_app_has_routes(self) -> None:
        """Test that app has expected routes."""
        routes = [route.path for route in app.routes]
        assert "/health" in routes
        assert "/run-task" in routes
        assert "/get-task-output" in routes

    def test_app_has_docs(self) -> None:
        """Test that app has documentation endpoints."""
        assert app.docs_url == "/docs"
        assert app.redoc_url == "/redoc"
        assert app.openapi_url == "/openapi.json"

