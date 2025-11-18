"""User schema definitions for Surgitutor AI."""

from datetime import datetime
from typing import Optional
from fastapi_users import schemas
from pydantic import ConfigDict, Field, BaseModel, EmailStr


class UserRead(schemas.BaseUser[int]):
    """Schema for reading user information.

    Inherits from BaseUser[int]:
    - id (int)
    - email
    - is_active
    - is_superuser
    - is_verified
    """

    first_name: Optional[str] = None
    last_name: Optional[str] = None
   
    tenant_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

    @property
    def full_name(self) -> str:
        """Get user's full name."""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.first_name or self.last_name or self.email


class UserCreate(schemas.BaseUserCreate):
    """Schema for creating a new user (registration).

    Note: Do NOT use field_validator here as it interferes with
    FastAPI-Users' create_update_dict() method.
    """

    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    tenant_id: Optional[int] = Field(default=None)

    model_config = ConfigDict(from_attributes=True)


class UserUpdate(schemas.BaseUserUpdate):
    """Schema for updating an existing user."""

    first_name: Optional[str] = Field(default=None, min_length=1, max_length=100)
    last_name: Optional[str] = Field(default=None, min_length=1, max_length=100)
    password: Optional[str] = None  # Password updates

    model_config = ConfigDict(from_attributes=True)


class ResendVerificationRequest(BaseModel):
    """Request model for resending verification email."""

    email: EmailStr


class PasswordResetRequest(BaseModel):
    """Request model for password reset."""

    email: EmailStr


class PasswordResetConfirm(BaseModel):
    """Confirm password reset with token."""

    token: str
    password: str = Field(..., min_length=8)


class UserProfileResponse(BaseModel):
    """Comprehensive user profile response."""

    id: int
    email: str
    first_name: Optional[str]
    last_name: Optional[str]
    full_name: str
    tenant_id: Optional[int]
    is_active: bool
    is_verified: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
