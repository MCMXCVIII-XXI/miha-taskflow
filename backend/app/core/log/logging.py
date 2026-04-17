"""Application logging configuration and utilities.

This module provides centralized logging configuration for the TaskFlow application
using Loguru. It sets up both console and file logging with appropriate formatting
for development and production environments.

The logging system supports:
- Console output with colored formatting for development
- File output with JSON formatting for production
- Automatic log rotation and retention
- Structured logging with context binding
"""

import sys
from pathlib import Path
from typing import Any

from loguru import logger

from app.core.config import logging_settings


def setup_logging() -> None:
    """Configure application logging with console and file outputs.

    Sets up two logging handlers:
    1. Console handler with human-readable colored format for development
    2. File handler with JSON format for production environments

    Log files are automatically rotated daily and retained for 30 days.
    JSON serialization can be enabled via LOG_JSON environment variable.
    """
    # Get log path from environment or default
    log_path = Path(logging_settings.FILE_PATH)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    # Remove default handler
    logger.remove()

    # Stdout - human readable for development
    if logging_settings.CONSOLE_ENABLED:
        logger.add(
            sys.stdout,
            format=logging_settings.CONSOLE_FORMAT,
            level=logging_settings.CONSOLE_LEVEL,
            colorize=logging_settings.CONSOLE_COLORIZE,
        )

    if logging_settings.FILE_ENABLED:
        logger.add(
            str(log_path),
            format=logging_settings.FILE_FORMAT,
            rotation=logging_settings.FILE_ROTATION,
            retention=logging_settings.FILE_RETENTION,
            level=logging_settings.FILE_LEVEL,
            serialize=logging_settings.FILE_JSON,
            encoding=logging_settings.FILE_ENCODING,
            enqueue=logging_settings.FILE_ENQUEUE,
        )


def get_logger(name: str | None = None) -> Any:
    """Get a logger instance with optional name binding.

    Creates a logger instance that can be bound to a specific name
    for contextual logging. This helps identify the source of log
    messages in large applications.

    Args:
        name (str, optional): Name to bind to the logger instance

    Returns:
        Logger: Configured logger instance

    Example:
        logger = get_logger(__name__)
        logger.info("This is a log message")
    """
    if name:
        return logger.bind(name=name)
    return logger
