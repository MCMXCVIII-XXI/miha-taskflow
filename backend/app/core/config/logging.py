from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class LoggingSettings(BaseSettings):
    """Logging configuration settings."""

    CONSOLE_ENABLED: bool = Field(default=True, description="Enable console logging")
    CONSOLE_LEVEL: str = Field(default="DEBUG", description="Console logging level")
    CONSOLE_FORMAT: str = Field(
        default=(
            "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
            "<level>{message}</level>"
        ),
        description="Console log format",
    )
    CONSOLE_COLORIZE: bool = Field(default=True, description="Colorize console logs")

    FILE_ENABLED: bool = Field(default=True, description="Enable file logging")
    FILE_LEVEL: str = Field(default="DEBUG", description="File logging level")
    FILE_PATH: str = Field(default="logs/app.log", description="Log file path")
    FILE_ROTATION: str = Field(default="00:00", description="Log rotation time")
    FILE_RETENTION: str = Field(default="30 days", description="Log retention period")
    FILE_ENCODING: str = Field(default="utf-8", description="Log encoding")
    FILE_ENQUEUE: bool = Field(default=True, description="Thread-safe file writing")
    FILE_JSON: bool = Field(default=False, description="Serialize file logs as JSON")
    FILE_FORMAT: str = Field(
        default=(
            "{time:YYYY-MM-DD HH:mm:ss.SSS} | "
            "{level: <8} | "
            "{name}:{function}:{line} - "
            "{message}"
        ),
        description="Text file log format",
    )

    model_config = SettingsConfigDict(
        env_file=".env", env_prefix="LOG_", extra="ignore"
    )
