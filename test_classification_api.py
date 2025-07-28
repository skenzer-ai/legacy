#!/usr/bin/env python3
"""
Test script for Man-O-Man Classification API endpoints.
Tests service classification, merge/split operations, and conflict detection.
"""

import sys
sys.path.append('/home/heramb/source/augment/legacy/backend')

import asyncio
import json
import time
from io import BytesIO

import pytest
from fastapi.testclient import TestClient
from fastapi import FastAPI

from backend.app.core.manoman.api.upload import router as upload_router
from backend.app.core.manoman.api.classification import router as classification_router


def create_test_app() -> FastAPI:
    """Create FastAPI test application with both routers"""
    app = FastAPI(title="Man-O-Man Test API")
    app.include_router(upload_router, prefix="/api/v1/manoman")
    app.include_router(classification_router, prefix="/api/v1/manoman")
    return app


def create_sample_openapi_spec() -> str:
    """Create a sample OpenAPI specification for testing classification"""
    return json.dumps({
        "openapi": "3.0.0",
        "info": {
            "title": "Test Classification API",
            "version": "1.0.0",
            "description": "Sample API for testing classification functionality"
        },
        "paths": {
            "/users": {
                "get": {
                    "operationId": "listUsers",
                    "summary": "List all users",
                    "tags": ["users"],
                    "responses": {"200": {"description": "List of users"}}
                },
                "post": {
                    "operationId": "createUser",
                    "summary": "Create a new user",
                    "tags": ["users"],
                    "responses": {"201": {"description": "User created"}}
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
                    "responses": {"200": {"description": "User details"}}
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
                    "responses": {"200": {"description": "User updated"}}
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
                    "responses": {"204": {"description": "User deleted"}}
                }
            },
            "/incidents": {
                "get": {
                    "operationId": "listIncidents",
                    "summary": "List all incidents",
                    "tags": ["incidents"],
                    "responses": {"200": {"description": "List of incidents"}}
                },
                "post": {
                    "operationId": "createIncident",
                    "summary": "Create new incident",
                    "tags": ["incidents"],
                    "responses": {"201": {"description": "Incident created"}}
                }
            },
            "/incidents/{incident_id}": {
                "get": {
                    "operationId": "getIncidentById",
                    "summary": "Get incident by ID",
                    "tags": ["incidents"],
                    "parameters": [
                        {
                            "name": "incident_id",
                            "in": "path",
                            "required": True,
                            "schema": {"type": "string"}
                        }
                    ],
                    "responses": {"200": {"description": "Incident details"}}
                },
                "put": {
                    "operationId": "updateIncident",
                    "summary": "Update incident",
                    "tags": ["incidents"],
                    "responses": {"200": {"description": "Incident updated"}}
                },
                "delete": {
                    "operationId": "deleteIncident",
                    "summary": "Delete incident",
                    "tags": ["incidents"],
                    "responses": {"204": {"description": "Incident deleted"}}
                }
            },
            "/tickets/export": {
                "get": {
                    "operationId": "exportTickets",
                    "summary": "Export tickets to CSV",
                    "tags": ["tickets"],
                    "responses": {"200": {"description": "CSV export"}}
                }
            },
            "/tickets/bulk-import": {
                "post": {
                    "operationId": "bulkImportTickets",
                    "summary": "Bulk import tickets",
                    "tags": ["tickets"],
                    "responses": {"201": {"description": "Import completed"}}
                }
            }
        }
    }, indent=2)


def setup_test_upload():
    """Upload a test file and wait for processing completion"""
    print("🔧 Setting up test upload...")
    
    app = create_test_app()
    client = TestClient(app)
    
    # Create and upload test file
    json_content = create_sample_openapi_spec()
    file_content = BytesIO(json_content.encode('utf-8'))
    
    response = client.post(
        "/api/v1/manoman/upload",
        files={"file": ("test_classification.json", file_content, "application/json")}
    )
    
    assert response.status_code == 200, f"Upload failed: {response.text}"
    upload_id = response.json()["upload_id"]
    
    # Wait for processing to complete
    max_wait = 10  # seconds
    wait_time = 0
    while wait_time < max_wait:
        status_response = client.get(f"/api/v1/manoman/upload/{upload_id}/status")
        status_data = status_response.json()
        
        if status_data["status"] == "completed":
            print(f"✅ Upload {upload_id} completed successfully")
            return client, upload_id
        elif status_data["status"] == "failed":
            raise Exception(f"Upload failed: {status_data.get('error_message', 'Unknown error')}")
        
        time.sleep(0.5)
        wait_time += 0.5
    
    raise Exception(f"Upload did not complete within {max_wait} seconds")


