"""Chat service for tenant chat functionality."""

from typing import List, Dict, Optional
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from loguru import logger

from app.core.repositories.chat_repository import ChatRepository
from app.core.repositories.chat_message_repository import ChatMessageRepository
from app.core.repositories.tenant_repository import TenantRepository
from app.core.schema.chat_schema import (
    ChatCreate,
    ChatResponse,
    ChatDetailResponse,
    MessageResponse,
    SendMessageResponse,
    ChatWithLastMessage,
)
from fastapi import HTTPException, status

from app.core.exceptions.api_exceptions import (
    ApiNotFoundError
)
from app.core.services.ai_service import AIService


class ChatService:
    """Service for chat management."""

    def __init__(self, session: AsyncSession) -> None:
        self.chat_repo = ChatRepository(session)
        self.message_repo = ChatMessageRepository(session)
        self.tenant_repo = TenantRepository(session)
        self.ai_service = AIService()
        self.session = session

    async def create_chat(self, tenant_id: int, data: ChatCreate) -> ChatResponse:
        """Create a new chat session.
        
        Args:
            tenant_id: Tenant ID
            data: Chat creation data
            
        Returns:
            Created chat response
        """
        # Verify tenant exists and is active
        tenant = await self.tenant_repo.get_by_id(tenant_id)
        if not tenant or tenant.is_deleted or not tenant.is_active:
            raise ApiNotFoundError(
                error="Tenant not found",
                message="Tenant not found or inactive"
            )
        
        # Verify agent is assigned to tenant
        agent_names = [agent.agent_name for agent in tenant.agents]
        if data.agent_name not in agent_names:
            raise HTTPException(
               status_code=status.HTTP_403_FORBIDDEN,
               detail="Agent '{data.agent_name}' is not assigned to your account"

            )
                
        # Create chat
        chat_data = {
            "tenant_id": tenant_id,
            "agent_name": data.agent_name,
            "title": data.title if data.title else None,
        }
        
        chat = await self.chat_repo.create(chat_data, commit=True, refresh=True)
        
        logger.info(f" Created chat {chat.id} for tenant {tenant_id}")
        
        return ChatResponse.model_validate(chat)

    async def get_tenant_chats(
        self,
        tenant_id: int, 
        agent_name: Optional[str] = None, 
        limit: int = 10
    ) -> List[ChatWithLastMessage]:
        """
        Get all chats for a tenant, optionally filtered by agent name, limited.
        """
        filters = {"tenant_id": tenant_id}
        if agent_name:
            filters["agent_name"] = agent_name
        
        chats = await self.chat_repo.get_all_by_filter(
            order_by="updated_at",
            order_desc=True,
            limit=limit,
            **filters,   # dynamically adds agent_name if present
        )

        result = []
        for chat in chats:
            last_messages = await self.message_repo.get_all_by_filter(
                chat_id=chat.id,
                order_by="created_at",
                order_desc=True,
                limit=1,
            )
            if last_messages and len(last_messages) > 0:
                last_message = last_messages[0]
                last_message_content = last_message.content
                last_message_at = last_message.created_at
            else:
                last_message_content = None
                last_message_at = None

            result.append(ChatWithLastMessage(
                id=chat.id,
                tenant_id=chat.tenant_id,
                agent_name=chat.agent_name,
                title=chat.title,
                created_at=chat.created_at,
                updated_at=chat.updated_at,
                last_message=last_message_content,
                last_message_at=last_message_at,
            ))

        return result
    
    async def get_chat_detail(
        self, chat_id: int, tenant_id: int, limit: int = 50
    ) -> ChatDetailResponse:
        """Get chat with messages.
        
        Args:
            chat_id: Chat ID
            tenant_id: Tenant ID (for authorization)
            limit: Maximum number of messages to return (default: 50)
            
        Returns:
            Chat with messages
        """
        # Get chat
        chat = await self.chat_repo.get_by_id(chat_id)
        if not chat:
            raise ApiNotFoundError(
                error="Chat not found",
                message="Chat not found"
            )
        
        # Verify ownership
        if chat.tenant_id != tenant_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have access to this chat"
            )
        
        # Get messages (last N messages)
        messages = await self.message_repo.get_all_by_filter(
            chat_id=chat_id,
            order_by="created_at",
            order_desc=False,
            limit=limit,
        )
        
        return ChatDetailResponse(
            chat=ChatResponse.model_validate(chat),
            messages=[MessageResponse.model_validate(msg) for msg in messages],
        )
        
    async def _generate_title_from_message(self, message: str) -> str:
        # For now, simple truncate and prefix
        short_title = message.strip()[:15]
        return f"Chat: {short_title}..."


    async def send_message(
        self, chat_id: int, tenant_id: int, content: str
    ) -> SendMessageResponse:
        """Send a message and get AI response.
        
        Args:
            chat_id: Chat ID
            tenant_id: Tenant ID (for authorization)
            content: User message content
            
        Returns:
            User message and AI response
        """
        # Verify chat access
        chat = await self.chat_repo.get_by_id(chat_id)
        if not chat:
            raise ApiNotFoundError(
                error="Chat not found",
                message="Chat not found"
            )
        
        if chat.tenant_id != tenant_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have access to this chat"
            )
            
        if not chat.title or chat.title == "New Chat":
            new_title = await self._generate_title_from_message(content)
            await self.chat_repo.update(chat_id, {"title": new_title}, commit=True)
            
        # Save user message
        user_message_data = {
            "chat_id": chat_id,
            "role": "user",
            "content": content,
        }
        user_message = await self.message_repo.create(
            user_message_data, commit=True, refresh=True
        )
        
        logger.info(f"User message saved: chat {chat_id}")
        
        # Get conversation history for context (last 10 messages)
        history = await self.message_repo.get_all_by_filter(
            chat_id=chat_id,
            order_by="created_at",
            order_desc=False,
            limit=10,
        )
        
        # Generate AI response
        ai_response = await self.ai_service.get_response(
            agent_name=chat.agent_name,
            user_message=content,
            chat_history=history,
        )
        
        # Save assistant message
        assistant_message_data = {
            "chat_id": chat_id,
            "role": "assistant",
            "content": ai_response,
        }
        assistant_message = await self.message_repo.create(
            assistant_message_data, commit=True, refresh=True
        )
        
        # Update chat updated_at timestamp
        await self.chat_repo.update(
            chat_id,
            {"updated_at": datetime.utcnow()},
            commit=True,
        )
        
        logger.info(f" AI response saved: chat {chat_id}")
        
        return SendMessageResponse(
            user_message=MessageResponse.model_validate(user_message),
            assistant_message=MessageResponse.model_validate(assistant_message),
        )

    async def delete_chat(self, chat_id: int, tenant_id: int) -> None:
        """Delete a chat (hard delete).
        
        Args:
            chat_id: Chat ID
            tenant_id: Tenant ID (for authorization)
        """
        # Verify chat access
        chat = await self.chat_repo.get_by_id(chat_id)
        if not chat:
            raise ApiNotFoundError(
                error="Chat not found",
                message="Chat not found"
            )
        
        if chat.tenant_id != tenant_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have access to this chat"

            )
        
        # Hard delete (cascade will delete messages)
        await self.chat_repo.delete(chat)
        
        logger.info(f" Deleted chat {chat_id}")



