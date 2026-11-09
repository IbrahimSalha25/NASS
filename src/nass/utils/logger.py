"""
Central logging configuration for the NASS application.
"""

from __future__ import annotations

import logging
import sys

LOGGER_NAME = "nass"


def setup_logger(level: int = logging.INFO) -> logging.Logger:
    """Configure and return the root NASS application logger."""
    app_logger = logging.getLogger(LOGGER_NAME)
    if not app_logger.handlers:
        app_logger.setLevel(level)
        formatter = logging.Formatter(
            fmt="[%(asctime)s] [%(levelname)s] [%(name)s]: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(formatter)
        app_logger.addHandler(handler)
        app_logger.propagate = False
    return app_logger


logger = setup_logger()