def test_get_classified_services():
    """Test getting classified services for an upload"""
    print("🧪 Testing service classification...")
    
    client, upload_id = setup_test_upload()
    
    # Get classified services
    response = client.get(f"/api/v1/manoman/classification/{upload_id}/services")
    
    assert response.status_code == 200, f"Classification failed: {response.text}"
    
    data = response.json()
    assert data["upload_id"] == upload_id, "Upload ID should match"
    assert "total_services" in data, "Should have total_services"
    assert "services" in data, "Should have services list"
    assert "classification_summary" in data, "Should have classification summary"
    
    # Check classification summary
    summary = data["classification_summary"]
    assert "high_confidence" in summary, "Should have high confidence count"
    assert "medium_confidence" in summary, "Should have medium confidence count"
    assert "needs_review" in summary, "Should have needs review count"
    
    # Check individual services
    services = data["services"]
    assert len(services) > 0, "Should have at least one service"
    
    for service in services:
        assert "service_name" in service, "Service should have name"
        assert "endpoint_count" in service, "Service should have endpoint count"
        assert "tier1_operations" in service, "Service should have tier1 count"
        assert "tier2_operations" in service, "Service should have tier2 count"
        assert "confidence_score" in service, "Service should have confidence score"
        assert 0 <= service["confidence_score"] <= 1, "Confidence should be 0-1"
    
    print(f"✅ Classification successful: {data['total_services']} services identified")
    print(f"   High confidence: {summary['high_confidence']}")
    print(f"   Medium confidence: {summary['medium_confidence']}")
    print(f"   Needs review: {summary['needs_review']}")
    
    for service in services[:3]:  # Show first 3 services
        print(f"   - {service['service_name']}: {service['endpoint_count']} endpoints, "
              f"confidence: {service['confidence_score']:.2f}")
    
    return client, upload_id, data


def test_merge_services():
    """Test merging multiple services"""
    print("🧪 Testing service merge...")
    
    client, upload_id, classification_data = test_get_classified_services()
    
    services = classification_data["services"]
    if len(services) < 2:
        print("⚠️ Not enough services to test merge, skipping...")
        return client, upload_id
    
    # Select first two services for merging
    service1 = services[0]["service_name"]
    service2 = services[1]["service_name"]
    
    merge_request = {
        "source_services": [service1, service2],
        "new_service_name": "merged_service",
        "merge_strategy": "combine_all"
    }
    
    response = client.post(
        f"/api/v1/manoman/classification/{upload_id}/services/merge",
        json=merge_request
    )
    
    assert response.status_code == 200, f"Merge failed: {response.text}"
    
    data = response.json()
    assert data["success"] == True, "Merge should be successful"
    assert data["new_service_name"] == "merged_service", "New service name should match"
    assert set(data["merged_services"]) == {service1, service2}, "Merged services should match"
    assert data["total_operations"] > 0, "Should have total operations"
    
    print(f"✅ Successfully merged services: {service1} + {service2} → merged_service")
    print(f"   Total operations: {data['total_operations']}")
    
    # Verify services list is updated
    updated_response = client.get(f"/api/v1/manoman/classification/{upload_id}/services")
    updated_data = updated_response.json()
    
    service_names = [s["service_name"] for s in updated_data["services"]]
    assert "merged_service" in service_names, "Merged service should be in list"
    assert service1 not in service_names, "Original service1 should be removed"
    assert service2 not in service_names, "Original service2 should be removed"
    
    return client, upload_id


def test_split_service():
    """Test splitting a service into multiple services"""
    print("🧪 Testing service split...")
    
    client, upload_id = test_merge_services()
    
    # Get current services
    response = client.get(f"/api/v1/manoman/classification/{upload_id}/services")
    services = response.json()["services"]
    
    # Find a service with multiple operations to split
    target_service = None
    for service in services:
        if service["endpoint_count"] >= 2:
            target_service = service
            break
    
    if not target_service:
        print("⚠️ No service with multiple endpoints to split, skipping...")
        return client, upload_id
    
    # Create split configuration (simplified)
    split_request = {
        "source_service": target_service["service_name"],
        "split_config": {
            "service_part_1": ["op1", "op2"],  # Mock operation IDs
            "service_part_2": ["op3"]  # Mock operation IDs
        }
    }
    
    # Adjust split config based on actual endpoint count
    total_ops = target_service["endpoint_count"]
    split_request["split_config"] = {
        "service_part_1": [f"op{i}" for i in range(1, total_ops)],
        "service_part_2": [f"op{total_ops}"]
    }
    
    response = client.post(
        f"/api/v1/manoman/classification/{upload_id}/services/split",
        json=split_request
    )
    
    assert response.status_code == 200, f"Split failed: {response.text}"
    
    data = response.json()
    assert data["success"] == True, "Split should be successful"
    assert data["original_service"] == target_service["service_name"], "Original service should match"
    assert len(data["new_services"]) == 2, "Should create 2 new services"
    
    print(f"✅ Successfully split service: {target_service['service_name']} → {', '.join(data['new_services'])}")
    
    return client, upload_id


