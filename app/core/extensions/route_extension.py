"""This module contains the extension for the route.

Functions:
    initialize_routes: Includes a router into the application.
"""

from fastapi import FastAPI

from app.web.api.router import api_router


def initialize_routes(app: FastAPI) -> None:
    """Initializes the routes for the application."""
    app.include_router(router=api_router, prefix="/api")
