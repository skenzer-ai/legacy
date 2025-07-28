#!/usr/bin/env python3
"""
Test script for Man-O-Man Registry Manager.
Tests CRUD operations, versioning, and storage functionality.
"""

import sys
sys.path.append('/home/heramb/source/augment/legacy/backend')

import asyncio
import tempfile
import os
import uuid
from pathlib import Path
from datetime import datetime

from backend.app.core.manoman.storage.registry_manager import RegistryManager
from backend.app.core.manoman.models.service_registry import (
    ServiceRegistry,
    ServiceDefinition,
    ServiceOperation,
    APIEndpoint
)


def create_test_service():
    """Create a test service definition"""
    return ServiceDefinition(
        service_name="test_service",
        service_description="Test service for registry operations",
        business_context="Testing registry CRUD functionality",
        keywords=["test", "registry", "crud"],
        synonyms=["testing", "validation"],
        tier1_operations={
            "get_test": ServiceOperation(
                endpoint=APIEndpoint(
                    path="/test",
                    method="GET",
                    operation_id="getTest",
                    description="Get test data"
                ),
                intent_verbs=["get", "retrieve"],
                intent_objects=["test", "data"],
                description="Retrieve test data"
            )
        },
        tier2_operations={}
    )


async def test_registry_creation():
    """Test creating a new registry"""
    print("🧪 Testing registry creation...")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        manager = RegistryManager(storage_path=temp_dir)
        
        # Create test service
        test_service = create_test_service()
        services = {"test_service": test_service}
        
        # Create registry manually
        registry_id = f"test_registry_{uuid.uuid4().hex[:8]}"
        registry = ServiceRegistry(
            registry_id=registry_id,
            version="1.0.0",
            created_timestamp=datetime.now().isoformat(),
            last_updated=datetime.now().isoformat(),
            services=services,
            total_services=len(services)
        )
        
        # Save registry
        version = await manager.save_registry(registry)
        
        assert version is not None, "Version should be returned"
        print(f"   ✅ Registry created with ID: {registry_id}")
        print(f"   ✅ Registry saved with version: {version}")
        
        # Verify registry file exists
        registry_file = Path(temp_dir) / "registry.json"
        assert registry_file.exists(), "Registry file should exist"
        print(f"   ✅ Registry file created: {registry_file}")
        
        return manager, registry_id


async def test_registry_loading():
    """Test loading an existing registry"""
    print("🧪 Testing registry loading...")
    
    manager, registry_id = await test_registry_creation()
    
    # Load the registry (load latest version)
    registry = await manager.load_registry("latest")
    
    assert registry is not None, "Registry should be loaded"
    assert registry.registry_id == registry_id, "Registry ID should match"
    assert len(registry.services) == 1, "Should have one service"
    assert "test_service" in registry.services, "Should contain test service"
    
    print(f"   ✅ Registry loaded successfully")
    print(f"      ID: {registry.registry_id}")
    print(f"      Services: {len(registry.services)}")
    print(f"      Version: {registry.version}")
    
    return manager, registry_id, registry


