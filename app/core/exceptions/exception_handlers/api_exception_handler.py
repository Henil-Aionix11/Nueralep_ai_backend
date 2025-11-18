"""API exception handler.

Attributes:
    api_exception_handler (function): The API exception handler.
"""

from fastapi import Request
from fastapi.responses import JSONResponse

from app.core.exceptions.api_exceptions.base_api_exception import BaseApiError


async def api_exception_handler(
    _: Request,
    exception: BaseApiError,
) -> JSONResponse:
    """Handles the API exception.

    Args:
        exception (BaseApiError): The exception to handle.

    Returns:
        JSONResponse: The response of the exception.
    """
    return exception.to_api_response()
