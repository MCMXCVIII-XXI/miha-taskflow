from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class SSESettings(BaseSettings):
    """Server-Sent Events configuration settings.

    Configuration for real-time notification system including connection
    limits, heartbeat intervals, and reconnection policies.

    Environment variables prefix: SSE_
    """

    ENABLED: bool = Field(default=False, description="Enable SSE")
    HEARTBEAT_INTERVAL: int = Field(
        default=30, description="Heartbeat interval in seconds"
    )
    RECONNECT_INTERVAL: int = Field(
        default=5, description="Reconnect interval in seconds"
    )
    MAX_CONNECTIONS_PER_USER: int = Field(
        default=3, description="Max connections per user"
    )

    model_config = SettingsConfigDict(
        env_file=".env", env_prefix="SSE_", extra="ignore"
    )
