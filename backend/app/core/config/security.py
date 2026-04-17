from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class SecuritySettings(BaseSettings):
    """Security configuration settings.

    Configuration for security-related settings including CORS origins
    and other security policies.

    Environment variables prefix: SECURITY_
    """

    ALLOWED_ORIGINS: list[str] = Field(
        default=[],
        description="Allowed origins",
    )

    model_config = SettingsConfigDict(
        env_file=".env", env_prefix="SECURITY_", extra="ignore"
    )
