"""User manager for FastAPI-Users integration."""

from typing import Optional
from fastapi import Depends, Request, Response
from fastapi_users import BaseUserManager, IntegerIDMixin
from fastapi_users.db import SQLAlchemyUserDatabase
from loguru import logger

from app.core.database import get_db
from app.core.models.user_model import User
from app.core.utils.email_utils.smtp_util import (
    send_verification_email,
    send_reset_password_email,
)
from app.web.settings import settings
from sqlalchemy.ext.asyncio import AsyncSession


class UserManager(IntegerIDMixin, BaseUserManager[User, int]):
    """Custom user manager for Surgitutor AI.

    Handles user registration, verification, and password reset events.
    """

    reset_password_token_secret = settings.reset_password_token_secret
    verification_token_secret = settings.verification_token_secret

    async def on_after_register(
        self, user: User, request: Optional[Request] = None
    ) -> None:
        """Called after user registration - Send verification email.

        Args:
            user: Newly registered user
            request: HTTP request object (optional)
        """
        logger.info(
            f"User registered: {user.email} (ID: {user.id})"
        )

        try:
            await self.request_verify(user, request)
            logger.info(f"Verification email requested for {user.email}")
        except Exception as e:
            logger.error(f"Failed to request verification for {user.email}: {e}")
            raise

    async def on_after_request_verify(
        self, user: User, token: str, request: Optional[Request] = None
    ) -> None:
        """Called when verification token is generated - Send verification email.

        Args:
            user: User requesting verification
            token: Verification token
            request: HTTP request object (optional)
        """
        if user.is_verified:
            logger.info(f"User {user.id} is already verified")
            return

        try:
            verification_url = (
                f"{settings.frontend_base_url}/auth/verify-email?token={token}"
            )
            send_verification_email(user.email, verification_url)
            logger.info(f"Verification email sent to {user.email}")

        except Exception as e:
            logger.error(f"Failed to send verification email to {user.email}: {e}")
            raise

    async def on_after_forgot_password(
        self, user: User, token: str, request: Optional[Request] = None
    ) -> None:
        """Called when password reset is requested - Send reset email.

        Args:
            user: User requesting password reset
            token: Password reset token
            request: HTTP request object (optional)
        """
        logger.info(f"User {user.id} requested password reset")

        try:
            reset_url = (
                f"{settings.frontend_base_url}/auth/reset-password?token={token}"
            )
            send_reset_password_email(user.email, reset_url)
            logger.info(f"Password reset email sent to {user.email}")

        except Exception as e:
            logger.error(f"Failed to send reset email to {user.email}: {e}")
            raise

    async def on_after_login(
        self,
        user: User,
        request: Optional[Request] = None,
        response: Optional[Response] = None,
    ) -> None:
        """Called after successful login.

        Args:
            user: Logged-in user
            request: HTTP request object (optional)
            response: HTTP response object (optional)
        """
        logger.info(
            f"User logged in: {user.email} (ID: {user.id})"
        )

    async def on_after_update(
        self, user: User, update_dict: dict, request: Optional[Request] = None
    ) -> None:
        """Called after user profile update.

        Args:
            user: Updated user
            update_dict: Dictionary of updated fields
            request: HTTP request object (optional)
        """
        logger.info(
            f"User updated: {user.email} (ID: {user.id}) - Fields: {list(update_dict.keys())}"
        )

    async def validate_password(self, password: str, user=None) -> None:
        """Validate password strength.

        Args:
            password: Password to validate
            user: User object (optional)

        Raises:
            ValueError: If password doesn't meet requirements
        """
        if len(password) < 8:
            raise ValueError("Password must be at least 8 characters long")


async def get_user_db(db: AsyncSession = Depends(get_db)) -> SQLAlchemyUserDatabase:
    """Get SQLAlchemy user database instance.

    Args:
        db: Database session

    Yields:
        SQLAlchemyUserDatabase instance
    """
    yield SQLAlchemyUserDatabase(db, User)


async def get_user_manager(
    user_db: SQLAlchemyUserDatabase = Depends(get_user_db),
) -> UserManager:  # type: ignore
    """Get user manager instance.

    Args:
        user_db: SQLAlchemy user database

    Yields:
        UserManager instance
    """
    yield UserManager(user_db)
