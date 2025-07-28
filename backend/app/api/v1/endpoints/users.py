"""
User management routes using FastAPI Users.
Based on latest FastAPI Users 14.0.1 best practices.
"""
from fastapi import APIRouter

from app.core.auth import fastapi_users
from app.schemas.user import UserRead, UserUpdate

router = APIRouter()

# User Management Routes
router.include_router(
    fastapi_users.get_users_router(UserRead, UserUpdate),
    prefix="",
    tags=["users"],
)