"""
Validation Workflow Integration Tests

Simple integration tests that verify the validation workflow components
work together correctly without complex mocking.
"""

import pytest
import asyncio
import uuid
from datetime import datetime

# Add backend to sys.path
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[2]))

from app.core.manoman.agents.testing_agent import TestingAgent, TestPhase
from app.core.manoman.models.service_registry import ServiceRegistry, ServiceDefinition, ServiceOperation, APIEndpoint
from app.core.manoman.models.validation_models import TestSuite, TestResults
from app.core.manoman.utils.infraon_api_client import InfraonAPIClient
from app.core.agents.base.llm_service import LLMService
from app.core.manoman.engines.query_classifier import QueryClassifier
from app.core.manoman.storage.registry_manager import RegistryManager


def create_test_registry():
    """Create a simple test registry for integration testing"""
    
    # Create test API endpoint
    create_endpoint = APIEndpoint(
        path="/api/test-entities",
        method="POST",
        operation_id="create_test_entity",
        description="Create a test entity",
        parameters={}
    )
    
    read_endpoint = APIEndpoint(
        path="/api/test-entities/{id}",
        method="GET", 
        operation_id="get_test_entity",
        description="Get test entity by ID",
        parameters={"id": {"type": "string", "required": True}}
    )
    
    delete_endpoint = APIEndpoint(
        path="/api/test-entities/{id}",
        method="DELETE",
        operation_id="delete_test_entity", 
        description="Delete test entity by ID",
        parameters={"id": {"type": "string", "required": True}}
    )
    
    # Create service operations
    create_op = ServiceOperation(
        endpoint=create_endpoint,
        intent_verbs=["create", "add", "new"],
        intent_objects=["test entity", "entity"],
        intent_indicators=["create new", "add entity"],
        description="Create a new test entity",
        confidence_score=0.9
    )
    
    read_op = ServiceOperation(
        endpoint=read_endpoint,
        intent_verbs=["get", "read", "show", "find"],
        intent_objects=["test entity", "entity"],
        intent_indicators=["get entity", "show entity"],
        description="Get test entity by ID",
        confidence_score=0.9
    )
    
    delete_op = ServiceOperation(
        endpoint=delete_endpoint,
        intent_verbs=["delete", "remove"],
        intent_objects=["test entity", "entity"],
        intent_indicators=["delete entity", "remove entity"],
        description="Delete test entity by ID",
        confidence_score=0.9
    )
    
    # Create service definition
    service_def = ServiceDefinition(
        service_name="test_entity_management",
        service_description="Service for managing test entities",
        business_context="Handles test entity CRUD operations for validation testing",
        keywords=["test", "entity", "management"],
        synonyms=["validation", "testing"],
        tier1_operations={
            "create": create_op,
            "read": read_op,
            "delete": delete_op
        },
        tier2_operations={}
    )
    
    # Create registry
    registry = ServiceRegistry(
        registry_id="test-validation-registry-001",
        version="1.0.0",
        created_timestamp=datetime.utcnow().isoformat(),
        last_updated=datetime.utcnow().isoformat(),
        services={"test_entity_management": service_def},
        total_services=1
    )
    
    return registry


