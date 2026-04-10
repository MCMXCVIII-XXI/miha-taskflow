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

import os
import sys
from pathlib import Path
from typing import Any

from loguru import logger


def setup_logging() -> None:
    """Configure application logging with console and file outputs.

    Sets up two logging handlers:
    1. Console handler with human-readable colored format for development
    2. File handler with JSON format for production environments

    Log files are automatically rotated daily and retained for 30 days.
    JSON serialization can be enabled via LOG_JSON environment variable.
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
