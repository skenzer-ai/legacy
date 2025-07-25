from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import Optional, Dict, Any
import logging

from app.core.agents.augment.agent import AugmentAgent, create_augment_agent
from app.core.agents.augment.config import AugmentConfig
from app.core.agents.base.response import AgentRequest, AgentResponse

logger = logging.getLogger(__name__)

router = APIRouter()

# Global agent instance for stateful interactions
_global_augment_agent: Optional[AugmentAgent] = None


def get_augment_agent() -> AugmentAgent:
    """Get or create the global augment agent instance"""
    global _global_augment_agent
    if _global_augment_agent is None:
        _global_augment_agent = create_augment_agent()
        logger.info("Created new AugmentAgent instance")
    return _global_augment_agent


@router.post("/augment", response_model=AgentResponse)
async def augment_agent_query(request: AgentRequest):
    """
    Process a query using the Augment Agent for intelligent Q&A about Infraon platform.
    
    The Augment Agent provides:
    - Intelligent answers based on Infraon documentation and API specs
    - Source attribution for transparency
    - Reasoning chain to show thought process
    - Support for both direct and ReAct reasoning strategies
    """
    try:
        agent = get_augment_agent()
        response = await agent.process(request)
        
        logger.info(f"Processed query successfully: {request.query[:50]}...")
        return response
        
    except Exception as e:
        logger.error(f"Error processing augment agent query: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process query: {str(e)}"
        )


@router.get("/augment/info")
async def get_augment_agent_info():
    """Get information about the current Augment Agent configuration"""
    try:
        agent = get_augment_agent()
        return agent.get_agent_info()
    except Exception as e:
        logger.error(f"Error getting agent info: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get agent info: {str(e)}"
        )


@router.post("/augment/config")
async def update_augment_agent_config(config_updates: Dict[str, Any]):
    """
    Update the Augment Agent configuration dynamically.
    
    Supported configuration options:
    - strategy: "direct" or "react"
    - model_name: LLM model to use
    - system_prompt_template: "default", "technical", etc.
    - max_reasoning_loops: For ReAct strategy
    - temperature: LLM temperature setting
    - retrieval_top_k: Number of retrieval results to use
    """
    try:
        agent = get_augment_agent()
        agent.update_config(**config_updates)
        
        logger.info(f"Updated agent config: {config_updates}")
        return {
            "message": "Configuration updated successfully",
            "updated_config": agent.get_agent_info()
        }
        
    except Exception as e:
        logger.error(f"Error updating agent config: {str(e)}")
        raise HTTPException(
            status_code=400,
            detail=f"Failed to update configuration: {str(e)}"
        )


@router.post("/augment/memory/clear")
async def clear_augment_agent_memory():
    """Clear the Augment Agent's conversation memory"""
    try:
        agent = get_augment_agent()
        agent.clear_memory()
        
        logger.info("Cleared agent memory")
        return {"message": "Agent memory cleared successfully"}
        
    except Exception as e:
        logger.error(f"Error clearing agent memory: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to clear memory: {str(e)}"
        )


@router.get("/augment/memory/context")
async def get_augment_agent_memory():
    """Get the current conversation context from agent memory"""
    try:
        agent = get_augment_agent()
        context = agent.get_memory_context()
        
        return {
            "context": context,
            "context_length": len(context),
            "has_memory": agent.memory is not None
        }
        
    except Exception as e:
        logger.error(f"Error getting agent memory: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get memory context: {str(e)}"
        )


@router.post("/augment/session")
async def set_augment_agent_session_data(session_data: Dict[str, Any]):
    """Set session-specific data in agent memory"""
    try:
        agent = get_augment_agent()
        
        for key, value in session_data.items():
            agent.set_session_data(key, value)
        
        logger.info(f"Set session data: {list(session_data.keys())}")
        return {"message": f"Set {len(session_data)} session data items"}
        
    except Exception as e:
        logger.error(f"Error setting session data: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to set session data: {str(e)}"
        )


@router.get("/augment/session/{key}")
async def get_augment_agent_session_data(key: str):
    """Get specific session data from agent memory"""
    try:
        agent = get_augment_agent()
        value = agent.get_session_data(key)
        
        if value is None:
            raise HTTPException(
                status_code=404,
                detail=f"Session data key '{key}' not found"
            )
        
        return {"key": key, "value": value}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting session data: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get session data: {str(e)}"
        )


@router.post("/augment/create")
async def create_new_augment_agent(config: Optional[AugmentConfig] = None):
    """
    Create a new Augment Agent instance with custom configuration.
    This replaces the global agent instance.
    """
    try:
        global _global_augment_agent
        
        if config:
            _global_augment_agent = AugmentAgent(config)
        else:
            _global_augment_agent = create_augment_agent()
        
        logger.info("Created new AugmentAgent instance")
        return {
            "message": "New agent created successfully",
            "agent_info": _global_augment_agent.get_agent_info()
        }
        
    except Exception as e:
        logger.error(f"Error creating new agent: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create new agent: {str(e)}"
        )


@router.get("/augment/templates")
async def list_available_prompt_templates():
    """List all available prompt templates"""
    try:
        from app.core.agents.augment.prompts.manager import PromptManager
        
        manager = PromptManager()
        templates = manager.list_available_templates()
        
        return {
            "available_templates": templates,
            "count": len(templates)
        }
        
    except Exception as e:
        logger.error(f"Error listing templates: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list templates: {str(e)}"
        )


@router.post("/augment/templates/{template_name}/reload")
async def reload_prompt_template(template_name: str):
    """Reload a specific prompt template from file"""
    try:
        from app.core.agents.augment.prompts.manager import PromptManager
        
        manager = PromptManager()
        manager.reload_template(template_name)
        
        logger.info(f"Reloaded template: {template_name}")
        return {"message": f"Template '{template_name}' reloaded successfully"}
        
    except Exception as e:
        logger.error(f"Error reloading template: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to reload template: {str(e)}"
        )