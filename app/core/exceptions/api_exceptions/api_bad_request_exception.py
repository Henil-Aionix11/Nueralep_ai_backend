"""This module defines the ApiBadRequestError class.

Classes:
    ApiBadRequestError: Exception raised for bad requests.
"""

from typing import Any

from fastapi import status

from app.core.exceptions.api_exceptions.base_api_exception import BaseApiError


class ApiBadRequestError(BaseApiError):
    """Exception raised for bad requests.

    Attributes:
        error (Any): The error type/code of the exception.
        message (str): The message of the exception.
    """

    def __init__(self, error: Any, message: str) -> None:
        super().__init__(error, message, status.HTTP_400_BAD_REQUEST)