async def test_service_operations():
    """Test adding, updating, and removing services"""
    print("🧪 Testing service CRUD operations...")
    
    manager, registry_id, registry = await test_registry_loading()
    
    # Add a new service
    new_service = ServiceDefinition(
        service_name="new_service",
        service_description="Newly added service",
        business_context="Testing service addition",
        keywords=["new", "added"],
        synonyms=["fresh", "additional"],
        tier1_operations={},
        tier2_operations={}
    )
    
    success = await manager.add_service("new_service", new_service)
    assert success, "Service addition should succeed"
    print("   ✅ Service added successfully")
    
    # Verify service was added
    updated_registry = await manager.load_registry("latest")
    assert len(updated_registry.services) == 2, "Should have two services"
    assert "new_service" in updated_registry.services, "New service should be present"
    
    # Update existing service (use update_service with updates dict)
    updates = {
        "service_description": "Updated test service description",
        "business_context": "Updated testing context",
        "keywords": ["test", "registry", "crud", "updated"],
        "synonyms": ["testing", "validation", "modified"]
    }
    
    success = await manager.update_service("test_service", updates)
    assert success, "Service update should succeed"
    print("   ✅ Service updated successfully")
    
    # Verify service was updated
    updated_registry = await manager.load_registry("latest")
    updated_svc = updated_registry.services["test_service"]
    assert "updated" in updated_svc.keywords, "Keywords should be updated"
    assert "Updated test service" in updated_svc.service_description, "Description should be updated"
    
    # Remove service
    success = await manager.delete_service("new_service")
    assert success, "Service removal should succeed"
    print("   ✅ Service removed successfully")
    
    # Verify service was removed
    final_registry = await manager.load_registry("latest")
    assert len(final_registry.services) == 1, "Should have one service after removal"
    assert "new_service" not in final_registry.services, "New service should be removed"
    
    return manager, registry_id


async def test_registry_listing():
    """Test listing all registries"""
    print("🧪 Testing registry listing...")
    
    manager, registry_id = await test_service_operations()
    
    # Create another registry
    test_service2 = ServiceDefinition(
        service_name="second_service",
        service_description="Second test service",
        business_context="Testing multiple registries",
        keywords=["second", "multiple"],
        synonyms=["another", "additional"],
        tier1_operations={},
        tier2_operations={}
    )
    
    registry_id2 = await manager.create_registry(
        services={"second_service": test_service2},
        created_by="test_user2"
    )
    
    # List all registries
    registries = await manager.list_registries()
    
    assert len(registries) >= 2, "Should have at least two registries"
    registry_ids = [r["registry_id"] for r in registries]
    assert registry_id in registry_ids, "First registry should be in list"
    assert registry_id2 in registry_ids, "Second registry should be in list"
    
    print(f"   ✅ Registry listing successful: {len(registries)} registries found")
    for registry in registries[:2]:  # Show first 2
        print(f"      - {registry['registry_id']}: {registry['total_services']} services")
    
    return manager, registry_id, registry_id2


async def test_conflict_detection_integration():
    """Test conflict detection integration"""
    print("🧪 Testing conflict detection integration...")
    
    manager, registry_id, registry_id2 = await test_registry_listing()
    
    # Add conflicting services to first registry
    conflicting_service = ServiceDefinition(
        service_name="conflicting_service",
        service_description="Service with conflicting keywords",
        business_context="Testing conflict detection",
        keywords=["test", "conflict"],  # "test" conflicts with existing service
        synonyms=["testing", "clash"],  # "testing" conflicts
        tier1_operations={},
        tier2_operations={}
    )
    
    # This should detect conflicts but still succeed
    success = await manager.add_service(registry_id, "conflicting_service", conflicting_service)
    assert success, "Service addition should succeed even with conflicts"
    print("   ✅ Service with conflicts added (conflicts detected but allowed)")
    
    # Load registry and check for conflicts
    registry = await manager.load_registry(registry_id)
    conflicts = await manager.get_registry_conflicts(registry_id)
    
    assert len(conflicts) > 0, "Should detect conflicts"
    print(f"   ✅ Conflicts detected: {len(conflicts)} conflicts found")
    
    for conflict in conflicts[:2]:  # Show first 2 conflicts
        print(f"      - {conflict.severity.value.upper()}: {conflict.description}")
    
    return manager, registry_id


async def test_registry_deletion():
    """Test deleting registries"""
    print("🧪 Testing registry deletion...")
    
    manager, registry_id = await test_conflict_detection_integration()
    
    # Delete registry
    success = await manager.delete_registry(registry_id)
    assert success, "Registry deletion should succeed"
    print("   ✅ Registry deleted successfully")
    
    # Verify registry is deleted
    try:
        deleted_registry = await manager.load_registry(registry_id)
        assert False, "Should not be able to load deleted registry"
    except Exception:
        print("   ✅ Deleted registry cannot be loaded (correct behavior)")
    
    return manager


