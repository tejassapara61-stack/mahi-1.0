"""Centralized logging configuration for the assistant services."""

import logging
import logging.config
import os
from pathlib import Path
from typing import Optional

_LOGGING_INITIALIZED = False


def _build_log_directory() -> Path:
    base_dir = Path(__file__).resolve().parent.parent
    log_dir = base_dir / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    return log_dir


def setup_logging(default_level: str = "INFO", log_file: Optional[str] = None) -> None:
    """Configure project-wide logging.

    Parameters
    ----------
    default_level: str
        Fallback level if the LOG_LEVEL environment variable is not set.
    log_file: Optional[str]
        Optional override for the log file path. When omitted the log file is
        created in the repository level ``logs`` directory.
    """
    global _LOGGING_INITIALIZED

    if _LOGGING_INITIALIZED:
        return

    env_level = os.getenv("LOG_LEVEL", default_level).upper()

    log_path = Path(log_file) if log_file else _build_log_directory() / "assistant.log"

    logging_config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "detailed": {
                "format": "%(asctime)s | %(levelname)s | %(name)s | %(message)s",
            },
            "console": {
                "format": "%(levelname)s | %(name)s | %(message)s",
            },
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "formatter": "console",
                "level": env_level,
            },
            "file": {
                "class": "logging.handlers.RotatingFileHandler",
                "formatter": "detailed",
                "level": "DEBUG",
                "filename": str(log_path),
                "maxBytes": 5 * 1024 * 1024,
                "backupCount": 3,
                "encoding": "utf-8",
            },
        },
        "root": {
            "handlers": ["console", "file"],
            "level": env_level,
        },
    }

    logging.config.dictConfig(logging_config)
    _LOGGING_INITIALIZED = True


__all__ = ["setup_logging"]
