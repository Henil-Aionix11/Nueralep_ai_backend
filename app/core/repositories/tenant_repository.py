"""Repository for tenant-related database operations."""

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.models.tenant_model import Tenant
from app.core.repositories.base_repository import BaseRepository
from app.core.schema.tenant_schema import TenantCreate, TenantUpdate


class TenantRepository(BaseRepository[Tenant, TenantCreate, TenantUpdate]):
    """Repository for Tenant model operations.
    
    Inherits all CRUD operations from BaseRepository:
    - create
    - create_all
    - get_by_id
    - get_all
    - get_all_by_field
    - get_first_by_filter
    - get_all_by_filter
    - get_paginated
    - update
    - delete
    - delete_by_ids
    - commit
    - count_by_filter
    - get_by_field
    - increment_field
    """

    def __init__(self, session: AsyncSession) -> None:
        """Initialize repository with session and model.

        Args:
            session: AsyncSession database session
        """
        super().__init__(model=Tenant, session=session)
