"""
User schemas for FastAPI Users authentication system.
Based on latest FastAPI Users 14.0.1 best practices.
"""
import uuid
from typing import Optional

from fastapi_users import schemas


class UserRead(schemas.BaseUser[uuid.UUID]):
    """Schema for reading user data (responses)."""
    id: uuid.UUID
    email: str
    is_active: bool = True
    is_superuser: bool = False
    is_verified: bool = False
    
    # Custom fields for our application
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    role: str = "viewer"  # admin, developer, viewer
    department: Optional[str] = None


class UserCreate(schemas.BaseUserCreate):
    """Schema for creating new users."""
    email: str
    password: str
    is_active: Optional[bool] = True
    is_superuser: Optional[bool] = False
    is_verified: Optional[bool] = False
    
    # Custom fields
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    role: Optional[str] = "viewer"
    department: Optional[str] = None


class UserUpdate(schemas.BaseUserUpdate):
    """Schema for updating existing users."""
    password: Optional[str] = None
    email: Optional[str] = None
    is_active: Optional[bool] = None
    is_superuser: Optional[bool] = None
    is_verified: Optional[bool] = None
    
    # Custom fields
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    role: Optional[str] = None
    department: Optional[str] = None