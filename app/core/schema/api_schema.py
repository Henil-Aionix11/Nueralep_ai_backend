"""This module contains the API schema definitions.

Classes:
    ApiResponseResult: Represents the result of an API response.
    ApiResponseError: Represents an error in an API response.
    ApiResponse: Represents a generic API response.

Functions:
    create_json_api_response: Creates a JSON API response.
"""

from typing import Any, Generic, TypeVar

from fastapi import status
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from pydantic import BaseModel


# Create a type variable for the generic type
T = TypeVar("T")


class ApiResponseResult(BaseModel, Generic[T]):
    """Represents the result of an API response.

    Attributes:
        data (T): The data of the response.
        metadata (dict[str, Any] | None): The metadata of the response.
    """

    data: T
    metadata: dict[str, Any] | None = None


class ApiResponseError(BaseModel):
    """Represents an error in an API response.

    Attributes:
        code (str | None): The error code.
        message (str | None): The error message.
        details (dict[str, Any] | str | None): The details of the error.
    """

    code: str | None = None
    message: str | None = None
    details: dict[str, Any] | str | None = None


class ApiResponse(BaseModel, Generic[T]):
    """Represents a generic API response.

    Attributes:
        status (int): The status code of the response.
        message (str | None): The message of the response.
        result (ApiResponseResult[T] | None): The result of the response.
        errors (list[ApiResponseError] | None): The errors of the response.
    """

    status: int
    message: str | None = None
    result: ApiResponseResult[T] | None = None
    errors: list[ApiResponseError] | None = None


def create_json_api_response(
    data: T | None = None,
    metadata: dict[str, Any] | None = None,
    status_code: int = status.HTTP_200_OK,
    message: str | None = None,
    errors: list[dict[str, Any]] | None = None,
) -> JSONResponse:
    """Creates a JSON API response.

    Arguments:
        data (T | None): The data of the response.
        metadata (dict[str, Any] | None): The metadata of the response.
        status_code (int): The status code of the response.
        message (str | None): The message of the response.
        errors (list[dict[str, Any]] | None): The errors of the response.

    Returns:
        JSONResponse: The FastAPI JSON response.
    """
    response = None

    if errors:
        response = ApiResponse(
            status=status_code,
            message=message,
            errors=[ApiResponseError(**error) for error in errors] if errors else None,
        )
    else:
        response = ApiResponse(
            status=status_code,
            message=message,
            result=ApiResponseResult(data=data, metadata=metadata)
            if data is not None
            else None,
        )

    json_compatible_item_data = jsonable_encoder(
        response.model_dump() if response else None,
    )
    return JSONResponse(content=json_compatible_item_data, status_code=status_code)
