"""Custom exception class for all api-related exceptions in the project.

Attributes:
    error (Any): The error of the exception.
    message (str): The message of the exception.
    status_code (int): The status code of the exception
"""

from typing import Any

from fastapi.responses import JSONResponse

from app.core.schema.api_schema import create_json_api_response


class BaseApiError(Exception):
    """Custom exception class for all api-related exceptions in the project.

    Attributes:
        error (Any): The error type/code of the exception.
        message (str): The message of the exception.
        status_code (int): The status code of the exception
    """

    def __init__(self, error: Any, message: str, status_code: int) -> None:
        """Initializes the BaseApiError.

        Args:
            error (Any): The error type/code of the exception.
            message (str): The message of the exception.
            status_code (int): The status code of the exception
        """
        self.error = error
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)

    def __repr__(self) -> str:
        """Returns the string representation of the exception.

        Returns:
            str: The string representation of the exception.
        """
        return f"{self.__class__.__name__}(error={self.error}, message={self.message}, status_code={self.status_code})"

    def __str__(self) -> str:
        """Returns the string representation of the exception.

        Returns:
            str: The string representation of the exception.
        """
        return f"{self.__class__.__name__}: {self.message}"

    def to_dict(self) -> dict[str, Any]:
        """Returns the dictionary representation of the exception.

        Returns:
            dict: The dictionary representation of the exception.
        """
        return {
            "error": self.error,
            "message": self.message,
            "status_code": self.status_code,
        }

    def to_api_response(self) -> JSONResponse:
        """Returns the API response of the exception.

        Returns:
            JSONResponse: The API response of the exception.
        """
        return create_json_api_response(
            errors=[
                {
                    "details": self.error,
                },
            ],
            message=self.message,
            status_code=self.status_code,
        )
