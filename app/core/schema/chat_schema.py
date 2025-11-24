"""Pydantic schemas for Chat and ChatMessage."""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field


# ========== Chat Schemas ==========

class ChatCreate(BaseModel):
    """Schema for creating a new chat."""
    agent_name: str = Field(..., min_length=1, max_length=100)
    title: Optional[str] = Field(None, max_length=255)


class ChatResponse(BaseModel):
    """Schema for chat response."""
    id: int
    tenant_id: int
    agent_name: str
    title: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ChatWithLastMessage(BaseModel):
    """Chat with last message preview."""
    id: int
    tenant_id: int
    agent_name: str
    title: str
    created_at: datetime
    updated_at: datetime
    last_message: Optional[str] = None
    last_message_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ========== Message Schemas ==========

class MessageCreate(BaseModel):
    """Schema for creating a message (user message only)."""
    content: str = Field(..., min_length=1)


class MessageResponse(BaseModel):
    """Schema for message response."""
    id: int
    chat_id: int
    role: str
    content: str
    created_at: datetime

    class Config:
        from_attributes = True


class ChatDetailResponse(BaseModel):
    """Schema for chat with all messages."""
    chat: ChatResponse
    messages: List[MessageResponse]


class SendMessageResponse(BaseModel):
    """Response after sending a message (includes AI response)."""
    user_message: MessageResponse
    assistant_message: MessageResponse
