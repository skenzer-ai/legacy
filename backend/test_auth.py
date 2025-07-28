#!/usr/bin/env python3
"""
Test script for FastAPI Users authentication system.
"""
import asyncio
import httpx
import json

async def test_authentication():
    """Test the authentication endpoints."""
    base_url = "http://localhost:8000/api/v1"
    
    async with httpx.AsyncClient() as client:
        try:
            # Test health endpoint
            response = await client.get("http://localhost:8000/")
            print(f"✅ Health check: {response.status_code} - {response.json()}")
            
            # Test login with admin user
            login_data = {
                "username": "admin@augment.local",  # FastAPI Users expects 'username' field
                "password": "admin123"
            }
            
            print("🔐 Testing JWT login...")
            response = await client.post(f"{base_url}/auth/jwt/login", data=login_data)
            if response.status_code == 200:
                token_data = response.json()
                print(f"✅ JWT Login successful: {token_data['token_type']}")
                access_token = token_data["access_token"]
                
                # Test authenticated endpoint
                headers = {"Authorization": f"Bearer {access_token}"}
                response = await client.get(f"{base_url}/users/me", headers=headers)
                if response.status_code == 200:
                    user_data = response.json()
                    print(f"✅ User info retrieved: {user_data['email']} (role: {user_data['role']})")
                else:
                    print(f"❌ Failed to get user info: {response.status_code}")
            else:
                print(f"❌ JWT Login failed: {response.status_code} - {response.text}")
                
            print("🍪 Testing Cookie login...")
            response = await client.post(f"{base_url}/auth/cookie/login", data=login_data)
            if response.status_code == 200:
                print(f"✅ Cookie Login successful")
                
                # Test authenticated endpoint with cookies
                response = await client.get(f"{base_url}/users/me")
                if response.status_code == 200:
                    user_data = response.json()
                    print(f"✅ User info via cookie: {user_data['email']} (role: {user_data['role']})")
                else:
                    print(f"❌ Failed to get user info via cookie: {response.status_code}")
            else:
                print(f"❌ Cookie Login failed: {response.status_code} - {response.text}")
                
        except Exception as e:
            print(f"❌ Error: {e}")

if __name__ == "__main__":
    print("Testing FastAPI Users authentication endpoints...")
    print("Make sure the server is running with: uvicorn app.main:app --reload")
    print()
    asyncio.run(test_authentication())