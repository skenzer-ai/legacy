#!/usr/bin/env python3
"""
Test script for Man-O-Man service registry data models.
Tests model validation, serialization, and core functionality.
"""

import sys
sys.path.append('/home/heramb/source/augment/legacy/backend')

from datetime import datetime
from backend.app.core.manoman.models.service_registry import (
    OperationType,
    TierLevel,
    APIEndpoint,
    ServiceOperation,
    ServiceDefinition,
    ServiceRegistry
)


def test_api_endpoint():
    """Test APIEndpoint model"""
    print("🧪 Testing APIEndpoint model...")
    
    endpoint = APIEndpoint(
        path="/api/v1/business-rules",
        method="POST",
        operation_id="create_business_rule",
        description="Create a new business rule",
        parameters={"name": "string", "conditions": "array"}
    )
    
    assert endpoint.path == "/api/v1/business-rules"
    assert endpoint.method == "POST"
    assert endpoint.operation_id == "create_business_rule"
    assert endpoint.parameters["name"] == "string"
    
    # Test serialization
    json_data = endpoint.model_dump()
    assert "path" in json_data
    assert "method" in json_data
    
    print("✅ APIEndpoint model tests passed!")
    return endpoint


def test_service_operation():
    """Test ServiceOperation model"""
    print("🧪 Testing ServiceOperation model...")
    
    endpoint = test_api_endpoint()
    
    operation = ServiceOperation(
        endpoint=endpoint,
        intent_verbs=["create", "add", "make"],
        intent_objects=["rule", "policy", "business rule"],
        intent_indicators=["automation", "workflow"],
        description="Creates new business rules for automation workflows",
        confidence_score=0.92
    )
    
    assert len(operation.intent_verbs) == 3
    assert "create" in operation.intent_verbs
    assert operation.confidence_score == 0.92
    assert operation.endpoint.method == "POST"
    
    print("✅ ServiceOperation model tests passed!")
    return operation


def test_service_definition():
    """Test ServiceDefinition model"""
    print("🧪 Testing ServiceDefinition model...")
    
    operation = test_service_operation()
    
    service_def = ServiceDefinition(
        service_name="business_rule",
        service_description="Business rule management and automation system",
        business_context="Handles automated business logic, rule management, and workflow automation for approval processes",
        keywords=["rule", "policy", "automation", "workflow", "condition"],
        synonyms=["business rule", "policy rule", "workflow rule", "automation rule"],
        tier1_operations={"create": operation},
        tier2_operations={}
    )
    
    assert service_def.service_name == "business_rule"
    assert len(service_def.keywords) == 5
    assert len(service_def.synonyms) == 4
    assert "create" in service_def.tier1_operations
    
    # Test helper methods
    all_ops = service_def.get_all_operations()
    assert len(all_ops) == 1
    assert "create" in all_ops
    
    op_count = service_def.get_operation_count()
    assert op_count["tier1"] == 1
    assert op_count["tier2"] == 0
    assert op_count["total"] == 1
    
    crud_check = service_def.has_crud_operations()
    assert crud_check["create"] == True
    assert crud_check["list"] == False
    
    print("✅ ServiceDefinition model tests passed!")
    return service_def


def test_service_registry():
    """Test ServiceRegistry model"""
    print("🧪 Testing ServiceRegistry model...")
    
    service_def = test_service_definition()
    
    registry = ServiceRegistry(
        version="1.0.0",
        classification_rules={"min_confidence": 0.8}
    )
    
    # Test adding service
    result = registry.add_service("business_rule", service_def)
    assert result == True
    assert "business_rule" in registry.services
    
    # Test duplicate service
    result = registry.add_service("business_rule", service_def)
    assert result == False  # Should fail for duplicate
    
    # Test global keywords
    assert len(registry.global_keywords) > 0
    assert "rule" in registry.global_keywords
    assert "business_rule" in registry.global_keywords["rule"]
    
    # Test registry stats
    stats = registry.get_registry_stats()
    assert stats["total_services"] == 1
    assert stats["total_operations"] == 1
    assert stats["tier1_operations"] == 1
    assert stats["tier2_operations"] == 0
    assert stats["version"] == "1.0.0"
    
    # Test updating service
    service_def.service_description = "Updated business rule management system"
    result = registry.update_service("business_rule", service_def)
    assert result == True
    
    # Test removing service
    result = registry.remove_service("business_rule")
    assert result == True
    assert "business_rule" not in registry.services
    assert registry.get_service_count() == 0
    
    print("✅ ServiceRegistry model tests passed!")
    return registry


def test_enum_types():
    """Test enum types"""
    print("🧪 Testing enum types...")
    
    # Test OperationType
    assert OperationType.LIST == "list"
    assert OperationType.CREATE == "create"
    assert len(OperationType) == 5
    
    # Test TierLevel
    assert TierLevel.TIER1 == "tier1"
    assert TierLevel.TIER2 == "tier2"
    
    print("✅ Enum types tests passed!")


def test_model_serialization():
    """Test JSON serialization/deserialization"""
    print("🧪 Testing model serialization...")
    
    registry = test_service_registry()
    service_def = test_service_definition()
    registry.add_service("test_service", service_def)
    
    # Test serialization
    json_data = registry.model_dump()
    assert "version" in json_data
    assert "services" in json_data
    assert "global_keywords" in json_data
    
    # Test deserialization
    new_registry = ServiceRegistry(**json_data)
    assert new_registry.version == registry.version
    assert len(new_registry.services) == len(registry.services)
    
    print("✅ Model serialization tests passed!")


def run_all_tests():
    """Run all tests"""
    print("🚀 Starting Man-O-Man Service Registry Model Tests\n")
    
    try:
        test_enum_types()
        test_api_endpoint()
        test_service_operation()
        test_service_definition()
        test_service_registry()
        test_model_serialization()
        
        print("\n🎉 All service registry model tests passed successfully!")
        print("✅ Models are ready for integration with Man-O-Man system")
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)