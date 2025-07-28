"""
Tests for Enhanced Testing Agent

Tests the comprehensive procedural testing capabilities including:
- Create-Read-Delete cycle testing
- Schema discovery and validation
- Performance metrics collection
- Test entity cleanup
"""

import pytest
import asyncio
import uuid
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime

from app.core.manoman.agents.testing_agent import TestingAgent, TestPhase, ServiceTestPlan, ProceduralTestSession
from app.core.manoman.models.service_registry import ServiceRegistry, ServiceDefinition, ServiceOperation
from app.core.manoman.models.validation_models import TestSuite, TestResults, ProceduralTestResults
from app.core.manoman.utils.infraon_api_client import InfraonAPIClient, APIEndpoint, APITestResult, APIOperation
from app.core.agents.base.llm_service import LLMService
from app.core.manoman.engines.query_classifier import QueryClassifier
from app.core.manoman.storage.registry_manager import RegistryManager


@pytest.fixture
def mock_llm_service():
    """Mock LLM service"""
    llm = Mock(spec=LLMService)
    llm.generate_response = AsyncMock(return_value="Mock LLM response")
    return llm


@pytest.fixture
def mock_query_classifier():
    """Mock query classifier"""
    classifier = Mock(spec=QueryClassifier)
    classifier.classify_query = AsyncMock(return_value={
        "service": "test_service",
        "operation": "create",
        "confidence": 0.95
    })
    return classifier


@pytest.fixture
def mock_api_client():
    """Mock Infraon API client"""
    client = Mock(spec=InfraonAPIClient)
    
    # Mock successful CRD cycle
    create_result = APITestResult(
        endpoint=APIEndpoint("/api/test", "POST", "create_test", {}),
        operation=APIOperation.CREATE,
        success=True,
        response_status=201,
        response_data={"id": "test-123", "name": "Test Entity"},
        execution_time_ms=120.5,
        discovered_schema={"type": "object", "properties": {"id": {"type": "string"}}}
    )
    
    read_result = APITestResult(
        endpoint=APIEndpoint("/api/test/{id}", "GET", "get_test", {}),
        operation=APIOperation.READ,
        success=True,
        response_status=200,
        response_data={"id": "test-123", "name": "Test Entity"},
        execution_time_ms=85.2,
        discovered_schema={"type": "object", "properties": {"id": {"type": "string"}}}
    )
    
    delete_result = APITestResult(
        endpoint=APIEndpoint("/api/test/{id}", "DELETE", "delete_test", {}),
        operation=APIOperation.DELETE,
        success=True,
        response_status=204,
        response_data={},
        execution_time_ms=95.1
    )
    
    client.perform_crd_cycle = AsyncMock(return_value={
        "create": create_result,
        "read": read_result, 
        "delete": delete_result
    })
    
    client.test_endpoint = AsyncMock(return_value=create_result)
    client.cleanup_test_entities = AsyncMock(return_value={
        "total_entities": 5,
        "cleanup_successful": 5,
        "cleanup_failed": 0,
        "manual_cleanup_required": []
    })
    
    return client


@pytest.fixture
def mock_registry_manager():
    """Mock registry manager"""
    manager = Mock(spec=RegistryManager)
    manager.load_registry = Mock()
    manager.save_registry = Mock()
    return manager


@pytest.fixture
def sample_service_registry():
    """Create a sample service registry for testing"""
    
    # Create test API endpoints
    from app.core.manoman.models.service_registry import APIEndpoint
    
    create_endpoint = APIEndpoint(
        path="/api/business-rules",
        method="POST",
        operation_id="create_business_rule",
        description="Create a new business rule",
        parameters={}
    )
    
    read_endpoint = APIEndpoint(
        path="/api/business-rules/{id}",
        method="GET", 
        operation_id="get_business_rule",
        description="Get business rule by ID",
        parameters={"id": {"type": "string", "required": True}}
    )
    
    delete_endpoint = APIEndpoint(
        path="/api/business-rules/{id}",
        method="DELETE",
        operation_id="delete_business_rule", 
        description="Delete business rule by ID",
        parameters={"id": {"type": "string", "required": True}}
    )
    
    # Create test service operations
    create_op = ServiceOperation(
        endpoint=create_endpoint,
        intent_verbs=["create", "add", "new"],
        intent_objects=["business rule", "rule"],
        intent_indicators=["create new", "add rule"],
        description="Create a new business rule",
        confidence_score=0.9
    )
    
    read_op = ServiceOperation(
        endpoint=read_endpoint,
        intent_verbs=["get", "read", "show", "find"],
        intent_objects=["business rule", "rule"],
        intent_indicators=["get rule", "show rule"],
        description="Get business rule by ID",
        confidence_score=0.9
    )
    
    delete_op = ServiceOperation(
        endpoint=delete_endpoint,
        intent_verbs=["delete", "remove"],
        intent_objects=["business rule", "rule"],
        intent_indicators=["delete rule", "remove rule"],
        description="Delete business rule by ID",
        confidence_score=0.9
    )
    
    # Create test service definition
    service_def = ServiceDefinition(
        service_name="business_rule_management",
        service_description="Service for managing business rules",
        business_context="Handles business rule creation, modification, and enforcement",
        keywords=["business", "rule", "management"],
        synonyms=["policy", "regulation"],
        tier1_operations={
            "create": create_op,
            "read": read_op,
            "delete": delete_op
        },
        tier2_operations={}
    )
    
    # Create registry
    registry = ServiceRegistry(
        registry_id="test-registry-001",
        version="1.0.0",
        created_timestamp=datetime.utcnow().isoformat(),
        last_updated=datetime.utcnow().isoformat(),
        services={"business_rule_management": service_def},
        total_services=1
    )
    
    return registry


