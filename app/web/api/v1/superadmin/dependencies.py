"""Dependencies for superadmin routes - Hardcoded superadmin authentication."""

from fastapi import Depends, HTTPException, status, Header
from typing import Optional
from loguru import logger
import jwt
from datetime import datetime, timedelta

from app.web.settings import settings

# ==================== HARDCODED SUPERADMIN CREDENTIALS ====================

 

# ==================== JWT UTILITIES ====================

def create_superadmin_token(email: str) -> str:
    """Create JWT token for superadmin.
    
    Args:
        email: Superadmin email
        
    Returns:
        JWT token string
    """
    payload = {
        "sub": email,
        "type": "superadmin",
        "exp": datetime.utcnow() + timedelta(days=7),  # 7 days expiry
        "iat": datetime.utcnow(),
    }
    token = jwt.encode(payload, settings.secret_key, algorithm="HS256")
    return token


def verify_superadmin_token(token: str) -> dict:
    """Verify superadmin JWT token.
    
    Args:
        token: JWT token
        
    Returns:
        Decoded token payload
        
    Raises:
        HTTPException: If token is invalid
    """
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=["HS256"])
        
        # Check if it's a superadmin token
        if payload.get("type") != "superadmin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Invalid token type",
            )
        
        return payload
    
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        )


# ==================== DEPENDENCY ====================

async def get_current_superadmin(
    authorization: Optional[str] = Header(None)
) -> dict:
    """Verify current user is the hardcoded superadmin.
    
    Args:
        authorization: Authorization header with Bearer token
        
    Returns:
        Superadmin info dict
        
    Raises:
        HTTPException: If not authenticated or not superadmin
    """
    if not authorization:
        logger.warning("⚠️ Superadmin access attempt without authorization header")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header missing",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Extract token from "Bearer <token>"
    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        logger.warning("⚠️ Invalid authorization header format")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization header format",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    token = parts[1]
    
    # Verify token
    payload = verify_superadmin_token(token)
    
    # Check if email matches hardcoded superadmin
    if payload.get("sub") != settings.superadmin_email:
        logger.warning(f"⚠️ Unauthorized superadmin access attempt: {payload.get('sub')}")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. Superadmin privileges required.",
        )
    
    logger.info(f" Superadmin access granted: {settings.superadmin_email}")
    
    return {
        "email": settings.superadmin_email,
        "type": "superadmin",
    }


# ==================== AUTHENTICATION HELPER ====================

def authenticate_superadmin(email: str, password: str) -> bool:
    """Authenticate superadmin with hardcoded credentials.
    
    Args:
        email: Email
        password: Password
        
    Returns:
        True if credentials match, False otherwise
    """
    return email == settings.superadmin_email and password == settings.superadmin_password
