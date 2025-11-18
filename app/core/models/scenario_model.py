"""Scenario model for training scenarios."""

from typing import List, Optional, TYPE_CHECKING
from sqlalchemy import String, BigInteger, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.models.base_model import Base, BigIntIDModel, TimestampedModel

if TYPE_CHECKING:
    from app.core.models.topic_model import Topic
    from app.core.models.session_model import Session


class Scenario(BigIntIDModel, TimestampedModel, Base):
    """Scenario model - training scenarios with prompts and metadata."""

    __tablename__ = "scenarios"

    # Basic Info
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    topic_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey("topics.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Scenario Content
    brief_description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    full_prompt: Mapped[str] = mapped_column(Text, nullable=False)

    # Relationships
    topic: Mapped["Topic"] = relationship(
        "Topic", back_populates="scenarios", lazy="selectin"
    )
    sessions: Mapped[List["Session"]] = relationship(
        "Session", back_populates="scenario"
    )

    def __repr__(self) -> str:
        return f"<Scenario(id={self.id}, title={self.title}, topic_id={self.topic_id})>"
