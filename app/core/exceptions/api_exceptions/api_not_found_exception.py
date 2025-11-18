"""This module contains the ApiNotFoundError class which is a custom exception class for not found requests.

Classes:
    ApiNotFoundError: Exception raised for not found requests.
"""

from typing import Any

from fastapi import status

from app.core.exceptions.api_exceptions.base_api_exception import BaseApiError


class ApiNotFoundError(BaseApiError):
    """Exception raised for not found requests.

    Attributes:
        error (Any): The error type/code of the exception.
        message (str): The message of the exception.
    """

    def __init__(self, error: Any, message: str) -> None:
        super().__init__(error, message, status.HTTP_404_NOT_FOUND)
