"""Production logging configuration for APEX Vision AI."""

from __future__ import annotations

import logging
import os
from logging.config import dictConfig


def configure_logging() -> None:
    """Configure consistent, process-wide application logging."""
    level = os.getenv("APEX_LOG_LEVEL", "INFO").upper()
    if level not in {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}:
        level = "INFO"

    dictConfig(
        {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "standard": {
                    "format": "%(asctime)s %(levelname)s %(name)s %(message)s",
                },
            },
            "handlers": {
                "console": {
                    "class": "logging.StreamHandler",
                    "formatter": "standard",
                    "stream": "ext://sys.stdout",
                }
            },
            "root": {"level": level, "handlers": ["console"]},
        }
    )


logger = logging.getLogger("apex")
