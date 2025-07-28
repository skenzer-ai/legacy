"""
Tests for Validation API Endpoints

Tests the comprehensive validation API endpoints including:
- Procedural testing session management
- Schema discovery and validation
- Test entity cleanup
- Accuracy testing
"""

import pytest
import asyncio
import uuid
from unittest.mock import Mock, AsyncMock, patch
from fastapi.testclient import TestClient
from datetime import datetime

# Add backend to sys.path
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[2]))

from app.main import app
from app.core.manoman.agents.testing_agent import TestingAgent, TestPhase, ServiceTestPlan, ProceduralTestSession
from app.core.manoman.models.service_registry import ServiceRegistry, ServiceDefinition, ServiceOperation, APIEndpoint
from app.core.manoman.models.validation_models import TestSuite, TestResults
from app.core.manoman.utils.infraon_api_client import InfraonAPIClient, APITestResult, APIOperation
from app.core.agents.base.llm_service import LLMService
from app.core.manoman.engines.query_classifier import QueryClassifier
from app.core.manoman.storage.registry_manager import RegistryManager

client = TestClient(app)


@pytest.fixture
def sample_registry():
    """Create a sample service registry for testing"""
    
    # Create test API endpoint
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


class TestValidationAPI:
    """Test cases for validation API endpoints"""

    @patch('app.core.manoman.api.validation.get_testing_agent')
    @patch('app.core.manoman.api.validation.get_registry_manager')
    def test_start_procedural_testing(self, mock_registry_manager_dep, mock_testing_agent_dep, sample_registry):
        """Test starting procedural testing"""
        
        # Mock registry manager
        mock_registry_manager = Mock(spec=RegistryManager)
        mock_registry_manager.load_registry_async = AsyncMock(return_value=sample_registry)
        mock_registry_manager_dep.return_value = mock_registry_manager
        
        # Mock testing agent
        mock_testing_agent = Mock(spec=TestingAgent)
        mock_testing_agent.api_client = Mock(spec=InfraonAPIClient)
        mock_testing_agent.api_client.initialize = AsyncMock()
        mock_testing_agent.start_procedural_testing = AsyncMock(return_value="test-session-123")
        mock_testing_agent_dep.return_value = mock_testing_agent
        
        # Test request
        request_data = {
            "registry_id": "test-registry-001",
            "services_to_test": ["business_rule_management"],
            "max_concurrent_services": 1,
            "api_base_url": "http://localhost:8080",
            "api_credentials": {
                "api_key": "test-key"
            }
        }
        
        response = client.post("/api/v1/manoman/start-procedural-testing", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["session_id"] == "test-session-123"
        assert data["services_count"] == 1
        assert "message" in data
        assert "estimated_duration_minutes" in data
        
        # Verify calls
        mock_registry_manager.load_registry_async.assert_called_once_with("test-registry-001")
        mock_testing_agent.api_client.initialize.assert_called_once()
        mock_testing_agent.start_procedural_testing.assert_called_once()

    @patch('app.core.manoman.api.validation.get_testing_agent')
    def test_get_testing_progress(self, mock_testing_agent_dep):
        """Test getting testing progress"""
        
        # Mock testing agent
        mock_testing_agent = Mock(spec=TestingAgent)
        mock_testing_agent.get_testing_progress = AsyncMock(return_value={
            "session_id": "test-session-123",
            "phase": "tier1_testing",
            "services_total": 1,
            "services_completed": 0,
            "progress_percentage": 25.0,
            "current_service": "business_rule_management",
            "start_time": "2024-01-01T10:00:00Z",
            "elapsed_minutes": 2.5,
            "services_tested": 0,
            "successful_services": 0,
            "failed_services": 0,
            "success_rate": 0.0
        })
        mock_testing_agent_dep.return_value = mock_testing_agent
        
        response = client.get("/api/v1/manoman/testing-progress/test-session-123")
        
        assert response.status_code == 200
        data = response.json()
        assert data["session_id"] == "test-session-123"
        assert data["phase"] == "tier1_testing"
        assert data["services_total"] == 1
        assert data["progress_percentage"] == 25.0
        
        mock_testing_agent.get_testing_progress.assert_called_once_with("test-session-123")

    @patch('app.core.manoman.api.validation.get_testing_agent')
    @patch('app.core.manoman.api.validation.get_registry_manager')
    def test_generate_test_suite(self, mock_registry_manager_dep, mock_testing_agent_dep, sample_registry):
        """Test generating test suite"""
        
        # Mock registry manager
        mock_registry_manager = Mock(spec=RegistryManager)
        mock_registry_manager.load_registry_async = AsyncMock(return_value=sample_registry)
        mock_registry_manager_dep.return_value = mock_registry_manager
        
        # Mock test suite
        mock_test_suite = Mock(spec=TestSuite)
        mock_test_suite.suite_id = "test-suite-456"
        mock_test_suite.service_registry_version = "1.0.0"
        mock_test_suite.total_tests = 5
        mock_test_suite.test_categories = {
            "basic_crud": ["test1", "test2"],
            "service_identification": ["test3"]
        }
        
        # Mock testing agent
        mock_testing_agent = Mock(spec=TestingAgent)
        mock_testing_agent.generate_test_suite = AsyncMock(return_value=mock_test_suite)
        mock_testing_agent_dep.return_value = mock_testing_agent
        
        request_data = {
            "registry_id": "test-registry-001"
        }
        
        response = client.post("/api/v1/manoman/generate-test-suite", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["suite_id"] == "test-suite-456"
        assert data["total_tests"] == 5
        assert data["registry_version"] == "1.0.0"
        assert "test_categories" in data
        assert "message" in data
        
        mock_testing_agent.generate_test_suite.assert_called_once_with(sample_registry)

    @patch('app.core.manoman.api.validation.get_testing_agent')
    def test_cleanup_test_entities(self, mock_testing_agent_dep):
        """Test cleaning up test entities"""
        
        # Mock testing agent
        mock_testing_agent = Mock(spec=TestingAgent)
        mock_testing_agent.api_client = Mock(spec=InfraonAPIClient)
        mock_testing_agent.api_client.initialize = AsyncMock()
        mock_testing_agent.api_client.cleanup_test_entities = AsyncMock(return_value={
            "total_entities": 5,
            "cleanup_successful": 4,
            "cleanup_failed": 1,
            "manual_cleanup_required": [{"entity_id": "test-123", "service": "test_service"}]
        })
        mock_testing_agent_dep.return_value = mock_testing_agent
        
        request_data = {
            "api_base_url": "http://localhost:8080",
            "api_credentials": {
                "api_key": "test-key"
            }
        }
        
        response = client.post("/api/v1/manoman/cleanup-test-entities", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["cleanup_summary"]["total_entities"] == 5
        assert data["cleanup_summary"]["cleanup_successful"] == 4
        assert "message" in data
        
        mock_testing_agent.api_client.cleanup_test_entities.assert_called_once()

    def test_start_procedural_testing_registry_not_found(self):
        """Test starting procedural testing with non-existent registry"""
        
        with patch('app.core.manoman.api.validation.get_registry_manager') as mock_registry_manager_dep:
            mock_registry_manager = Mock(spec=RegistryManager)
            mock_registry_manager.load_registry_async = AsyncMock(return_value=None)
            mock_registry_manager_dep.return_value = mock_registry_manager
            
            request_data = {
                "registry_id": "non-existent-registry"
            }
            
            response = client.post("/api/v1/manoman/start-procedural-testing", json=request_data)
            
            assert response.status_code == 404
            assert "not found" in response.json()["detail"]

    def test_get_testing_progress_session_not_found(self):
        """Test getting progress for non-existent session"""
        
        with patch('app.core.manoman.api.validation.get_testing_agent') as mock_testing_agent_dep:
            mock_testing_agent = Mock(spec=TestingAgent)
            mock_testing_agent.get_testing_progress = AsyncMock(return_value={"error": "Session not found"})
            mock_testing_agent_dep.return_value = mock_testing_agent
            
            response = client.get("/api/v1/manoman/testing-progress/non-existent-session")
            
            assert response.status_code == 404
            assert "Session not found" in response.json()["detail"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])