"""Base model definitions for SQLAlchemy classes.

This module provides base model classes with common functionality like:
- Automatic table naming
- UUID primary keys
- Created/updated timestamps
"""

from datetime import UTC, datetime
from uuid import UUID, uuid4

from sqlalchemy import DateTime, BigInteger, func
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models."""

    @declared_attr.directive
    def __tablename__(cls) -> str:
        """Automatically generate table name from class name."""
        return cls.__name__.lower()


class IDModel:
    """Adds UUID primary key."""

    id: Mapped[UUID] = mapped_column(
        PostgresUUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
        index=True,
        nullable=False,
    )


class BigIntIDModel:
    """Adds auto-incrementing BigInt primary key."""

    id: Mapped[int] = mapped_column(
        BigInteger, primary_key=True, autoincrement=True, nullable=False
    )


class TimestampedModel:
    """Adds created_at and updated_at timestamps."""

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(UTC).replace(tzinfo=None),
        server_default=func.timezone("UTC", func.now()),
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.now(UTC).replace(tzinfo=None),
        onupdate=lambda: datetime.now(UTC).replace(tzinfo=None),
        server_default=func.timezone("UTC", func.now()),
        nullable=False,
    )
