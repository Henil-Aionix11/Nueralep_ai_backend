"""Tenant schema definitions."""

from datetime import date, datetime
from typing import Optional, List
from pydantic import BaseModel, EmailStr, ConfigDict, Field


# ==================== AGENT SCHEMAS ====================

class AgentRead(BaseModel):
    """Schema for reading agent information."""

    id: int
    agent_name: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AgentCreate(BaseModel):
    """Schema for creating an agent (used internally, not exposed)."""

    tenant_id: int
    agent_name: str


# ==================== TENANT SCHEMAS ====================

class TenantCreate(BaseModel):
    """Schema for creating a new tenant (by superadmin)."""

    name: str = Field(..., min_length=2, max_length=255, description="Tenant name")
    email: EmailStr = Field(..., description="Tenant email (used for login)")
    password: str = Field(..., min_length=8, description="Tenant password")
    country: str = Field(..., min_length=2, max_length=100, description="Country")
    agent_names: List[str] = Field(
        ..., min_items=1, description="List of agent names to assign"
    )
    end_date: Optional[date] = Field(None, description="Tenant access end date")

    model_config = ConfigDict(from_attributes=True)


class TenantRead(BaseModel):
    """Schema for reading tenant information."""

    id: int
    name: str
    email: str
    country: str
    is_active: bool
    created_at: datetime
    updated_at: datetime
    agents: List[AgentRead] = []
    end_date: Optional[date] = None

    model_config = ConfigDict(from_attributes=True)


class TenantLogin(BaseModel):
    """Schema for tenant login."""

    email: EmailStr
    password: str


class TenantUpdate(BaseModel):
    """Schema for updating tenant information."""

    name: Optional[str] = Field(None, min_length=2, max_length=255)
    country: Optional[str] = Field(None, min_length=2, max_length=100)
    is_active: Optional[bool] = None

    model_config = ConfigDict(from_attributes=True)


class TenantListResponse(BaseModel):
    """Schema for tenant list response."""

    tenants: List[TenantRead]
    total: int


class TenantUpdateByAdmin(BaseModel):
    """Schema for updating tenant by superadmin."""

    name: Optional[str] = Field(None, min_length=2, max_length=255, description="Tenant name")
    country: Optional[str] = Field(None, min_length=2, max_length=100, description="Country")
    is_active: Optional[bool] = Field(None, description="Active status")
    agent_names: Optional[List[str]] = Field(None, min_items=1, description="List of agent names (replaces existing)")
    end_date: Optional[date] = Field(None, description="Tenant access end date")
    
    model_config = ConfigDict(from_attributes=True)
