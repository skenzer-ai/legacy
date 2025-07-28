"""
User models for authentication and authorization.
"""

from sqlalchemy import Column, String, Boolean, DateTime, Enum as SQLEnum, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from fastapi_users_db_sqlalchemy import SQLAlchemyBaseUserTableUUID
from fastapi_users import schemas
import uuid
from enum import Enum
from typing import Optional

from ..core.database import Base


class UserRole(str, Enum):
    """User roles for role-based access control."""
    ADMIN = "admin"
    DEVELOPER = "developer"
    VIEWER = "viewer"


class User(SQLAlchemyBaseUserTableUUID, Base):
    """
    User model extending FastAPI Users base table with additional fields.
    """
    __tablename__ = "users"
    
    # Additional fields beyond FastAPI Users base
    first_name = Column(String(50), nullable=True)
    last_name = Column(String(50), nullable=True)
    role = Column(SQLEnum(UserRole), default=UserRole.VIEWER, nullable=False)
    department = Column(String(100), nullable=True)
    preferences = Column(Text, nullable=True)  # JSON string for user preferences
    last_active = Column(DateTime(timezone=True), server_default=func.now())
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    def __repr__(self):
        return f"<User {self.email} ({self.role})>"


# Pydantic schemas for FastAPI Users
class UserRead(schemas.BaseUser[uuid.UUID]):
    """Schema for reading user data."""
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    role: UserRole
    department: Optional[str] = None
    last_active: Optional[str] = None
    created_at: Optional[str] = None


class UserCreate(schemas.BaseUserCreate):
    """Schema for creating users."""
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    role: UserRole = UserRole.VIEWER
    department: Optional[str] = None


class UserUpdate(schemas.BaseUserUpdate):
    """Schema for updating users."""
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    role: Optional[UserRole] = None
    department: Optional[str] = None
    preferences: Optional[str] = None


# For backward compatibility with existing code
UserDB = UserRead