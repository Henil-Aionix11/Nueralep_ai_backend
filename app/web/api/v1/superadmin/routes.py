"""Superadmin routes for tenant management."""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from loguru import logger
from pydantic import BaseModel, EmailStr

from app.core.services.superadmin_service import (
    SuperadminService,
    get_superadmin_service,
)
from app.core.schema.tenant_schema import TenantCreate,TenantUpdateByAdmin
from app.core.schema.api_schema import create_json_api_response
from app.core.exceptions.api_exceptions import (
    ApiNotFoundError,
    ApiConflictError,
)
from app.web.api.v1.superadmin.dependencies import get_current_superadmin,authenticate_superadmin, create_superadmin_token
 


router = APIRouter(prefix="/superadmin", tags=["superadmin"])

class SuperadminLoginRequest(BaseModel):
    email: EmailStr
    password: str

# === Superadmin Auth Route ===
@router.post(
    "/auth/login",
    status_code=status.HTTP_200_OK,
    summary="Superadmin login",
    description="Login as superadmin with hardcoded credentials.",
)
async def superadmin_login(
    login_data: SuperadminLoginRequest,
) -> JSONResponse:
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

@router.post(
    "/tenants",
    status_code=status.HTTP_201_CREATED,
    summary="Create new tenant",
)
async def create_tenant(
    tenant_data: TenantCreate,
    current_superadmin: dict = Depends(get_current_superadmin),  # 🔒 Protected
    service: SuperadminService = Depends(get_superadmin_service),
) -> JSONResponse:
    """Create a new tenant with agents."""
    try:
        result = await service.create_tenant(tenant_data)
        logger.info(
            f" Superadmin {current_superadmin['email']} created tenant: {result['name']}"
        )

        return create_json_api_response(
            data=result,
            status_code=status.HTTP_201_CREATED,
            message="Tenant created successfully",
        )

    except ApiConflictError as e:
        return create_json_api_response(
            status_code=status.HTTP_409_CONFLICT,
            message=e.message,
            errors=[{"code": "CONFLICT", "message": e.message}],
        )
    except Exception as e:
        logger.error(f" Failed to create tenant: {e}")
        return create_json_api_response(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message="Failed to create tenant",
            errors=[{"code": "FAILED", "message": str(e)}],
        )


@router.get(
    "/tenants",
    status_code=status.HTTP_200_OK,
    summary="List all tenants",
)
async def list_tenants(
    current_superadmin: dict = Depends(get_current_superadmin),  # 🔒 Protected
    service: SuperadminService = Depends(get_superadmin_service),
) -> JSONResponse:
    """List all active tenants."""
    try:
        tenants = await service.get_all_tenants()

        return create_json_api_response(
            data={"tenants": tenants, "total": len(tenants)},
            status_code=status.HTTP_200_OK,
            message="Tenants retrieved successfully",
        )

    except Exception as e:
        logger.error(f" Failed to list tenants: {e}")
        return create_json_api_response(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message="Failed to retrieve tenants",
            errors=[{"code": "FAILED", "message": str(e)}],
        )


@router.get(
    "/tenants/{tenant_id}",
    status_code=status.HTTP_200_OK,
    summary="Get tenant details",
)
async def get_tenant_details(
    tenant_id: int,
    current_superadmin: dict = Depends(get_current_superadmin),  # 🔒 Protected
    service: SuperadminService = Depends(get_superadmin_service),
) -> JSONResponse:
    """Get tenant details by ID."""
    try:
        result = await service.get_tenant_by_id(tenant_id)

        return create_json_api_response(
            data=result,
            status_code=status.HTTP_200_OK,
            message="Tenant retrieved successfully",
        )

    except ApiNotFoundError as e:
        return create_json_api_response(
            status_code=status.HTTP_404_NOT_FOUND,
            message=e.message,
            errors=[{"code": "NOT_FOUND", "message": e.message}],
        )
    except Exception as e:
        logger.error(f" Failed to get tenant details: {e}")
        return create_json_api_response(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message="Failed to retrieve tenant details",
            errors=[{"code": "FAILED", "message": str(e)}],
        )


@router.delete(
    "/tenants/{tenant_id}",
    status_code=status.HTTP_200_OK,
    summary="Delete tenant",
)
async def delete_tenant(
    tenant_id: int,
    current_superadmin: dict = Depends(get_current_superadmin),  # 🔒 Protected
    service: SuperadminService = Depends(get_superadmin_service),
) -> JSONResponse:
    """Delete tenant (soft delete)."""
    try:
        await service.soft_delete_tenant(tenant_id)
        logger.info(f" Superadmin deleted tenant {tenant_id}")

        return create_json_api_response(
            status_code=status.HTTP_200_OK,
            message="Tenant deleted successfully",
        )

    except ApiNotFoundError as e:
        return create_json_api_response(
            status_code=status.HTTP_404_NOT_FOUND,
            message=e.message,
            errors=[{"code": "NOT_FOUND", "message": e.message}],
        )
    except Exception as e:
        logger.error(f" Failed to delete tenant: {e}")
        return create_json_api_response(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message="Failed to delete tenant",
            errors=[{"code": "FAILED", "message": str(e)}],
        )


@router.patch(
    "/tenants/{tenant_id}",
    status_code=status.HTTP_200_OK,
    summary="Update tenant",
    description="Update tenant name, country, status, and agents.",
)
async def update_tenant(
    tenant_id: int,
    update_data: TenantUpdateByAdmin,
    current_superadmin: dict = Depends(get_current_superadmin),  # 🔒 Protected
    service: SuperadminService = Depends(get_superadmin_service),
) -> JSONResponse:
    """Update tenant information."""
    try:
        # Convert to dict and exclude unset fields
        update_dict = update_data.model_dump(exclude_unset=True)
        
        result = await service.update_tenant(tenant_id, update_dict)
        logger.info(
            f" Superadmin {current_superadmin['email']} updated tenant: {tenant_id}"
        )

        return create_json_api_response(
            data=result,
            status_code=status.HTTP_200_OK,
            message="Tenant updated successfully",
        )

    except ApiNotFoundError as e:
        return create_json_api_response(
            status_code=status.HTTP_404_NOT_FOUND,
            message=e.message,
            errors=[{"code": "NOT_FOUND", "message": e.message}],
        )
    except Exception as e:
        logger.error(f" Failed to update tenant: {e}")
        return create_json_api_response(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message="Failed to update tenant",
            errors=[{"code": "FAILED", "message": str(e)}],
        )