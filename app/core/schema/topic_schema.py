"""Topic schema definitions."""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict


class TopicCreate(BaseModel):
    """Schema for creating a new topic."""

    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    category: Optional[str] = Field(default=None, max_length=50)
    difficulty_level: Optional[int] = Field(
        default=None,
        ge=1,
        le=5,
        description="Difficulty level from 1 (easiest) to 5 (hardest)",
    )

    model_config = ConfigDict(from_attributes=True)


class TopicRead(BaseModel):
    """Schema for reading topic information."""

    id: int
    name: str
    description: Optional[str]
    category: Optional[str]
    difficulty_level: Optional[int]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TopicUpdate(BaseModel):
    """Schema for updating topic information."""

    name: Optional[str] = Field(default=None, min_length=1, max_length=100)
    description: Optional[str] = None
    category: Optional[str] = None
    difficulty_level: Optional[int] = Field(default=None, ge=1, le=5)

    model_config = ConfigDict(from_attributes=True)
