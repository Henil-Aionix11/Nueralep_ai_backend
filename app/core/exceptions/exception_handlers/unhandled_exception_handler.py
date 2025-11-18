"""The unhandled exception handler.

Attributes:
    unhandled_exception_handler (function): The unhandled exception handler.
"""

from fastapi import Request, status
from fastapi.responses import JSONResponse

from app.core.schema.api_schema import create_json_api_response


async def unhandled_exception_handler(_: Request, exc: Exception) -> JSONResponse:
    """Handles the unhandled exceptions.

    Args:
        exc (Exception): The exception to handle.
    """
    return create_json_api_response(
        errors=[
            {
                "details": str(exc),
            },
        ],
        message="Internal server error",
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
    )
