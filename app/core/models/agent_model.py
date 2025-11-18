"""Agent model definition - Agents assigned to tenants."""

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, String, BigInteger, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.models.base_model import Base

if TYPE_CHECKING:
    from app.core.models.tenant_model import Tenant


class Agent(Base):
    """Agent model - AI agents assigned to tenants.
    
    Examples: Support Agent, Billing Agent, Data Agent, etc.
    """

    __tablename__ = "agents"

    # Primary key
    id: Mapped[int] = mapped_column(
        BigInteger, primary_key=True, autoincrement=True, nullable=False
    )

    # Foreign key to tenant
    tenant_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("tenants.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Agent information
    agent_name: Mapped[str] = mapped_column(
        String(100), nullable=False
    )
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )

    # Relationship
    tenant: Mapped["Tenant"] = relationship(
        "Tenant",
        back_populates="agents"
    )

    def __repr__(self) -> str:
        return f"<Agent(id={self.id}, name={self.agent_name}, tenant_id={self.tenant_id})>"
