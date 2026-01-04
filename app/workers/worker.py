"""Celery worker entry point."""

from app.core.celery_app import celery_app
from app.core.logging import configure_logging

# Configure logging for workers
configure_logging()

# Export celery app for the worker command
# Run with: celery -A app.workers.worker worker --loglevel=info
app = celery_app

if __name__ == "__main__":
    celery_app.start()

