"""Service layer for tenant authentication and management operations."""

from typing import Optional
from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger
from passlib.context import CryptContext

from app.core.database import get_db
from app.core.repositories.tenant_repository import TenantRepository
from app.core.repositories.agent_repository import AgentRepository
from app.core.models.tenant_model import Tenant
from app.core.schema.tenant_schema import TenantCreate, TenantUpdate, TenantLogin
from app.core.exceptions.api_exceptions import (
    ApiNotFoundError,
    ApiConflictError,
    ApiInternalServerError,
)

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class TenantService:
    """Handles business logic for tenant operations."""

    def __init__(self, session: AsyncSession) -> None:
        """Initialize tenant service.

        Args:
            session: Database session
        """
        self.tenant_repo = TenantRepository(session)
        self.agent_repo = AgentRepository(session)
        self.session = session

    # ==================== PASSWORD UTILITIES ====================

    @staticmethod
    def hash_password(password: str) -> str:
        """Hash a password.

        Args:
            password: Plain text password

        Returns:
            Hashed password
        """
        return pwd_context.hash(password)

    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verify a password against a hash.

        Args:
            plain_password: Plain text password
            hashed_password: Hashed password

        Returns:
            True if password matches
        """
        return pwd_context.verify(plain_password, hashed_password)

    # ==================== TENANT AUTHENTICATION ====================

    async def authenticate_tenant(self, email: str, password: str) -> Tenant:
        """Authenticate tenant by email and password.

        Args:
            email: Tenant email
            password: Tenant password

        Returns:
            Authenticated tenant

        Raises:
            HTTPException: If authentication fails
        """
        try:
            # Get tenant by email
            tenant = await self.tenant_repo.get_by_field("email", email.lower())

            if not tenant:
                logger.warning(f"Login attempt with non-existent email: {email}")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Incorrect email or password",
                )

            # Check if tenant is active
            if not tenant.is_active or tenant.is_deleted:
                logger.warning(f"Login attempt for inactive tenant: {email}")
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Tenant account is inactive",
                )

            # Verify password
            if not self.verify_password(password, tenant.hashed_password):
                logger.warning(f"Failed login attempt for tenant: {email}")
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Incorrect email or password",
                )

            logger.info(f"Tenant authenticated successfully: {email}")
            return tenant

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Authentication error for {email}: {e}")
            raise ApiInternalServerError(
                error=f"Authentication failed: {str(e)}",
                message="Authentication failed",
            ) from e

    # ==================== TENANT RETRIEVAL ====================

    async def get_tenant_by_id(self, tenant_id: int) -> Tenant:
        """Get tenant by ID with agents.

        Args:
            tenant_id: Tenant ID

        Returns:
            Tenant object with agents

        Raises:
            ApiNotFoundError: If tenant not found
        """
        try:
            tenant = await self.tenant_repo.get_by_id(tenant_id)

            if not tenant or tenant.is_deleted:
                logger.warning(f"Tenant not found: {tenant_id}")
                raise ApiNotFoundError(
                    error=f"Tenant with ID {tenant_id} not found",
                    message=f"Tenant with ID {tenant_id} not found",
                )

            return tenant

        except ApiNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Failed to get tenant by ID {tenant_id}: {e}")
            raise ApiInternalServerError(
                error=f"Failed to retrieve tenant: {str(e)}",
                message="Failed to retrieve tenant",
            ) from e

    async def get_tenant_by_email(self, email: str) -> Optional[Tenant]:
        """Get tenant by email.

        Args:
            email: Tenant email

        Returns:
            Tenant object or None
        """
        try:
            tenant = await self.tenant_repo.get_by_field("email", email.lower())
            return tenant
        except Exception as e:
            logger.error(f"Failed to get tenant by email {email}: {e}")
            raise ApiInternalServerError(
                error=f"Failed to retrieve tenant: {str(e)}",
                message="Failed to retrieve tenant",
            ) from e

    async def get_all_tenants(self) -> list[Tenant]:
        """Get all active tenants.

        Returns:
            List of active tenants
        """
        try:
            tenants = await self.tenant_repo.get_all_by_filter(is_deleted=False)
            logger.debug(f"Retrieved {len(tenants)} active tenants")
            return tenants

        except Exception as e:
            logger.error(f"Failed to get all tenants: {e}")
            raise ApiInternalServerError(
                error=f"Failed to retrieve tenants: {str(e)}",
                message="Failed to retrieve tenants",
            ) from e

    # ==================== TENANT UPDATE ====================

    async def update_tenant(self, tenant_id: int, update_data: TenantUpdate) -> Tenant:
        """Update tenant information.

        Args:
            tenant_id: Tenant ID
            update_data: Data to update

        Returns:
            Updated tenant object

        Raises:
            ApiNotFoundError: If tenant not found
            ApiInternalServerError: If update fails
        """
        try:
            # Check if tenant exists
            tenant = await self.get_tenant_by_id(tenant_id)

            # Update tenant
            updated_tenant = await self.tenant_repo.update(
                record_id=tenant_id, update_data=update_data, commit=True
            )

            logger.info(f"Updated tenant: {tenant_id}")
            return updated_tenant

        except ApiNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Failed to update tenant {tenant_id}: {e}")
            raise ApiInternalServerError(
                error=f"Failed to update tenant: {str(e)}",
                message="Failed to update tenant",
            ) from e

    # ==================== TENANT SOFT DELETE ====================

    async def soft_delete_tenant(self, tenant_id: int) -> bool:
        """Soft delete tenant.

        Args:
            tenant_id: Tenant ID

        Returns:
            True if successful

        Raises:
            ApiNotFoundError: If tenant not found
        """
        try:
            tenant = await self.get_tenant_by_id(tenant_id)

            # Soft delete
            await self.tenant_repo.update(
                tenant_id, {"is_deleted": True}, commit=True
            )

            logger.info(f"Soft deleted tenant: {tenant_id}")
            return True

        except ApiNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Failed to delete tenant {tenant_id}: {e}")
            raise ApiInternalServerError(
                error=f"Failed to delete tenant: {str(e)}",
                message="Failed to delete tenant",
            ) from e


# Dependency injection
async def get_tenant_service(
    session: AsyncSession = Depends(get_db),
) -> TenantService:  # type: ignore
    """Get tenant service instance.

    Args:
        session: Database session

    Yields:
        TenantService instance
    """
    yield TenantService(session)
