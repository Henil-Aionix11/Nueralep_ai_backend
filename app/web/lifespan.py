"""Lifespan management module for FastAPI application.

This module handles database connection setup and cleanup during application startup and shutdown.
It provides connection pooling and proper resource management for database interactions.
"""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.web.settings import settings


@asynccontextmanager
async def lifespan_setup(app: FastAPI) -> AsyncGenerator[None]:
    """Initialize database connections and cleanup on shutdown.

    Args:
        app (FastAPI): The FastAPI application instance

    Yields:
        None

    Raises:
        SQLAlchemyError: If database connection or table creation fails
    """
    # Create engine with proper configuration
    engine: AsyncEngine = create_async_engine(
        settings.postgres_database_url,
        pool_size=20,
        max_overflow=10,
        pool_recycle=3600,
        echo=settings.postgres_database_echo,
        connect_args={
            "server_settings": {"application_name": settings.application_name},
        },
    )

    # Create session factory with explicit type
    session_factory: async_sessionmaker[AsyncSession] = async_sessionmaker(
        bind=engine,
        autocommit=False,
        autoflush=False,
        expire_on_commit=False,
        class_=AsyncSession,
    )

    # Store in app state
    app.state.db_engine = engine
    app.state.db_session_factory = session_factory

    yield

    # Cleanup
    await engine.dispose()
