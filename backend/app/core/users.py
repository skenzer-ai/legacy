"""
User management for FastAPI Users authentication system.
Based on latest FastAPI Users 14.0.1 best practices.
"""
import uuid
from typing import Optional

from fastapi import Depends, Request
from fastapi_users import BaseUserManager, UUIDIDMixin
from fastapi_users.db import SQLAlchemyUserDatabase

from app.core.config import settings
from app.core.database import get_async_session
from app.models.user import User


class UserManager(UUIDIDMixin, BaseUserManager[User, uuid.UUID]):
    """User manager for handling authentication logic."""
    
    reset_password_token_secret = settings.secret_key
    verification_token_secret = settings.secret_key
    
    async def on_after_register(self, user: User, request: Optional[Request] = None):
        """Called after a user registers."""
        print(f"User {user.id} has registered with email {user.email}")
    
    async def on_after_forgot_password(
        self, user: User, token: str, request: Optional[Request] = None
    ):
        """Called after a user requests password reset."""
        print(f"User {user.id} has forgot their password. Reset token: {token}")
    
    async def on_after_request_verify(
        self, user: User, token: str, request: Optional[Request] = None
    ):
        """Called after a user requests verification."""
        print(f"Verification requested for user {user.id}. Verification token: {token}")


async def get_user_db(session = Depends(get_async_session)):
    """Get the user database adapter."""
    yield SQLAlchemyUserDatabase(session, User)


async def get_user_manager(user_db: SQLAlchemyUserDatabase = Depends(get_user_db)):
    """Get the user manager."""
    yield UserManager(user_db)