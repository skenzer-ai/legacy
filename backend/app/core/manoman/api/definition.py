"""
Definition API Endpoints

FastAPI endpoints for the interactive service definition process.
Provides conversational interface for collecting comprehensive service metadata.
"""

import logging
from typing import Dict, Any, Optional
import uuid

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field

from ..agents.definition_agent import ServiceDefinitionAgent
from ..models.service_registry import ServiceDefinition
from ..models.api_specification import RawAPIEndpoint
from ..engines.json_parser import JSONParser
from ..storage.registry_manager import RegistryManager
from ....core.agents.base.llm_service import LLMService
from .upload import upload_status_store
from .classification import classification_store

logger = logging.getLogger(__name__)

router = APIRouter()  # Tags will be overridden by main router

# In-memory store for active definition agents (replace with a proper session manager in production)
active_agents: Dict[str, ServiceDefinitionAgent] = {}

# --- Pydantic Models ---

class StartSessionRequest(BaseModel):
    """Request to start a new definition session."""
    service_name: str = Field(..., description="The name of the service to define.")
    upload_id: str = Field(..., description="The upload ID containing the classified service.")

class InitialAnalysis(BaseModel):
    """Initial analysis of the service."""
    suggested_description: str
    suggested_keywords: list[str]
    endpoint_summary: Dict[str, Any]
    tier1_count: int
    tier2_count: int

class StartSessionResponse(BaseModel):
    """Response for a newly started session."""
    session_id: str
    service_name: str
    initial_analysis: InitialAnalysis
    first_question: str

class UserResponseRequest(BaseModel):
    """Request model for a user's response."""
    user_response: str = Field(..., description="The user's text response.")

class SessionResponse(BaseModel):
    """Response from the agent during a conversation."""
    response: str
    current_step: str
    progress: float
    data_collected: Dict[str, Any]
    needs_user_input: bool
    completion_status: str
    service_definition: Optional[ServiceDefinition] = None

class SessionPreviewResponse(BaseModel):
    """Preview of the current service definition."""
    session_id: str
    service_name: str
    current_step: str
    progress: float
    partial_definition: ServiceDefinition
    
class SessionStatusResponse(BaseModel):
    """Status information about a session."""
    session_id: str
    service_name: str
    current_step: str
    data_collected: Dict[str, Any]
    conversation_length: int
    
class CompleteSessionResponse(BaseModel):
    """Response when completing a session."""
    session_id: str
    service_name: str
    final_definition: ServiceDefinition
    registry_updated: bool
    message: str

# --- Helper Functions ---

def get_llm_service():
    """Dependency injection for the LLMService."""
    from ....core.agents.base.config import BaseAgentConfig
    return LLMService(config=BaseAgentConfig())

def get_registry_manager():
    """Dependency injection for the RegistryManager."""
    return RegistryManager()

async def get_service_endpoints(upload_id: str, service_name: str) -> list[RawAPIEndpoint]:
    """Retrieve service endpoints from classification data."""
    if upload_id not in classification_store:
        raise HTTPException(status_code=404, detail="Upload not found in classification store")
    
    classification_data = classification_store[upload_id]
    
    # Find the service in classified services
    for service in classification_data.get("services", []):
        if service["service_name"] == service_name:
            # Get the parsed specification from upload data
            upload_data = upload_status_store.get(upload_id)
            if not upload_data:
                raise HTTPException(status_code=404, detail="Original upload data not found")
            
            # Check if we have parsed specification in upload data
            if "parsed_specification" in upload_data:
                from ..models.api_specification import APISpecification
                spec_data = upload_data["parsed_specification"]
                api_spec = APISpecification.parse_obj(spec_data)
                
                # Filter endpoints for this service (simplified logic)
                service_endpoints = []
                for endpoint in api_spec.endpoints:
                    # This is a simplified matching - use service name keywords
                    service_keywords = service_name.lower().replace('_', ' ').split()
                    if any(keyword in endpoint.path.lower() for keyword in service_keywords):
                        service_endpoints.append(endpoint)
                
                return service_endpoints[:10]  # Limit for demo
            
            # Fallback: reparse from file content
            elif "file_content" in upload_data:
                parser = JSONParser()
                spec_format = upload_data.get("format_hint", "openapi_3")
                parsed_spec = await parser.parse_specification(
                    upload_data["file_content"], 
                    upload_data["filename"], 
                    spec_format
                )
                
                # Filter endpoints for this service
                service_endpoints = []
                for endpoint in parsed_spec.endpoints:
                    service_keywords = service_name.lower().replace('_', ' ').split()
                    if any(keyword in endpoint.path.lower() for keyword in service_keywords):
                        service_endpoints.append(endpoint)
                
                return service_endpoints[:10]  # Limit for demo
            
            else:
                raise HTTPException(status_code=404, detail="No specification data found in upload")
    
    raise HTTPException(status_code=404, detail=f"Service '{service_name}' not found in classification")

