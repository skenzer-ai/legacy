"""
Tests for the Testing Agent.

This test suite validates the functionality of the TestingAgent, including
test suite generation, accuracy testing, and procedural API testing.
"""

import pytest
from unittest.mock import MagicMock, AsyncMock

# Add backend to sys.path
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[2]))

from app.core.manoman.agents.testing_agent import TestingAgent
from app.core.agents.base.llm_service import LLMService
from app.core.manoman.models.service_registry import ServiceRegistry, ServiceDefinition, ServiceOperation, APIEndpoint
from app.core.manoman.models.validation_models import TestSuite, TestCase, TestCategoryType, DifficultyLevel, ProceduralTestResults, TestResults
from app.core.manoman.engines.query_classifier import QueryClassifier
from app.core.manoman.clients.infraon_api_client import InfraonAPIClient

@pytest.fixture
def mock_llm_service():
    """
    Mock LLMService for agent testing.
    """
    return MagicMock(spec=LLMService)

@pytest.fixture
def mock_query_classifier():
    """
    Mock QueryClassifier for agent testing.
    """
    return MagicMock(spec=QueryClassifier)

@pytest.fixture
def mock_api_client():
    """
    Mock InfraonAPIClient for agent testing.
    """
    return MagicMock(spec=InfraonAPIClient)

@pytest.fixture
def testing_agent(mock_llm_service, mock_query_classifier, mock_api_client):
    """
    Fixture for a TestingAgent instance.
    """
    return TestingAgent(
        llm_service=mock_llm_service,
        query_classifier=mock_query_classifier,
        api_client=mock_api_client
    )

def test_agent_initialization(testing_agent):
    """
    Test that the TestingAgent initializes correctly.
    """
    assert isinstance(testing_agent, TestingAgent)
    assert testing_agent.llm_service is not None

@pytest.fixture
def sample_service_registry():
    """
    Provides a sample ServiceRegistry for testing.
    """
    service_def = ServiceDefinition(
        service_name="user_management",
        service_description="Handles user creation and management.",
        business_context="Core identity service for the platform.",
        tier1_operations={
            "create_user": ServiceOperation(
                endpoint=APIEndpoint(path="/users", method="POST", operation_id="createUser", description="Create a new user"),
                description="Create a new user.",
            ),
            "get_user": ServiceOperation(
                endpoint=APIEndpoint(path="/users/{id}", method="GET", operation_id="getUser", description="Get a user by ID"),
                description="Get a user by ID.",
            )
        }
    )
    registry = ServiceRegistry(
        registry_id="test-registry",
        version="1.0",
        services={"user_management": service_def},
        created_timestamp="2025-01-01T00:00:00Z",
        last_updated="2025-01-01T00:00:00Z",
    )
    return registry

@pytest.mark.asyncio
async def test_generate_test_suite(testing_agent, sample_service_registry):
    """
    Test the generation of a test suite from a service registry.
    """
    test_suite = await testing_agent.generate_test_suite(sample_service_registry)
    assert isinstance(test_suite, TestSuite)
    assert test_suite.total_tests == 3
    assert len(test_suite.test_categories[TestCategoryType.BASIC_CRUD.value]) == 2
    assert len(test_suite.test_categories[TestCategoryType.SERVICE_IDENTIFICATION.value]) == 1

    id_test_case = test_suite.test_categories[TestCategoryType.SERVICE_IDENTIFICATION.value][0]
    assert id_test_case.expected_service == "user_management"
    assert id_test_case.query == "Handles user creation and management."
    assert id_test_case.difficulty_level == DifficultyLevel.MEDIUM

@pytest.mark.asyncio
async def test_run_accuracy_tests(testing_agent, sample_service_registry):
    """
    Test the execution of accuracy tests.
    """
    test_suite = await testing_agent.generate_test_suite(sample_service_registry)
    results = await testing_agent.run_accuracy_tests(sample_service_registry, test_suite)

    assert isinstance(results, TestResults)
    assert results.total_tests == 3
    assert results.passed == 3
    assert results.failed == 0
    assert results.accuracy_percentage == 100.0

@pytest.mark.asyncio
async def test_run_procedural_api_tests(testing_agent, sample_service_registry):
    """
    Test the execution of procedural API tests for a service.
    """
    service_name = "user_management"
    service_def = sample_service_registry.services[service_name]
    
    results = await testing_agent.run_procedural_api_tests(service_name, service_def)
    
    assert isinstance(results, ProceduralTestResults)
    assert results.service_name == service_name
    assert results.successful_crd_cycles == 1
    assert results.failed_crd_cycles == 0
    assert results.test_entity_cleanup_status == "completed"