@pytest.fixture
def testing_agent(mock_llm_service, mock_query_classifier, mock_api_client, mock_registry_manager):
    """Create testing agent with mocked dependencies"""
    return TestingAgent(
        llm_service=mock_llm_service,
        query_classifier=mock_query_classifier,
        api_client=mock_api_client,
        registry_manager=mock_registry_manager
    )


class TestTestingAgent:
    """Test cases for the enhanced Testing Agent"""
    
    @pytest.mark.asyncio
    async def test_start_procedural_testing(self, testing_agent, sample_service_registry):
        """Test starting a procedural testing session"""
        session_id = await testing_agent.start_procedural_testing(
            registry=sample_service_registry,
            services_to_test=["business_rule_management"],
            max_concurrent_services=1
        )
        
        assert session_id is not None
        assert session_id in testing_agent.active_sessions
        
        session = testing_agent.active_sessions[session_id]
        assert session.phase == TestPhase.INITIALIZATION
        assert len(session.test_plans) == 1
        assert session.test_plans[0].service_name == "business_rule_management"
        
    @pytest.mark.asyncio
    async def test_get_testing_progress(self, testing_agent, sample_service_registry):
        """Test getting testing progress"""
        session_id = await testing_agent.start_procedural_testing(
            registry=sample_service_registry,
            services_to_test=["business_rule_management"]
        )
        
        # Wait a bit for background task to start
        await asyncio.sleep(0.1)
        
        progress = await testing_agent.get_testing_progress(session_id)
        
        assert progress["session_id"] == session_id
        assert "phase" in progress
        assert "services_total" in progress
        assert "progress_percentage" in progress
        assert progress["services_total"] == 1
        
    @pytest.mark.asyncio
    async def test_get_testing_progress_invalid_session(self, testing_agent):
        """Test getting progress for invalid session"""
        progress = await testing_agent.get_testing_progress("invalid-session-id")
        assert "error" in progress
        
    @pytest.mark.asyncio
    async def test_create_service_test_plan(self, testing_agent, sample_service_registry):
        """Test creating a service test plan"""
        service_name = "business_rule_management"
        service_def = sample_service_registry.services[service_name]
        
        test_plan = await testing_agent._create_service_test_plan(service_name, service_def)
        
        assert test_plan is not None
        assert test_plan.service_name == service_name
        assert test_plan.service_definition == service_def
        assert len(test_plan.tier1_endpoints) == 3  # create, read, delete
        assert len(test_plan.tier2_endpoints) == 0
        
        # Check endpoints are properly converted
        endpoint_methods = [ep.method for ep in test_plan.tier1_endpoints]
        assert "POST" in endpoint_methods
        assert "GET" in endpoint_methods
        assert "DELETE" in endpoint_methods
        
    @pytest.mark.asyncio
    async def test_convert_operation_to_endpoint(self, testing_agent):
        """Test converting service operation to API endpoint"""
        operation = ServiceOperation(
            operation_id="test_op",
            operation_name="Test Operation",
            api_path="/api/test",
            http_method="POST",
            operation_type="create",
            description="Test operation",
            parameters={},
            requires_auth=True
        )
        
        endpoint = testing_agent._convert_operation_to_endpoint(operation)
        
        assert endpoint is not None
        assert endpoint.path == "/api/test"
        assert endpoint.method == "POST"
        assert endpoint.operation_id == "test_op"
        assert endpoint.authentication_required == True
        
    def test_find_endpoint_by_operation(self, testing_agent):
        """Test finding endpoints by operation type"""
        endpoints = [
            APIEndpoint("/api/test", "POST", "create", {}),
            APIEndpoint("/api/test/{id}", "GET", "read", {}),
            APIEndpoint("/api/test", "GET", "list", {}),
            APIEndpoint("/api/test/{id}", "DELETE", "delete", {})
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
        
    def test_generate_test_data(self, testing_agent):
        """Test generating test data for services"""
        # Test with known service template
        test_data = testing_agent._generate_test_data("user_management")
        assert "username" in test_data
        assert "email" in test_data
        assert "test_user_" in test_data["username"]
        
        # Test with default template
        test_data = testing_agent._generate_test_data("unknown_service")
        assert "name" in test_data
        assert "description" in test_data
        assert "Test Entity" in test_data["name"]
        
    def test_extract_documented_schema(self, testing_agent, sample_service_registry):
        """Test extracting documented schema from service definition"""
        service_def = sample_service_registry.services["business_rule_management"]
        schema = testing_agent._extract_documented_schema(service_def)
        
        assert "create_request" in schema
        assert "read_response" in schema
        assert schema["create_request"]["type"] == "object"
        
    def test_calculate_schema_accuracy(self, testing_agent):
        """Test calculating schema accuracy between documented and discovered schemas"""
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
        
    @pytest.mark.asyncio
    async def test_execute_create_read_delete_cycle_success(self, testing_agent, sample_service_registry):
        """Test successful CRD cycle execution"""
        service_def = sample_service_registry.services["business_rule_management"]
        
        result = await testing_agent._execute_create_read_delete_cycle(service_def)
        
        assert result.service_name == "business_rule_management"
        assert result.overall_success == True
        assert result.create_result.success == True
        assert result.read_result.success == True
        assert result.delete_result.success == True
        assert result.cleanup_completed == True
        
    @pytest.mark.asyncio
    async def test_execute_create_read_delete_cycle_missing_endpoints(self, testing_agent):
        """Test CRD cycle with missing endpoints"""
        # Create service with no operations
        service_def = ServiceDefinition(
            service_name="incomplete_service",
            service_description="Service with missing operations",
            business_context="Test service",
            keywords=["test"],
            synonyms=[],
            tier1_operations={},  # No operations
            tier2_operations={}
        )
        
        result = await testing_agent._execute_create_read_delete_cycle(service_def)
        
        assert result.service_name == "incomplete_service"
        assert result.overall_success == False
        assert result.create_result.success == False
        assert result.cleanup_completed == False
        
    @pytest.mark.asyncio 
    async def test_full_procedural_testing_workflow(self, testing_agent, sample_service_registry):
        """Test the complete procedural testing workflow"""
        session_id = await testing_agent.start_procedural_testing(
            registry=sample_service_registry,
            services_to_test=["business_rule_management"],
            max_concurrent_services=1
        )
        
        # Wait for testing to complete
        max_wait = 10  # seconds
        wait_time = 0
        while wait_time < max_wait:
            progress = await testing_agent.get_testing_progress(session_id)
            if progress.get("phase") == TestPhase.COMPLETED.value:
                break
            await asyncio.sleep(0.5)
            wait_time += 0.5
            
        # Get final results
        results = await testing_agent.get_testing_results(session_id)
        
        assert results is not None
        assert results["session_id"] == session_id
        assert results["status"] == TestPhase.COMPLETED.value
        assert results["services_tested"] >= 1
        assert "results_by_service" in results
        assert "business_rule_management" in results["results_by_service"]
        
        service_results = results["results_by_service"]["business_rule_management"]
        assert "crd_cycle_success" in service_results
        assert "discovered_schemas" in service_results
        assert "performance_metrics" in service_results
        
    @pytest.mark.asyncio
    async def test_legacy_test_suite_generation(self, testing_agent, sample_service_registry):
        """Test the legacy test suite generation still works"""
        test_suite = await testing_agent.generate_test_suite(sample_service_registry)
        
        assert test_suite.total_tests > 0
        assert test_suite.service_registry_version == sample_service_registry.version
        assert len(test_suite.test_categories) > 0
        
    @pytest.mark.asyncio
    async def test_legacy_accuracy_tests(self, testing_agent, sample_service_registry):
        """Test the legacy accuracy testing functionality"""
        test_suite = await testing_agent.generate_test_suite(sample_service_registry)
        test_results = await testing_agent.run_accuracy_tests(sample_service_registry, test_suite)
        
        assert test_results.total_tests == test_suite.total_tests
        assert test_results.accuracy_percentage >= 0
        assert len(test_results.detailed_results) == test_suite.total_tests
        
    @pytest.mark.asyncio
    async def test_legacy_procedural_api_tests(self, testing_agent, sample_service_registry):
        """Test the legacy procedural API testing functionality"""
        service_name = "business_rule_management"
        service_def = sample_service_registry.services[service_name]
        
        results = await testing_agent.run_procedural_api_tests(service_name, service_def)
        
        assert results.service_name == service_name
        assert results.total_tier1_apis == len(service_def.tier1_operations)
        assert results.successful_crd_cycles >= 0
        assert results.schema_validation_accuracy >= 0
        
    def test_test_data_templates(self, testing_agent):
        """Test that test data templates are properly configured"""
        assert "user_management" in testing_agent.test_data_templates
        assert "asset_management" in testing_agent.test_data_templates
        assert "incident_management" in testing_agent.test_data_templates
        assert "default" in testing_agent.test_data_templates
        
        # Check template structure
        user_template = testing_agent.test_data_templates["user_management"]
        assert "create" in user_template
        assert "username" in user_template["create"]
        assert "{{uuid}}" in user_template["create"]["username"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])