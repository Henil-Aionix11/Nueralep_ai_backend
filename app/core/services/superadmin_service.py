"""Service layer for superadmin tenant management operations."""

from typing import List
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger
from passlib.context import CryptContext

from app.core.database import get_db
from app.core.repositories.tenant_repository import TenantRepository
from app.core.repositories.agent_repository import AgentRepository
from app.core.schema.tenant_schema import TenantCreate, AgentCreate
from app.core.exceptions.api_exceptions import (
    ApiNotFoundError,
    ApiConflictError,
    ApiInternalServerError,
)

# Password hashing context
pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")


class SuperadminService:
    """Handles business logic for superadmin operations."""

    def __init__(self, session: AsyncSession) -> None:
        """Initialize superadmin service."""
        self.tenant_repo = TenantRepository(session)
        self.agent_repo = AgentRepository(session)
        self.session = session

    @staticmethod
    def hash_password(password: str) -> str:
        """Hash a password."""
        return pwd_context.hash(password)

    # ==================== TENANT CREATION ====================

    async def create_tenant(self, tenant_data: TenantCreate) -> dict:
        """Create a new tenant with agents.
        
        If a soft-deleted tenant with the same email exists, it will be restored
        and updated with new data instead of creating a duplicate.

        Args:
            tenant_data: Tenant creation data

        Returns:
            Created or restored tenant with agents

        Raises:
            ApiConflictError: If email already exists (for active tenants only)
            ApiInternalServerError: If creation fails
        """
        try:
            # Check if tenant email already exists
            existing_tenant = await self.tenant_repo.get_first_by_filter(
                email=tenant_data.email.lower()
            )
            
            # If tenant exists and is NOT deleted, raise conflict error
            if existing_tenant and not existing_tenant.is_deleted:
                raise ApiConflictError(
                    error=f"Tenant with email '{tenant_data.email}' already exists",
                    message=f"Tenant with email '{tenant_data.email}' already exists",
                )

            # Hash password
            hashed_password = self.hash_password(tenant_data.password)

            # If soft-deleted tenant exists, restore it
            if existing_tenant and existing_tenant.is_deleted:
                logger.info(f"♻️ Restoring soft-deleted tenant: {existing_tenant.id}")
                
                # Update existing tenant with new data
                update_dict = {
                    "name": tenant_data.name,
                    "hashed_password": hashed_password,
                    "country": tenant_data.country,
                    "is_active": True,
                    "is_deleted": False,
                }
                tenant = await self.tenant_repo.update(
                    existing_tenant.id, update_dict, commit=True
                )
                
                # Delete old agents
                old_agents = await self.agent_repo.get_all_by_field("tenant_id", tenant.id)
                for agent in old_agents:
                    await self.agent_repo.delete(agent)
                
                # Create new agents
                agents = []
                for agent_name in tenant_data.agent_names:
                    agent_create = AgentCreate(
                        tenant_id=tenant.id,
                        agent_name=agent_name.strip(),
                    )
                    agent = await self.agent_repo.create(agent_create, commit=True)
                    agents.append(agent)
                
                logger.info(
                    f" Restored tenant: {tenant.name} (ID: {tenant.id}) "
                    f"with {len(agents)} agent(s)"
                )
            
            else:
                # Create new tenant
                tenant_dict = {
                    "name": tenant_data.name,
                    "email": tenant_data.email.lower(),
                    "hashed_password": hashed_password,
                    "country": tenant_data.country,
                    "is_active": True,
                    "is_deleted": False,
                }

                tenant = await self.tenant_repo.create(tenant_dict, commit=True)

                # Create agents
                agents = []
                for agent_name in tenant_data.agent_names:
                    agent_create = AgentCreate(
                        tenant_id=tenant.id,
                        agent_name=agent_name.strip(),
                    )
                    agent = await self.agent_repo.create(agent_create, commit=True)
                    agents.append(agent)

                logger.info(
                    f" Created tenant: {tenant.name} (ID: {tenant.id}) "
                    f"with {len(agents)} agent(s)"
                )

            # Return tenant data with agents
            return {
                "id": tenant.id,
                "name": tenant.name,
                "email": tenant.email,
                "country": tenant.country,
                "is_active": tenant.is_active,
                "created_at": tenant.created_at,
                "updated_at": tenant.updated_at,
                "agents": [
                    {
                        "id": agent.id,
                        "agent_name": agent.agent_name,
                        "created_at": agent.created_at,
                    }
                    for agent in agents
                ],
            }

        except ApiConflictError:
            raise
        except Exception as e:
            logger.error(f" Failed to create tenant: {e}")
            raise ApiInternalServerError(
                error=f"Failed to create tenant: {str(e)}",
                message="Failed to create tenant",
            ) from e

    # ==================== TENANT RETRIEVAL ====================

    async def get_tenant_by_id(self, tenant_id: int) -> dict:
        """Get tenant by ID with agents.

        Args:
            tenant_id: Tenant ID

        Returns:
            Tenant data with agents

        Raises:
            ApiNotFoundError: If tenant not found
        """
        try:
            tenant = await self.tenant_repo.get_by_id(tenant_id)

            if not tenant or tenant.is_deleted:
                raise ApiNotFoundError(
                    error=f"Tenant with ID {tenant_id} not found",
                    message=f"Tenant with ID {tenant_id} not found",
                )

            # Get agents for this tenant
            agents = await self.agent_repo.get_all_by_field("tenant_id", tenant.id)

            return {
                "id": tenant.id,
                "name": tenant.name,
                "email": tenant.email,
                "country": tenant.country,
                "is_active": tenant.is_active,
                "created_at": tenant.created_at,
                "updated_at": tenant.updated_at,
                "agents": [
                    {
                        "id": agent.id,
                        "agent_name": agent.agent_name,
                        "created_at": agent.created_at,
                    }
                    for agent in agents
                ],
            }

        except ApiNotFoundError:
            raise
        except Exception as e:
            logger.error(f" Failed to get tenant {tenant_id}: {e}")
            raise ApiInternalServerError(
                error=f"Failed to retrieve tenant: {str(e)}",
                message="Failed to retrieve tenant",
            ) from e

    async def get_all_tenants(self) -> List[dict]:
        """Get all active tenants with agents.

        Returns:
            List of tenant data with agents
        """
        try:
            tenants = await self.tenant_repo.get_all_by_filter(is_deleted=False)

            result_list = []
            for tenant in tenants:
                # Get agents for each tenant
                agents = await self.agent_repo.get_all_by_field("tenant_id", tenant.id)

                result_list.append(
                    {
                        "id": tenant.id,
                        "name": tenant.name,
                        "email": tenant.email,
                        "country": tenant.country,
                        "is_active": tenant.is_active,
                        "created_at": tenant.created_at,
                        "updated_at": tenant.updated_at,
                        "agents": [
                            {
                                "id": agent.id,
                                "agent_name": agent.agent_name,
                                "created_at": agent.created_at,
                            }
                            for agent in agents
                        ],
                    }
                )

            logger.debug(f"📋 Retrieved {len(result_list)} active tenants")
            return result_list

        except Exception as e:
            logger.error(f" Failed to get tenants: {e}")
            raise ApiInternalServerError(
                error=f"Failed to retrieve tenants: {str(e)}",
                message="Failed to retrieve tenants",
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
            tenant = await self.tenant_repo.get_by_id(tenant_id)

            if not tenant or tenant.is_deleted:
                raise ApiNotFoundError(
                    error=f"Tenant with ID {tenant_id} not found",
                    message=f"Tenant with ID {tenant_id} not found",
                )

            # Soft delete (agents will be cascade deleted due to relationship)
            await self.tenant_repo.update(tenant_id, {"is_deleted": True}, commit=True)

            logger.info(f"🗑️ Soft deleted tenant: {tenant_id}")
            return True

        except ApiNotFoundError:
            raise
        except Exception as e:
            logger.error(f" Failed to delete tenant {tenant_id}: {e}")
            raise ApiInternalServerError(
                error=f"Failed to delete tenant: {str(e)}",
                message="Failed to delete tenant",
            ) from e

    # ==================== TENANT UPDATE ====================

    async def update_tenant(self, tenant_id: int, update_data: dict) -> dict:
        """Update tenant information and agents.

        Args:
            tenant_id: Tenant ID
            update_data: Data to update (name, country, is_active, agent_names)

        Returns:
            Updated tenant with agents

        Raises:
            ApiNotFoundError: If tenant not found
            ApiInternalServerError: If update fails
        """
        try:
            # Check if tenant exists
            tenant = await self.tenant_repo.get_by_id(tenant_id)

            if not tenant or tenant.is_deleted:
                raise ApiNotFoundError(
                    error=f"Tenant with ID {tenant_id} not found",
                    message=f"Tenant with ID {tenant_id} not found",
                )

            # Extract agent_names if provided
            agent_names = update_data.pop("agent_names", None)

            # Update tenant basic info (name, country, is_active)
            if update_data:
                await self.tenant_repo.update(tenant_id, update_data, commit=True)

            # Update agents if agent_names provided
            if agent_names is not None:
                # Delete existing agents
                existing_agents = await self.agent_repo.get_all_by_field("tenant_id", tenant_id)
                for agent in existing_agents:
                    await self.agent_repo.delete(agent)

                # Create new agents
                for agent_name in agent_names:
                    agent_create = AgentCreate(
                        tenant_id=tenant_id,
                        agent_name=agent_name.strip(),
                    )
                    await self.agent_repo.create(agent_create, commit=True)

            # Get updated tenant with agents
            updated_tenant = await self.tenant_repo.get_by_id(tenant_id)
            agents = await self.agent_repo.get_all_by_field("tenant_id", tenant_id)

            logger.info(f" Updated tenant: {tenant_id}")

            return {
                "id": updated_tenant.id,
                "name": updated_tenant.name,
                "email": updated_tenant.email,
                "country": updated_tenant.country,
                "is_active": updated_tenant.is_active,
                "created_at": updated_tenant.created_at,
                "updated_at": updated_tenant.updated_at,
                "agents": [
                    {
                        "id": agent.id,
                        "agent_name": agent.agent_name,
                        "created_at": agent.created_at,
                    }
                    for agent in agents
                ],
            }

        except ApiNotFoundError:
            raise
        except Exception as e:
            logger.error(f" Failed to update tenant {tenant_id}: {e}")
            raise ApiInternalServerError(
                error=f"Failed to update tenant: {str(e)}",
                message="Failed to update tenant",
            ) from e


async def get_superadmin_service(
    session: AsyncSession = Depends(get_db),
) -> SuperadminService:  # type: ignore
    """Get superadmin service instance."""
    yield SuperadminService(session)
