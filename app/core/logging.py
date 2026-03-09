"""Structured logging configuration."""

import logging
import sys


def configure_logging(level: int = logging.DEBUG) -> None:
    """Configure application-wide structured logging."""

    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
    )
