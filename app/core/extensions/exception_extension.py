"""Exception extension module - COMPLETELY DISABLED."""

from fastapi import FastAPI


def enable_exception_extension(app: FastAPI) -> None:
    """Exception handlers completely disabled.

    This function does nothing - all exception handling uses FastAPI defaults.
    """
    # All exception handlers are disabled
    # FastAPI will use its built-in validation error responses
    pass
