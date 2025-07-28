"""
Tests for the Definition API endpoints.

This test suite validates the complete interactive service definition workflow
through FastAPI endpoints.
"""

import pytest
import json
from unittest.mock import MagicMock, AsyncMock, patch
from fastapi.testclient import TestClient

# Add backend to sys.path
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[2]))

from app.main import app
from app.core.manoman.models.api_specification import RawAPIEndpoint, HTTPMethod
from app.core.manoman.models.service_registry import ServiceDefinition
from app.core.manoman.api.definition import active_agents
from app.core.manoman.api.classification import classification_store
from app.core.manoman.api.upload import upload_status_store

client = TestClient(app)

@pytest.fixture
def mock_upload_data():
    """Mock upload data in the store."""
    upload_id = "test-upload-123"
    upload_data = {
        "upload_id": upload_id,
        "file_path": "/tmp/test-api.json",
        "status": "completed"
    }
    upload_status_store[upload_id] = upload_data
    return upload_id, upload_data

@pytest.fixture
def mock_classification_data(mock_upload_data):
    """Mock classification data in the store."""
    upload_id, _ = mock_upload_data
    classification_data = {
        "upload_id": upload_id,
        "services": [
            {
                "service_name": "incident_management",
                "endpoint_count": 6,
                "suggested_description": "Incident management service",
                "tier1_operations": 4,
                "tier2_operations": 2,
                "confidence_score": 0.85
            }
        ]
    }
    classification_store[upload_id] = classification_data
    return upload_id, classification_data

@pytest.fixture
def mock_parsed_endpoints():
    """Mock parsed API endpoints."""
    return [
        RawAPIEndpoint(path="/incidents", method=HTTPMethod.GET, operation_id="list_incidents"),
        RawAPIEndpoint(path="/incidents/{id}", method=HTTPMethod.GET, operation_id="get_incident"),
        RawAPIEndpoint(path="/incidents", method=HTTPMethod.POST, operation_id="create_incident")
    ]

@pytest.fixture(autouse=True)
def clean_active_agents():
    """Clean up active agents after each test."""
    yield
    active_agents.clear()

def test_start_definition_session_success(mock_classification_data, mock_parsed_endpoints):
    """Test successfully starting a definition session."""
    upload_id, _ = mock_classification_data
    
    # Mock the JSON parser and agent
    with patch('app.core.manoman.api.definition.JSONParser') as mock_parser, \
         patch('app.core.manoman.api.definition.ServiceDefinitionAgent') as mock_agent_class:
        
        # Setup parser mock
        mock_parser_instance = MagicMock()
        mock_parser.return_value = mock_parser_instance
        mock_parsed_spec = MagicMock()
        mock_parsed_spec.endpoints = mock_parsed_endpoints
        mock_parser_instance.parse_file.return_value = mock_parsed_spec
        
        # Setup agent mock
        mock_agent = AsyncMock()
        mock_agent_class.return_value = mock_agent
        mock_agent.start_definition_session.return_value = "session-123"
        mock_agent.conversation_memory = {
            "session-123": {
                "history": [{"agent": "What is the main purpose of the incident management service?"}]
            }
        }
        
        # Make request
        response = client.post("/api/v1/manoman/definition/start-session", json={
            "service_name": "incident_management",
            "upload_id": upload_id
        })
        
        assert response.status_code == 200
        data = response.json()
        
        assert "session_id" in data
        assert data["service_name"] == "incident_management"
        assert "initial_analysis" in data
        assert "first_question" in data

def test_respond_in_session_success():
    """Test successfully responding in a session."""
    session_id = "test-session-123"
    
    # Mock agent in active_agents
    mock_agent = AsyncMock()
    mock_agent.process_user_response.return_value = {
        "response": "Great! Now let's work on keywords.",
        "current_step": "keywords",
        "progress": 0.4,
        "data_collected": {"description": "Incident management service"},
        "needs_user_input": True,
        "completion_status": "in_progress"
    }
    active_agents[session_id] = mock_agent
    
    response = client.post(f"/api/v1/manoman/definition/session/{session_id}/respond", json={
        "user_response": "This service manages incident tickets."
    })
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["response"] == "Great! Now let's work on keywords."
    assert data["current_step"] == "keywords"
    assert data["progress"] == 0.4

def test_session_not_found():
    """Test accessing non-existent session."""
    response = client.post("/api/v1/manoman/definition/session/fake-session/respond", json={
        "user_response": "test"
    })
    assert response.status_code == 404
    assert "Session not found" in response.json()["detail"]

def test_list_active_sessions():
    """Test listing active sessions."""
    mock_agent = MagicMock()
    mock_agent.get_session_status.return_value = {
        "session_id": "session-1",
        "service_name": "incident_management", 
        "current_step": "description",
        "conversation_length": 2
    }
    active_agents["session-1"] = mock_agent
    
    response = client.get("/api/v1/manoman/definition/sessions")
    
    assert response.status_code == 200
    data = response.json()
    assert data["active_sessions"] == 1