"""This module contains the exception handlers for the API.

Functions:
    api_exception_handler: Handles the API exceptions.
    request_validation_exception_handler: Handles the request validation exceptions.
    unhandled_exception_handler: Handles the unhandled exceptions.
"""

from app.core.exceptions.exception_handlers.api_exception_handler import (
    api_exception_handler,
)
from app.core.exceptions.exception_handlers.request_validation_exception_handler import (
    request_validation_exception_handler,
)
from app.core.exceptions.exception_handlers.unhandled_exception_handler import (
    unhandled_exception_handler,
)


__all__ = [
    "api_exception_handler",
    "request_validation_exception_handler",
    "unhandled_exception_handler",
]
