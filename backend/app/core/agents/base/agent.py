from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List
import logging

from .config import BaseAgentConfig
from .memory import AgentMemory
from .response import AgentRequest, AgentResponse
from .strategy import AgentStrategy


logger = logging.getLogger(__name__)


class BaseAgent(ABC):
    """Abstract base class for all AI agents"""
    
    def __init__(self, config: BaseAgentConfig):
        self.config = config
        self.memory: Optional[AgentMemory] = None
        self.retriever = None
        self.tools: List[Any] = []
        self.strategy: Optional[AgentStrategy] = None
        
        self._initialize_components()
    
    def _initialize_components(self) -> None:
        """Initialize agent components"""
        # Initialize memory if enabled
        if self.config.enable_memory:
            self.memory = AgentMemory(
                max_tokens=self.config.max_context_tokens,
                model_name=self.config.model_name
            )
        
        # Initialize retriever
        if self.config.retrieval_enabled:
            self.retriever = self._initialize_retriever()
        
        # Initialize tools
        self.tools = self._initialize_tools()
        
        # Initialize strategy
        self.strategy = self._initialize_strategy()
        
        logger.info(f"Initialized {self.__class__.__name__} with strategy: {self.strategy.get_strategy_name()}")
    
    @abstractmethod
    def _initialize_retriever(self) -> Any:
        """Initialize the retrieval component"""
        pass
    
    @abstractmethod
    def _initialize_tools(self) -> List[Any]:
        """Initialize tools available to the agent"""
        pass
    
    @abstractmethod
    def _initialize_strategy(self) -> AgentStrategy:
        """Initialize the reasoning strategy"""
        pass
    
    async def process(self, request: AgentRequest) -> AgentResponse:
        """Main processing method for handling requests"""
        try:
            # Get memory context if available
            memory_context = ""
            if self.memory:
                memory_context = self.memory.get_context_string()
            
            # Execute strategy
            response = await self.strategy.execute(
                query=request.query,
                context=request.context,
                tools=self.tools,
                memory_context=memory_context
            )
            
            # Store in memory if enabled
            if self.memory:
                self.memory.add_exchange(request, response)
            
            logger.info(f"Successfully processed query: {request.query[:50]}...")
            return response
            
        except Exception as e:
            logger.error(f"Error processing request: {str(e)}")
            return AgentResponse(
                answer=f"I encountered an error processing your request: {str(e)}",
                confidence=0.0,
                metadata={"error": str(e)}
            )
    
    def clear_memory(self) -> None:
        """Clear agent memory"""
        if self.memory:
            self.memory.clear()
            logger.info("Agent memory cleared")
    
    def get_memory_context(self) -> str:
        """Get current memory context"""
        if self.memory:
            return self.memory.get_context_string()
        return ""
    
    def set_session_data(self, key: str, value: Any) -> None:
        """Store session data in memory"""
        if self.memory:
            self.memory.set_session_data(key, value)
    
    def get_session_data(self, key: str, default: Any = None) -> Any:
        """Retrieve session data from memory"""
        if self.memory:
            return self.memory.get_session_data(key, default)
        return default