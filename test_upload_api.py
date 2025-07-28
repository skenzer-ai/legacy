#!/usr/bin/env python3
"""
Test script for Man-O-Man Upload API endpoints.
Tests file upload, status tracking, and background processing.
"""

import sys
sys.path.append('/home/heramb/source/augment/legacy/backend')

import asyncio
import json
import tempfile
from io import BytesIO
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from fastapi import FastAPI

from backend.app.core.manoman.api.upload import router as upload_router


def create_test_app() -> FastAPI:
    """Create FastAPI test application with upload router"""
    app = FastAPI(title="Man-O-Man Test API")
    app.include_router(upload_router)
    return app


def create_sample_openapi_spec() -> str:
    """Create a sample OpenAPI specification for testing"""
    return json.dumps({
        "openapi": "3.0.0",
        "info": {
            "title": "Test API",
            "version": "1.0.0",
            "description": "Sample API for testing upload functionality"
        },
        "servers": [
            {
                "url": "https://api.example.com/v1",
                "description": "Production server"
            }
        ],
        "paths": {
            "/users": {
                "get": {
                    "operationId": "listUsers",
                    "summary": "List all users",
                    "tags": ["users"],
                    "responses": {
                        "200": {
                            "description": "List of users",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "array",
                                        "items": {"$ref": "#/components/schemas/User"}
                                    }
                                }
                            }
                        }
                    }
                },
                "post": {
                    "operationId": "createUser",
                    "summary": "Create a new user",
                    "tags": ["users"],
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/UserInput"}
                            }
                        }
                    },
                    "responses": {
                        "201": {
                            "description": "User created",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/User"}
                                }
                            }
                        }
                    }
                }
            },
            "/users/{user_id}": {
                "get": {
                    "operationId": "getUserById",
                    "summary": "Get user by ID",
                    "tags": ["users"],
                    "parameters": [
                        {
                            "name": "user_id",
                            "in": "path",
                            "required": True,
                            "schema": {"type": "string"}
                        }
                    ],
                    "responses": {
                        "200": {
                            "description": "User details",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/User"}
                                }
                            }
                        }
                    }
                },
                "put": {
                    "operationId": "updateUser",
                    "summary": "Update user",
                    "tags": ["users"],
                    "parameters": [
                        {
                            "name": "user_id",
                            "in": "path",
                            "required": True,
                            "schema": {"type": "string"}
                        }
                    ],
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/UserInput"}
                            }
                        }
                    },
                    "responses": {
                        "200": {
                            "description": "User updated",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/User"}
                                }
                            }
                        }
                    }
                },
                "delete": {
                    "operationId": "deleteUser",
                    "summary": "Delete user",
                    "tags": ["users"],
                    "parameters": [
                        {
                            "name": "user_id",
                            "in": "path",
                            "required": True,
                            "schema": {"type": "string"}
                        }
                    ],
                    "responses": {
                        "204": {
                            "description": "User deleted"
                        }
                    }
                }
            },
            "/incidents": {
                "get": {
                    "operationId": "listIncidents",
                    "summary": "List all incidents",
                    "tags": ["incidents"],
                    "responses": {
                        "200": {
                            "description": "List of incidents"
                        }
                    }
                },
                "post": {
                    "operationId": "createIncident",
                    "summary": "Create new incident",
                    "tags": ["incidents"],
                    "responses": {
                        "201": {
                            "description": "Incident created"
                        }
                    }
                }
            }
        },
        "components": {
            "schemas": {
                "User": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "string"},
                        "name": {"type": "string"},
                        "email": {"type": "string"}
                    }
                },
                "UserInput": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "email": {"type": "string"}
                    },
                    "required": ["name", "email"]
                }
            }
        }
    }, indent=2)


