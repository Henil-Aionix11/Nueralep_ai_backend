"""Superadmin authentication routes."""

from fastapi import APIRouter, status, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, EmailStr
from loguru import logger

from app.web.api.v1.superadmin.dependencies import (
    authenticate_superadmin,
    create_superadmin_token,
)
from app.core.schema.api_schema import create_json_api_response

router = APIRouter(prefix="/superadmin/auth", tags=["superadmin-auth"])


class SuperadminLoginRequest(BaseModel):
    """Superadmin login request schema."""
    email: EmailStr
    password: str


@router.post(
    "/login",
    status_code=status.HTTP_200_OK,
    summary="Superadmin login",
    description="Login as superadmin with hardcoded credentials.",
)
async def superadmin_login(
    login_data: SuperadminLoginRequest,
) -> JSONResponse:
    """Superadmin login endpoint.
    
    Args:
        login_data: Email and password
        
    Returns:
        JWT token for superadmin
    """
    # Authenticate
    if not authenticate_superadmin(login_data.email, login_data.password):
        logger.warning(f" Failed superadmin login attempt: {login_data.email}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )
    
    # Create token
    token = create_superadmin_token(login_data.email)
    
    logger.info(f" Superadmin logged in: {login_data.email}")
    
    return create_json_api_response(
        data={
            "access_token": token,
            "token_type": "bearer",
            "email": login_data.email,
        },
        status_code=status.HTTP_200_OK,
        message="Superadmin logged in successfully",
    )
