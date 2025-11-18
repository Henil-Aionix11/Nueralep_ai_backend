"""Healthcheck API routes."""

from typing import Any
from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db

router = APIRouter(tags=["healthcheck"])


@router.get("/health")
async def health_check() -> dict[str, str]:
    """Basic health check endpoint.

    Returns:
        Simple status message
    """
    return {"status": "healthy", "service": "psychotherapy-backend"}


@router.get("/db", response_model=dict[str, Any])
async def database_health_check(db: AsyncSession = Depends(get_db)) -> dict[str, Any]:
    """Database health check endpoint.

    Verifies database connectivity and returns status.

    Args:
        db: Database session from dependency injection

    Returns:
        Database connection status
    """
    try:
        # Execute a simple query to check database connectivity
        result = await db.execute(text("SELECT 1"))
        result.scalar()

        return {
            "status": "healthy",
            "database": "connected",
            "message": "Database connection is working",
        }
    except Exception as e:
        return {"status": "unhealthy", "database": "disconnected", "error": str(e)}