class TestValidationWorkflowIntegration:
    """Integration tests for validation workflow components"""

    @pytest.mark.asyncio
    async def test_testing_agent_initialization(self):
        """Test that TestingAgent can be initialized with all dependencies"""
        
        # Create mock dependencies
        llm_service = LLMService()
        query_classifier = QueryClassifier()
        api_client = InfraonAPIClient(base_url="http://localhost:8080", timeout=30)
        registry_manager = RegistryManager()
        
        # Initialize testing agent
        testing_agent = TestingAgent(
            llm_service=llm_service,
            query_classifier=query_classifier,
            api_client=api_client,
            registry_manager=registry_manager
        )
        
        # Verify initialization
        assert testing_agent.llm_service is not None
        assert testing_agent.query_classifier is not None
        assert testing_agent.api_client is not None
        assert testing_agent.registry_manager is not None
        assert testing_agent.active_sessions == {}
        assert "default" in testing_agent.test_data_templates
        
    @pytest.mark.asyncio
    async def test_test_suite_generation(self):
        """Test test suite generation from service registry"""
        
        # Create test registry
        registry = create_test_registry()
        
        # Initialize testing agent with minimal dependencies
        llm_service = LLMService()
        query_classifier = QueryClassifier()
        api_client = InfraonAPIClient(base_url="http://localhost:8080", timeout=30)
        registry_manager = RegistryManager()
        
        testing_agent = TestingAgent(
            llm_service=llm_service,
            query_classifier=query_classifier,
            api_client=api_client,
            registry_manager=registry_manager
        )
        
        # Generate test suite
        test_suite = await testing_agent.generate_test_suite(registry)
        
        # Verify test suite
        assert test_suite is not None
        assert test_suite.total_tests > 0
        assert test_suite.service_registry_version == "1.0.0"
        assert len(test_suite.test_categories) > 0
        
        # Verify test categories contain tests
        basic_crud_tests = test_suite.test_categories.get("basic_crud", [])
        assert len(basic_crud_tests) > 0
        
        # Verify test case structure
        if basic_crud_tests:
            test_case = basic_crud_tests[0]
            assert hasattr(test_case, 'test_id')
            assert hasattr(test_case, 'query')
            assert hasattr(test_case, 'expected_service')
            assert hasattr(test_case, 'expected_operation')

    @pytest.mark.asyncio
    async def test_accuracy_testing_workflow(self):
        """Test accuracy testing workflow components"""
        
        # Create test registry
        registry = create_test_registry()
        
        # Initialize testing agent
        llm_service = LLMService()
        query_classifier = QueryClassifier()
        api_client = InfraonAPIClient(base_url="http://localhost:8080", timeout=30)
        registry_manager = RegistryManager()
        
        testing_agent = TestingAgent(
            llm_service=llm_service,
            query_classifier=query_classifier,
            api_client=api_client,
            registry_manager=registry_manager
        )
        
        # Generate test suite
        test_suite = await testing_agent.generate_test_suite(registry)
        
        # Run accuracy tests
        test_results = await testing_agent.run_accuracy_tests(registry, test_suite)
        
        # Verify test results
        assert test_results is not None
        assert test_results.total_tests == test_suite.total_tests
        assert test_results.passed >= 0
        assert test_results.failed >= 0
        assert test_results.passed + test_results.failed == test_results.total_tests
        assert 0 <= test_results.accuracy_percentage <= 100
        assert test_results.execution_time_total_ms >= 0
        assert len(test_results.detailed_results) == test_results.total_tests

    @pytest.mark.asyncio
    async def test_service_test_plan_creation(self):
        """Test creation of service test plans"""
        
        # Create test registry
        registry = create_test_registry()
        service_def = registry.services["test_entity_management"]
        
        # Initialize testing agent
        llm_service = LLMService()
        query_classifier = QueryClassifier()
        api_client = InfraonAPIClient(base_url="http://localhost:8080", timeout=30)
        registry_manager = RegistryManager()
        
        testing_agent = TestingAgent(
            llm_service=llm_service,
            query_classifier=query_classifier,
            api_client=api_client,
            registry_manager=registry_manager
        )
        
        # Create test plan
        test_plan = await testing_agent._create_service_test_plan(
            "test_entity_management",
            service_def
        )
        
        # Verify test plan
        assert test_plan is not None
        assert test_plan.service_name == "test_entity_management"
        assert test_plan.service_definition == service_def
        assert len(test_plan.tier1_endpoints) > 0
        assert len(test_plan.tier2_endpoints) == 0
        
        # Verify endpoints are properly converted
        endpoint_methods = [ep.method for ep in test_plan.tier1_endpoints]
        assert "POST" in endpoint_methods
        assert "GET" in endpoint_methods
        assert "DELETE" in endpoint_methods

    @pytest.mark.asyncio
    async def test_operation_to_endpoint_conversion(self):
        """Test conversion of service operations to API endpoints"""
        
        # Create test registry
        registry = create_test_registry()
        service_def = registry.services["test_entity_management"]
        create_operation = service_def.tier1_operations["create"]
        
        # Initialize testing agent
        llm_service = LLMService()
        query_classifier = QueryClassifier()
        api_client = InfraonAPIClient(base_url="http://localhost:8080", timeout=30)
        registry_manager = RegistryManager()
        
        testing_agent = TestingAgent(
            llm_service=llm_service,
            query_classifier=query_classifier,
            api_client=api_client,
            registry_manager=registry_manager
        )
        
        # Convert operation to endpoint
        endpoint = testing_agent._convert_operation_to_endpoint(create_operation)
        
        # Verify conversion
        assert endpoint is not None
        assert endpoint.path == "/api/test-entities"
        assert endpoint.method == "POST"
        assert endpoint.operation_id == "create_test_entity"
        assert hasattr(endpoint, 'authentication_required')

    def test_test_data_generation(self):
        """Test generation of test data for services"""
        
        # Initialize testing agent
        llm_service = LLMService()
        query_classifier = QueryClassifier()
        api_client = InfraonAPIClient(base_url="http://localhost:8080", timeout=30)
        registry_manager = RegistryManager()
        
        testing_agent = TestingAgent(
            llm_service=llm_service,
            query_classifier=query_classifier,
            api_client=api_client,
            registry_manager=registry_manager
        )
        
        # Test known service template
        user_test_data = testing_agent._generate_test_data("user_management")
        assert "username" in user_test_data
        assert "email" in user_test_data
        assert "test_user_" in user_test_data["username"]
        
        # Test default template
        default_test_data = testing_agent._generate_test_data("unknown_service")
        assert "name" in default_test_data
        assert "description" in default_test_data
        assert "Test Entity" in default_test_data["name"]
        
        # Verify UUID replacement
        assert "{{uuid}}" not in str(user_test_data)
        assert "{{uuid}}" not in str(default_test_data)

    def test_endpoint_classification(self):
        """Test endpoint operation classification"""
        
        # Initialize testing agent
        llm_service = LLMService()
        query_classifier = QueryClassifier()
        api_client = InfraonAPIClient(base_url="http://localhost:8080", timeout=30)
        registry_manager = RegistryManager()
        
        testing_agent = TestingAgent(
            llm_service=llm_service,
            query_classifier=query_classifier,
            api_client=api_client,
            registry_manager=registry_manager
        )
        
        # Test endpoint finding
        from app.core.manoman.utils.infraon_api_client import APIEndpoint as ClientAPIEndpoint
        
        endpoints = [
            ClientAPIEndpoint("/api/test", "POST", "create", {}),
            ClientAPIEndpoint("/api/test/{id}", "GET", "read", {}),
            ClientAPIEndpoint("/api/test", "GET", "list", {}),
            ClientAPIEndpoint("/api/test/{id}", "DELETE", "delete", {})
        ]
        
        # Test finding POST endpoint without ID
        create_endpoint = testing_agent._find_endpoint_by_operation(endpoints, "POST", with_id=False)
        assert create_endpoint is not None
        assert create_endpoint.method == "POST"
        assert "{id}" not in create_endpoint.path
        
        # Test finding GET endpoint with ID
        read_endpoint = testing_agent._find_endpoint_by_operation(endpoints, "GET", with_id=True)
        assert read_endpoint is not None
        assert read_endpoint.method == "GET"
        assert "{id}" in read_endpoint.path
        
        # Test finding DELETE endpoint
        delete_endpoint = testing_agent._find_endpoint_by_operation(endpoints, "DELETE")
        assert delete_endpoint is not None
        assert delete_endpoint.method == "DELETE"

    def test_schema_accuracy_calculation(self):
        """Test schema accuracy calculation"""
        
        # Initialize testing agent
        llm_service = LLMService()
        query_classifier = QueryClassifier()
        api_client = InfraonAPIClient(base_url="http://localhost:8080", timeout=30)
        registry_manager = RegistryManager()
        
        testing_agent = TestingAgent(
            llm_service=llm_service,
            query_classifier=query_classifier,
            api_client=api_client,
            registry_manager=registry_manager
        )
        
        # Test perfect match
        documented = {
            "create_request": {
                "type": "object",
                "properties": {"name": {"type": "string"}, "description": {"type": "string"}}
            }
        }
        
        discovered = {
            "create": {
                "type": "object", 
                "properties": {"name": {"type": "string"}, "description": {"type": "string"}}
            }
        }
        
        accuracy = testing_agent._calculate_schema_accuracy(documented, discovered)
        assert accuracy == 1.0  # Perfect match
        
        # Test partial match
        discovered_partial = {
            "create": {
                "type": "object",
                "properties": {"name": {"type": "string"}}  # Missing description
            }
        }
        
        accuracy = testing_agent._calculate_schema_accuracy(documented, discovered_partial)
        assert accuracy == 0.5  # 50% match

    def test_documented_schema_extraction(self):
        """Test extraction of documented schema from service definition"""
        
        # Create test registry
        registry = create_test_registry()
        service_def = registry.services["test_entity_management"]
        
        # Initialize testing agent
        llm_service = LLMService()
        query_classifier = QueryClassifier()
        api_client = InfraonAPIClient(base_url="http://localhost:8080", timeout=30)
        registry_manager = RegistryManager()
        
        testing_agent = TestingAgent(
            llm_service=llm_service,
            query_classifier=query_classifier,
            api_client=api_client,
            registry_manager=registry_manager
        )
        
        # Extract documented schema
        schema = testing_agent._extract_documented_schema(service_def)
        
        # Verify schema extraction (should handle missing request/response schemas gracefully)
        assert isinstance(schema, dict)
        
    @pytest.mark.asyncio
    async def test_api_client_initialization(self):
        """Test InfraonAPIClient initialization"""
        
        # Test basic initialization
        api_client = InfraonAPIClient(
            base_url="http://localhost:8080",
            api_key="test-key",
            timeout=30
        )
        
        assert api_client.base_url == "http://localhost:8080"
        assert api_client.api_key == "test-key"
        assert api_client.timeout == 30
        assert api_client.session is None
        assert api_client.test_entities == []
        assert api_client.cleanup_queue == []
        
        # Test URL building
        url = api_client._build_url("/api/test/{id}", {"id": "123"})
        assert url == "http://localhost:8080/api/test/123"
        
        # Test operation classification
        from app.core.manoman.utils.infraon_api_client import APIEndpoint, APIOperation
        
        post_endpoint = APIEndpoint("/api/test", "POST", "create", {})
        operation = api_client._classify_operation(post_endpoint)
        assert operation == APIOperation.CREATE
        
        get_endpoint = APIEndpoint("/api/test/{id}", "GET", "read", {})
        operation = api_client._classify_operation(get_endpoint)
        assert operation == APIOperation.READ
        
        delete_endpoint = APIEndpoint("/api/test/{id}", "DELETE", "delete", {})
        operation = api_client._classify_operation(delete_endpoint)
        assert operation == APIOperation.DELETE


if __name__ == "__main__":
    pytest.main([__file__, "-v"])