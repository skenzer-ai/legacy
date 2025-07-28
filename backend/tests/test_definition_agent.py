"""
Tests for the Service Definition Agent.

This test suite validates the conversational flow and session management
of the ServiceDefinitionAgent.
"""

import pytest
import asyncio
from unittest.mock import MagicMock, AsyncMock

# Add backend to sys.path
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[2]))

from app.core.manoman.agents.definition_agent import ServiceDefinitionAgent
from app.core.manoman.models.api_specification import RawAPIEndpoint
from app.core.agents.base.llm_service import LLMService

@pytest.fixture
def mock_llm_service():
    """
    Mock LLMService for agent testing.
    """
    return MagicMock(spec=LLMService)

@pytest.fixture
def definition_agent(mock_llm_service):
    """
    Fixture for a ServiceDefinitionAgent instance.
    """
    return ServiceDefinitionAgent(llm_service=mock_llm_service)

@pytest.fixture
def sample_endpoints():
    """
    Sample RawAPIEndpoint list for testing.
    """
    return [
        RawAPIEndpoint(path="/test", method="GET", operation_id="get_test"),
        RawAPIEndpoint(path="/test", method="POST", operation_id="create_test")
    ]

@pytest.mark.asyncio
async def test_start_definition_session(definition_agent, sample_endpoints):
    """
    Test the successful start of a definition session.
    """
    service_name = "test_service"
    session_id = await definition_agent.start_definition_session(service_name, sample_endpoints)

    assert isinstance(session_id, str)
    assert session_id in definition_agent.conversation_memory
    
    session = definition_agent.conversation_memory[session_id]
    assert session["service_name"] == service_name
    assert session["current_step"] == "description"
    assert len(session["history"]) == 1
    assert "agent" in session["history"][0]

@pytest.mark.asyncio
async def test_process_user_response_valid_session(definition_agent, sample_endpoints):
    """
    Test processing a user response in a valid session.
    """
    service_name = "test_service"
    session_id = await definition_agent.start_definition_session(service_name, sample_endpoints)
    
    user_input = "This service manages test data."
    response = await definition_agent.process_user_response(session_id, user_input)

    assert "response" in response
    assert response["completion_status"] == "in_progress"
    
    session = definition_agent.conversation_memory[session_id]
    assert len(session["history"]) == 3 # Initial question, user response, agent response
    assert session["history"][1]["user"] == user_input

@pytest.mark.asyncio
async def test_process_user_response_invalid_session(definition_agent):
    """
    Test processing a response with an invalid session ID.
    """
    with pytest.raises(ValueError, match="Invalid session ID"):
        await definition_agent.process_user_response("invalid-id", "test input")

@pytest.mark.asyncio
async def test_conversation_flow(definition_agent, sample_endpoints):
    """
    Test the multi-step conversation flow.
    """
    service_name = "test_service"
    session_id = await definition_agent.start_definition_session(service_name, sample_endpoints)

    # Step 1: Provide description
    description = "This is a test service for managing test data."
    response1 = await definition_agent.process_user_response(session_id, description)
    
    assert response1["current_step"] == "keywords"
    assert response1["data_collected"]["description"] == description
    assert "keywords" in response1["response"]

    # Step 2: Provide keywords
    keywords = "test, data, management"
    response2 = await definition_agent.process_user_response(session_id, keywords)

    assert response2["current_step"] == "operations"
    assert response2["data_collected"]["keywords"] == ["test", "data", "management"]
    assert "operations" in response2["response"]