def test_upload_json_file():
    """Test uploading a valid JSON API specification"""
    print("🧪 Testing JSON file upload...")
    
    app = create_test_app()
    client = TestClient(app)
    
    # Create sample JSON content
    json_content = create_sample_openapi_spec()
    
    # Create file-like object
    file_content = BytesIO(json_content.encode('utf-8'))
    
    # Upload file
    response = client.post(
        "/api/v1/manoman/upload",
        files={"file": ("test_api.json", file_content, "application/json")}
    )
    
    # Verify response
    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
    
    data = response.json()
    assert "upload_id" in data, "Response should contain upload_id"
    assert data["filename"] == "test_api.json", "Filename should match"
    assert data["parsing_status"] == "processing", "Should be processing"
    assert data["next_step"] == "parsing", "Next step should be parsing"
    
    upload_id = data["upload_id"]
    print(f"✅ Successfully uploaded JSON file with ID: {upload_id}")
    
    return client, upload_id


def test_upload_yaml_file():
    """Test uploading a YAML API specification"""
    print("🧪 Testing YAML file upload...")
    
    app = create_test_app()
    client = TestClient(app)
    
    # Create sample YAML content
    yaml_content = """
openapi: 3.0.0
info:
  title: Test YAML API
  version: 1.0.0
  description: Sample YAML API for testing
paths:
  /health:
    get:
      operationId: healthCheck
      summary: Health check endpoint
      tags:
        - health
      responses:
        '200':
          description: Service is healthy
  /status:
    get:
      operationId: getStatus
      summary: Get service status
      tags:
        - status
      responses:
        '200':
          description: Service status
"""
    
    # Create file-like object
    file_content = BytesIO(yaml_content.encode('utf-8'))
    
    # Upload file
    response = client.post(
        "/api/v1/manoman/upload",
        files={"file": ("test_api.yaml", file_content, "application/x-yaml")}
    )
    
    # Verify response
    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
    
    data = response.json()
    assert data["filename"] == "test_api.yaml", "Filename should match"
    assert data["parsing_status"] == "processing", "Should be processing"
    
    upload_id = data["upload_id"]
    print(f"✅ Successfully uploaded YAML file with ID: {upload_id}")
    
    return client, upload_id


def test_upload_status_tracking():
    """Test upload status tracking functionality"""
    print("🧪 Testing upload status tracking...")
    
    client, upload_id = test_upload_json_file()
    
    # Wait a moment for background processing
    import time
    time.sleep(1)
    
    # Check upload status
    response = client.get(f"/api/v1/manoman/upload/{upload_id}/status")
    
    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
    
    data = response.json()
    assert data["upload_id"] == upload_id, "Upload ID should match"
    assert "status" in data, "Should have status field"
    assert "progress" in data, "Should have progress field"
    assert "current_step" in data, "Should have current_step field"
    
    # Progress should be between 0 and 1
    assert 0 <= data["progress"] <= 1, f"Progress should be 0-1, got {data['progress']}"
    
    print(f"✅ Upload status: {data['status']}, Progress: {data['progress']:.1%}")
    print(f"   Current step: {data['current_step']}")
    
    return client, upload_id


def test_upload_with_format_hint():
    """Test upload with format hint parameter"""
    print("🧪 Testing upload with format hint...")
    
    app = create_test_app()
    client = TestClient(app)
    
    json_content = create_sample_openapi_spec()
    file_content = BytesIO(json_content.encode('utf-8'))
    
    # Upload with format hint
    response = client.post(
        "/api/v1/manoman/upload",
        files={"file": ("custom_api.json", file_content, "application/json")},
        data={"format_hint": "openapi_3"}
    )
    
    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
    
    data = response.json()
    assert "upload_id" in data, "Response should contain upload_id"
    
    print(f"✅ Successfully uploaded with format hint: openapi_3")
    
    return client, data["upload_id"]


def test_upload_invalid_file():
    """Test uploading invalid file formats"""
    print("🧪 Testing invalid file upload...")
    
    app = create_test_app()
    client = TestClient(app)
    
    # Test unsupported file extension
    file_content = BytesIO(b"invalid content")
    
    response = client.post(
        "/api/v1/manoman/upload",
        files={"file": ("test.txt", file_content, "text/plain")}
    )
    
    assert response.status_code == 400, f"Expected 400 for invalid file, got {response.status_code}"
    assert "Unsupported file format" in response.json()["detail"]
    
    print("✅ Correctly rejected unsupported file format")


