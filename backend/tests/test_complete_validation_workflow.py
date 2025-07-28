"""
Complete Validation Workflow Tests

Tests the end-to-end validation workflow including:
- Integration between validation API endpoints
- Procedural testing session lifecycle
- Schema discovery and validation workflow
- Test entity cleanup workflow
- Accuracy testing workflow
"""

import pytest
import asyncio
import uuid
import json
from unittest.mock import Mock, AsyncMock, patch
from fastapi.testclient import TestClient
from datetime import datetime

# Add backend to sys.path
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[2]))

from app.main import app
from app.core.manoman.agents.testing_agent import TestingAgent, TestPhase
from app.core.manoman.models.service_registry import ServiceRegistry, ServiceDefinition, ServiceOperation, APIEndpoint
from app.core.manoman.models.validation_models import TestSuite, TestResults, TestCase, TestCategoryType, DifficultyLevel, TestResult
from app.core.manoman.utils.infraon_api_client import InfraonAPIClient, APITestResult, APIOperation
from app.core.manoman.storage.registry_manager import RegistryManager

@pytest.fixture(scope="module")
def client():
    """Test client for the FastAPI application"""
    return TestClient(app)

@pytest.fixture
def mock_registry_data():
    """Create mock registry data for testing"""
    
    # Create test API endpoints
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

@pytest.fixture
def mock_procedural_test_results():
    """Mock results for procedural testing"""
    return {
        "session_id": "test-session-123",
        "status": "completed",
        "start_time": "2024-01-01T10:00:00Z",
        "services_total": 1,
        "services_tested": 1,
        "successful_services": 1,
        "failed_services": 0,
        "results_by_service": {
            "test_entity_management": {
                "service_name": "test_entity_management",
                "crd_cycle_success": True,
                "schema_validation_accuracy": 0.95,
                "discovered_schemas": {
                    "create": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string"},
                            "description": {"type": "string"}
                        }
                    },
                    "read": {
                        "type": "object",
                        "properties": {
                            "id": {"type": "string"},
                            "name": {"type": "string"},
                            "description": {"type": "string"}
                        }
                    }
                },
                "parameter_validation": {
                    "required_fields": ["name"],
                    "optional_fields": ["description"]
                },
                "test_entity_cleanup": "completed",
                "performance_metrics": {
                    "avg_create_time_ms": 120.5,
                    "avg_read_time_ms": 85.2,
                    "avg_delete_time_ms": 95.1
                },
                "errors": []
            }
        },
        "schema_discrepancies": [],
        "cleanup_summary": {
            "total_entities": 3,
            "cleanup_successful": 3,
            "cleanup_failed": 0,
            "manual_cleanup_required": []
        },
        "performance_metrics": {
            "total_tests": 9,
            "avg_response_time_ms": 100.3,
            "success_rate": 1.0
        }
    }

@pytest.fixture  
def mock_test_suite():
    """Mock test suite for accuracy testing"""
    test_case = TestCase(
        test_id="test-case-001",
        query="Create a new test entity",
        expected_service="test_entity_management",
        expected_operation="create",
        expected_tier="tier1",
        difficulty_level=DifficultyLevel.EASY,
        category=TestCategoryType.BASIC_CRUD
    )
    
    return TestSuite(
        suite_id="test-suite-456",
        service_registry_version="1.0.0",
        total_tests=3,
        test_categories={
            "basic_crud": [test_case],
            "service_identification": [],
            "intent_classification": []
        }
    )

@pytest.fixture
def mock_accuracy_results():
    """Mock accuracy test results"""
    test_result = TestResult(
        test_id="test-case-001",
        query="Create a new test entity",
        expected_service="test_entity_management",
        actual_service="test_entity_management",
        expected_operation="create",
        actual_operation="create",
        success=True,
        execution_time_ms=15.5
    )
    
    return TestResults(
        suite_id="test-suite-456",
        total_tests=3,
        passed=3,
        failed=0,
        accuracy_percentage=100.0,
        detailed_results=[test_result],
        execution_time_total_ms=45.5
    )


