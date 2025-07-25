from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from .response import AgentResponse, ReasoningStep, Source


class AgentStrategy(ABC):
    """Abstract base class for agent reasoning strategies"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
    
    @abstractmethod
    async def execute(
        self,
        query: str,
        context: Optional[Dict[str, Any]],
        tools: List[Any],
        memory_context: str = ""
    ) -> AgentResponse:
        """Execute the strategy and return an agent response"""
        pass
    
    @abstractmethod
    def get_strategy_name(self) -> str:
        """Return the name of this strategy"""
        pass


class StrategyResult:
    """Result from strategy execution"""
    def __init__(
        self,
        answer: str,
        reasoning_steps: List[ReasoningStep] = None,
        sources: List[Source] = None,
        confidence: float = None,
        metadata: Dict[str, Any] = None
    ):
        self.answer = answer
        self.reasoning_steps = reasoning_steps or []
        self.sources = sources or []
        self.confidence = confidence
        self.metadata = metadata or {}
    
    def to_agent_response(self) -> AgentResponse:
        """Convert to AgentResponse"""
        return AgentResponse(
            answer=self.answer,
            reasoning_chain=self.reasoning_steps,
            sources=self.sources,
            confidence=self.confidence,
            metadata=self.metadata
        )