def create_initial_analysis(service_name: str, endpoints: list[RawAPIEndpoint]) -> InitialAnalysis:
    """Create initial analysis of the service."""
    # Simple analysis - could be enhanced with ML
    suggested_description = f"Service for managing {service_name.replace('_', ' ')} operations"
    suggested_keywords = [service_name.replace('_', ' '), "management", "service"]
    
    # Count likely CRUD vs specialized operations
    tier1_count = sum(1 for ep in endpoints if ep.method.upper() in ['GET', 'POST', 'PUT', 'DELETE'] and 'list' not in ep.operation_id.lower())
    tier2_count = len(endpoints) - tier1_count
    
    endpoint_summary = {
        "total_endpoints": len(endpoints),
        "methods": list(set(ep.method.upper() for ep in endpoints)),
        "sample_paths": [ep.path for ep in endpoints[:5]]
    }
    
    return InitialAnalysis(
        suggested_description=suggested_description,
        suggested_keywords=suggested_keywords,
        endpoint_summary=endpoint_summary,
        tier1_count=tier1_count,
        tier2_count=tier2_count
    )

# --- API Endpoints ---

@router.post("/definition/start-session", response_model=StartSessionResponse)
async def start_definition_session(
    request: StartSessionRequest,
    llm_service: LLMService = Depends(get_llm_service)
):
    """
    Start an interactive service definition session.
    """
    try:
        # Get endpoints for the service
        endpoints = await get_service_endpoints(request.upload_id, request.service_name)
        
        # Create initial analysis
        initial_analysis = create_initial_analysis(request.service_name, endpoints)
        
        # Create definition agent and start session
        agent = ServiceDefinitionAgent(llm_service)
        session_id = await agent.start_definition_session(request.service_name, endpoints)
        
        # Store the agent for future interactions
        active_agents[session_id] = agent
        
        # Get the first question from the agent's history
        session = agent.conversation_memory[session_id]
        first_question = session["history"][0]["agent"]
        
        logger.info(f"Started definition session {session_id} for service {request.service_name}")
        
        return StartSessionResponse(
            session_id=session_id,
            service_name=request.service_name,
            initial_analysis=initial_analysis,
            first_question=first_question
        )
        
    except Exception as e:
        logger.error(f"Error starting definition session: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to start session: {str(e)}")

@router.post("/definition/session/{session_id}/respond", response_model=SessionResponse)
async def respond_in_session(session_id: str, request: UserResponseRequest):
    """
    Continue a definition conversation.
    """
    if session_id not in active_agents:
        raise HTTPException(status_code=404, detail="Session not found")

    try:
        agent = active_agents[session_id]
        agent_response = await agent.process_user_response(session_id, request.user_response)
        
        logger.info(f"Processed response in session {session_id}, step: {agent_response['current_step']}")
        
        return SessionResponse(**agent_response)
        
    except Exception as e:
        logger.error(f"Error processing response in session {session_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to process response: {str(e)}")

