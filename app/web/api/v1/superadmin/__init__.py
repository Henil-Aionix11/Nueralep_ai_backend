"""Superadmin API module for tenant management."""

from app.web.api.v1.superadmin.auth import router as auth_router
from app.web.api.v1.superadmin.routes import router as routes_router

__all__ = ["auth_router", "routes_router"]
