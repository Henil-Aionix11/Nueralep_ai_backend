"""Schemas package - exports all schema classes."""

from app.core.schema.user_schema import (
    UserRead,
    UserCreate,
    UserUpdate,
    ResendVerificationRequest,
    PasswordResetRequest,
    PasswordResetConfirm,
    UserProfileResponse,
)
from app.core.schema.tenant_schema import (
    TenantCreate,
    TenantRead,
    TenantUpdate,
)
from app.core.schema.topic_schema import (
    TopicCreate,
    TopicRead,
    TopicUpdate,
)
from app.core.schema.scenario_schema import (
    ScenarioCreate,
    ScenarioRead,
    ScenarioUpdate,
)
from app.core.schema.session_schema import (
    SessionCreate,
    SessionRead,
    SessionUpdate,
    SessionStartRequest,
    SessionEndRequest,
)
from app.core.schema.api_schema import (
    ApiResponse,
    ApiResponseResult,
    ApiResponseError,
    create_json_api_response,
)


from app.core.schema.pagination_schema import PaginationParams

__all__ = [
    # User schemas
    "UserRead",
    "UserCreate",
    "UserUpdate",
    "ResendVerificationRequest",
    "PasswordResetRequest",
    "PasswordResetConfirm",
    "UserProfileResponse",
    # Tenant schemas
    "TenantCreate",
    "TenantRead",
    "TenantUpdate",
    # Topic schemas
    "TopicCreate",
    "TopicRead",
    "TopicUpdate",
    # Scenario schemas
    "ScenarioCreate",
    "ScenarioRead",
    "ScenarioUpdate",
    # Session schemas
    "SessionCreate",
    "SessionRead",
    "SessionUpdate",
    "SessionStartRequest",
    "SessionEndRequest",
    # API schemas
    "ApiResponse",
    "ApiResponseResult",
    "ApiResponseError",
    "create_json_api_response",
    PaginationParams,
]