class TestCompleteValidationWorkflow:
    """Test cases for complete validation workflow"""

    @patch('app.core.manoman.api.validation.get_testing_agent')
    @patch('app.core.manoman.api.validation.get_registry_manager')
    def test_end_to_end_procedural_testing_workflow(self, mock_registry_manager_dep, mock_testing_agent_dep, 
                                                   client, mock_registry_data, mock_procedural_test_results):
        """Test complete end-to-end procedural testing workflow"""
        
        # Setup mocks
        mock_registry_manager = Mock(spec=RegistryManager)
        mock_registry_manager.load_registry_async = AsyncMock(return_value=mock_registry_data)
        mock_registry_manager_dep.return_value = mock_registry_manager
        
        mock_testing_agent = Mock(spec=TestingAgent)
        mock_testing_agent.api_client = Mock(spec=InfraonAPIClient)
        mock_testing_agent.api_client.initialize = AsyncMock()
        
        # Mock progressive responses for session lifecycle
        session_id = "test-session-123"
        mock_testing_agent.start_procedural_testing = AsyncMock(return_value=session_id)
        
        # Mock progress responses (initial, in-progress, completed)
        progress_responses = [
            {
                "session_id": session_id,
                "phase": "initialization",
                "services_total": 1,
                "services_completed": 0,
                "progress_percentage": 0.0,
                "current_service": None,
                "start_time": "2024-01-01T10:00:00Z",
                "elapsed_minutes": 0.1
            },
            {
                "session_id": session_id,
                "phase": "tier1_testing",
                "services_total": 1,
                "services_completed": 0,
                "progress_percentage": 25.0,
                "current_service": "test_entity_management",
                "start_time": "2024-01-01T10:00:00Z",
                "elapsed_minutes": 1.5,
                "services_tested": 0,
                "successful_services": 0,
                "failed_services": 0,
                "success_rate": 0.0
            },
            {
                "session_id": session_id,
                "phase": "completed",
                "services_total": 1,
                "services_completed": 1,
                "progress_percentage": 100.0,
                "current_service": None,
                "start_time": "2024-01-01T10:00:00Z",
                "elapsed_minutes": 3.0,
                "services_tested": 1,
                "successful_services": 1,
                "failed_services": 0,
                "success_rate": 1.0
            }
        ]
        
        mock_testing_agent.get_testing_progress = AsyncMock(side_effect=progress_responses)
        mock_testing_agent.get_testing_results = AsyncMock(return_value=mock_procedural_test_results)
        mock_testing_agent_dep.return_value = mock_testing_agent
        
        # Step 1: Start procedural testing
        start_request = {
            "registry_id": "test-validation-registry-001",
            "services_to_test": ["test_entity_management"],
            "max_concurrent_services": 1,
            "api_base_url": "http://localhost:8080",
            "api_credentials": {
                "api_key": "test-validation-key"
            }
        }
        
        start_response = client.post("/api/v1/manoman/start-procedural-testing", json=start_request)
        
        assert start_response.status_code == 200
        start_data = start_response.json()
        assert start_data["session_id"] == session_id
        assert start_data["services_count"] == 1
        assert "estimated_duration_minutes" in start_data
        
        # Step 2: Check initial progress
        progress_response = client.get(f"/api/v1/manoman/testing-progress/{session_id}")
        
        assert progress_response.status_code == 200
        progress_data = progress_response.json()
        assert progress_data["session_id"] == session_id
        assert progress_data["phase"] == "initialization"
        assert progress_data["progress_percentage"] == 0.0
        
        # Step 3: Check in-progress status
        progress_response = client.get(f"/api/v1/manoman/testing-progress/{session_id}")
        
        assert progress_response.status_code == 200
        progress_data = progress_response.json()
        assert progress_data["phase"] == "tier1_testing"
        assert progress_data["current_service"] == "test_entity_management"
        assert progress_data["progress_percentage"] == 25.0
        
        # Step 4: Check completion status
        progress_response = client.get(f"/api/v1/manoman/testing-progress/{session_id}")
        
        assert progress_response.status_code == 200
        progress_data = progress_response.json()
        assert progress_data["phase"] == "completed"
        assert progress_data["progress_percentage"] == 100.0
        assert progress_data["success_rate"] == 1.0
        
        # Step 5: Get final results
        results_response = client.get(f"/api/v1/manoman/testing-results/{session_id}")
        
        assert results_response.status_code == 200
        results_data = results_response.json()
        assert results_data["session_id"] == session_id
        assert results_data["status"] == "completed"
        assert results_data["successful_services"] == 1
        assert results_data["failed_services"] == 0
        
        # Verify service-specific results
        service_results = results_data["results_by_service"]["test_entity_management"]
        assert service_results["crd_cycle_success"] is True
        assert service_results["schema_validation_accuracy"] == 0.95
        assert "discovered_schemas" in service_results
        assert "performance_metrics" in service_results
        
        # Verify cleanup was successful
        cleanup_summary = results_data["cleanup_summary"]
        assert cleanup_summary["total_entities"] == 3
        assert cleanup_summary["cleanup_successful"] == 3
        assert cleanup_summary["cleanup_failed"] == 0

    @patch('app.core.manoman.api.validation.get_testing_agent')
    @patch('app.core.manoman.api.validation.get_registry_manager')
    def test_accuracy_testing_workflow(self, mock_registry_manager_dep, mock_testing_agent_dep,
                                      client, mock_registry_data, mock_test_suite, mock_accuracy_results):
        """Test complete accuracy testing workflow"""
        
        # Setup mocks
        mock_registry_manager = Mock(spec=RegistryManager)
        mock_registry_manager.load_registry_async = AsyncMock(return_value=mock_registry_data)
        mock_registry_manager_dep.return_value = mock_registry_manager
        
        mock_testing_agent = Mock(spec=TestingAgent)
        mock_testing_agent.generate_test_suite = AsyncMock(return_value=mock_test_suite)
        mock_testing_agent.run_accuracy_tests = AsyncMock(return_value=mock_accuracy_results)
        mock_testing_agent_dep.return_value = mock_testing_agent
        
        # Step 1: Generate test suite
        generate_request = {
            "registry_id": "test-validation-registry-001"
        }
        
        generate_response = client.post("/api/v1/manoman/generate-test-suite", json=generate_request)
        
        assert generate_response.status_code == 200
        generate_data = generate_response.json()
        assert generate_data["suite_id"] == "test-suite-456"
        assert generate_data["total_tests"] == 3
        assert generate_data["registry_version"] == "1.0.0"
        assert "test_categories" in generate_data
        
        # Step 2: Run accuracy tests
        accuracy_request = {
            "registry_id": "test-validation-registry-001",
            "test_suite_id": "test-suite-456"
        }
        
        accuracy_response = client.post("/api/v1/manoman/run-accuracy-tests", json=accuracy_request)
        
        assert accuracy_response.status_code == 200
        accuracy_data = accuracy_response.json()
        assert accuracy_data["suite_id"] == "test-suite-456"
        assert accuracy_data["total_tests"] == 3
        assert accuracy_data["passed"] == 3
        assert accuracy_data["failed"] == 0
        assert accuracy_data["accuracy_percentage"] == 100.0
        assert "execution_time_total_ms" in accuracy_data
        assert "detailed_results" in accuracy_data

    @patch('app.core.manoman.api.validation.get_testing_agent')
    @patch('app.core.manoman.api.validation.get_registry_manager')
    def test_schema_discovery_workflow(self, mock_registry_manager_dep, mock_testing_agent_dep,
                                      client, mock_registry_data):
        """Test schema discovery workflow"""
        
        # Setup mocks
        mock_registry_manager = Mock(spec=RegistryManager)
        mock_registry_manager.load_registry_async = AsyncMock(return_value=mock_registry_data)
        mock_registry_manager_dep.return_value = mock_registry_manager
        
        mock_testing_agent = Mock(spec=TestingAgent)
        mock_testing_agent.api_client = Mock(spec=InfraonAPIClient)
        mock_testing_agent.api_client.initialize = AsyncMock()
        
        # Mock schema discovery results
        discovery_results = {
            "service_name": "test_entity_management",
            "operations": {
                "create": {
                    "endpoint": {
                        "path": "/api/test-entities",
                        "method": "POST",
                        "operation_id": "create_test_entity"
                    },
                    "schema": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string", "required": True},
                            "description": {"type": "string", "required": False}
                        }
                    },
                    "success": True,
                    "response_status": 201
                },
                "read": {
                    "endpoint": {
                        "path": "/api/test-entities/{id}",
                        "method": "GET",
                        "operation_id": "get_test_entity"
                    },
                    "schema": {
                        "type": "object",
                        "properties": {
                            "id": {"type": "string"},
                            "name": {"type": "string"},
                            "description": {"type": "string"}
                        }
                    },
                    "success": True,
                    "response_status": 200
                }
            },
            "discovery_timestamp": "2024-01-01T10:00:00Z",
            "endpoints_tested": 3
        }
        
        mock_testing_agent.api_client.discover_service_schema = AsyncMock(return_value=discovery_results)
        mock_testing_agent._convert_operation_to_endpoint = Mock(return_value=Mock())
        mock_testing_agent_dep.return_value = mock_testing_agent
        
        # Execute schema discovery
        discovery_request = {
            "registry_id": "test-validation-registry-001",
            "service_name": "test_entity_management",
            "api_base_url": "http://localhost:8080",
            "api_credentials": {
                "api_key": "test-validation-key"
            }
        }
        
        discovery_response = client.post("/api/v1/manoman/discover-service-schema", json=discovery_request)
        
        assert discovery_response.status_code == 200
        discovery_data = discovery_response.json()
        assert discovery_data["service_name"] == "test_entity_management"
        assert discovery_data["endpoints_tested"] == 3
        assert "discovered_schema" in discovery_data
        
        # Verify schema structure
        discovered_schema = discovery_data["discovered_schema"]
        assert "operations" in discovered_schema
        assert "create" in discovered_schema["operations"]
        assert "read" in discovered_schema["operations"]
        
        # Verify create operation schema
        create_schema = discovered_schema["operations"]["create"]["schema"]
        assert create_schema["type"] == "object"
        assert "name" in create_schema["properties"]
        assert "description" in create_schema["properties"]

    @patch('app.core.manoman.api.validation.get_testing_agent')
    def test_test_entity_cleanup_workflow(self, mock_testing_agent_dep, client):
        """Test test entity cleanup workflow"""
        
        # Setup mocks
        mock_testing_agent = Mock(spec=TestingAgent)
        mock_testing_agent.api_client = Mock(spec=InfraonAPIClient)
        mock_testing_agent.api_client.initialize = AsyncMock()
        
        # Mock cleanup results
        cleanup_results = {
            "total_entities": 5,
            "cleanup_attempted": 5,
            "cleanup_successful": 4,
            "cleanup_failed": 1,
            "manual_cleanup_required": [
                {
                    "entity_id": "test-entity-5",
                    "service": "test_entity_management",
                    "endpoint": "/api/test-entities/test-entity-5",
                    "error": "Entity not found"
                }
            ]
        }
        
        mock_testing_agent.api_client.cleanup_test_entities = AsyncMock(return_value=cleanup_results)
        mock_testing_agent_dep.return_value = mock_testing_agent
        
        # Execute cleanup
        cleanup_request = {
            "api_base_url": "http://localhost:8080",
            "api_credentials": {
                "api_key": "test-validation-key"
            }
        }
        
        cleanup_response = client.post("/api/v1/manoman/cleanup-test-entities", json=cleanup_request)
        
        assert cleanup_response.status_code == 200
        cleanup_data = cleanup_response.json()
        
        # Verify cleanup summary
        cleanup_summary = cleanup_data["cleanup_summary"]
        assert cleanup_summary["total_entities"] == 5
        assert cleanup_summary["cleanup_successful"] == 4
        assert cleanup_summary["cleanup_failed"] == 1
        assert len(cleanup_summary["manual_cleanup_required"]) == 1
        
        # Verify manual cleanup details
        manual_cleanup = cleanup_summary["manual_cleanup_required"][0]
        assert manual_cleanup["entity_id"] == "test-entity-5"
        assert manual_cleanup["service"] == "test_entity_management"
        assert "error" in manual_cleanup

    @patch('app.core.manoman.api.validation.get_testing_agent')
    def test_session_management_workflow(self, mock_testing_agent_dep, client):
        """Test session management workflow"""
        
        # Setup mocks
        mock_session = Mock()
        mock_session.phase = TestPhase.TIER1_TESTING
        mock_session.registry = Mock()
        mock_session.registry.registry_id = "test-validation-registry-001"
        mock_session.test_plans = [Mock(), Mock()]
        mock_session.current_service_index = 1
        mock_session.start_time = datetime(2024, 1, 1, 10, 0, 0)
        mock_session.results = {}
        
        mock_testing_agent = Mock(spec=TestingAgent)
        mock_testing_agent.active_sessions = {
            "test-session-123": mock_session,
            "test-session-456": mock_session
        }
        mock_testing_agent.api_client = Mock(spec=InfraonAPIClient)
        mock_testing_agent.api_client.cleanup_test_entities = AsyncMock(return_value={
            "total_entities": 2,
            "cleanup_successful": 2,
            "cleanup_failed": 0
        })
        mock_testing_agent_dep.return_value = mock_testing_agent
        
        # Step 1: Get active sessions
        sessions_response = client.get("/api/v1/manoman/active-sessions")
        
        assert sessions_response.status_code == 200
        sessions_data = sessions_response.json()
        assert sessions_data["total_sessions"] == 2
        assert len(sessions_data["active_sessions"]) == 2
        
        # Verify session details
        session_info = sessions_data["active_sessions"][0]
        assert "session_id" in session_info
        assert session_info["phase"] == "tier1_testing"
        assert session_info["registry_id"] == "test-validation-registry-001"
        assert session_info["services_total"] == 2
        
        # Step 2: Terminate a session
        terminate_response = client.delete("/api/v1/manoman/session/test-session-123")
        
        assert terminate_response.status_code == 200
        terminate_data = terminate_response.json()
        assert terminate_data["session_id"] == "test-session-123"
        assert terminate_data["message"] == "Testing session terminated"
        assert "cleanup_summary" in terminate_data
        
        # Verify cleanup was performed
        cleanup_summary = terminate_data["cleanup_summary"]
        assert cleanup_summary["total_entities"] == 2
        assert cleanup_summary["cleanup_successful"] == 2

    def test_validation_workflow_error_handling(self, client):
        """Test error handling in validation workflow"""
        
        # Test 1: Non-existent registry
        start_request = {
            "registry_id": "non-existent-registry"
        }
        
        with patch('app.core.manoman.api.validation.get_registry_manager') as mock_registry_manager_dep:
            mock_registry_manager = Mock(spec=RegistryManager)
            mock_registry_manager.load_registry_async = AsyncMock(return_value=None)
            mock_registry_manager_dep.return_value = mock_registry_manager
            
            response = client.post("/api/v1/manoman/start-procedural-testing", json=start_request)
            assert response.status_code == 404
            assert "not found" in response.json()["detail"]
        
        # Test 2: Non-existent session
        with patch('app.core.manoman.api.validation.get_testing_agent') as mock_testing_agent_dep:
            mock_testing_agent = Mock(spec=TestingAgent)
            mock_testing_agent.get_testing_progress = AsyncMock(return_value={"error": "Session not found"})
            mock_testing_agent_dep.return_value = mock_testing_agent
            
            response = client.get("/api/v1/manoman/testing-progress/non-existent-session")
            assert response.status_code == 404
            assert "Session not found" in response.json()["detail"]
        
        # Test 3: Non-existent service for schema discovery
        discovery_request = {
            "registry_id": "test-registry",
            "service_name": "non-existent-service",
            "api_base_url": "http://localhost:8080"
        }
        
        with patch('app.core.manoman.api.validation.get_registry_manager') as mock_registry_manager_dep:
            mock_registry_manager = Mock(spec=RegistryManager)
            mock_registry = Mock()
            mock_registry.services = {}  # Empty services
            mock_registry_manager.load_registry_async = AsyncMock(return_value=mock_registry)
            mock_registry_manager_dep.return_value = mock_registry_manager
            
            response = client.post("/api/v1/manoman/discover-service-schema", json=discovery_request)
            assert response.status_code == 404
            assert "not found in registry" in response.json()["detail"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])