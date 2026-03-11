from pydantic import PostgresDsn
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
    URL: PostgresDsn
    echo: bool = False
    echo_pool: bool = False
    pool_size: int = 5
    max_overflow: int = 10
    model_config = SettingsConfigDict(env_file=".env", env_prefix="DB_", extra="ignore")


token_settings = TokenSettings()
db_settings = DBSettings()
