"""
Centralized logging configuration for the Kafka Order Processing System.
Provides consistent logging setup across all components.
"""

import logging
import sys
from typing import Optional


def setup_logger(
    name: str = __name__,
    level: int = logging.INFO,
    format_string: Optional[str] = None,
    stream: Optional[object] = None
) -> logging.Logger:
    """
    Set up and return a configured logger.

    Args:
        name: Logger name (usually __name__)
        level: Logging level (e.g., logging.DEBUG, logging.INFO)
        format_string: Custom format string, uses default if None
        stream: Output stream, uses sys.stdout if None

    Returns:
        Configured logger instance
    """
    if format_string is None:
        format_string = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    if stream is None:
        stream = sys.stdout

    # Create logger
    logger = logging.getLogger(name)

    # Avoid duplicate handlers if logger already configured
    if logger.handlers:
        return logger

    # Set level
    logger.setLevel(level)

    # Create console handler
    console_handler = logging.StreamHandler(stream)
    console_handler.setLevel(level)

    # Create formatter
    formatter = logging.Formatter(format_string)
    console_handler.setFormatter(formatter)

    # Add handler to logger
    logger.addHandler(console_handler)

    return logger


def get_logger(name: str = __name__) -> logging.Logger:
    """
    Get a logger with default configuration.

    Args:
        name: Logger name (usually __name__)

    Returns:
        Configured logger instance
    """
    return setup_logger(name)


# Default logger for this module
logger = get_logger(__name__)