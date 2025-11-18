"""FastAPI application factory module."""

from fastapi import FastAPI
from fastapi.responses import UJSONResponse

from app.core.database import get_db
from app.core.extensions.cors_extension import enable_cors_extension
from app.core.extensions.logging_extension import enable_logging_extension
from app.core.extensions.route_extension import initialize_routes
from app.core.middleware.logging_middleware import LoggingMiddleware
from app.web.lifespan import lifespan_setup


def get_app() -> FastAPI:
    """
    Create and configure FastAPI application.

    Services are initialized during lifespan startup for optimal performance.
    Database connections are pooled and managed through lifespan context.

    Returns:
        FastAPI: Configured FastAPI application instance
    """
    app = FastAPI(
        version="1.0.0",
        title="Psychotherapy Backend API",
        summary="Psychotherapy Backend API",
        description="User authentication and chat management API with AI-powered responses",
        docs_url="/api/v1/docs",
        redoc_url="/api/v1/redoc",
        openapi_url="/api/openapi.json",
        default_response_class=UJSONResponse,
        debug=True,
        lifespan=lifespan_setup,  # Database + Services initialized here
    )

    # Add CORS extension first
    enable_cors_extension(app)

    # Add logging extension
    enable_logging_extension()

    # Initialize routes
    initialize_routes(app)

    # Add logging middleware
    app.add_middleware(LoggingMiddleware)

    # Database dependency
    app.dependency_overrides[get_db] = get_db

    return app
