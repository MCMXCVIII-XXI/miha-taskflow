import os

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+asyncpg://user:pass@localhost:5432/taskflow"
    DB_HOST: str = "localhost"
    DB_PORT: int = 5432

    @property
    def async_database_url(self) -> str:
        return self.DATABASE_URL.replace("localhost", os.getenv("DB_HOST", "localhost"))

    class Config:
        env_file = "backend/.env"
