"""Repository for chat message-related database operations."""

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.models.chat_message_model import ChatMessage
from app.core.repositories.base_repository import BaseRepository
from app.core.schema.chat_schema import MessageCreate


class ChatMessageRepository(BaseRepository[ChatMessage, MessageCreate, dict]):
    """Repository for ChatMessage model operations."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(model=ChatMessage, session=session)
