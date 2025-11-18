"""FastAPI-Users authentication setup."""

from fastapi_users.authentication import (
    AuthenticationBackend,
    BearerTransport,
    JWTStrategy,
)
from fastapi_users import FastAPIUsers

from app.core.models.user_model import User
from app.web.api.v1.user.user_manager import get_user_manager
from app.web.settings import settings

# Bearer transport for JWT tokens
bearer_transport = BearerTransport(tokenUrl="auth/jwt/login")


def get_jwt_strategy() -> JWTStrategy:
    """Get JWT strategy with token secret and lifetime.

    Returns:
        JWTStrategy instance
    """
    return JWTStrategy(
        secret=settings.secret_key,
        lifetime_seconds=settings.access_token_expire_seconds,  # 7 days
    )


# Define authentication backend
auth_backend = AuthenticationBackend(
    name="jwt",
    transport=bearer_transport,
    get_strategy=get_jwt_strategy,
)

# Initialize FastAPI-Users
fastapi_users = FastAPIUsers[User, int](
    get_user_manager,
    [auth_backend],
)

# Current user dependency
current_user = fastapi_users.current_user(optional=False)
current_user_optional = fastapi_users.current_user(optional=True)
