from typing import List, Dict, Any, Optional
from datetime import datetime
from pydantic import BaseModel, Field
from enum import Enum


class ReasoningStepType(str, Enum):
    THOUGHT = "thought"
    ACTION = "action"
    OBSERVATION = "observation"
    CONCLUSION = "conclusion"


class ReasoningStep(BaseModel):
    """Represents a single step in the agent's reasoning process"""
    step_type: ReasoningStepType
    content: str
    timestamp: datetime = Field(default_factory=datetime.now)
    confidence: Optional[float] = None
    metadata: Optional[Dict[str, Any]] = None


class Source(BaseModel):
    """Represents a source of information used in the response"""
    type: str  # "document", "api", "calculation"
    content: str
    reference: Optional[str] = None  # file path, API endpoint, etc.
    confidence: Optional[float] = None
    metadata: Optional[Dict[str, Any]] = None


class AgentResponse(BaseModel):
    """Standard response format for all agents"""
    answer: str
    sources: List[Source] = Field(default_factory=list)
    reasoning_chain: List[ReasoningStep] = Field(default_factory=list)
    confidence: Optional[float] = None
    metadata: Optional[Dict[str, Any]] = None
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class AgentRequest(BaseModel):
    """Standard request format for all agents"""
    query: str
    context: Optional[Dict[str, Any]] = None
    session_id: Optional[str] = None
    options: Optional[Dict[str, Any]] = None