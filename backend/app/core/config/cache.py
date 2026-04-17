from pydantic import AnyUrl, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class CacheSettings(BaseSettings):
    """Redis cache configuration settings.

    Configuration for Redis cache connection including URL, timeouts,
    connection limits, and retry policies.

    Environment variables prefix: CACHE_
    """

    URL: AnyUrl = Field(
        default="redis://localhost:6379/0",
        description="Cache URL",
    )
    CONNECT_RETRY: bool = Field(default=False, description="Connect retry")
    RETRY_ON_ERROR: list[str] = Field(
        default=["CONNECTION_ERROR"], description="Retry on error"
    )
    SOCKET_TIMEOUT: float = Field(default=5.0, description="Socket timeout")
    SOCKET_CONNECT_TIMEOUT: float = Field(
        default=3.0, description="Socket connect timeout"
    )
    MAX_CONNECTIONS: int = Field(default=10, description="Max connections")
    RETRY_ON_TIMEOUT: bool = Field(default=True, description="Retry on timeout")

    model_config = SettingsConfigDict(
        env_file=".env", env_prefix="CACHE_", extra="ignore"
    )
