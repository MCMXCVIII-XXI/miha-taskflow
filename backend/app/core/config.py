from pydantic import AnyUrl
from pydantic_settings import BaseSettings, SettingsConfigDict


class TokenSettings(BaseSettings):
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30
    model_config = SettingsConfigDict(
        env_file=".env", env_prefix="TOKEN_", extra="ignore"
    )


class DBSettings(BaseSettings):
    URL: AnyUrl
    echo: bool = False
    echo_pool: bool = False
    pool_size: int = 5
    max_overflow: int = 10
    model_config = SettingsConfigDict(env_file=".env", env_prefix="DB_", extra="ignore")


class CacheSettings(BaseSettings):
    URL: str
    connect_retry: bool = True
    retry_on_error: list[str] = ["CONNECTION_ERROR"]
    socket_timeout: float = 5.0
    socket_connect_timeout: float = 3.0
    max_connections: int = 10
    retry_on_timeout: bool = True

    model_config = SettingsConfigDict(
        env_file=".env", env_prefix="CACHE_", extra="ignore"
    )


class SecuritySettings(BaseSettings):
    ALLOWED_ORIGINS: list[str] = ["http://localhost:3000"]
    model_config = SettingsConfigDict(
        env_file=".env", env_prefix="SECURITY_", extra="ignore"
    )


token_settings = TokenSettings()
db_settings = DBSettings()
cache_settings = CacheSettings()
