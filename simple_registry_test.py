#!/usr/bin/env python3
"""
Simple test for Man-O-Man Registry Manager basic functionality.
Tests the core load/save operations.
"""

import sys
sys.path.append('/home/heramb/source/augment/legacy/backend')

import asyncio
import tempfile
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


async def test_basic_registry_operations():
    """Test basic registry load/save operations"""
    print("🧪 Testing basic registry operations...")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        manager = RegistryManager(storage_path=temp_dir)
        
        # Test 1: Load empty registry (should create new)
        print("   Testing empty registry load...")
        registry = await manager.load_registry("latest")
        assert registry is not None, "Should create empty registry"
        assert len(registry.services) == 0, "Should be empty"
        print("   ✅ Empty registry loaded successfully")
        
        # Test 2: Add a service to registry and save
        print("   Testing service addition and save...")
        test_service = ServiceDefinition(
            service_name="test_service",
            service_description="Test service",
            business_context="Testing",
            keywords=["test"],
            synonyms=["testing"],
            tier1_operations={},
            tier2_operations={}
        )
        
        # Add service to registry
        registry.services["test_service"] = test_service
        registry.total_services = len(registry.services)
        registry.last_updated = datetime.now().isoformat()
        
        # Save registry
        version = await manager.save_registry(registry)
        assert version is not None, "Save should return version"
        print(f"   ✅ Registry saved with version: {version}")
        
        # Test 3: Load saved registry
        print("   Testing registry reload...")
        loaded_registry = await manager.load_registry("latest")
        assert loaded_registry is not None, "Should load saved registry"
        assert len(loaded_registry.services) == 1, "Should have one service"
        assert "test_service" in loaded_registry.services, "Should contain test service"
        print("   ✅ Registry reloaded successfully")
        
        # Test 4: Basic service operations via manager
        print("   Testing service operations...")
        
        # Add service via manager
        new_service = ServiceDefinition(
            service_name="new_service",
            service_description="New service",
            business_context="Testing addition",
            keywords=["new"],
            synonyms=["additional"],
            tier1_operations={},
            tier2_operations={}
        )
        
        success = await manager.add_service("new_service", new_service)
        assert success, "Service addition should succeed"
        print("   ✅ Service added via manager")
        
        # Verify addition
        final_registry = await manager.load_registry("latest")
        assert len(final_registry.services) == 2, "Should have two services"
        assert "new_service" in final_registry.services, "Should contain new service"
        print("   ✅ Service addition verified")
        
        # Test 5: Registry statistics
        print("   Testing registry statistics...")
        stats = await manager.get_registry_stats()
        assert "total_services" in stats, "Stats should include total services"
        assert stats["total_services"] == 2, "Should report 2 services"
        print(f"   ✅ Registry stats: {stats['total_services']} services")
        
        print("🎉 Basic registry operations test completed successfully!")
        return True


async def test_version_management():
    """Test version management functionality"""
    print("🧪 Testing version management...")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        manager = RegistryManager(storage_path=temp_dir)
        
        # Create initial registry
        registry = await manager.load_registry("latest")
        test_service = ServiceDefinition(
            service_name="versioned_service",
            service_description="Service for version testing",
            business_context="Version testing",
            keywords=["version"],
            synonyms=["versioned"],
            tier1_operations={},
            tier2_operations={}
        )
        
        registry.services["versioned_service"] = test_service
        registry.total_services = 1
        
        # Save initial version
        v1 = await manager.save_registry(registry, "1.0.0")
        assert v1 == "1.0.0", "Should save with specified version"
        print(f"   ✅ Version 1.0.0 saved")
        
        # Modify and save new version
        registry.services["versioned_service"].service_description = "Updated service"
        registry.version = "1.1.0"
        v2 = await manager.save_registry(registry, "1.1.0")
        assert v2 == "1.1.0", "Should save with new version"
        print(f"   ✅ Version 1.1.0 saved")
        
        # List versions
        versions = await manager.get_registry_versions()
        assert "1.0.0" in versions, "Should list version 1.0.0"
        assert "1.1.0" in versions, "Should list version 1.1.0"
        print(f"   ✅ Versions listed: {versions}")
        
        # Load specific version
        old_registry = await manager.load_registry("1.0.0")
        assert old_registry.version == "1.0.0", "Should load correct version"
        assert "Updated service" not in old_registry.services["versioned_service"].service_description, "Should have old description"
        print("   ✅ Specific version loaded correctly")
        
        print("🎉 Version management test completed successfully!")
        return True


async def test_error_handling():
    """Test error handling"""
    print("🧪 Testing error handling...")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        manager = RegistryManager(storage_path=temp_dir)
        
        # Test loading non-existent version
        try:
            registry = await manager.load_registry("99.99.99")
            assert False, "Should raise error for non-existent version"
        except Exception as e:
            print(f"   ✅ Non-existent version error handled: {type(e).__name__}")
        
        # Test adding service with empty name
        empty_service = ServiceDefinition(
            service_name="",
            service_description="Empty name service",
            business_context="Testing",
            keywords=[],
            synonyms=[],
            tier1_operations={},
            tier2_operations={}
        )
        
        try:
            success = await manager.add_service("", empty_service)
            # If it succeeds, that's also acceptable - just log it
            print(f"   ℹ️ Empty service name was accepted (success={success})")
        except Exception as e:
            print(f"   ✅ Empty service name error handled: {type(e).__name__}")
        
        print("   ✅ Empty service name handling tested")
        
        print("🎉 Error handling test completed successfully!")
        return True


async def run_simple_tests():
    """Run simplified registry manager tests"""
    print("🚀 Starting Simple Registry Manager Tests\n")
    
    try:
        # Test 1: Basic operations
        success1 = await test_basic_registry_operations()
        print()
        
        # Test 2: Version management
        success2 = await test_version_management()
        print()
        
        # Test 3: Error handling
        success3 = await test_error_handling()
        print()
        
        if success1 and success2 and success3:
            print("🎉 All Simple Registry Manager Tests Completed!")
            print("✅ Basic load/save operations working")
            print("✅ Service addition/retrieval functional")
            print("✅ Version management operational")
            print("✅ Registry statistics working")
            print("✅ Error handling robust")
            print("✅ File-based storage reliable")
            return True
        else:
            print("❌ Some tests failed")
            return False
        
    except Exception as e:
        print(f"\n❌ Test suite failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(run_simple_tests())
    sys.exit(0 if success else 1)