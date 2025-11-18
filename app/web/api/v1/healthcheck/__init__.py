"""Healthcheck API module for monitoring application status.

This module exports the healthcheck router which provides endpoints
for checking the health and status of the application.
"""

from app.web.api.v1.healthcheck.routes import router as healthcheck_router


__all__ = ["healthcheck_router"]
