"""
Enhanced tests for the ServiceDefinitionAgent with LLM integration.

This test suite validates the comprehensive conversation flow, LLM integration,
and service definition building capabilities.
"""

import pytest
import asyncio
import json
from unittest.mock import MagicMock, AsyncMock

# Add backend to sys.path
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[2]))

from app.core.manoman.agents.definition_agent import ServiceDefinitionAgent
from app.core.manoman.models.api_specification import RawAPIEndpoint
from app.core.manoman.models.service_registry import ServiceDefinition
from app.core.agents.base.llm_service import LLMService

@pytest.fixture
def mock_llm_service():
    """
    Mock LLMService with async responses.
    """
    service = MagicMock(spec=LLMService)
    
    # Mock different responses based on prompts
    async def mock_generate_response(prompt, system_prompt=None):
        if "business description" in prompt:
            return "I've analyzed your incident management service with 2 endpoints. What specific business processes does this service support in your organization?"
        elif "keywords" in prompt:
            return "Based on your service description, what are the main terms and synonyms your users might search for when looking for incident management functionality?"
        elif "Tier 1" in prompt:
            return "Let's classify these operations. Tier 1 operations are standard CRUD (Create, Read, Update, Delete). Which of your endpoints would you consider basic CRUD operations versus specialized functions?"
        elif "Extract all keywords" in prompt:
            return '["incident", "ticket", "issue", "problem", "request", "management"]'
        elif "Analyze the response and return a JSON" in prompt:
            return '{"tier1_operations": ["get_test"], "tier2_operations": ["create_test"], "user_notes": "User classified get_test as CRUD operation"}'
        else:
            return "Thank you for providing that information. Let's continue with the next step."
    
    service.generate_response = AsyncMock(side_effect=mock_generate_response)
    return service

@pytest.fixture
def enhanced_definition_agent(mock_llm_service):
    """
    Fixture for an enhanced ServiceDefinitionAgent instance.
    """
    return ServiceDefinitionAgent(llm_service=mock_llm_service)

@pytest.fixture
def sample_endpoints():
    """
    Sample RawAPIEndpoint list for testing.
    """
    return [
        RawAPIEndpoint(path="/incidents", method="GET", operation_id="list_incidents"),
        RawAPIEndpoint(path="/incidents/{id}", method="GET", operation_id="get_incident"),
        RawAPIEndpoint(path="/incidents", method="POST", operation_id="create_incident"),
        RawAPIEndpoint(path="/incidents/{id}", method="PUT", operation_id="update_incident"),
        RawAPIEndpoint(path="/incidents/{id}", method="DELETE", operation_id="delete_incident"),
        RawAPIEndpoint(path="/incidents/bulk-import", method="POST", operation_id="bulk_import_incidents")
    ]

@pytest.mark.asyncio
async def test_enhanced_start_session(enhanced_definition_agent, sample_endpoints):
    """
    Test enhanced session initialization with LLM-generated questions.
    """
    service_name = "incident_management"
    session_id = await enhanced_definition_agent.start_definition_session(service_name, sample_endpoints)

    assert isinstance(session_id, str)
    assert session_id in enhanced_definition_agent.conversation_memory
    
    session = enhanced_definition_agent.conversation_memory[session_id]
    assert session["service_name"] == service_name
    assert session["current_step"] == "description"
    assert len(session["history"]) == 1
    assert "endpoints" in session["history"][0]["agent"]

@pytest.mark.asyncio
async def test_enhanced_conversation_flow(enhanced_definition_agent, sample_endpoints):
    """
    Test the complete enhanced conversation flow with LLM integration.
    """
    service_name = "incident_management"
    session_id = await enhanced_definition_agent.start_definition_session(service_name, sample_endpoints)

    # Step 1: Provide description
    description = "This service manages incident tickets in our ITSM system, allowing users to create, track, and resolve service incidents."
    response1 = await enhanced_definition_agent.process_user_response(session_id, description)
    
    assert response1["current_step"] == "keywords"
    assert response1["data_collected"]["description"] == description
    assert isinstance(response1["response"], str)
    assert response1["progress"] == 0.4

    # Step 2: Provide keywords
    keywords_input = "incident, ticket, issue, problem, service request, ITSM"
    response2 = await enhanced_definition_agent.process_user_response(session_id, keywords_input)

    assert response2["current_step"] == "operations"
    assert "incident" in response2["data_collected"]["keywords"]
    assert "ticket" in response2["data_collected"]["keywords"]
    assert isinstance(response2["response"], str)
    assert response2["progress"] == 0.6

    # Step 3: Classify operations
    operations_input = "The list, get, create, update, and delete operations are standard CRUD. The bulk import is specialized."
    response3 = await enhanced_definition_agent.process_user_response(session_id, operations_input)

    assert response3["current_step"] == "review"
    assert "operations" in response3["data_collected"]
    assert isinstance(response3["response"], str)
    assert response3["progress"] == 0.8

    # Step 4: Confirm the definition
    confirm_input = "Yes, this looks correct. Please confirm."
    response4 = await enhanced_definition_agent.process_user_response(session_id, confirm_input)

    assert response4["current_step"] == "completed"
    assert response4["completion_status"] == "completed"
    assert response4["needs_user_input"] == False
    assert "service_definition" in response4
    assert isinstance(response4["service_definition"], ServiceDefinition)

