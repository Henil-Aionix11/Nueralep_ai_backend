"""Logging extension.

This module configures and enables application-wide logging using loguru.

Classes:
    InterceptHandler: Default handler from examples in loguru documentation.

Functions:
    record_formatter: Custom formatter for log records with essential context.
    enable_logging_extension: Enables logging extension with enhanced configuration.
"""

import logging
import sys
from typing import Any

from loguru import logger

from app.core.enums.app_env_enum import AppEnv
from app.web.settings import settings


class InterceptHandler(logging.Handler):
    """Default handler from examples in loguru documentation.

    This handler intercepts all log requests and passes them to loguru.
    """

    def emit(self, record: logging.LogRecord) -> None:
        """Emit a log record by passing it to loguru.

        Args:
            record (logging.LogRecord): The log record to emit.
        """
        try:
            level: str | int = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        frame, depth = logging.currentframe(), 2
        while frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back  # type: ignore
            depth += 1

        logger.opt(depth=depth, exception=record.exc_info).log(
            level,
            record.getMessage(),
        )


def record_formatter(record: dict[str, Any]) -> str:
    """Custom formatter for log records with essential context."""
    #  CHANGE: Check for both LOCAL and DEV
    if settings.app_env in (AppEnv.LOCAL, AppEnv.DEV):
        # Keep the existing detailed format for local development
        log_format = (
            "<white>{time:YYYY-MM-DD HH:mm:ss}</white> | "
            "<yellow>{extra[app_env]}</yellow> | "
            "<level>{level: <8}</level> | "
            "<green>{extra[request_id]}</green> | "
            "<cyan>{name}</cyan>:{line} | "
            "<level>{message}</level>\n"
        )

        # Add payload and exception for local format
        if record["extra"].get("payload"):
            log_format += "<dim>Payload: {extra[payload]}</dim>\n"
        if record["exception"]:
            log_format += "<red>{exception}</red>\n"

        return log_format

    return "{message}"


def enable_logging_extension() -> None:
    """Enables and configures the logging extension."""
    # Intercept standard logging
    intercept_handler = InterceptHandler()
    logging.basicConfig(handlers=[intercept_handler], level=logging.NOTSET)

    # Intercept uvicorn and gunicorn logs
    seen = set()
    for name in [
        *logging.getLogger().manager.loggerDict.keys(),
        "gunicorn",
        "gunicorn.access",
        "gunicorn.error",
        "uvicorn",
        "uvicorn.access",
        "uvicorn.error",
    ]:
        if name not in seen:
            seen.add(name.split(".")[0])
            logging.getLogger(name).handlers = [intercept_handler]

    # Remove default logger
    logger.remove()

    # Common configuration for file handlers
    base_config = {
        "rotation": settings.log_rotation,
        "retention": f"{settings.log_retention_days} days",
        "compression": "zip",
        "format": record_formatter,
        "enqueue": True,
        "catch": True,
        "serialize": settings.app_env != AppEnv.LOCAL,
    }

    # Define handlers list starting with console handler
    handlers = [
        {
            "sink": sys.stdout,
            "level": settings.log_level,
            "colorize": settings.app_env == AppEnv.LOCAL,
            "backtrace": settings.app_env in (AppEnv.LOCAL, AppEnv.DEV),
            "diagnose": settings.app_env in (AppEnv.LOCAL, AppEnv.DEV),
            "format": record_formatter,
            "enqueue": False,
            "serialize": False,
        },
    ]

    # Add file handlers only if enabled in settings
    if settings.enable_file_logging:
        base_logs_dir = settings.logs_dir
        app_logs_dir = base_logs_dir / "application"
        error_logs_dir = base_logs_dir / "error"

        app_logs_dir.mkdir(parents=True, exist_ok=True)
        error_logs_dir.mkdir(parents=True, exist_ok=True)

        handlers.extend(
            [
                {
                    **base_config,
                    "sink": str(app_logs_dir / "app_{time:YYYY-MM-DD}.log"),
                    "level": "DEBUG" if settings.app_env == AppEnv.DEV else "INFO",
                    "filter": lambda record: record["level"].name
                    not in ("ERROR", "CRITICAL"),  # type: ignore
                },
                {
                    **base_config,
                    "sink": str(error_logs_dir / "error_{time:YYYY-MM-DD}.log"),
                    "level": "ERROR",
                    "backtrace": True,
                },
            ]
        )

    # Configure logging with handlers
    logger.configure(
        handlers=handlers,  # type: ignore
        extra={
            "service_name": settings.application_name,
            "request_id": "",
            "app_env": settings.app_env,
        },
    )
