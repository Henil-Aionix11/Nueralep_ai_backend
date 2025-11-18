"""This module contains the LogLevel enum.

This enum represents the possible log levels.

Attributes:
    LogLevel {class} -- LogLevel enum class.
"""

from app.core.enums.base_enum import BaseEnum


class ApplicationLogLevel(BaseEnum):
    """Possible log levels.

    Attributes:
        NOTSET {str} -- Not set log level.
        DEBUG {str} -- Debug log level.
        INFO {str} -- Info log level.
        WARNING {str} -- Warning log level.
        ERROR {str} -- Error log level.
        FATAL {str} -- Fatal log level
    """

    NOTSET = "NOTSET"
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    FATAL = "FATAL"
