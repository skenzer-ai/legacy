"""
Tests for Registry Helper Utilities

Comprehensive tests for service registry validation, transformation,
merging, comparison, and other registry management operations.
"""

import pytest
from datetime import datetime, timezone
from typing import Dict, List
import uuid

# Add backend to sys.path
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[2]))

from app.core.manoman.models.service_registry import (
    ServiceRegistry, ServiceDefinition, ServiceOperation, APIEndpoint,
    OperationType, TierLevel
)
from app.core.manoman.models.api_specification import RawAPIEndpoint, HTTPMethod, APIParameter, ParameterLocation
from app.core.manoman.utils.registry_helpers import (
    RegistryHelper,
    registry_helper,
    validate_registry,
    merge_services,
    split_service,
    compare_registries,
    extract_service_statistics
)


class TestRegistryHelper:
    """Test cases for RegistryHelper class"""
    
    @pytest.fixture
    def sample_endpoint(self):
        """Create a sample API endpoint"""
        return APIEndpoint(
            path="/api/users/{id}",
            method="GET",
            operation_id="get_user",
            description="Get user by ID",
            parameters={"id": {"type": "string", "required": True}}
        )
    
    @pytest.fixture
    def sample_operation(self, sample_endpoint):
        """Create a sample service operation"""
        return ServiceOperation(
            endpoint=sample_endpoint,
            intent_verbs=["get", "read", "fetch"],
            intent_objects=["user", "account"],
            intent_indicators=["get user", "fetch account"],
            description="Retrieve user information",
            confidence_score=0.95
        )
    
    @pytest.fixture
    def sample_service(self, sample_operation):
        """Create a sample service definition"""
        create_endpoint = APIEndpoint(
            path="/api/users",
            method="POST",
            operation_id="create_user",
            description="Create a new user",
            parameters={}
        )
        
        create_operation = ServiceOperation(
            endpoint=create_endpoint,
            intent_verbs=["create", "add"],
            intent_objects=["user"],
            intent_indicators=["create user"],
            description="Create new user",
            confidence_score=0.9
        )
        
        return ServiceDefinition(
            service_name="user_management",
            service_description="User management service",
            business_context="Handles user lifecycle operations",
            keywords=["user", "account", "profile"],
            synonyms=["member", "person"],
            tier1_operations={
                "create": create_operation,
                "read": sample_operation
            },
            tier2_operations={}
        )
    
    @pytest.fixture
    def sample_registry(self, sample_service):
        """Create a sample service registry"""
        return ServiceRegistry(
            registry_id="test-registry-001",
            version="1.0.0",
            created_timestamp=datetime.now(timezone.utc).isoformat(),
            last_updated=datetime.now(timezone.utc).isoformat(),
            services={"user_management": sample_service},
            total_services=1
        )
    
    def test_create_registry_id(self):
        """Test registry ID generation"""
        id1 = RegistryHelper.create_registry_id()
        id2 = RegistryHelper.create_registry_id()
        
        # Should be unique
        assert id1 != id2
        
        # Should follow format
        assert id1.startswith("registry_")
        assert len(id1.split("_")) >= 3  # Format: registry_YYYYMMDD_HHMMSS_XXXXX
    
    def test_validate_registry_valid(self, sample_registry):
        """Test validation of valid registry"""
        errors = RegistryHelper.validate_registry(sample_registry)
        assert len(errors) == 0
    
    def test_validate_registry_missing_fields(self):
        """Test validation with missing required fields"""
        # Missing registry ID
        registry = ServiceRegistry(
            registry_id="",
            version="1.0.0",
            created_timestamp=datetime.now(timezone.utc).isoformat(),
            last_updated=datetime.now(timezone.utc).isoformat(),
            services={},
            total_services=0
        )
        errors = RegistryHelper.validate_registry(registry)
        assert any("Registry ID is required" in error for error in errors)
        
        # Missing version
        registry.registry_id = "test-id"
        registry.version = ""
        errors = RegistryHelper.validate_registry(registry)
        assert any("Registry version is required" in error for error in errors)
        
        # No services
        registry.version = "1.0.0"
        errors = RegistryHelper.validate_registry(registry)
        assert any("at least one service" in error for error in errors)
    
    def test_validate_registry_count_mismatch(self, sample_registry):
        """Test validation with service count mismatch"""
        sample_registry.total_services = 5  # Actual is 1
        errors = RegistryHelper.validate_registry(sample_registry)
        assert any("Total services count" in error for error in errors)
    
    def test_validate_service_definition(self, sample_service):
        """Test service definition validation"""
        # Valid service
        errors = RegistryHelper.validate_service_definition(sample_service, "user_management")
        assert len(errors) == 0
        
        # Name mismatch
        errors = RegistryHelper.validate_service_definition(sample_service, "wrong_name")
        assert any("name mismatch" in error for error in errors)
        
        # Missing description
        sample_service.service_description = ""
        errors = RegistryHelper.validate_service_definition(sample_service)
        assert any("missing description" in error for error in errors)
        
        # No operations
        sample_service.service_description = "Test service"
        sample_service.tier1_operations = {}
        sample_service.tier2_operations = {}
        errors = RegistryHelper.validate_service_definition(sample_service)
        assert any("has no operations" in error for error in errors)
    
    def test_validate_service_operation(self, sample_operation):
        """Test service operation validation"""
        # Valid operation
        errors = RegistryHelper.validate_service_operation(sample_operation, "read")
        assert len(errors) == 0
        
        # Missing endpoint
        sample_operation.endpoint = None
        errors = RegistryHelper.validate_service_operation(sample_operation, "read")
        assert any("missing endpoint" in error for error in errors)
        
        # Invalid confidence score
        sample_operation.confidence_score = 1.5
        errors = RegistryHelper.validate_service_operation(sample_operation, "read")
        assert any("invalid confidence score" in error for error in errors)
    
    def test_validate_api_endpoint(self, sample_endpoint):
        """Test API endpoint validation"""
        # Valid endpoint
        errors = RegistryHelper.validate_api_endpoint(sample_endpoint)
        assert len(errors) == 0
        
        # Missing path
        sample_endpoint.path = ""
        errors = RegistryHelper.validate_api_endpoint(sample_endpoint)
        assert any("path is required" in error for error in errors)
        
        # Invalid path format
        sample_endpoint.path = "api/users"  # Missing leading slash
        errors = RegistryHelper.validate_api_endpoint(sample_endpoint)
        assert any("should start with '/'" in error for error in errors)
        
        # Invalid HTTP method
        sample_endpoint.path = "/api/users"
        sample_endpoint.method = "INVALID"
        errors = RegistryHelper.validate_api_endpoint(sample_endpoint)
        assert any("Invalid HTTP method" in error for error in errors)
    
    def test_validate_cross_service_consistency(self, sample_service):
        """Test cross-service consistency validation"""
        # Create registry with duplicate endpoints
        service2 = ServiceDefinition(
            service_name="account_service",
            service_description="Account service",
            business_context="Account management",
            keywords=["account"],
            synonyms=[],
            tier1_operations={
                "read": sample_service.tier1_operations["read"]  # Duplicate endpoint
            },
            tier2_operations={}
        )
        
        registry = ServiceRegistry(
            registry_id="test-registry",
            version="1.0.0",
            created_timestamp=datetime.now(timezone.utc).isoformat(),
            last_updated=datetime.now(timezone.utc).isoformat(),
            services={
                "user_management": sample_service,
                "account_service": service2
            },
            total_services=2
        )
        
        errors = RegistryHelper.validate_cross_service_consistency(registry)
        assert any("Duplicate endpoint" in error for error in errors)
        
        # Test keyword overlap
        service2.tier1_operations = {}  # Remove duplicate endpoint
        service2.keywords = ["user", "profile"]  # Overlapping keywords
        errors = RegistryHelper.validate_cross_service_consistency(registry)
        assert any("Keyword overlap" in error for error in errors)
    
    def test_merge_services(self, sample_registry, sample_service):
        """Test service merging functionality"""
        # Create second service
        incident_service = ServiceDefinition(
            service_name="incident_management",
            service_description="Incident service",
            business_context="Incident handling",
            keywords=["incident", "ticket"],
            synonyms=["issue"],
            tier1_operations={},
            tier2_operations={}
        )
        
        sample_registry.services["incident_management"] = incident_service
        sample_registry.total_services = 2
        
        # Merge services
        merged_registry = RegistryHelper.merge_services(
            sample_registry,
            ["user_management", "incident_management"],
            "unified_service",
            "Unified service for users and incidents"
        )
        
        # Verify merge
        assert len(merged_registry.services) == 1
        assert "unified_service" in merged_registry.services
        
        unified = merged_registry.services["unified_service"]
        assert unified.service_description == "Unified service for users and incidents"
        assert "user" in unified.keywords
        assert "incident" in unified.keywords
        assert "issue" in unified.synonyms
        assert len(unified.tier1_operations) == 2  # From user_management
    
    def test_merge_services_errors(self, sample_registry):
        """Test merge service error cases"""
        # Empty source list
        with pytest.raises(ValueError, match="At least one source service"):
            RegistryHelper.merge_services(sample_registry, [], "new_service")
        
        # Non-existent service
        with pytest.raises(ValueError, match="Services not found"):
            RegistryHelper.merge_services(sample_registry, ["non_existent"], "new_service")
    
    def test_split_service(self, sample_service):
        """Test service splitting functionality"""
        # Add more operations
        delete_endpoint = APIEndpoint(
            path="/api/users/{id}",
            method="DELETE",
            operation_id="delete_user",
            description="Delete user",
            parameters={"id": {"type": "string", "required": True}}
        )
        
        delete_operation = ServiceOperation(
            endpoint=delete_endpoint,
            intent_verbs=["delete", "remove"],
            intent_objects=["user"],
            intent_indicators=["delete user"],
            description="Delete user",
            confidence_score=0.9
        )
        
        sample_service.tier1_operations["delete"] = delete_operation
        
        registry = ServiceRegistry(
            registry_id="test-registry",
            version="1.0.0",
            created_timestamp=datetime.now(timezone.utc).isoformat(),
            last_updated=datetime.now(timezone.utc).isoformat(),
            services={"user_management": sample_service},
            total_services=1
        )
        
        # Split service
        split_config = {
            "user_read_service": ["read"],
            "user_write_service": ["create", "delete"]
        }
        
        split_registry = RegistryHelper.split_service(
            registry,
            "user_management",
            split_config
        )
        
        # Verify split
        assert len(split_registry.services) == 2
        assert "user_read_service" in split_registry.services
        assert "user_write_service" in split_registry.services
        
        read_service = split_registry.services["user_read_service"]
        write_service = split_registry.services["user_write_service"]
        
        assert len(read_service.tier1_operations) == 1
        assert "read" in read_service.tier1_operations
        
        assert len(write_service.tier1_operations) == 2
        assert "create" in write_service.tier1_operations
        assert "delete" in write_service.tier1_operations
    
    def test_split_service_errors(self, sample_registry):
        """Test split service error cases"""
        # Non-existent service
        with pytest.raises(ValueError, match="Service .* not found"):
            RegistryHelper.split_service(sample_registry, "non_existent", {})
        
        # Missing operations in split config
        split_config = {
            "partial_service": ["read"]  # Missing "create"
        }
        with pytest.raises(ValueError, match="Missing operations"):
            RegistryHelper.split_service(sample_registry, "user_management", split_config)
        
        # Unknown operations in split config
        split_config = {
            "service1": ["read", "create", "unknown_op"]
        }
        with pytest.raises(ValueError, match="Unknown operations"):
            RegistryHelper.split_service(sample_registry, "user_management", split_config)
    
    def test_compare_registries(self, sample_registry, sample_service):
        """Test registry comparison"""
        # Create modified registry
        registry2 = ServiceRegistry(
            registry_id="test-registry-002",
            version="1.0.1",
            created_timestamp=datetime.now(timezone.utc).isoformat(),
            last_updated=datetime.now(timezone.utc).isoformat(),
            services={},
            total_services=0
        )
        
        # Add modified service
        modified_service = ServiceDefinition(
            service_name="user_management",
            service_description="Updated user service",  # Changed
            business_context=sample_service.business_context,
            keywords=["user", "account", "profile", "admin"],  # Added "admin"
            synonyms=["member"],  # Removed "person"
            tier1_operations=sample_service.tier1_operations,
            tier2_operations={}
        )
        registry2.services["user_management"] = modified_service
        
        # Add new service
        new_service = ServiceDefinition(
            service_name="new_service",
            service_description="New service",
            business_context="New context",
            keywords=["new"],
            synonyms=[],
            tier1_operations={},
            tier2_operations={}
        )
        registry2.services["new_service"] = new_service
        registry2.total_services = 2
        
        # Compare registries
        comparison = RegistryHelper.compare_registries(sample_registry, registry2)
        
        # Verify comparison results
        assert comparison["added_services"] == ["new_service"]
        assert comparison["removed_services"] == []
        assert len(comparison["modified_services"]) == 1
        
        modified = comparison["modified_services"][0]
        assert modified["service_name"] == "user_management"
        assert "description" in modified["changes"]
        assert "keywords" in modified["changes"]
        assert modified["changes"]["keywords"]["added"] == ["admin"]
        assert "synonyms" in modified["changes"]
        assert modified["changes"]["synonyms"]["removed"] == ["person"]
        
        # Summary verification
        summary = comparison["summary"]
        assert summary["total_services_before"] == 1
        assert summary["total_services_after"] == 2
        assert summary["services_added"] == 1
        assert summary["services_modified"] == 1
    
    def test_convert_raw_endpoint(self):
        """Test RawAPIEndpoint to APIEndpoint conversion"""
        raw_endpoint = RawAPIEndpoint(
            path="/api/test",
            method=HTTPMethod.POST,
            operation_id="test_operation",
            summary="Test operation summary",
            parameters=[APIParameter(
                name="test",
                location=ParameterLocation.QUERY,
                type="string",
                required=False
            )]
        )
        
        api_endpoint = RegistryHelper.convert_raw_endpoint_to_api_endpoint(raw_endpoint)
        
        assert api_endpoint.path == "/api/test"
        assert api_endpoint.method == "POST"
        assert api_endpoint.operation_id == "test_operation"
        assert api_endpoint.description == "Test operation summary"
        assert api_endpoint.parameters == {
            "test": {
                "name": "test",
                "location": "query",
                "type": "string",
                "required": False,
                "description": None
            }
        }
    
    def test_extract_service_statistics(self, sample_registry, sample_service):
        """Test service statistics extraction"""
        # Add another service with more operations
        service2 = ServiceDefinition(
            service_name="incident_service",
            service_description="Incident management",
            business_context="Handle incidents",
            keywords=["incident", "ticket", "issue"],
            synonyms=["problem"],
            tier1_operations={},
            tier2_operations={}
        )
        
        # Add some tier2 operations
        endpoint = APIEndpoint(
            path="/api/incidents/bulk",
            method="POST",
            operation_id="bulk_create_incidents",
            description="Bulk create incidents",
            parameters={}
        )
        operation = ServiceOperation(
            endpoint=endpoint,
            intent_verbs=["create"],
            intent_objects=["incidents"],
            intent_indicators=["bulk create"],
            description="Bulk operation",
            confidence_score=0.8
        )
        service2.tier2_operations["bulk_create"] = operation
        
        sample_registry.services["incident_service"] = service2
        sample_registry.total_services = 2
        
        # Extract statistics
        stats = RegistryHelper.extract_service_statistics(sample_registry)
        
        # Verify registry info
        assert stats["registry_info"]["registry_id"] == "test-registry-001"
        assert stats["registry_info"]["version"] == "1.0.0"
        assert stats["registry_info"]["total_services"] == 2
        
        # Verify service statistics
        service_stats = stats["service_statistics"]
        assert service_stats["total_services"] == 2
        assert service_stats["total_tier1_operations"] == 2
        assert service_stats["total_tier2_operations"] == 1
        assert service_stats["total_operations"] == 3
        assert service_stats["avg_operations_per_service"] == 1.5
        
        # Verify HTTP methods
        assert stats["http_methods"]["GET"] == 1
        assert stats["http_methods"]["POST"] == 2
        
        # Verify keywords
        assert stats["keywords"]["user"] == 1
        assert stats["keywords"]["incident"] == 1
        
        # Verify service details
        assert len(stats["service_details"]) == 2
        user_detail = next(d for d in stats["service_details"] if d["service_name"] == "user_management")
        assert user_detail["tier1_operations"] == 2
        assert user_detail["tier2_operations"] == 0
        assert user_detail["keywords_count"] == 3


