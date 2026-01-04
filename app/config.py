"""Application configuration using pydantic-settings."""

from functools import lru_cache
from typing import Literal

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # Application
    app_name: str = "Tasker"
    app_env: Literal["development", "production", "testing"] = "development"
    debug: bool = False

    # Security
    cors_origins: list[str] = ["http://localhost:3000", "http://localhost:8000"]
    
    # Rate limiting
    rate_limit_requests: int = 100  # requests per minute
    rate_limit_enabled: bool = True

    # Database
    database_url: str = "postgresql+asyncpg://tasker:tasker@localhost:5432/tasker"
    database_pool_size: int = 5
    database_max_overflow: int = 10

    # Redis
    redis_url: str = "redis://localhost:6379/0"
    cache_ttl_seconds: int = 3600  # 1 hour

    # Celery
    celery_broker_url: str = "redis://localhost:6379/1"
    celery_result_backend: str = "redis://localhost:6379/2"

    # External APIs
    openai_api_key: str = ""
    openweather_api_key: str = ""
    
    # Input validation limits
    max_prompt_length: int = 10000
    max_city_length: int = 100
    max_number_value: float = 1e15  # Prevent overflow

    # Logging
    log_level: str = "INFO"
    log_json: bool = True

    # Metrics
    metrics_enabled: bool = True

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, v):
        """Parse CORS origins from comma-separated string or list."""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v

    @property
    def is_development(self) -> bool:
        """Check if running in development mode."""
        return self.app_env == "development"

    @property
    def is_production(self) -> bool:
        """Check if running in production mode."""
        return self.app_env == "production"

    @property
    def is_testing(self) -> bool:
        """Check if running in testing mode."""
        return self.app_env == "testing"


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()

