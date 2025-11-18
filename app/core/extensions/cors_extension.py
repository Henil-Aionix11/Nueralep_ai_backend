"""CORS extension module.

Functions:
    enable_cors_extension: Adds CORS extension to the application.

"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.web.settings import settings


def enable_cors_extension(app: FastAPI) -> None:
    """Adds CORS extension to the application.

    :param app: FastAPI application.
    """
    # Extract CORS settings from the application settings.
    origins = settings.cors_allow_origins_list
    methods = settings.cors_allow_methods_list
    headers = settings.cors_allow_headers_list

    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=methods,
        allow_headers=headers,
    )