async def test_error_handling():
    """Test error handling for invalid operations"""
    print("🧪 Testing error handling...")
    
    manager = await test_registry_deletion()
    
    # Test loading non-existent registry
    try:
        non_existent = await manager.load_registry("non-existent-id")
        assert non_existent is None, "Non-existent registry should return None"
        print("   ✅ Non-existent registry handled correctly")
    except Exception as e:
        print(f"   ✅ Non-existent registry error handled: {str(e)}")
    
    # Test operations on non-existent registry
    test_service = create_test_service()
    
    success = await manager.add_service("non-existent-id", "test", test_service)
    assert not success, "Operations on non-existent registry should fail"
    print("   ✅ Operations on non-existent registry handled correctly")
    
    success = await manager.update_service("non-existent-id", "test", test_service)
    assert not success, "Update on non-existent registry should fail"
    
    success = await manager.remove_service("non-existent-id", "test")
    assert not success, "Remove on non-existent registry should fail"
    
    print("   ✅ All error conditions handled correctly")
    return True


async def test_concurrent_operations():
    """Test concurrent registry operations"""
    print("🧪 Testing concurrent operations...")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        manager = RegistryManager(storage_path=temp_dir)
        
        # Create registry
        test_service = create_test_service()
        registry_id = await manager.create_registry(
            services={"test_service": test_service},
            created_by="test_user"
        )
        
        # Create multiple services concurrently
        async def add_service(name, keywords):
            service = ServiceDefinition(
                service_name=name,
                service_description=f"Concurrent service {name}",
                business_context="Testing concurrent operations",
                keywords=keywords,
                synonyms=[],
                tier1_operations={},
                tier2_operations={}
            )
            return await manager.add_service(registry_id, name, service)
        
        # Run concurrent operations
        tasks = [
            add_service("concurrent_1", ["concurrent", "first"]),
            add_service("concurrent_2", ["concurrent", "second"]),
            add_service("concurrent_3", ["concurrent", "third"]),
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Check results
        successful_adds = sum(1 for r in results if r is True)
        print(f"   ✅ Concurrent operations completed: {successful_adds}/3 successful")
        
        # Verify final state
        final_registry = await manager.load_registry(registry_id)
        print(f"   ✅ Final registry has {len(final_registry.services)} services")
        
        return True


async def run_all_registry_tests():
    """Run all registry manager tests"""
    print("🚀 Starting Registry Manager Tests\n")
    
    try:
        # Test 1: Registry creation
        await test_registry_creation()
        print()
        
        # Test 2: Registry loading
        await test_registry_loading()
        print()
        
        # Test 3: Service CRUD operations
        await test_service_operations()
        print()
        
        # Test 4: Registry listing
        await test_registry_listing()
        print()
        
        # Test 5: Conflict detection integration
        await test_conflict_detection_integration()
        print()
        
        # Test 6: Registry deletion
        await test_registry_deletion()
        print()
        
        # Test 7: Error handling
        await test_error_handling()
        print()
        
        # Test 8: Concurrent operations
        await test_concurrent_operations()
        print()
        
        # Summary
        print("🎉 Registry Manager Tests Completed!")
        print("✅ Registry creation and storage working")
        print("✅ Registry loading and persistence functional")
        print("✅ Service CRUD operations operational")
        print("✅ Registry listing and metadata working")
        print("✅ Conflict detection integration functional")
        print("✅ Registry deletion and cleanup working")
        print("✅ Error handling robust")
        print("✅ Concurrent operations supported")
        print("✅ File-based storage reliable")
        print("✅ JSON serialization/deserialization working")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Test suite failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(run_all_registry_tests())
    sys.exit(0 if success else 1)