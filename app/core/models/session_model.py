"""Session model for training session records."""

from typing import Optional, Dict, Any, TYPE_CHECKING
from datetime import datetime
from sqlalchemy import (
    String,
    BigInteger,
    Integer,
    Text,
    ForeignKey,
    CheckConstraint,
    TIMESTAMP,
    Numeric,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.models.base_model import Base, BigIntIDModel, TimestampedModel

if TYPE_CHECKING:
    from app.core.models.user_model import User
    from app.core.models.scenario_model import Scenario
    from app.core.models.topic_model import Topic


class Session(BigIntIDModel, TimestampedModel, Base):
    """Session model - individual training session records."""

    __tablename__ = "sessions"

    # Relationships
    user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    scenario_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("scenarios.id", ondelete="CASCADE"), nullable=False
    )
    topic_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("topics.id", ondelete="CASCADE"), nullable=False
    )

    # Session Configuration
    bot_mode: Mapped[str] = mapped_column(String(20), nullable=False)

    # Session Lifecycle
    status: Mapped[str] = mapped_column(
        String(20), default="not_started", nullable=False
    )

    # Timing
    started_at: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP, nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(TIMESTAMP, nullable=True)
    duration_seconds: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Conversation Data
    transcript: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSONB, nullable=True)
    audio_recording_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # AI Evaluation & Scoring
    overall_score: Mapped[Optional[float]] = mapped_column(Numeric(3, 1), nullable=True)
    ai_feedback_full: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSONB, nullable=True
    )

    # Relationships
    user: Mapped["User"] = relationship(
        "User", back_populates="sessions", lazy="selectin"
    )
    scenario: Mapped["Scenario"] = relationship(
        "Scenario", back_populates="sessions", lazy="selectin"
    )
    topic: Mapped["Topic"] = relationship(
        "Topic", back_populates="sessions", lazy="selectin"
    )

    # Table constraints
    __table_args__ = (
        CheckConstraint(
            "bot_mode IN ('tutor', 'exam', 'rapid')", name="check_bot_mode"
        ),
        CheckConstraint(
            "status IN ('not_started', 'in_progress', 'paused', 'completed', 'abandoned')",
            name="check_status",
        ),
        CheckConstraint(
            "overall_score >= 0 AND overall_score <= 10", name="check_overall_score"
        ),
    )

    def __repr__(self) -> str:
        return (
            f"<Session(id={self.id}, user_id={self.user_id}, "
            f"scenario_id={self.scenario_id}, status={self.status})>"
        )
