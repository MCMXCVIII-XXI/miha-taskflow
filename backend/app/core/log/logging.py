import os
import sys
from pathlib import Path
from typing import Any

from loguru import logger


def setup_logging() -> None:
    """
    Configure application logging.

    - stdout: human-readable format for development
    - file: JSON format for production
    """
    # Get log path from environment or default
    log_path = Path("logs/app.log")
    log_path.parent.mkdir(parents=True, exist_ok=True)

    # Remove default handler
    logger.remove()

    # Stdout - human readable for development
    logger.add(
        sys.stdout,
        format=(
            "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
            "<level>{message}</level>"
        ),
        level="DEBUG",
        colorize=True,
    )

    # File - JSON format for production/processing
    serialize_json = os.getenv("LOG_JSON", "false").lower() == "true"

    logger.add(
        str(log_path),
        format=(
            "{time:YYYY-MM-DD HH:mm:ss.SSS} | "
            "{level: <8} | "
            "{name}:{function}:{line} - "
            "{message}"
        ),
        rotation="00:00",  # Rotate at midnight
        retention="30 days",  # Keep 30 days
        level="DEBUG",
        serialize=serialize_json,  # JSON format for production
        encoding="utf-8",
        enqueue=True,  # Thread-safe writing
    )


def get_logger(name: str | None = None) -> Any:
    """
    Get a logger instance.

    Args:
        name: Optional name for the logger

    Returns:
        Logger instance
    """
    if name:
        return logger.bind(name=name)
    return logger
