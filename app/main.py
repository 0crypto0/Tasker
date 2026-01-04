"""FastAPI application entry point."""

import uuid
from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from prometheus_fastapi_instrumentator import Instrumentator

from app import __version__
from app.api.routes import router
from app.config import get_settings
from app.core.cache import cache_service
from app.core.database import close_db, init_db
from app.core.logging import bind_context, clear_context, configure_logging
from app.core.metrics import init_metrics

settings = get_settings()

# Configure logging
configure_logging(
    json_logs=settings.log_json,
    log_level=settings.log_level,
)

logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    logger.info("application_starting", version=__version__)

    # Initialize database
    await init_db()
    logger.info("database_initialized")

    # Initialize cache
    await cache_service.connect()
    logger.info("cache_connected")

    # Initialize metrics
    init_metrics()
    logger.info("metrics_initialized")

    logger.info("application_started", version=__version__)

    yield

    # Shutdown
    logger.info("application_stopping")

    await cache_service.disconnect()
    await close_db()

    logger.info("application_stopped")


# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    description="Async Task Management Service",
    version=__version__,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# Add CORS middleware with configured origins
# In development, allow all origins; in production, use configured origins
cors_origins = ["*"] if settings.is_development else settings.cors_origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)


# Request ID middleware
@app.middleware("http")
async def add_request_id_middleware(request: Request, call_next):
    """Add request ID to all requests for correlation."""
    request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))

    # Clear and bind context for this request
    clear_context()
    bind_context(request_id=request_id)

    logger.debug(
        "request_started",
        method=request.method,
        path=request.url.path,
    )

    response = await call_next(request)

    response.headers["X-Request-ID"] = request_id

    logger.debug(
        "request_completed",
        method=request.method,
        path=request.url.path,
        status_code=response.status_code,
    )

    return response


# Exception handlers
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle validation errors with user-friendly messages."""
    # Format errors for better readability
    formatted_errors = []
    for error in exc.errors():
        loc = " -> ".join(str(x) for x in error.get("loc", []))
        msg = error.get("msg", "Invalid value")
        formatted_errors.append({
            "field": loc,
            "message": msg,
            "type": error.get("type", "value_error"),
        })
    
    logger.warning(
        "validation_error",
        errors=formatted_errors,
        path=request.url.path,
        method=request.method,
    )
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "detail": "Request validation failed. Please check your input.",
            "errors": formatted_errors,
        },
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions with consistent format."""
    logger.warning(
        "http_exception",
        status_code=exc.status_code,
        detail=exc.detail,
        path=request.url.path,
        method=request.method,
    )
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "detail": exc.detail,
        },
        headers=exc.headers,
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Handle unhandled exceptions."""
    # Log full error details for debugging
    logger.error(
        "unhandled_exception",
        error=str(exc),
        error_type=type(exc).__name__,
        path=request.url.path,
        method=request.method,
        exc_info=True,
    )
    
    # In development, include error details; in production, hide them
    if settings.is_development:
        content = {
            "detail": "Internal server error",
            "error": str(exc),
            "error_type": type(exc).__name__,
        }
    else:
        # Don't leak internal error details in production
        content = {
            "detail": "Internal server error. Please try again later.",
        }
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=content,
    )


# Include API routes
app.include_router(router, tags=["tasks"])

# Setup Prometheus metrics
if settings.metrics_enabled:
    Instrumentator().instrument(app).expose(app)

