"""
Authentication routes using FastAPI Users.
Based on latest FastAPI Users 14.0.1 best practices.
"""
from fastapi import APIRouter

from app.core.auth import fastapi_users, jwt_backend, cookie_backend
from app.schemas.user import UserCreate, UserRead

router = APIRouter()

# JWT Authentication Routes
router.include_router(
    fastapi_users.get_auth_router(jwt_backend),
    prefix="/jwt",
    tags=["auth-jwt"],
)

# Cookie Authentication Routes  
router.include_router(
    fastapi_users.get_auth_router(cookie_backend),
    prefix="/cookie",
    tags=["auth-cookie"],
)

# Registration Routes
router.include_router(
    fastapi_users.get_register_router(UserRead, UserCreate),
    prefix="",
    tags=["auth"],
)

# Password Reset Routes
router.include_router(
    fastapi_users.get_reset_password_router(),
    prefix="",
    tags=["auth"],
)

# Email Verification Routes
router.include_router(
    fastapi_users.get_verify_router(UserRead),
    prefix="",
    tags=["auth"],
)