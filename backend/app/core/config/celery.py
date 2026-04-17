from pydantic import AnyUrl, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class CelerySettings(BaseSettings):
    """Celery configuration settings.

    Configuration for Celery task queue including broker, result backend,
    serialization, retry policies, and worker performance settings.

    Environment variables prefix: CELERY_
    """

    BROKER_URL: AnyUrl = Field(
        description="Celery broker URL",
    )
    BACKEND_URL: AnyUrl = Field(
        description="Celery result backend URL",
    )
    TASK_SERIALIZER: str = Field(
        default="json",
        description="Task serializer (json, pickle, etc.)",
    )
    ACCEPT_CONTENT: list[str] = Field(
        default=["json"],
        description="Accepted content types",
    )
    RESULT_SERIALIZER: str = Field(
        default="json",
        description="Result serializer",
    )
    TIMEZONE: str = Field(
        default="UTC",
        description="Timezone",
    )
    ENABLE_UTC: bool = Field(
        default=True,
        description="Enable UTC",
    )
    TASK_ACKS_LATE: bool = Field(
        default=True,
        description="Acknowledge tasks after execution (reduces duplicates)",
    )
    WORKER_PREFETCH_MULTIPLIER: int = Field(
        default=1,
        description="Prefetch multiplier (1 = fair distribution)",
    )
    WORKER_CONCURRENCY: int = Field(
        default=2,
        description="Number of worker processes/threads",
    )
    WORKER_POOL: str = Field(
        default="prefork",
        description="Worker pool: prefork, eventlet, gevent, solo",
    )
    TASK_DEFAULT_RETRY_DELAY: int = Field(
        default=60,
        description="Default retry delay in seconds",
    )
    TASK_MAX_RETRIES: int = Field(
        default=3,
        description="Maximum number of retries",
    )
    RESULT_EXPIRES: int = Field(
        default=3600,
        description="Result expires in seconds (1 hour)",
    )

    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="CELERY_",
        extra="ignore",
    )