class TestConvenienceFunctions:
    """Test module-level convenience functions"""
    
    @pytest.fixture
    def sample_registry(self):
        """Create a simple test registry"""
        endpoint = APIEndpoint(
            path="/api/test",
            method="GET",
            operation_id="test_op",
            description="Test",
            parameters={}
        )
        
        operation = ServiceOperation(
            endpoint=endpoint,
            intent_verbs=["get"],
            intent_objects=["test"],
            intent_indicators=["get test"],
            description="Test operation",
            confidence_score=0.9
        )
        
        service = ServiceDefinition(
            service_name="test_service",
            service_description="Test service",
            business_context="Testing",
            keywords=["test"],
            synonyms=[],
            tier1_operations={"read": operation},
            tier2_operations={}
        )
        
        return ServiceRegistry(
            registry_id="test-registry",
            version="1.0.0",
            created_timestamp=datetime.now(timezone.utc).isoformat(),
            last_updated=datetime.now(timezone.utc).isoformat(),
            services={"test_service": service},
            total_services=1
        )
    
    def test_validate_registry_function(self, sample_registry):
        """Test validate_registry convenience function"""
        errors = validate_registry(sample_registry)
        assert len(errors) == 0
        
        # Test with invalid registry
        sample_registry.total_services = 10
        errors = validate_registry(sample_registry)
        assert len(errors) > 0
    
    def test_merge_services_function(self, sample_registry):
        """Test merge_services convenience function"""
        # Add another service
        service2 = sample_registry.services["test_service"].copy()
        service2.service_name = "test_service2"
        sample_registry.services["test_service2"] = service2
        sample_registry.total_services = 2
        
        merged = merge_services(
            sample_registry,
            ["test_service", "test_service2"],
            "merged_service"
        )
        
        assert len(merged.services) == 1
        assert "merged_service" in merged.services
    
    def test_split_service_function(self, sample_registry):
        """Test split_service convenience function"""
        split_config = {
            "new_service": ["read"]
        }
        
        split_registry = split_service(
            sample_registry,
            "test_service",
            split_config
        )
        
        assert len(split_registry.services) == 1
        assert "new_service" in split_registry.services
    
    def test_compare_registries_function(self, sample_registry):
        """Test compare_registries convenience function"""
        registry2 = sample_registry.copy()
        registry2.registry_id = "test-registry-2"
        
        comparison = compare_registries(sample_registry, registry2)
        
        assert comparison["summary"]["services_unchanged"] == 1
        assert comparison["summary"]["services_added"] == 0
        assert comparison["summary"]["services_removed"] == 0
    
    def test_extract_service_statistics_function(self, sample_registry):
        """Test extract_service_statistics convenience function"""
        stats = extract_service_statistics(sample_registry)
        
        assert stats["registry_info"]["registry_id"] == "test-registry"
        assert stats["service_statistics"]["total_services"] == 1
        assert stats["service_statistics"]["total_operations"] == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])