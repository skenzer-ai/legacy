"""
Authentication configuration for FastAPI Users.
Based on latest FastAPI Users 14.0.1 best practices with JWT and Cookie auth.
"""
import uuid
from fastapi_users import FastAPIUsers
from fastapi_users.authentication import (
    AuthenticationBackend,
    BearerTransport,
    CookieTransport,
    JWTStrategy,
)

from app.core.config import settings
from app.core.users import get_user_manager
from app.models.user import User

# JWT Authentication Transport (for API access)
bearer_transport = BearerTransport(tokenUrl="auth/jwt/login")

def get_jwt_strategy() -> JWTStrategy:
    """Get JWT strategy for authentication."""
    return JWTStrategy(
        secret=settings.secret_key, 
        lifetime_seconds=settings.access_token_expire_minutes * 60,
        algorithm=settings.algorithm
    )

# JWT Authentication Backend
jwt_backend = AuthenticationBackend(
    name="jwt",
    transport=bearer_transport,
    get_strategy=get_jwt_strategy,
)

# Cookie Authentication Transport (for web interface)
cookie_transport = CookieTransport(
    cookie_name="augmentauth",
    cookie_max_age=settings.access_token_expire_minutes * 60,
    cookie_secure=settings.environment == "production",
    cookie_httponly=True,
    cookie_samesite="lax"
)

# Cookie Authentication Backend
cookie_backend = AuthenticationBackend(
    name="cookie",
    transport=cookie_transport,
    get_strategy=get_jwt_strategy,  # Same JWT strategy for both
)

# FastAPI Users instance
fastapi_users = FastAPIUsers[User, uuid.UUID](
    get_user_manager,
    [jwt_backend, cookie_backend],  # Support both authentication methods
)

# Current user dependencies
current_active_user = fastapi_users.current_user(active=True)
current_active_verified_user = fastapi_users.current_user(active=True, verified=True)
current_superuser = fastapi_users.current_user(active=True, superuser=True)

# Role-based dependencies
def current_admin_user():
    """Dependency for admin users."""
    def check_admin(user: User = current_active_user):
        if user.role != "admin":
            from fastapi import HTTPException, status
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Admin access required"
            )
        return user
    return check_admin

def current_developer_user():
    """Dependency for developer+ users."""
    def check_developer(user: User = current_active_user):
        if user.role not in ["admin", "developer"]:
            from fastapi import HTTPException, status
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Developer access required"
            )
        return user
    return check_developer