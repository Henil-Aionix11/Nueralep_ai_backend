"""User model definition."""

from datetime import datetime
from typing import Optional, List, TYPE_CHECKING

from fastapi_users.db import SQLAlchemyBaseUserTable
from sqlalchemy import DateTime, String, BigInteger, ForeignKey, CheckConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.models.base_model import Base


if TYPE_CHECKING:
    from app.core.models.tenant_model import Tenant
    from app.core.models.session_model import Session


class User(SQLAlchemyBaseUserTable[int], Base):
    """User model - stores both university and individual users.

    Note: We explicitly define id field here to work with Base.
    SQLAlchemyBaseUserTable[int] provides email, hashed_password, is_active, is_superuser, is_verified
    """

    __tablename__ = "users"

    # Override ID to use BigInt with autoincrement (works with Base)
    id: Mapped[int] = mapped_column(
        BigInteger, primary_key=True, autoincrement=True, nullable=False
    )

    # User fields (from FastAPI-Users)
    # email, hashed_password, is_active, is_superuser, is_verified inherited

    # Additional user info
    first_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    last_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    tenant_id: Mapped[Optional[int]] = mapped_column(
        BigInteger,
        ForeignKey("tenants.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now(), onupdate=func.now()
    )




    @property
    def full_name(self) -> str:
        """Get user's full name."""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.first_name or self.last_name or self.email
