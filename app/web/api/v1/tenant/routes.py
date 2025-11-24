"""Combined Tenant Authentication & Chat Routes"""

from fastapi import APIRouter, Depends, status, Query, HTTPException, UploadFile, File
from fastapi.responses import JSONResponse
from pydantic import BaseModel, EmailStr
from typing import Dict
from loguru import logger
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.schema.api_schema import create_json_api_response
from app.core.schema.chat_schema import (
    ChatCreate,
    MessageCreate,
)
from app.core.services.tenant_auth_service import TenantAuthService
from app.core.services.chat_service import ChatService
from app.core.database import get_db
from app.core.services.tenant_service import TenantService, get_tenant_service
from app.web.api.v1.tenant.dependencies import get_current_tenant

router = APIRouter(prefix="/tenant", tags=["tenant"])

# ---------------- Tenant Authentication ----------------

class TenantLoginRequest(BaseModel):
    email: EmailStr
    password: str
    
def get_chat_service(
    session: AsyncSession = Depends(get_db)
) -> ChatService:
    return ChatService(session)

@router.post("/auth/login")
async def tenant_login(
    data: TenantLoginRequest,
    session: AsyncSession = Depends(get_db),
) -> JSONResponse:
    try:
        service = TenantAuthService(session)
        result = await service.authenticate_tenant(data.email, data.password)
        logger.info(f" Tenant logged in: {data.email}")
        return create_json_api_response(
            data=result,
            status_code=status.HTTP_200_OK,
            message="Login successful",
        )
    except HTTPException as e:
        # Propagate HTTPException directly
        raise e
    except Exception as e:
        logger.error(f" Login error: {e}")
        return create_json_api_response(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message="Login failed",
            errors=[{"code": "FAILED", "message": str(e)}],
        )

# ---------------- Tenant Chat Management ----------------

@router.post("/chats")
async def create_chat(
    data: ChatCreate,
    current_tenant: Dict = Depends(get_current_tenant),
    service: ChatService = Depends(get_chat_service),
) -> JSONResponse:
    try:
       
        result = await service.create_chat(
            tenant_id=current_tenant["tenant_id"],
            data=data,
        )
        logger.info(f" Chat created: {result.id}")
        return create_json_api_response(
            data=result.model_dump(),
            status_code=status.HTTP_201_CREATED,
            message="Chat created successfully",
        )
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f" Failed to create chat: {e}")
        return create_json_api_response(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message="Failed to create chat",
            errors=[{"code": "FAILED", "message": str(e)}],
        )

@router.get("/chats")
async def list_chats(
    agent_name: str = Query(None),  # Optional filter
    limit: int = Query(10, ge=1, le=100),  # Default: recent 10
    current_tenant: Dict = Depends(get_current_tenant),
    service: ChatService = Depends(get_chat_service),
) -> JSONResponse:
    try:
        chats = await service.get_tenant_chats(
            tenant_id=current_tenant["tenant_id"],
            agent_name=agent_name,
            limit=limit,
        )
        return create_json_api_response(
            data={
                "chats": [chat.model_dump() for chat in chats],
                "total": len(chats),
            },
            status_code=status.HTTP_200_OK,
            message="Chats retrieved successfully",
        )
    except Exception as e:
        logger.error(f" Failed to list chats: {e}")
        return create_json_api_response(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message="Failed to retrieve chats",
            errors=[{"code": "FAILED", "message": str(e)}],
        )

@router.get("/chats/{chat_id}")
async def get_chat_detail(
    chat_id: int,
    limit: int = Query(50, ge=1, le=100),
    current_tenant: Dict = Depends(get_current_tenant),
   service: ChatService = Depends(get_chat_service),
) -> JSONResponse:
    try:
       
        result = await service.get_chat_detail(
            chat_id=chat_id,
            tenant_id=current_tenant["tenant_id"],
            limit=limit,
        )
        return create_json_api_response(
            data=result.model_dump(),
            status_code=status.HTTP_200_OK,
            message="Chat retrieved successfully",
        )
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f" Failed to get chat: {e}")
        return create_json_api_response(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message="Failed to retrieve chat",
            errors=[{"code": "FAILED", "message": str(e)}],
        )