@router.get("/definition/session/{session_id}/preview", response_model=SessionPreviewResponse)
async def preview_session(session_id: str):
    """
    Preview the current service definition.
    """
    if session_id not in active_agents:
        raise HTTPException(status_code=404, detail="Session not found")
    
    try:
        agent = active_agents[session_id]
        session_status = agent.get_session_status(session_id)
        
        if "error" in session_status:
            raise HTTPException(status_code=404, detail=session_status["error"])
        
        # Build partial definition from current data
        partial_definition = await agent._build_service_definition(session_id)
        
        return SessionPreviewResponse(
            session_id=session_id,
            service_name=session_status["service_name"],
            current_step=session_status["current_step"],
            progress=0.5,  # Estimate based on current step
            partial_definition=partial_definition
        )
        
    except Exception as e:
        logger.error(f"Error previewing session {session_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to preview session: {str(e)}")

@router.get("/definition/session/{session_id}/status", response_model=SessionStatusResponse)
async def get_session_status(session_id: str):
    """
    Get current session status and progress.
    """
    if session_id not in active_agents:
        raise HTTPException(status_code=404, detail="Session not found")
    
    try:
        agent = active_agents[session_id]
        session_status = agent.get_session_status(session_id)
        
        if "error" in session_status:
            raise HTTPException(status_code=404, detail=session_status["error"])
        
        return SessionStatusResponse(**session_status)
        
    except Exception as e:
        logger.error(f"Error getting session status {session_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get session status: {str(e)}")

@router.post("/definition/session/{session_id}/complete", response_model=CompleteSessionResponse)
async def complete_session(
    session_id: str,
    registry_manager: RegistryManager = Depends(get_registry_manager)
):
    """
    Finalize service definition and add to registry.
    """
    if session_id not in active_agents:
        raise HTTPException(status_code=404, detail="Session not found")
    
    try:
        agent = active_agents[session_id]
        session_status = agent.get_session_status(session_id)
        
        if "error" in session_status:
            raise HTTPException(status_code=404, detail=session_status["error"])
        
        if session_status["current_step"] != "completed":
            raise HTTPException(status_code=400, detail="Session not completed yet")
        
        # Build final service definition
        final_definition = await agent._build_service_definition(session_id)
        service_name = session_status["service_name"]
        
        # Add to registry
        try:
            registry = await registry_manager.load_registry()
        except Exception:
            # Create new registry if none exists or loading fails
            from ..models.service_registry import ServiceRegistry
            registry = ServiceRegistry()
        
        registry.services[service_name] = final_definition
        await registry_manager.save_registry(registry)
        
        # Clean up session
        agent.clear_session(session_id)
        del active_agents[session_id]
        
        logger.info(f"Completed definition session {session_id} for service {service_name}")
        
        return CompleteSessionResponse(
            session_id=session_id,
            service_name=service_name,
            final_definition=final_definition,
            registry_updated=True,
            message="Service definition completed and added to registry successfully"
        )
        
    except Exception as e:
        logger.error(f"Error completing session {session_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to complete session: {str(e)}")

@router.delete("/definition/session/{session_id}")
async def cancel_session(session_id: str):
    """
    Cancel and clean up a definition session.
    """
    if session_id not in active_agents:
        raise HTTPException(status_code=404, detail="Session not found")
    
    try:
        agent = active_agents[session_id]
        agent.clear_session(session_id)
        del active_agents[session_id]
        
        logger.info(f"Cancelled definition session {session_id}")
        
        return {"message": "Session cancelled successfully"}
        
    except Exception as e:
        logger.error(f"Error cancelling session {session_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to cancel session: {str(e)}")

@router.get("/definition/sessions")
async def list_active_sessions():
    """
    List all active definition sessions.
    """
    try:
        sessions = []
        for session_id, agent in active_agents.items():
            status = agent.get_session_status(session_id)
            if "error" not in status:
                sessions.append({
                    "session_id": session_id,
                    "service_name": status["service_name"],
                    "current_step": status["current_step"],
                    "conversation_length": status["conversation_length"]
                })
        
        return {
            "active_sessions": len(sessions),
            "sessions": sessions
        }
        
    except Exception as e:
        logger.error(f"Error listing sessions: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to list sessions: {str(e)}")