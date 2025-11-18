"""Repository for user-related database operations."""

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.models.user_model import User
from app.core.repositories.base_repository import BaseRepository
from app.core.schema.user_schema import UserCreate, UserUpdate


class UserRepository(BaseRepository[User, UserCreate, UserUpdate]):
    """Repository for User model operations."""

    def __init__(self, session: AsyncSession) -> None:
        """Initialize repository with session and model.

        Args:
            session: AsyncSession database session
        """
        super().__init__(model=User, session=session)
