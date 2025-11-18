"""Request validation exception handler.

This module handles the request validation exception.

Functions:
    request_validation_exception_handler: Handles the request validation exception.
"""

from fastapi import Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.core.schema.api_schema import create_json_api_response


async def request_validation_exception_handler(
    _: Request,
    exc: RequestValidationError,
) -> JSONResponse:
    """Handles the request validation exception.

    Args:
        exc (RequestValidationError): The exception to handle.
    """
    errors = exc.errors()
    formatted_errors = []

    for error in errors:
        loc = " -> ".join([str(loc) for loc in error["loc"]])

        formatted_errors.append(
            {
                "details": {
                    "loc": loc,
                    "type": error["type"],
                    "input": error["input"],
                },
                "message": f"{error['msg']}",
            },
        )

    return create_json_api_response(
        errors=formatted_errors,
        message="Request validation error",
        status_code=status.HTTP_400_BAD_REQUEST,
    )
