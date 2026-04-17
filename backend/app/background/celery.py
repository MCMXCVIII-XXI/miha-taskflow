from celery import Celery

from app.core.config import CelerySettings
from app.core.log import logging

from .exceptions import bt_exc

logger = logging.get_logger(__name__)


class CeleryConfig:
    """
    Configuration for Celery app, using CelerySettings from app core config.

    Details:
        Uses CelerySettings to configure Celery app instance.
    """

    def __init__(self, celery_settings: CelerySettings):
        self._celery_settings = celery_settings

    def get_celery_settings(self) -> CelerySettings:
        return self._celery_settings

    def validate(self) -> None:
        """Basic validation of Celery settings."""
        settings = self._celery_settings
        if not settings.BROKER_URL:
            raise bt_exc.BackgroundBrokerUrlError(
                "Celery broker URL is not set or empty"
            )

        if not settings.BACKEND_URL:
            raise bt_exc.BackgroundBackendUrlError(
                "Celery backend URL is not set or empty"
            )

    def update_celery_app(self, celery_app: Celery) -> None:
        """Apply CelerySettings to a Celery app instance."""
        self.validate()

        celery_settings = self.get_celery_settings()

        celery_app.conf.update(
            task_serializer=celery_settings.TASK_SERIALIZER,
            accept_content=celery_settings.ACCEPT_CONTENT,
            result_serializer=celery_settings.RESULT_SERIALIZER,
            timezone=celery_settings.TIMEZONE,
            enable_utc=celery_settings.ENABLE_UTC,
            task_acks_late=celery_settings.TASK_ACKS_LATE,
            worker_prefetch_multiplier=celery_settings.WORKER_PREFETCH_MULTIPLIER,
            worker_concurrency=celery_settings.WORKER_CONCURRENCY,
            task_default_retry_delay=celery_settings.TASK_DEFAULT_RETRY_DELAY,
            task_max_retries=celery_settings.TASK_MAX_RETRIES,
            result_expires=celery_settings.RESULT_EXPIRES,
        )

        logger.info(
            "Celery app configured from CelerySettings. "
            f"broker={celery_app.conf.broker_url}, "
            f"backend={celery_app.conf.result_backend}, "
            f"worker_concurrency={celery_settings.WORKER_CONCURRENCY}, "
            f"acks_late={celery_settings.TASK_ACKS_LATE}"
        )

    def print_debug_settings(self) -> None:
        """Dump all CelerySettings (for debugging / CI)."""
        s = self._celery_settings
        logger.debug(
            f"CelerySettings: "
            f"BROKER_URL={s.BROKER_URL}, "
            f"BACKEND_URL={s.BACKEND_URL}, "
            f"TASK_ACKS_LATE={s.TASK_ACKS_LATE}, "
            f"WORKER_CONCURRENCY={s.WORKER_CONCURRENCY}, "
            f"TASK_MAX_RETRIES={s.TASK_MAX_RETRIES}, "
            f"RESULT_EXPIRES={s.RESULT_EXPIRES}"
        )


celery_config = CeleryConfig(celery_settings=CelerySettings())
celery_config.print_debug_settings()

celery_settings = celery_config.get_celery_settings()
celery_app = Celery(
    "taskflow",
    broker=celery_settings.BROKER_URL,
    backend=celery_settings.BACKEND_URL,
    worker_pool=celery_settings.WORKER_POOL,
    include=["app.background.tasks"],
)

celery_config.update_celery_app(celery_app)
