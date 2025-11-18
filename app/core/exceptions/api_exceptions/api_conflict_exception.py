"""This module contains the ApiConflictError class which is a subclass of BaseApiError.

Classes:
    ApiConflictError: Exception raised for conflicts.
"""

from typing import Any

from fastapi import status

from app.core.exceptions.api_exceptions.base_api_exception import BaseApiError


class ApiConflictError(BaseApiError):
    """Exception raised for conflicts.

    Attributes:
        error (Any): The error type/code of the exception.
        message (str): The message of the exception.
    """

    def __init__(self, error: Any, message: str) -> None:
        super().__init__(error, message, status.HTTP_409_CONFLICT)
