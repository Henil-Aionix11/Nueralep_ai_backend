"""Tenant authentication service."""

from datetime import datetime, timedelta
from typing import Dict
from fastapi import HTTPException,status
import jwt
from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.repositories.tenant_repository import TenantRepository
from app.web.settings import settings



pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")


class TenantAuthService:
    """Service for tenant authentication."""

    def __init__(self, session: AsyncSession) -> None:
        self.tenant_repo = TenantRepository(session)

    async def authenticate_tenant(self, email: str, password: str) -> Dict:
        """Authenticate tenant with email and password."""
        # Get tenant by email
        tenant = await self.tenant_repo.get_by_field("email", email)
        
        if not tenant:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password"
            )
        
        # Check if active
        if not tenant.is_active or tenant.is_deleted:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Your account has been deactivated"
            )
            
        # Check end_date validity
        if tenant.end_date and datetime.now() > tenant.end_date:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Tenant access period has expired"
            )
        
        # Verify password
        if not pwd_context.verify(password, tenant.hashed_password):
            raise HTTPException(
               status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password"
            )
        
        # Create JWT token
        token = self._create_access_token(tenant.id, tenant.email)
        
        return {
            "access_token": token,
            "token_type": "bearer",
            "tenant": {
                "id": tenant.id,
                "name": tenant.name,
                "email": tenant.email,
                "agents": [{"id": a.id, "name": a.agent_name} for a in tenant.agents]
            }
        }

    def _create_access_token(self, tenant_id: int, email: str) -> str:
        """Create JWT access token."""
        expire =  datetime.utcnow() + timedelta(days=1)
        to_encode = {
            "sub": str(tenant_id),
            "email": email,
            "type": "tenant",
            "exp": expire,
            "iat": datetime.utcnow()
        }
        return jwt.encode(to_encode, settings.secret_key, algorithm="HS256")
