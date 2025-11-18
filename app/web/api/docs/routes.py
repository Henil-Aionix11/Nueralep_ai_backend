"""This module contains the views for the documentation endpoints.

Functions:
    swagger_ui_html: Returns the Swagger UI documentation interface.
    swagger_ui_redirect: Handles the OAuth2 redirect for the Swagger UI interface.
    redoc_html: Returns the ReDoc documentation interface.
"""

import secrets

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.openapi.docs import (
    get_redoc_html,
    get_swagger_ui_html,
    get_swagger_ui_oauth2_redirect_html,
)
from fastapi.responses import HTMLResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials

from app.web.settings import settings


router = APIRouter()
security = HTTPBasic()


def verify_credentials(
    credentials: HTTPBasicCredentials = Depends(security),
) -> HTTPBasicCredentials:
    """Verify the HTTP Basic Auth credentials."""
    username = str(settings.swagger_username)
    password = str(settings.swagger_password)

    is_username_correct = secrets.compare_digest(
        credentials.username.encode("utf8"),
        username.encode("utf8"),
    )
    is_password_correct = secrets.compare_digest(
        credentials.password.encode("utf8"),
        password.encode("utf8"),
    )

    if not (is_username_correct and is_password_correct):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Basic"},
        )

    return credentials


@router.get("/docs", include_in_schema=False)
async def swagger_ui_html(
    request: Request,
    _: HTTPBasicCredentials = Depends(verify_credentials),
) -> HTMLResponse:
    """Serve the password-protected Swagger UI documentation interface.

    This endpoint returns an HTML page containing the Swagger UI, which provides
    an interactive interface for exploring and testing the API endpoints.

    Parameters:
        request (Request): The FastAPI request object containing the application
            context and request information.

    Returns:
        HTMLResponse: An HTML page containing the configured Swagger UI interface,
            customized with the application title and static asset URLs.
    """
    title = request.app.title
    return get_swagger_ui_html(
        openapi_url=request.app.openapi_url,
        title=f"{title} - Swagger UI",
        oauth2_redirect_url=str(request.url_for("swagger_ui_redirect")),
    )


@router.get("/swagger-redirect", include_in_schema=False)
async def swagger_ui_redirect(
    _: HTTPBasicCredentials = Depends(verify_credentials),
) -> HTMLResponse:
    """Handle OAuth2 redirect for Swagger UI authentication.

    This endpoint manages the OAuth2 authentication flow redirect
    for the Swagger UI interface.

    Returns:
        HTMLResponse: A redirect response handling the OAuth2 authentication flow.
    """
    return get_swagger_ui_oauth2_redirect_html()


@router.get("/redoc", include_in_schema=False)
async def redoc_html(
    request: Request,
    _: HTTPBasicCredentials = Depends(verify_credentials),
) -> HTMLResponse:
    """Serve the password-protected ReDoc documentation interface.

    This endpoint returns an HTML page containing the ReDoc UI, which provides
    an alternative documentation interface that is more focused on readability.

    Parameters:
        request (Request): The FastAPI request object containing the application
            context and request information.

    Returns:
        HTMLResponse: An HTML page containing the configured ReDoc interface,
            customized with the application title and static asset URLs.
    """
    title = request.app.title
    return get_redoc_html(
        openapi_url=request.app.openapi_url,
        title=f"{title} - ReDoc",
        redoc_js_url="https://cdn.jsdelivr.net/npm/redoc@next/bundles/redoc.standalone.js",
    )
