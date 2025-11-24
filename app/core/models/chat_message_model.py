"""ChatMessage model - Individual messages in chat conversations."""

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, String, BigInteger, ForeignKey, Text, func, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.models.base_model import Base

if TYPE_CHECKING:
    from app.core.models.chat_model import Chat


class ChatMessage(Base):
    """ChatMessage model - Messages in tenant-agent conversations."""

    __tablename__ = "chat_messages"

    # Primary key
    id: Mapped[int] = mapped_column(
        BigInteger, primary_key=True, autoincrement=True, nullable=False
    )

    # Foreign key to chat
    chat_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("chats.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Message content
    role: Mapped[str] = mapped_column(
        String(20), nullable=False  # "user" or "assistant"
    )
    
    content: Mapped[str] = mapped_column(
        Text, nullable=False
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )

    # Relationship
    chat: Mapped["Chat"] = relationship("Chat", back_populates="messages")

    # Indexes
    __table_args__ = (
        Index("idx_chat_messages_chat_created", "chat_id", "created_at"),
        Index("idx_chat_messages_role", "role"),
    )

    def __repr__(self) -> str:
        return f"<ChatMessage(id={self.id}, chat_id={self.chat_id}, role={self.role})>"
