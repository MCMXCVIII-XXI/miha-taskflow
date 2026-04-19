from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class DBSettings(BaseSettings):
    """Database connection configuration settings.

    Configuration for PostgreSQL database connection including URL,
    connection pooling, and debugging options.

    Environment variables prefix: DB_
    """

    URL: str = Field(
        default="postgresql+asyncpg://user:pass@localhost:5432/taskflow",
        description="Database URL",
    )
    ECHO: bool = Field(default=False, description="Echo SQL queries")
    ECHO_POOL: bool = Field(default=False, description="Echo pool events")
    POOL_SIZE: int = Field(default=5, description="Pool size")
    MAX_OVERFLOW: int = Field(default=10, description="Max overflow")

    model_config = SettingsConfigDict(env_file=".env", env_prefix="DB_", extra="ignore")
