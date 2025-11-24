"""Chat model - Chat sessions between tenants and agents."""

from datetime import datetime
from typing import List, TYPE_CHECKING

from sqlalchemy import DateTime, String, BigInteger, ForeignKey, func, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.models.base_model import Base

if TYPE_CHECKING:
    from app.core.models.tenant_model import Tenant
    from app.core.models.chat_message_model import ChatMessage


class Chat(Base):
    """Chat model - Tenant conversations with specific agents."""

    __tablename__ = "chats"

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
        String(100), nullable=False, index=True
    )

    # Chat metadata
    title: Mapped[str] = mapped_column(
        String(255), nullable=False, default="New Chat"
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )
    
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    tenant: Mapped["Tenant"] = relationship("Tenant", backref="chats")
    
    messages: Mapped[List["ChatMessage"]] = relationship(
        "ChatMessage",
        back_populates="chat",
        cascade="all, delete-orphan",
        lazy="selectin",
        order_by="ChatMessage.created_at"
    )

    # Indexes
    __table_args__ = (
        Index("idx_chats_tenant_updated", "tenant_id", "updated_at"),
        Index("idx_chats_agent", "agent_name"),
    )

    def __repr__(self) -> str:
        return f"<Chat(id={self.id}, tenant_id={self.tenant_id}, agent={self.agent_name})>"
