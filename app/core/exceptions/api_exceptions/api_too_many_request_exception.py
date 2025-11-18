"""This module contains the ApiTooManyRequestsError class which is a custom exception class for too many requests.

Classes:
    ApiTooManyRequestsError: Exception raised when too many requests are made.
"""

from typing import Any

from fastapi import status

from app.core.exceptions.api_exceptions.base_api_exception import BaseApiError


class ApiTooManyRequestsError(BaseApiError):
    """Exception raised when too many requests are made.

    Attributes:
        error (Any): The error type/code of the exception.
        message (str): The message of the exception.
    """

    def __init__(self, error: Any, message: str) -> None:
        super().__init__(error, message, status.HTTP_429_TOO_MANY_REQUESTS)
