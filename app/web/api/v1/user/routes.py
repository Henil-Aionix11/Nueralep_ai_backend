"""User routes with proper separation of concerns."""

from http.client import HTTPException
from fastapi import APIRouter, Depends, Body, status
from fastapi.responses import JSONResponse
from loguru import logger

from app.core.schema.user_schema import (
    UserCreate,
    UserRead,
    UserUpdate,
    ResendVerificationRequest,
)
from app.core.services.user_service import UserService, get_user_service
from app.core.exceptions.api_exceptions import ApiNotFoundError, ApiInternalServerError
from app.web.api.v1.user.auth import auth_backend, fastapi_users
from app.core.schema.api_schema import create_json_api_response

router = APIRouter()

# ==================== FASTAPI-USERS ROUTES ====================

# Auth routes (register, login, logout)
router.include_router(
    fastapi_users.get_register_router(UserRead, UserCreate),
    prefix="/auth",
    tags=["auth"],
)

router.include_router(
    fastapi_users.get_auth_router(auth_backend, requires_verification=True),
    prefix="/auth/jwt",
    tags=["auth"],
)

# Password reset routes
router.include_router(
    fastapi_users.get_reset_password_router(),
    prefix="/auth",
    tags=["auth"],
)

# Email verification routes
router.include_router(
    fastapi_users.get_verify_router(UserRead),
    prefix="/auth",
    tags=["auth"],
)

# User management routes (get user, update user, delete user)
router.include_router(
    fastapi_users.get_users_router(UserRead, UserUpdate, requires_verification=True),
    prefix="/users",
    tags=["users"],
)

# ==================== CUSTOM ROUTES ====================


@router.post(
    "/auth/resend-verification",
    tags=["auth"],
    summary="Resend verification email",
    description="""
    Resend email verification link to user.
    
    **Public Endpoint** - No authentication required.
    """,
)
async def resend_verification_email(
    request_body: ResendVerificationRequest = Body(...),
    service: UserService = Depends(get_user_service),
) -> JSONResponse:
    """Resend verification email to user.

    Args:
        request_body: Email to resend verification to
        service: User service

    Returns:
        JSON response with success message
    """
    try:
        result = await service.resend_verification_email(request_body.email)
        logger.info(f"Verification email resent to {request_body.email}")
        return create_json_api_response(
            data=result,
            status_code=status.HTTP_200_OK,
            message="Verification email sent successfully",
        )
    except HTTPException as e:
        logger.warning(f"HTTP exception: {e.detail}")
        return create_json_api_response(
            status_code=e.status_code,
            message=str(e.detail),
            errors=[{"code": "VERIFICATION_ERROR", "message": str(e.detail)}],
        )
    except ApiNotFoundError as e:
        logger.warning(f"User not found: {e.message}")
        # Security: don't reveal if user exists
        return create_json_api_response(
            data={"message": "If email exists, you will receive a verification link"},
            status_code=status.HTTP_200_OK,
            message="Check your email",
        )
    except ApiInternalServerError as e:
        logger.error(f"Internal error: {e.message}")
        return create_json_api_response(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message="Failed to send verification email",
            errors=[{"code": "EMAIL_SEND_FAILED", "message": str(e.message)}],
        )
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return create_json_api_response(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message="Failed to send verification email",
            errors=[
                {"code": "UNEXPECTED_ERROR", "message": "An unexpected error occurred"}
            ],
        )
