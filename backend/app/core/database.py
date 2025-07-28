"""
Database configuration and session management for Augment platform.

This module provides async SQLAlchemy setup with PostgreSQL backend,
session management, and database connection utilities.
"""

from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.pool import NullPool
import os
from .config import settings

# Create the SQLAlchemy engine
if settings.environment == "testing":
    # Use SQLite for testing
    DATABASE_URL = "sqlite+aiosqlite:///./test.db"
    engine = create_async_engine(
        DATABASE_URL, 
        poolclass=NullPool,
        echo=settings.debug
    )
else:
    # Use PostgreSQL for development and production
    engine = create_async_engine(
        settings.database_url,
        echo=settings.debug,
        pool_size=20,
        max_overflow=0,
    )

# Create async session factory
async_session_maker = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=True,
    autocommit=False,
)

# Create base class for models
Base = declarative_base()


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency to get async database session.
    
    Yields:
        AsyncSession: Database session for async operations
    """
    async with async_session_maker() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def create_db_and_tables():
    """
    Create database and all tables.
    Used for initialization and testing.
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def drop_db_and_tables():
    """
    Drop all tables and database.
    Used for testing cleanup.
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


# Database dependency for FastAPI
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency for database sessions."""
    async for session in get_async_session():
        yield session