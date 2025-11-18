"""Database configuration and session management."""

from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.ext.declarative import declarative_base
from fastapi import Request

# Create Base class for models
Base = declarative_base()


async def get_db(request: Request) -> AsyncGenerator[AsyncSession, None]:
    """Get database session from app state.

    Args:
        request: FastAPI request object

    Yields:
        Database session
    """
    session_factory = request.app.state.db_session_factory
    async with session_factory() as session:
        try:
            yield session
        finally:
            await session.close()


# Type alias for dependency injection
DbSession = AsyncSession