@pytest.mark.asyncio 
async def test_llm_keyword_extraction(enhanced_definition_agent):
    """
    Test LLM-based keyword extraction functionality.
    """
    agent = enhanced_definition_agent
    
    user_response = "We handle incidents, tickets, issues, problems, and service requests in our ITSM platform"
    keywords = await agent._extract_keywords_with_llm(user_response)
    
    assert isinstance(keywords, list)
    # Check that at least some keywords were extracted
    assert len(keywords) > 0
    # Should extract some form of relevant terms (either from LLM or fallback)
    keywords_str = ' '.join(keywords).lower()
    assert any(term in keywords_str for term in ["incident", "ticket", "issue", "problem", "request"])

@pytest.mark.asyncio
async def test_operation_classification(enhanced_definition_agent, sample_endpoints):
    """
    Test operation classification with LLM assistance.
    """
    service_name = "test_service"
    session_id = await enhanced_definition_agent.start_definition_session(service_name, sample_endpoints)
    
    user_response = "The GET and POST operations are basic CRUD, the others are specialized"
    operation_data = await enhanced_definition_agent._process_operation_response(session_id, user_response)
    
    assert isinstance(operation_data, dict)
    assert "tier1_operations" in operation_data
    assert "tier2_operations" in operation_data
    assert "user_notes" in operation_data

@pytest.mark.asyncio
async def test_service_definition_building(enhanced_definition_agent, sample_endpoints):
    """
    Test building the final ServiceDefinition object.
    """
    service_name = "incident_management"
    session_id = await enhanced_definition_agent.start_definition_session(service_name, sample_endpoints)
    
    # Simulate collected data
    session = enhanced_definition_agent.conversation_memory[session_id]
    session["data_collected"] = {
        "description": "Incident management service for ITSM",
        "keywords": ["incident", "ticket", "issue"],
        "operations": {
            "tier1_operations": ["list_incidents", "get_incident"],
            "tier2_operations": ["bulk_import_incidents"]
        }
    }
    
    service_def = await enhanced_definition_agent._build_service_definition(session_id)
    
    assert isinstance(service_def, ServiceDefinition)
    assert service_def.service_name == service_name
    assert service_def.service_description == "Incident management service for ITSM"
    assert "incident" in service_def.keywords
    assert len(service_def.tier1_operations) == 2
    # The remaining operations (6 total - 2 tier1 = 4 tier2)
    assert len(service_def.tier2_operations) == 4
    # Verify that the expected operations are in the right tiers
    assert "list_incidents" in service_def.tier1_operations
    assert "get_incident" in service_def.tier1_operations

@pytest.mark.asyncio
async def test_session_management(enhanced_definition_agent, sample_endpoints):
    """
    Test session status and management functionality.
    """
    service_name = "test_service"
    session_id = await enhanced_definition_agent.start_definition_session(service_name, sample_endpoints)
    
    # Test session status
    status = enhanced_definition_agent.get_session_status(session_id)
    assert status["session_id"] == session_id
    assert status["service_name"] == service_name
    assert status["current_step"] == "description"
    
    # Test session clearing
    success = enhanced_definition_agent.clear_session(session_id)
    assert success == True
    
    # Verify session is cleared
    status_after_clear = enhanced_definition_agent.get_session_status(session_id)
    assert "error" in status_after_clear

@pytest.mark.asyncio
async def test_fallback_functionality(enhanced_definition_agent, sample_endpoints):
    """
    Test fallback functionality when LLM calls fail.
    """
    # Mock LLM service to fail
    enhanced_definition_agent.llm_service.generate_response = AsyncMock(side_effect=Exception("LLM Error"))
    
    service_name = "test_service"
    session_id = await enhanced_definition_agent.start_definition_session(service_name, sample_endpoints)
    
    # Should fallback to static questions
    session = enhanced_definition_agent.conversation_memory[session_id]
    assert len(session["history"]) == 1
    assert isinstance(session["history"][0]["agent"], str)

@pytest.mark.asyncio
async def test_endpoint_summarization(enhanced_definition_agent, sample_endpoints):
    """
    Test endpoint summarization functionality.
    """
    summary = enhanced_definition_agent._summarize_endpoints(sample_endpoints)
    
    assert isinstance(summary, str)
    assert "GET /incidents" in summary
    assert "POST /incidents" in summary
    assert len(summary.split('\n')) == len(sample_endpoints)

def test_fallback_questions(enhanced_definition_agent):
    """
    Test fallback question generation.
    """
    service_name = "test_service"
    endpoint_count = 5
    
    desc_question = enhanced_definition_agent._get_fallback_question("description", service_name, endpoint_count)
    assert service_name in desc_question
    assert str(endpoint_count) in desc_question
    
    keyword_question = enhanced_definition_agent._get_fallback_question("keywords", service_name, endpoint_count)
    assert service_name in keyword_question
    
    ops_question = enhanced_definition_agent._get_fallback_question("operations", service_name, endpoint_count)
    assert "Tier 1" in ops_question

@pytest.mark.asyncio
async def test_review_summary_generation(enhanced_definition_agent, sample_endpoints):
    """
    Test review summary generation.
    """
    service_name = "incident_management"
    session_id = await enhanced_definition_agent.start_definition_session(service_name, sample_endpoints)
    
    # Setup collected data
    session = enhanced_definition_agent.conversation_memory[session_id]
    session["data_collected"] = {
        "description": "Incident management service",
        "keywords": ["incident", "ticket"],
        "operations": {
            "tier1_operations": ["get_incident", "create_incident"],
            "tier2_operations": ["bulk_import"]
        }
    }
    
    summary = await enhanced_definition_agent._generate_review_summary(session_id)
    
    assert isinstance(summary, str)
    assert service_name in summary
    assert "2 Tier 1, 1 Tier 2" in summary
    assert "confirm" in summary.lower()