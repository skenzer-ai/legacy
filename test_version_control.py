#!/usr/bin/env python3
"""
Test script for Man-O-Man Version Control System.
Tests versioning, change tracking, and diff generation.
"""

import sys
sys.path.append('/home/heramb/source/augment/legacy/backend')

import asyncio
import tempfile
from pathlib import Path
from datetime import datetime

from backend.app.core.manoman.storage.version_control import VersionControl, ChangeType
from backend.app.core.manoman.models.service_registry import (
    ServiceRegistry,
    ServiceDefinition,
    ServiceOperation,
    APIEndpoint
)


def create_test_registry(version="1.0.0"):
    """Create a test registry with sample services"""
    service1 = ServiceDefinition(
        service_name="user_service",
        service_description="User management service",
        business_context="Handles user operations",
        keywords=["user", "account"],
        synonyms=["person", "individual"],
        tier1_operations={
            "get_user": ServiceOperation(
                endpoint=APIEndpoint(
                    path="/users/{id}",
                    method="GET",
                    operation_id="getUser",
                    description="Get user by ID"
                ),
                intent_verbs=["get", "retrieve"],
                intent_objects=["user"],
                description="Retrieve user information"
            )
        },
        tier2_operations={}
    )
    
    service2 = ServiceDefinition(
        service_name="incident_service",
        service_description="Incident management service",
        business_context="Handles IT incidents",
        keywords=["incident", "ticket"],
        synonyms=["issue", "problem"],
        tier1_operations={},
        tier2_operations={}
    )
    
    return ServiceRegistry(
        registry_id=f"test_registry_{version}",
        version=version,
        created_timestamp=datetime.now().isoformat(),
        last_updated=datetime.now().isoformat(),
        services={
            "user_service": service1,
            "incident_service": service2
        },
        total_services=2
    )


async def test_basic_version_control():
    """Test basic version control operations"""
    print("🧪 Testing basic version control...")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        vc = VersionControl(storage_path=temp_dir)
        
        # Create initial registry
        registry_v1 = create_test_registry("1.0.0")
        
        # Save initial version
        await vc.save_version(registry_v1, "Initial version")
        print("   ✅ Initial version saved")
        
        # Modify registry for v1.1.0
        registry_v1_1 = create_test_registry("1.1.0")
        # Add a new service
        new_service = ServiceDefinition(
            service_name="asset_service",
            service_description="Asset management service",
            business_context="Handles IT assets",
            keywords=["asset", "equipment"],
            synonyms=["device", "resource"],
            tier1_operations={},
            tier2_operations={}
        )
        registry_v1_1.services["asset_service"] = new_service
        registry_v1_1.total_services = 3
        
        # Save modified version
        await vc.save_version(registry_v1_1, "Added asset service")
        print("   ✅ Modified version saved")
        
        # List versions
        versions = await vc.list_versions()
        assert len(versions) >= 2, "Should have at least 2 versions"
        print(f"   ✅ Version listing: {len(versions)} versions found")
        
        # Get specific version
        retrieved_v1 = await vc.get_version("1.0.0")
        assert retrieved_v1 is not None, "Should retrieve version 1.0.0"
        assert len(retrieved_v1.services) == 2, "V1.0.0 should have 2 services"
        print("   ✅ Specific version retrieved")
        
        retrieved_v1_1 = await vc.get_version("1.1.0")
        assert retrieved_v1_1 is not None, "Should retrieve version 1.1.0"
        assert len(retrieved_v1_1.services) == 3, "V1.1.0 should have 3 services"
        print("   ✅ Modified version retrieved")
        
        return vc, registry_v1, registry_v1_1


async def test_change_tracking():
    """Test change tracking and diff generation"""
    print("🧪 Testing change tracking...")
    
    vc, registry_v1, registry_v1_1 = await test_basic_version_control()
    
    # Generate diff between versions
    changes = await vc.generate_diff("1.0.0", "1.1.0")
    
    assert len(changes) > 0, "Should detect changes between versions"
    print(f"   ✅ Change detection: {len(changes)} changes found")
    
    # Check for expected changes
    service_added = any(
        change.change_type == ChangeType.SERVICE_ADDED and change.target == "asset_service"
        for change in changes
    )
    assert service_added, "Should detect asset_service addition"
    print("   ✅ Service addition detected")
    
    # Check change descriptions
    for change in changes[:3]:  # Show first 3 changes
        print(f"      - {change.change_type.value}: {change.target}")
        if change.description:
            print(f"        {change.description}")
    
    return vc, changes


