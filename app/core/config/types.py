"""Type definitions for configuration models used throughout the application.

This module contains Pydantic models that define the structure and validation
rules for various configuration objects used by the application's components.
"""

from pydantic import BaseModel, Field


class RouteConfig(BaseModel):
    """Configuration settings for individual API routes.

    Attributes:
        sample_rate (float): The sampling rate for logging (0.0 to 1.0).
            Defaults to 1.0 (100% sampling).
        description (str | None): Optional description of the route configuration.
            Defaults to None.
    """

    sample_rate: float = Field(default=1.0, ge=0.0, le=1.0)
    description: str | None = None


class LoggingMiddlewareConfig(BaseModel):
    """Configuration settings for the logging middleware.

    Attributes:
        default_sample_rate (float): The default sampling rate for all routes
            not specifically configured. Defaults to 1.0 (100% sampling).
        routes (dict[str, RouteConfig]): Route-specific configuration mappings.
            Keys are route paths, values are RouteConfig instances.
    """

    default_sample_rate: float = Field(default=1.0, ge=0.0, le=1.0)
    routes: dict[str, RouteConfig] = Field(default_factory=dict)


# Map config filenames to their type classes
CONFIG_TYPES = {
    "logging_middleware_config.yaml": LoggingMiddlewareConfig,
}
