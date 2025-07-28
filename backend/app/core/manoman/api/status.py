"""
Man-O-Man System Status API

Provides information about the current implementation status of Man-O-Man components.
"""

from fastapi import APIRouter
from pydantic import BaseModel
from typing import Dict, List

router = APIRouter()

class ComponentStatus(BaseModel):
    """Status of a system component."""
    name: str
    status: str  # "implemented", "placeholder", "not_started"
    description: str
    endpoints: List[str]
    dependencies: List[str]

class SystemStatus(BaseModel):
    """Overall system status."""
    version: str
    total_components: int
    implemented: int
    placeholders: int
    not_started: int
    components: List[ComponentStatus]

@router.get("/status", response_model=SystemStatus)
async def get_system_status():
    """Get current Man-O-Man system implementation status."""
    
    components = [
        ComponentStatus(
            name="Upload API",
            status="implemented",
            description="File upload and parsing for API specifications",
            endpoints=[
                "POST /upload",
                "GET /upload/{upload_id}/status",
                "GET /uploads"
            ],
            dependencies=["JSONParser", "APISpecification models"]
        ),
        ComponentStatus(
            name="Classification API", 
            status="implemented",
            description="Automatic service classification and conflict detection",
            endpoints=[
                "GET /classification/{upload_id}/services",
                "POST /classification/{upload_id}/services/merge",
                "POST /classification/{upload_id}/services/split",
                "GET /classification/{upload_id}/conflicts"
            ],
            dependencies=["ServiceClassifier", "ConflictDetector", "RegistryManager"]
        ),
        ComponentStatus(
            name="Definition API",
            status="implemented", 
            description="Interactive conversational service definition with LLM",
            endpoints=[
                "POST /definition/start-session",
                "POST /definition/session/{id}/respond",
                "GET /definition/session/{id}/preview",
                "GET /definition/session/{id}/status",
                "POST /definition/session/{id}/complete",
                "DELETE /definition/session/{id}",
                "GET /definition/sessions"
            ],
            dependencies=["ServiceDefinitionAgent", "LLMService", "RegistryManager"]
        ),
        ComponentStatus(
            name="Testing Agent",
            status="placeholder",
            description="Procedural API testing with Create-Read-Delete cycles",
            endpoints=[],
            dependencies=["InfraonAPIClient", "QueryClassifier", "ProceduralTesting"]
        ),
        ComponentStatus(
            name="Validation API",
            status="placeholder",
            description="Test suite generation and execution for accuracy validation",
            endpoints=[
                "POST /validation/generate-tests",
                "POST /validation/run-tests", 
                "GET /validation/results/{test_run_id}"
            ],
            dependencies=["TestingAgent", "InfraonAPIClient", "ValidationModels"]
        ),
        ComponentStatus(
            name="Utility Modules",
            status="not_started",
            description="Text processing, helpers, and utility functions",
            endpoints=[],
            dependencies=["TextProcessor", "Helpers"]
        )
    ]
    
    implemented = len([c for c in components if c.status == "implemented"])
    placeholders = len([c for c in components if c.status == "placeholder"])
    not_started = len([c for c in components if c.status == "not_started"])
    
    return SystemStatus(
        version="0.7.0-dev",
        total_components=len(components),
        implemented=implemented,
        placeholders=placeholders, 
        not_started=not_started,
        components=components
    )

@router.get("/health")
async def health_check():
    """Health check endpoint for Man-O-Man system."""
    return {
        "status": "healthy",
        "message": "Man-O-Man system is operational",
        "implemented_components": ["upload", "classification", "definition"],
        "placeholder_components": ["testing", "validation"], 
        "next_development_priority": "testing_agent"
    }