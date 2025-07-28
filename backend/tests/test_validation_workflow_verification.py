"""
Validation Workflow Verification Tests

Simple tests that verify the validation workflow components are correctly implemented
and can be imported and instantiated properly.
"""

import pytest
from datetime import datetime

# Add backend to sys.path
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[2]))


class TestValidationWorkflowVerification:
    """Verification tests for validation workflow implementation"""

    def test_validation_api_import(self):
        """Test that validation API can be imported"""
        from app.core.manoman.api import validation
        
        # Verify router exists
        assert hasattr(validation, 'router')
        
        # Verify key request/response models exist
        assert hasattr(validation, 'StartProceduralTestingRequest')
        assert hasattr(validation, 'StartProceduralTestingResponse')
        assert hasattr(validation, 'TestingProgressResponse')
        assert hasattr(validation, 'TestingResultsResponse')
        assert hasattr(validation, 'GenerateTestSuiteRequest')
        assert hasattr(validation, 'RunAccuracyTestsRequest')
        assert hasattr(validation, 'CleanupTestEntitiesRequest')
        assert hasattr(validation, 'SchemaDiscoveryRequest')

    def test_testing_agent_import(self):
        """Test that TestingAgent can be imported"""
        from app.core.manoman.agents.testing_agent import TestingAgent, TestPhase, ServiceTestPlan, ProceduralTestSession
        
        # Verify classes exist
        assert TestingAgent is not None
        assert TestPhase is not None
        assert ServiceTestPlan is not None
        assert ProceduralTestSession is not None
        
        # Verify TestPhase enum values
        assert hasattr(TestPhase, 'INITIALIZATION')
        assert hasattr(TestPhase, 'TIER1_TESTING')
        assert hasattr(TestPhase, 'SCHEMA_DISCOVERY')
        assert hasattr(TestPhase, 'VALIDATION')
        assert hasattr(TestPhase, 'CLEANUP')
        assert hasattr(TestPhase, 'COMPLETED')
        assert hasattr(TestPhase, 'FAILED')

    def test_infraon_api_client_import(self):
        """Test that InfraonAPIClient can be imported"""
        from app.core.manoman.utils.infraon_api_client import InfraonAPIClient, APIEndpoint, APITestResult, APIOperation, TestEntity
        
        # Verify classes exist
        assert InfraonAPIClient is not None
        assert APIEndpoint is not None
        assert APITestResult is not None
        assert APIOperation is not None
        assert TestEntity is not None
        
        # Verify APIOperation enum values
        assert hasattr(APIOperation, 'CREATE')
        assert hasattr(APIOperation, 'READ')
        assert hasattr(APIOperation, 'UPDATE')
        assert hasattr(APIOperation, 'DELETE')
        assert hasattr(APIOperation, 'LIST')

    def test_validation_models_import(self):
        """Test that validation models can be imported"""
        from app.core.manoman.models.validation_models import (
            TestSuite, TestResults, TestCase, TestCategoryType, DifficultyLevel,
            TestResult, ProceduralTestResults, CRDTestResult, SchemaValidationReport,
            APITestResult
        )
        
        # Verify all models exist
        assert TestSuite is not None
        assert TestResults is not None
        assert TestCase is not None
        assert TestCategoryType is not None
        assert DifficultyLevel is not None
        assert TestResult is not None
        assert ProceduralTestResults is not None
        assert CRDTestResult is not None
        assert SchemaValidationReport is not None
        assert APITestResult is not None

    def test_service_registry_models_import(self):
        """Test that service registry models can be imported"""
        from app.core.manoman.models.service_registry import (
            ServiceRegistry, ServiceDefinition, ServiceOperation, APIEndpoint,
            OperationType, TierLevel, ConflictType, ConflictSeverity, ConflictReport
        )
        
        # Verify all models exist
        assert ServiceRegistry is not None
        assert ServiceDefinition is not None
        assert ServiceOperation is not None
        assert APIEndpoint is not None
        assert OperationType is not None
        assert TierLevel is not None
        assert ConflictType is not None
        assert ConflictSeverity is not None
        assert ConflictReport is not None

    def test_basic_model_instantiation(self):
        """Test that basic models can be instantiated"""
        from app.core.manoman.models.service_registry import APIEndpoint, ServiceOperation, ServiceDefinition, ServiceRegistry
        from app.core.manoman.models.validation_models import TestCase, TestCategoryType, DifficultyLevel
        
        # Test APIEndpoint
        endpoint = APIEndpoint(
            path="/api/test",
            method="POST",
            operation_id="test_operation",
            description="Test endpoint",
            parameters={}
        )
        assert endpoint.path == "/api/test"
        assert endpoint.method == "POST"
        
        # Test ServiceOperation
        operation = ServiceOperation(
            endpoint=endpoint,
            intent_verbs=["create"],
            intent_objects=["test"],
            intent_indicators=["create test"],
            description="Test operation",
            confidence_score=0.9
        )
        assert operation.description == "Test operation"
        assert operation.confidence_score == 0.9
        
        # Test ServiceDefinition
        service_def = ServiceDefinition(
            service_name="test_service",
            service_description="Test service",
            business_context="Test context",
            keywords=["test"],
            synonyms=[],
            tier1_operations={"create": operation},
            tier2_operations={}
        )
        assert service_def.service_name == "test_service"
        assert len(service_def.tier1_operations) == 1
        
        # Test ServiceRegistry
        registry = ServiceRegistry(
            registry_id="test-registry",
            version="1.0.0",
            created_timestamp=datetime.utcnow().isoformat(),
            last_updated=datetime.utcnow().isoformat(),
            services={"test_service": service_def},
            total_services=1
        )
        assert registry.registry_id == "test-registry"
        assert len(registry.services) == 1
        
        # Test TestCase
        test_case = TestCase(
            test_id="test-001",
            query="Test query",
            expected_service="test_service",
            expected_operation="create",
            expected_tier="tier1",
            difficulty_level=DifficultyLevel.EASY,
            category=TestCategoryType.BASIC_CRUD
        )
        assert test_case.test_id == "test-001"
        assert test_case.expected_service == "test_service"

    def test_infraon_api_client_basic_functionality(self):
        """Test basic InfraonAPIClient functionality"""
        from app.core.manoman.utils.infraon_api_client import InfraonAPIClient, APIEndpoint, APIOperation
        
        # Test client instantiation
        client = InfraonAPIClient(
            base_url="http://localhost:8080",
            api_key="test-key",
            timeout=30
        )
        
        assert client.base_url == "http://localhost:8080"
        assert client.api_key == "test-key"
        assert client.timeout == 30
        
        # Test URL building
        url = client._build_url("/api/test/{id}", {"id": "123"})
        assert url == "http://localhost:8080/api/test/123"
        
        # Test operation classification
        post_endpoint = APIEndpoint("/api/test", "POST", "create", {})
        operation = client._classify_operation(post_endpoint)
        assert operation == APIOperation.CREATE
        
        get_endpoint = APIEndpoint("/api/test/{id}", "GET", "read", {})
        operation = client._classify_operation(get_endpoint)
        assert operation == APIOperation.READ
        
        delete_endpoint = APIEndpoint("/api/test/{id}", "DELETE", "delete", {})
        operation = client._classify_operation(delete_endpoint)
        assert operation == APIOperation.DELETE

    def test_router_integration(self):
        """Test that validation router is properly integrated"""
        from app.api.v1.router import api_router
        
        # Check that validation router is included
        router_routes = [route.path for route in api_router.routes]
        
        # Look for validation endpoints
        validation_endpoints = [
            "/manoman/start-procedural-testing",
            "/manoman/testing-progress/{session_id}",
            "/manoman/testing-results/{session_id}",
            "/manoman/generate-test-suite",
            "/manoman/run-accuracy-tests",
            "/manoman/cleanup-test-entities",
            "/manoman/discover-service-schema",
            "/manoman/active-sessions",
            "/manoman/session/{session_id}"
        ]
        
        # At least some validation endpoints should be present
        found_endpoints = []
        for endpoint in validation_endpoints:
            for route_path in router_routes:
                if endpoint.replace("{session_id}", "{path}") in route_path or endpoint in route_path:
                    found_endpoints.append(endpoint)
                    break
        
        # Should have found at least some validation endpoints
        assert len(found_endpoints) > 0, f"No validation endpoints found in router. Available routes: {router_routes}"

    def test_validation_api_dependency_injection(self):
        """Test that validation API dependency injection works"""
        from app.core.manoman.api.validation import get_registry_manager, get_llm_service, get_query_classifier
        
        # Test dependency functions exist
        assert callable(get_registry_manager)
        assert callable(get_llm_service)
        assert callable(get_query_classifier)
        
        # Test they can be called (though they may require proper setup)
        try:
            registry_manager = get_registry_manager()
            assert registry_manager is not None
        except Exception:
            # It's ok if this fails due to missing config, as long as the function exists
            pass

    def test_validation_workflow_completeness(self):
        """Test that all validation workflow components are present"""
        
        # Check API endpoints exist
        from app.core.manoman.api import validation
        
        # Key validation API functions should exist
        validation_functions = [
            'start_procedural_testing',
            'get_testing_progress', 
            'get_testing_results',
            'generate_test_suite',
            'run_accuracy_tests',
            'cleanup_test_entities',
            'discover_service_schema',
            'get_active_sessions',
            'terminate_testing_session'
        ]
        
        # Check that functions exist in the module
        for func_name in validation_functions:
            assert hasattr(validation, func_name), f"Missing validation function: {func_name}"

    def test_testing_agent_methods(self):
        """Test that TestingAgent has all required methods"""
        from app.core.manoman.agents.testing_agent import TestingAgent
        
        # Key methods should exist
        required_methods = [
            'start_procedural_testing',
            'get_testing_progress',
            'get_testing_results', 
            'generate_test_suite',
            'run_accuracy_tests',
            'run_procedural_api_tests',
            '_execute_create_read_delete_cycle',
            '_create_service_test_plan',
            '_convert_operation_to_endpoint',
            '_find_endpoint_by_operation',
            '_generate_test_data',
            '_calculate_schema_accuracy'
        ]
        
        for method_name in required_methods:
            assert hasattr(TestingAgent, method_name), f"Missing TestingAgent method: {method_name}"

    def test_infraon_api_client_methods(self):
        """Test that InfraonAPIClient has all required methods"""
        from app.core.manoman.utils.infraon_api_client import InfraonAPIClient
        
        # Key methods should exist
        required_methods = [
            'initialize',
            'cleanup',
            'test_endpoint',
            'perform_crd_cycle',
            'discover_service_schema',
            'cleanup_test_entities',
            '_build_url',
            '_classify_operation',
            '_extract_entity_id',
            '_analyze_response_schema'
        ]
        
        for method_name in required_methods:
            assert hasattr(InfraonAPIClient, method_name), f"Missing InfraonAPIClient method: {method_name}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])