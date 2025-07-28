#!/usr/bin/env python3
"""
Script to create the first admin user for the application.
"""
import asyncio
import sys
import os

# Add the backend directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from app.core.database import async_session_maker
from app.core.users import get_user_manager, get_user_db
from app.schemas.user import UserCreate

async def create_admin_user():
    """Create the first admin user."""
    async with async_session_maker() as session:
        try:
            # Get user database and manager
            user_db_gen = get_user_db(session)
            user_db = await user_db_gen.__anext__()
            
            user_manager_gen = get_user_manager(user_db)
            user_manager = await user_manager_gen.__anext__()
            
            # Create admin user data
            admin_data = UserCreate(
                email="admin@augment.local",
                password="admin123",  # Change this in production!
                is_superuser=True,
                is_verified=True,
                role="admin",
                first_name="System",
                last_name="Administrator",
                department="IT"
            )
            
            # Check if admin already exists
            existing_user = await user_db.get_by_email(admin_data.email)
            if existing_user:
                print(f"❌ Admin user {admin_data.email} already exists")
                return
            
            # Create the admin user
            user = await user_manager.create(admin_data)
            print(f"✅ Admin user created successfully:")
            print(f"   Email: {user.email}")
            print(f"   ID: {user.id}")
            print(f"   Role: {user.role}")
            print(f"   Is Superuser: {user.is_superuser}")
            print(f"   Is Verified: {user.is_verified}")
            
        except Exception as e:
            print(f"❌ Error creating admin user: {e}")
            raise

if __name__ == "__main__":
    print("Creating initial admin user...")
    asyncio.run(create_admin_user())
    print("Done!")