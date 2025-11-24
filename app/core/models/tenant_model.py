"""Tenant model definition - Tenants are the primary users of the system."""

from datetime import datetime
from typing import Any, Dict, List, Optional, TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, String, BigInteger, JSON, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.models.base_model import Base

if TYPE_CHECKING:
    from app.core.models.agent_model import Agent


class Tenant(Base):
    """Tenant model - Organizations that use the AI Excel Agents system.
    
    Tenants authenticate using email and password.
    """

    __tablename__ = "tenants"

    # Primary key
    id: Mapped[int] = mapped_column(
        BigInteger, primary_key=True, autoincrement=True, nullable=False
    )

    # Tenant information
    name: Mapped[str] = mapped_column(
        String(255), nullable=False, index=True
    )
    
    email: Mapped[str] = mapped_column(
        String(320), unique=True, nullable=False, index=True
    )
    
    hashed_password: Mapped[str] = mapped_column(
        String(1024), nullable=False
    )
    
    country: Mapped[str] = mapped_column(
        String(100), nullable=False, index=True
    )

    # Status
    is_active: Mapped[bool] = mapped_column(
        Boolean, default=True, nullable=False
    )
    
    is_deleted: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False, index=True
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )
    
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now(), onupdate=func.now()
    )
    
    end_date: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    dataset_storage_path: Mapped[Optional[str]] = mapped_column(
        String(1024), nullable=True
    )
    
    dataset_metadata: Mapped[Optional[Dict[str, Any]]] = mapped_column(
        JSON, nullable=True
    )

    # Relationships
    agents: Mapped[List["Agent"]] = relationship(
        "Agent",
        back_populates="tenant",
        cascade="all, delete-orphan",
        lazy="selectin"
    )

    def __repr__(self) -> str:
        return f"<Tenant(id={self.id}, name={self.name}, email={self.email})>"

    @property
    def is_deleted_property(self) -> bool:
        """Check if tenant is soft deleted."""
        return self.is_deleted
