"""Application configuration settings using Pydantic Settings.

This module defines configuration classes for all application components
using Pydantic Settings. Configuration values are loaded from environment
variables with appropriate prefixes for each component.

Configuration classes:
    TokenSettings: JWT token configuration
    DBSettings: Database connection settings
    CacheSettings: Redis cache configuration
    SecuritySettings: Security-related settings
    SSESettings: Server-Sent Events configuration
    ElasticsearchSettings: Elasticsearch cluster configuration
"""

from pydantic import AnyUrl, Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class TokenSettings(BaseSettings):
    """JWT token configuration settings.

    Configuration for JSON Web Token generation and validation including
    secret keys, algorithms, and token expiration times.

    Environment variables prefix: TOKEN_
    """

    SECRET_KEY: str = Field(description="Secret key for JWT signing")
    ALGORITHM: str = Field(default="HS256", description="JWT algorithm")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(
        default=30, description="Access token expire minutes"
    )
    REFRESH_TOKEN_EXPIRE_DAYS: int = Field(
        default=30, description="Refresh token expire days"
    )

    model_config = SettingsConfigDict(
        env_file=".env", env_prefix="TOKEN_", extra="ignore"
    )


class DBSettings(BaseSettings):
    """Database connection configuration settings.

    Configuration for PostgreSQL database connection including URL,
    connection pooling, and debugging options.

    Environment variables prefix: DB_
    """

    URL: AnyUrl = Field(
        default="http://localhost:5432",
        validate_default=True,
        description="Database URL",
    )
    ECHO: bool = Field(default=False, description="Echo SQL queries")
    ECHO_POOL: bool = Field(default=False, description="Echo pool events")
    POOL_SIZE: int = Field(default=5, description="Pool size")
    MAX_OVERFLOW: int = Field(default=10, description="Max overflow")

    model_config = SettingsConfigDict(env_file=".env", env_prefix="DB_", extra="ignore")


class CacheSettings(BaseSettings):
    """Redis cache configuration settings.

    Configuration for Redis cache connection including URL, timeouts,
    connection limits, and retry policies.

    Environment variables prefix: CACHE_
    """

    URL: AnyUrl = Field(
        default="redis://user:pass@localhost:6379/0",
        validate_default=True,
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


class SecuritySettings(BaseSettings):
    """Security configuration settings.

    Configuration for security-related settings including CORS origins
    and other security policies.

    Environment variables prefix: SECURITY_
    """

    ALLOWED_ORIGINS: list[AnyUrl] = Field(
        default=["http://localhost:3000"],
        validate_default=True,
        description="Allowed origins",
    )

    model_config = SettingsConfigDict(
        env_file=".env", env_prefix="SECURITY_", extra="ignore"
    )


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


class ElasticsearchSettings(BaseSettings):
    """Elasticsearch cluster configuration settings.

    Configuration for Elasticsearch connection including cluster URLs,
    authentication, timeouts, and cluster discovery settings.

    Environment variables prefix: ES_
    """

    URL: list[AnyUrl] = Field(
        default=["http://localhost:9200"],
        validate_default=True,
        description="Elasticsearch URL for the cluster",
    )
    USERNAME: str | None = Field(default=None, description="Elasticsearch username")
    PASSWORD: SecretStr | None = Field(
        default=None, description="Elasticsearch password"
    )
    API_KEY: SecretStr | None = Field(default=None, description="Elasticsearch API key")
    REQUEST_TIMEOUT: float = Field(
        default=30.0, description="Request timeout in seconds"
    )
    MAX_RETRIES: int = Field(
        default=3, description="Maximum number of retries on timeout"
    )
    RETRY_ON_TIMEOUT: bool = Field(default=True, description="Retry on timeout")

    # Cluster discovery
    SNIFF_ON_START: bool = Field(default=True, description="Sniff on start")
    SNIFF_ON_CONNECTION_FAIL: bool = Field(
        default=True, description="Sniff on connection fail"
    )
    SNIFFER_TIMEOUT: float = Field(
        default=300, description="Sniffer timeout in seconds"
    )
    INDEX_PREFIX: str = Field(default="", description="Index prefix")

    model_config = SettingsConfigDict(env_file=".env", env_prefix="ES_", extra="ignore")


# Global configuration instances
token_settings = TokenSettings()
db_settings = DBSettings()
cache_settings = CacheSettings()
security_settings = SecuritySettings()
sse_settings = SSESettings()
elasticsearch_settings = ElasticsearchSettings()