def test_get_classification_conflicts():
    """Test conflict detection in classified services"""
    print("🧪 Testing classification conflict detection...")
    
    client, upload_id = test_split_service()
    
    response = client.get(f"/api/v1/manoman/classification/{upload_id}/conflicts")
    
    assert response.status_code == 200, f"Conflict detection failed: {response.text}"
    
    data = response.json()
    assert data["upload_id"] == upload_id, "Upload ID should match"
    assert "total_conflicts" in data, "Should have total conflicts count"
    assert "conflicts" in data, "Should have conflicts list"
    assert "high_severity_count" in data, "Should have high severity count"
    assert "medium_severity_count" in data, "Should have medium severity count"
    assert "low_severity_count" in data, "Should have low severity count"
    
    # Check conflict structure
    for conflict in data["conflicts"]:
        assert "conflict_type" in conflict, "Conflict should have type"
        assert "severity" in conflict, "Conflict should have severity"
        assert "affected_services" in conflict, "Conflict should have affected services"
        assert "description" in conflict, "Conflict should have description"
        assert "suggested_resolutions" in conflict, "Conflict should have resolutions"
        assert "auto_resolvable" in conflict, "Conflict should have auto_resolvable flag"
    
    print(f"✅ Conflict detection completed: {data['total_conflicts']} conflicts found")
    print(f"   High severity: {data['high_severity_count']}")
    print(f"   Medium severity: {data['medium_severity_count']}")
    print(f"   Low severity: {data['low_severity_count']}")
    
    return client, upload_id


def test_clear_classification():
    """Test clearing classification results"""
    print("🧪 Testing classification clearing...")
    
    client, upload_id = test_get_classification_conflicts()
    
    response = client.delete(f"/api/v1/manoman/classification/{upload_id}")
    
    assert response.status_code == 200, f"Clear failed: {response.text}"
    
    data = response.json()
    assert data["upload_id"] == upload_id, "Upload ID should match"
    assert "message" in data, "Should have success message"
    
    # Verify classification is cleared
    response = client.get(f"/api/v1/manoman/classification/{upload_id}/services")
    # Should re-classify since cache is cleared
    assert response.status_code == 200, "Should re-classify after clearing"
    
    print(f"✅ Successfully cleared classification for upload {upload_id}")
    
    return client, upload_id


def test_classification_nonexistent_upload():
    """Test classification operations on non-existent upload"""
    print("🧪 Testing non-existent upload classification...")
    
    app = create_test_app()
    client = TestClient(app)
    
    fake_upload_id = "non-existent-upload-id"
    
    # Test get services
    response = client.get(f"/api/v1/manoman/classification/{fake_upload_id}/services")
    assert response.status_code == 404, f"Expected 404, got {response.status_code}"
    
    # Test merge
    merge_request = {
        "source_services": ["service1", "service2"],
        "new_service_name": "merged",
        "merge_strategy": "combine_all"
    }
    response = client.post(
        f"/api/v1/manoman/classification/{fake_upload_id}/services/merge",
        json=merge_request
    )
    assert response.status_code == 404, f"Expected 404, got {response.status_code}"
    
    print("✅ Correctly handled non-existent upload operations")


def run_all_tests():
    """Run all classification API tests"""
    print("🚀 Starting Man-O-Man Classification API Tests\n")
    
    try:
        # Run all test functions
        test_get_classified_services()
        print()
        
        test_merge_services()
        print()
        
        test_split_service()
        print()
        
        test_get_classification_conflicts()
        print()
        
        test_clear_classification()
        print()
        
        test_classification_nonexistent_upload()
        print()
        
        print("🎉 All classification API tests completed successfully!")
        print("✅ Service classification working")
        print("🔄 Service merge/split operational")
        print("⚠️ Conflict detection functional")
        print("🧹 Cache management working")
        print("🛡️ Error handling robust")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Test suite failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)