@router.post("/chats/{chat_id}/messages")
async def send_message(
    chat_id: int,
    data: MessageCreate,
    current_tenant: Dict = Depends(get_current_tenant),
    service: ChatService = Depends(get_chat_service),
) -> JSONResponse:
    try:
       
        result = await service.send_message(
            chat_id=chat_id,
            tenant_id=current_tenant["tenant_id"],
            content=data.content,
        )
        return create_json_api_response(
            data=result.model_dump(),
            status_code=status.HTTP_201_CREATED,
            message="Message sent successfully",
        )
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f" Failed to send message: {e}")
        return create_json_api_response(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message="Failed to send message",
            errors=[{"code": "FAILED", "message": str(e)}],
        )

@router.delete("/chats/{chat_id}")
async def delete_chat(
    chat_id: int,
    current_tenant: Dict = Depends(get_current_tenant),
    service: ChatService = Depends(get_chat_service),
) -> JSONResponse:
    try:
       
        await service.delete_chat(
            chat_id=chat_id,
            tenant_id=current_tenant["tenant_id"],
        )
        logger.info(f" Chat deleted: {chat_id}")
        return create_json_api_response(
            status_code=status.HTTP_200_OK,
            message="Chat deleted successfully",
        )
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f" Failed to delete chat: {e}")
        return create_json_api_response(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message="Failed to delete chat",
            errors=[{"code": "FAILED", "message": str(e)}],
        )

@router.get("/agents")
async def list_agents(
    current_tenant: Dict = Depends(get_current_tenant),
    service: TenantAuthService = Depends(get_tenant_service),
) -> JSONResponse:
    """
    Get all agents assigned to the current tenant.
    """
    try:
        agents = await service.get_tenant_agents(current_tenant["tenant_id"])
        return create_json_api_response(
            data={"agents": [{"id": a.id, "name": a.agent_name} for a in agents]},
            status_code=status.HTTP_200_OK,
            message="Agents retrieved successfully",
        )
    except Exception as e:
        logger.error(f"❌ Failed to get agents: {e}")
        return create_json_api_response(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message="Failed to retrieve agents",
            errors=[{"code": "FAILED", "message": str(e)}],
        )

# ---------------- Dataset Upload & Preview ----------------

@router.post("/dataset/upload")
async def upload_dataset(
    file: UploadFile = File(...),
    current_tenant: Dict = Depends(get_current_tenant),
    service: TenantService = Depends(get_tenant_service),
) -> JSONResponse:
    """
    Upload or replace the current tenant dataset (CSV/XLSX).
    """
    try:
        result = await service.upload_dataset(
            tenant_id=current_tenant["tenant_id"], upload_file=file
        )
        return create_json_api_response(
            data=result,
            status_code=status.HTTP_201_CREATED,
            message="Dataset uploaded successfully",
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to upload dataset: {e}")
        return create_json_api_response(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message="Failed to upload dataset",
            errors=[{"code": "FAILED", "message": str(e)}],
        )


@router.get("/dataset/preview")
async def get_dataset_preview(
    current_tenant: Dict = Depends(get_current_tenant),
    service: TenantService = Depends(get_tenant_service),
) -> JSONResponse:
    """
    Fetch stored dataset metadata & preview rows.
    """
    try:
        result = await service.get_dataset_preview(
            tenant_id=current_tenant["tenant_id"]
        )
        return create_json_api_response(
            data=result,
            status_code=status.HTTP_200_OK,
            message="Dataset preview retrieved successfully",
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to fetch dataset preview: {e}")
        return create_json_api_response(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message="Failed to retrieve dataset preview",
            errors=[{"code": "FAILED", "message": str(e)}],
        )