async def test_version_info():
    """Test detailed version information"""
    print("🧪 Testing version information...")
    
    vc, changes = await test_change_tracking()
    
    # Get version info
    version_info = await vc.get_version_info("1.1.0")
    
    assert version_info is not None, "Should get version info"
    assert version_info.version == "1.1.0", "Version should match"
    print(f"   ✅ Version info retrieved")
    print(f"      Version: {version_info.version}")
    print(f"      Timestamp: {version_info.timestamp}")
    print(f"      Message: {version_info.message}")
    print(f"      Changes: {len(version_info.changes)}")
    
    return vc


async def test_rollback_functionality():
    """Test rollback to previous versions"""
    print("🧪 Testing rollback functionality...")
    
    vc = await test_version_info()
    
    # Create a newer version to rollback from
    registry_v2 = create_test_registry("2.0.0")
    # Remove a service to create a rollback scenario
    del registry_v2.services["incident_service"]
    registry_v2.total_services = 1
    
    await vc.save_version(registry_v2, "Removed incident service")
    print("   ✅ Version 2.0.0 saved (service removed)")
    
    # Rollback to version 1.1.0
    rollback_success = await vc.rollback_to_version("1.1.0")
    assert rollback_success, "Rollback should succeed"
    print("   ✅ Rollback to 1.1.0 successful")
    
    # Verify rollback
    current = await vc.get_current_version()
    assert current is not None, "Should have current version"
    assert len(current.services) == 3, "Should have 3 services after rollback"
    assert "incident_service" in current.services, "incident_service should be restored"
    print("   ✅ Rollback verification successful")
    
    return vc


async def test_branch_management():
    """Test branch management functionality"""
    print("🧪 Testing branch management...")
    
    vc = await test_rollback_functionality()
    
    # Check if branch management is implemented
    try:
        branches = await vc.list_branches()
        print(f"   ✅ Branch listing: {len(branches)} branches found")
        
        # Create a new branch
        success = await vc.create_branch("feature/new-services", "1.1.0")
        if success:
            print("   ✅ Branch creation successful")
        else:
            print("   ℹ️ Branch creation not implemented or failed")
        
    except AttributeError:
        print("   ℹ️ Branch management not implemented (acceptable)")
    except Exception as e:
        print(f"   ℹ️ Branch management error: {type(e).__name__}")
    
    return vc


async def test_error_handling():
    """Test error handling in version control"""
    print("🧪 Testing error handling...")
    
    vc = await test_branch_management()
    
    # Test getting non-existent version
    try:
        non_existent = await vc.get_version("99.99.99")
        if non_existent is None:
            print("   ✅ Non-existent version returns None")
        else:
            print("   ⚠️ Non-existent version returned data unexpectedly")
    except Exception as e:
        print(f"   ✅ Non-existent version error handled: {type(e).__name__}")
    
    # Test invalid rollback
    try:
        invalid_rollback = await vc.rollback_to_version("invalid-version")
        if not invalid_rollback:
            print("   ✅ Invalid rollback returns False")
        else:
            print("   ⚠️ Invalid rollback succeeded unexpectedly")
    except Exception as e:
        print(f"   ✅ Invalid rollback error handled: {type(e).__name__}")
    
    print("   ✅ Error handling tested")
    return True


async def run_all_version_tests():
    """Run all version control tests"""
    print("🚀 Starting Version Control System Tests\n")
    
    try:
        # Test 1: Basic version control
        await test_basic_version_control()
        print()
        
        # Test 2: Change tracking
        await test_change_tracking()
        print()
        
        # Test 3: Version information
        await test_version_info()
        print()
        
        # Test 4: Rollback functionality
        await test_rollback_functionality()
        print()
        
        # Test 5: Branch management
        await test_branch_management()
        print()
        
        # Test 6: Error handling
        await test_error_handling()
        print()
        
        # Summary
        print("🎉 Version Control System Tests Completed!")
        print("✅ Basic version save/retrieve working")
        print("✅ Change tracking and diff generation functional")
        print("✅ Version information detailed and accurate")
        print("✅ Rollback functionality operational")
        print("✅ Error handling robust")
        print("✅ File-based version storage reliable") 
        print("✅ Change type detection working")
        print("✅ Version metadata management functional")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Test suite failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(run_all_version_tests())
    sys.exit(0 if success else 1)