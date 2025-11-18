"""Service layer for user management operations."""

from typing import Optional
from fastapi import Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from app.core.database import get_db
from app.core.repositories.user_repository import UserRepository
from app.core.models.user_model import User
from app.core.schema.user_schema import UserUpdate
from app.core.exceptions.api_exceptions import (
    ApiNotFoundError,
    ApiConflictError,
    ApiInternalServerError,
)
from app.web.api.v1.user.user_manager import get_user_manager


class UserService:
    """Handles business logic for user management."""

    def __init__(self, session: AsyncSession = Depends(get_db)) -> None:
        """Initialize user service.

        Args:
            session: Database session
        """
        self.repository = UserRepository(session)
        self.session = session

    # ==================== USER RETRIEVAL ====================

    async def get_user_by_id(self, user_id: int) -> User:
        """Get user by ID.

        Args:
            user_id: User ID

        Returns:
            User object

        Raises:
            ApiNotFoundError: If user not found
        """
        try:
            user = await self.repository.get_by_id(user_id)
            if not user:
                logger.warning(f"User not found: {user_id}")
                raise ApiNotFoundError(
                    error=f"User with ID {user_id} not found",
                    message=f"User with ID {user_id} not found",
                )
            return user
        except ApiNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Failed to get user by ID {user_id}: {e}")
            raise ApiInternalServerError(
                error=f"Failed to retrieve user: {str(e)}",
                message="Failed to retrieve user",
            ) from e

    async def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email address.

        Args:
            email: User email

        Returns:
            User object or None

        Raises:
            ApiInternalServerError: If query fails
        """
        try:
            user = await self.repository.get_by_field("email", email.lower())
            return user
        except ValueError as e:
            logger.error(f"Email field is not unique: {e}")
            raise ApiInternalServerError(
                error=f"Database configuration error: {str(e)}",
                message="Failed to retrieve user",
            ) from e
        except Exception as e:
            logger.error(f"Failed to get user by email {email}: {e}")
            raise ApiInternalServerError(
                error=f"Failed to retrieve user: {str(e)}",
                message="Failed to retrieve user",
            ) from e

    # ==================== USER UPDATE ====================

    async def update_user(self, user_id: int, update_data: UserUpdate) -> User:
        """Update user information.

        Args:
            user_id: User ID
            update_data: Data to update

        Returns:
            Updated user object

        Raises:
            ApiNotFoundError: If user not found
            ApiConflictError: If conflict during update
            ApiInternalServerError: If update fails
        """
        try:
            # Update user
            updated_user = await self.repository.update(
                record_id=user_id, update_data=update_data, commit=True
            )

            logger.info(f"Updated user: {user_id}")
            return updated_user

        except ApiNotFoundError:
            raise
        except ApiConflictError as e:
            logger.error(f"Conflict during user update: {e}")
            raise
        except Exception as e:
            logger.error(f"Failed to update user {user_id}: {e}")
            raise ApiInternalServerError(
                error=f"Failed to update user: {str(e)}",
                message="Failed to update user",
            ) from e

    # ==================== VERIFICATION & PASSWORD ====================

    async def resend_verification_email(self, email: str) -> dict:
        """Resend verification email to user.

        Args:
            email: User email

        Returns:
            Success message

        Raises:
            ApiNotFoundError: If user not found
            HTTPException: If user already verified
            ApiInternalServerError: If sending fails
        """
        try:
            # Get user by email
            user = await self.get_user_by_email(email)
            if not user:
                logger.warning(f"Resend verification: User not found: {email}")
                raise ApiNotFoundError(
                    error=f"User with email {email} not found",
                    message=f"User with email {email} not found",
                )

            if user.is_verified:
                logger.info(f"Resend verification: User already verified: {email}")
                raise HTTPException(status_code=400, detail="User is already verified")

            # Get user manager and request verification
            async for user_manager in get_user_manager():
                await user_manager.request_verify(user)
                logger.info(f"Verification email resent to {email}")
                break

            return {
                "message": "Verification email sent successfully. Please check your inbox."
            }

        except (ApiNotFoundError, HTTPException):
            raise
        except Exception as e:
            logger.error(f"Failed to resend verification email for {email}: {e}")
            raise ApiInternalServerError(
                error=f"Failed to send verification email: {str(e)}",
                message="Failed to send verification email",
            ) from e


# Dependency injection
async def get_user_service(
    session: AsyncSession = Depends(get_db),
) -> UserService:  # type: ignore
    """Get user service instance.

    Args:
        session: Database session

    Yields:
        UserService instance
    """
    yield UserService(session)
