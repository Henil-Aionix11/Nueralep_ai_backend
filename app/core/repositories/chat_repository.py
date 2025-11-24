"""Repository for chat-related database operations."""

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.models.chat_model import Chat
from app.core.repositories.base_repository import BaseRepository
from app.core.schema.chat_schema import ChatCreate


class ChatRepository(BaseRepository[Chat, ChatCreate, dict]):
    """Repository for Chat model operations."""

    def __init__(self, session: AsyncSession) -> None:
        super().__init__(model=Chat, session=session)
