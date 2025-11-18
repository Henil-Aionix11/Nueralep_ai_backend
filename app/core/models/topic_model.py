"""Topic model for surgical topics/categories."""

from typing import List, Optional, TYPE_CHECKING
from sqlalchemy import String, Integer, Text, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.models.base_model import Base, BigIntIDModel, TimestampedModel

if TYPE_CHECKING:
    from app.core.models.scenario_model import Scenario
    from app.core.models.session_model import Session


class Topic(BigIntIDModel, TimestampedModel, Base):
    """Topic model - surgical topics/categories for scenarios."""

    __tablename__ = "topics"

    # Topic Info
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Categorization
    category: Mapped[Optional[str]] = mapped_column(
        String(50), nullable=True, index=True
    )
    difficulty_level: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Relationships
    scenarios: Mapped[List["Scenario"]] = relationship(
        "Scenario", back_populates="topic", cascade="all, delete-orphan"
    )
    sessions: Mapped[List["Session"]] = relationship("Session", back_populates="topic")

    # Table constraints
    __table_args__ = (
        CheckConstraint(
            "difficulty_level >= 1 AND difficulty_level <= 5",
            name="check_difficulty_level",
        ),
    )

    def __repr__(self) -> str:
        return f"<Topic(id={self.id}, name={self.name}, category={self.category})>"
