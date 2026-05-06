from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class ESSettings(BaseSettings):
    """Elasticsearch cluster configuration settings.

    Configuration for Elasticsearch connection including cluster URLs,
    authentication, timeouts, and cluster discovery settings.

    Environment variables prefix: ES_
    """

    URL: list[str] = Field(
        default=["http://localhost:9200"],
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

    SNIFF_ON_START: bool = Field(default=True, description="Sniff on start")
    SNIFF_ON_CONNECTION_FAIL: bool = Field(
        default=True, description="Sniff on connection fail"
    )
    SNIFFER_TIMEOUT: float = Field(
        default=300, description="Sniffer timeout in seconds"
    )
    INDEX_PREFIX: str = Field(default="", description="Index prefix")

    model_config = SettingsConfigDict(env_file=".env", env_prefix="ES_", extra="ignore")
