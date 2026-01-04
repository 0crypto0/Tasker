"""ChatGPT query task implementation."""

import time
from typing import Any
from uuid import UUID

import structlog
from openai import OpenAI, OpenAIError

from app.config import get_settings
from app.core.celery_app import celery_app
from app.core.metrics import external_api_duration, external_api_requests
from app.tasks.base import BaseTask, run_async

settings = get_settings()
logger = structlog.get_logger()


class ChatGPTTask(BaseTask):
    """Task to query ChatGPT API."""

    task_name = "chatgpt"

    def __init__(self) -> None:
        """Initialize ChatGPT task."""
        self.client: OpenAI | None = None

    def _get_client(self) -> OpenAI:
        """Get or create OpenAI client."""
        if self.client is None:
            if not settings.openai_api_key:
                raise ValueError("OpenAI API key is not configured")
            self.client = OpenAI(api_key=settings.openai_api_key)
        return self.client

    async def execute(
        self,
        prompt: str,
        model: str = "gpt-3.5-turbo",
        max_tokens: int = 1000,
        temperature: float = 0.7,
        **kwargs: Any,
    ) -> dict[str, Any]:
        """Execute ChatGPT query.

        Args:
            prompt: The user prompt to send to ChatGPT
            model: The model to use (default: gpt-3.5-turbo)
            max_tokens: Maximum tokens in response
            temperature: Sampling temperature

        Returns:
            Dictionary with the ChatGPT response
        """
        if not prompt or not isinstance(prompt, str):
            raise ValueError("Parameter 'prompt' must be a non-empty string")

        if len(prompt) > settings.max_prompt_length:
            raise ValueError(f"Prompt exceeds maximum length of {settings.max_prompt_length} characters")

        logger.info(
            "chatgpt_request_started",
            prompt_length=len(prompt),
            model=model,
        )

        start_time = time.time()

        try:
            client = self._get_client()

            # Make the API call synchronously (OpenAI client handles this)
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {
                        "role": "user",
                        "content": prompt,
                    }
                ],
                max_tokens=max_tokens,
                temperature=temperature,
            )

            duration = time.time() - start_time

            # Record metrics
            external_api_requests.labels(api_name="openai", status="success").inc()
            external_api_duration.labels(api_name="openai").observe(duration)

            # Extract response
            message = response.choices[0].message
            usage = response.usage

            logger.info(
                "chatgpt_request_completed",
                model=model,
                duration_seconds=duration,
                prompt_tokens=usage.prompt_tokens if usage else None,
                completion_tokens=usage.completion_tokens if usage else None,
            )

            return {
                "prompt": prompt,
                "response": message.content,
                "model": model,
                "usage": {
                    "prompt_tokens": usage.prompt_tokens if usage else 0,
                    "completion_tokens": usage.completion_tokens if usage else 0,
                    "total_tokens": usage.total_tokens if usage else 0,
                },
            }

        except OpenAIError as e:
            duration = time.time() - start_time
            external_api_requests.labels(api_name="openai", status="error").inc()
            external_api_duration.labels(api_name="openai").observe(duration)

            logger.error(
                "chatgpt_request_failed",
                error=str(e),
                duration_seconds=duration,
            )
            raise


@celery_app.task(
    name="app.tasks.chatgpt_task.query_chatgpt",
    bind=True,
    max_retries=3,
    default_retry_delay=30,
    soft_time_limit=120,
    time_limit=180,
)
def query_chatgpt(
    self,
    task_uuid: str,
    prompt: str,
    model: str = "gpt-3.5-turbo",
    max_tokens: int = 1000,
    temperature: float = 0.7,
) -> dict[str, Any]:
    """Celery task to query ChatGPT.

    Args:
        task_uuid: UUID of the task record
        prompt: The user prompt
        model: The model to use
        max_tokens: Maximum tokens in response
        temperature: Sampling temperature

    Returns:
        Task result
    """
    task = ChatGPTTask()
    try:
        return run_async(
            task.run(
                UUID(task_uuid),
                prompt=prompt,
                model=model,
                max_tokens=max_tokens,
                temperature=temperature,
            )
        )
    except Exception as exc:
        logger.error(
            "chatgpt_task_failed",
            task_uuid=task_uuid,
            error=str(exc),
        )
        # Don't retry on validation errors
        if isinstance(exc, ValueError):
            raise
        raise self.retry(exc=exc)

