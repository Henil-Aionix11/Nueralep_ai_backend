"""Schemas package - exports all schema classes."""

from app.core.schema.tenant_schema import (
    TenantCreate,
    TenantRead,
    TenantUpdate,
)

from app.core.schema.api_schema import (
    ApiResponse,
    ApiResponseResult,
    ApiResponseError,
    create_json_api_response,
)


from app.core.schema.pagination_schema import PaginationParams

__all__ = [
    # Tenant schemas
    "TenantCreate",
    "TenantRead",
    "TenantUpdate",
    # API schemas
    "ApiResponse",
    "ApiResponseResult",
    "ApiResponseError",
    "create_json_api_response",
    PaginationParams,
]
