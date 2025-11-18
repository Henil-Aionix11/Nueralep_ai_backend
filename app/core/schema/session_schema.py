"""Session schema definitions."""

from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field, ConfigDict


class SessionCreate(BaseModel):
    """Schema for creating a new training session."""

    user_id: int
    scenario_id: int
    topic_id: int
    bot_mode: str = Field(..., pattern="^(tutor|exam|rapid)$")

    model_config = ConfigDict(from_attributes=True)


class SessionRead(BaseModel):
    """Schema for reading session information."""

    id: int
    user_id: int
    scenario_id: int
    topic_id: int
    bot_mode: str
    status: str
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    duration_seconds: Optional[int]
    transcript: Optional[Dict[str, Any]]
    audio_recording_url: Optional[str]
    overall_score: Optional[float]
    ai_feedback_full: Optional[Dict[str, Any]]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class SessionUpdate(BaseModel):
    """Schema for updating session information."""

    status: Optional[str] = Field(
        default=None, pattern="^(not_started|in_progress|paused|completed|abandoned)?$"
    )
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    duration_seconds: Optional[int] = None
    transcript: Optional[Dict[str, Any]] = None
    audio_recording_url: Optional[str] = None
    overall_score: Optional[float] = Field(default=None, ge=0, le=10)
    ai_feedback_full: Optional[Dict[str, Any]] = None

    model_config = ConfigDict(from_attributes=True)


class SessionStartRequest(BaseModel):
    """Request to start a training session."""

    scenario_id: int
    bot_mode: str = Field(..., pattern="^(tutor|exam|rapid)$")


class SessionEndRequest(BaseModel):
    """Request to end a training session."""

    transcript: Optional[Dict[str, Any]] = None
    overall_score: Optional[float] = Field(default=None, ge=0, le=10)
    ai_feedback_full: Optional[Dict[str, Any]] = None
