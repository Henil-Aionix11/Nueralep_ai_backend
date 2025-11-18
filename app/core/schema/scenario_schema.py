"""Scenario schema definitions."""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict


class ScenarioCreate(BaseModel):
    """Schema for creating a new scenario."""

    title: str = Field(..., min_length=1, max_length=255)
    topic_id: int
    brief_description: Optional[str] = None
    full_prompt: str = Field(..., min_length=1)

    model_config = ConfigDict(from_attributes=True)


class ScenarioRead(BaseModel):
    """Schema for reading scenario information."""

    id: int
    title: str
    topic_id: int
    brief_description: Optional[str]
    full_prompt: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ScenarioUpdate(BaseModel):
    """Schema for updating scenario information."""

    title: Optional[str] = Field(default=None, min_length=1, max_length=255)
    brief_description: Optional[str] = None
    full_prompt: Optional[str] = Field(default=None, min_length=1)
    topic_id: Optional[int] = None

    model_config = ConfigDict(from_attributes=True)
