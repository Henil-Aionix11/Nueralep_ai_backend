"""API Version 1 router configuration.

This module configures the main router for API version 1, combining all v1 API endpoints
from different modules including:
- Health check endpoints
- User authentication and management endpoints

The router serves as the entry point for all v1 API routes in the application.
"""

from fastapi import APIRouter

from app.web.api.v1.healthcheck import healthcheck_router
from app.web.api.v1.user import router as user_router

from app.web.api.v1.superadmin.auth import router as superadmin_auth_router
from app.web.api.v1.superadmin.routes import router as superadmin_router

# from app.web.api.v1.chat.chat_routes import chat_router


v1_router = APIRouter()

v1_router.include_router(healthcheck_router)
v1_router.include_router(user_router)

v1_router.include_router(superadmin_auth_router)  # Superadmin login
v1_router.include_router(superadmin_router)    
