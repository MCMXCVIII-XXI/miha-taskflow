from .cache import CacheSettings
from .celery import CelerySettings
from .db import DBSettings
from .es import ESSettings
from .logging import LoggingSettings
from .security import SecuritySettings
from .sse import SSESettings
from .token import TokenSettings

db_settings = DBSettings()
cache_settings = CacheSettings()
logging_settings = LoggingSettings()
token_settings = TokenSettings()
security_settings = SecuritySettings()
sse_settings = SSESettings()
es_settings = ESSettings()
celery_settings = CelerySettings()


__all__ = [
    "CacheSettings",
    "CelerySettings",
    "DBSettings",
    "ESSettings",
    "LoggingSettings",
    "SSESettings",
    "SecuritySettings",
    "TokenSettings",
    "cache_settings",
    "celery_settings",
    "db_settings",
    "es_settings",
    "logging_settings",
    "security_settings",
    "sse_settings",
    "token_settings",
]
