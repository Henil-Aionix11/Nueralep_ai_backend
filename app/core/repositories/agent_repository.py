"""Repository for agent-related database operations."""

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.models.agent_model import Agent
from app.core.repositories.base_repository import BaseRepository
from app.core.schema.tenant_schema import AgentCreate


class AgentRepository(BaseRepository[Agent, AgentCreate, dict]):
    """Repository for Agent model operations.
    
    Inherits all CRUD operations from BaseRepository.
    """

    def __init__(self, session: AsyncSession) -> None:
        """Initialize repository with session and model.

        Args:
            session: AsyncSession database session
        """
        super().__init__(model=Agent, session=session)