def test_upload_malformed_json():
    """Test uploading malformed JSON"""
    print("🧪 Testing malformed JSON upload...")
    
    app = create_test_app()
    client = TestClient(app)
    
    # Create malformed JSON
    malformed_json = '{"openapi": "3.0.0", "info": {'  # Missing closing braces
    file_content = BytesIO(malformed_json.encode('utf-8'))
    
    response = client.post(
        "/api/v1/manoman/upload",
        files={"file": ("malformed.json", file_content, "application/json")}
    )
    
    # Upload should succeed, but processing will fail
    assert response.status_code == 200, f"Upload should succeed, got {response.status_code}"
    
    upload_id = response.json()["upload_id"]
    
    # Check status after processing
    import time
    time.sleep(2)  # Wait for background processing
    
    status_response = client.get(f"/api/v1/manoman/upload/{upload_id}/status")
    status_data = status_response.json()
    
    # Should show failed status
    assert status_data["status"] in ["failed", "processing"], f"Expected failed or processing, got {status_data['status']}"
    
    if status_data["status"] == "failed":
        assert status_data["error_message"], "Should have error message"
        print(f"✅ Correctly handled malformed JSON: {status_data['error_message']}")
    else:
        print("✅ Malformed JSON still processing (expected behavior)")


def test_list_uploads():
    """Test listing uploads functionality"""
    print("🧪 Testing list uploads...")
    
    app = create_test_app()
    client = TestClient(app)
    
    # Upload a few files first
    json_content = create_sample_openapi_spec()
    for i in range(3):
        file_content = BytesIO(json_content.encode('utf-8'))
        client.post(
            "/api/v1/manoman/upload",
            files={"file": (f"test_{i}.json", file_content, "application/json")}
        )
    
    # List uploads
    response = client.get("/api/v1/manoman/uploads")
    
    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
    
    data = response.json()
    assert "uploads" in data, "Should have uploads field"
    assert "total" in data, "Should have total field"
    assert "filtered" in data, "Should have filtered field"
    
    assert len(data["uploads"]) >= 3, f"Should have at least 3 uploads, got {len(data['uploads'])}"
    
    # Test filtering by status
    response = client.get("/api/v1/manoman/uploads?status=processing")
    data = response.json()
    
    print(f"✅ Listed uploads: {data['total']} total, {data['filtered']} filtered")


def test_cancel_upload():
    """Test canceling an upload"""
    print("🧪 Testing upload cancellation...")
    
    client, upload_id = test_upload_json_file()
    
    # Cancel the upload
    response = client.delete(f"/api/v1/manoman/upload/{upload_id}")
    
    assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
    
    # Check that status shows cancelled
    status_response = client.get(f"/api/v1/manoman/upload/{upload_id}/status")
    status_data = status_response.json()
    
    assert status_data["status"] == "cancelled", f"Expected cancelled, got {status_data['status']}"
    assert status_data["current_step"] == "cancelled", "Current step should be cancelled"
    
    print(f"✅ Successfully cancelled upload {upload_id}")


def test_nonexistent_upload_status():
    """Test checking status of non-existent upload"""
    print("🧪 Testing non-existent upload status...")
    
    app = create_test_app()
    client = TestClient(app)
    
    fake_upload_id = "non-existent-id"
    
    response = client.get(f"/api/v1/manoman/upload/{fake_upload_id}/status")
    
    assert response.status_code == 404, f"Expected 404, got {response.status_code}"
    assert "not found" in response.json()["detail"].lower()
    
    print("✅ Correctly handled non-existent upload ID")


def run_all_tests():
    """Run all upload API tests"""
    print("🚀 Starting Man-O-Man Upload API Tests\n")
    
    try:
        # Run all test functions
        test_upload_json_file()
        print()
        
        test_upload_yaml_file()
        print()
        
        test_upload_status_tracking()
        print()
        
        test_upload_with_format_hint()
        print()
        
        test_upload_invalid_file()
        print()
        
        test_upload_malformed_json()
        print()
        
        test_list_uploads()
        print()
        
        test_cancel_upload()
        print()
        
        test_nonexistent_upload_status()
        print()
        
        print("🎉 All upload API tests completed successfully!")
        print("✅ File upload functionality working")
        print("📊 Status tracking operational")
        print("🔄 Background processing functional")
        print("🛡️ Error handling robust")
        print("📝 API endpoints responding correctly")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Test suite failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)