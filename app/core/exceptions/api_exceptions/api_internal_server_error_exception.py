"""This module contains the definition of the ApiInternalServerError class.

Classes:
    ApiInternalServerError: Exception raised for internal server errors.
"""

from typing import Any

from fastapi import status

from app.core.exceptions.api_exceptions.base_api_exception import BaseApiError


class ApiInternalServerError(BaseApiError):
    """Exception raised for internal server errors.

    Attributes:
        error (Any): The error type/code of the exception.
        message (str): The message of the exception.
    """

    def __init__(self, error: Any, message: str) -> None:
        super().__init__(error, message, status.HTTP_500_INTERNAL_SERVER_ERROR)
