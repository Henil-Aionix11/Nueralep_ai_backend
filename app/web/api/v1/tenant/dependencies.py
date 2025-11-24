"""Tenant authentication dependencies."""

from typing import Dict
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from loguru import logger

from app.web.settings import settings




security = HTTPBearer()


async def get_current_tenant(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> Dict:
    """Verify tenant JWT token and return tenant info.
    
    Args:
        credentials: HTTP Authorization credentials
        
    Returns:
        Dict with tenant_id and email
        
    Raises:
        HTTPException: If token is invalid or expired
    """
    token = credentials.credentials
    
    try:
        # Decode JWT token
        payload = jwt.decode(token, settings.secret_key, algorithms='HS256"')
        
        # Verify it's a tenant token
        if payload.get("type") != "tenant":
            raise HTTPException(
               status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type"
            )
        
        tenant_id = int(payload.get("sub"))
        email = payload.get("email")
        
        if not tenant_id or not email:
            raise HTTPException(
                 status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password"
            )
        
        logger.debug(f"🔐 Authenticated tenant: {tenant_id}")
        
        return {
            "tenant_id": tenant_id,
            "email": email,
        }
        
    except jwt.ExpiredSignatureError:
        logger.warning("⚠️ Expired token")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
        )
    except jwt.InvalidTokenError as e:
        logger.warning(f"⚠️ Invalid token: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        )
    except Exception as e:
        logger.error(f" Token validation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
        )
