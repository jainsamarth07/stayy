"""Structured logging configuration.

Configures JSON-formatted log output for production and human-readable
output for development.  Call ``setup_logging()`` once at application start.
"""

import logging
import logging.config
import sys

from app.config import settings

_LOG_FORMAT_DEV = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"

# JSON-style format string — for real structured logging use python-json-logger
_LOG_FORMAT_PROD = (
    '{"time":"%(asctime)s","level":"%(levelname)s","logger":"%(name)s","message":"%(message)s"}'
)


def setup_logging() -> None:
    """Configure root logger based on APP_ENV."""
    is_prod = settings.APP_ENV not in ("development", "test")
    level = logging.INFO if is_prod else logging.DEBUG

    config: dict = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "default": {
                "format": _LOG_FORMAT_PROD if is_prod else _LOG_FORMAT_DEV,
                "datefmt": "%Y-%m-%dT%H:%M:%S",
            },
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "formatter": "default",
                "stream": "ext://sys.stdout",
            },
        },
        "root": {
            "level": level,
            "handlers": ["console"],
        },
        # Quieten noisy libraries
        "loggers": {
            "uvicorn": {"level": "INFO"},
            "uvicorn.error": {"level": "INFO"},
            "uvicorn.access": {"level": "WARNING" if is_prod else "INFO"},
            "sqlalchemy.engine": {
                "level": "WARNING" if not settings.DATABASE_ECHO else "INFO"
            },
            "celery": {"level": "INFO"},
            "botocore": {"level": "WARNING"},
            "urllib3": {"level": "WARNING"},
        },
    }

    logging.config.dictConfig(config)

    # Ensure uncaught exceptions are logged
    def _exception_hook(exc_type, exc_value, exc_tb):  # noqa: ANN001
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_tb)
            return
        logging.getLogger("root").critical(
            "Uncaught exception", exc_info=(exc_type, exc_value, exc_tb)
        )

    sys.excepthook = _exception_hook
