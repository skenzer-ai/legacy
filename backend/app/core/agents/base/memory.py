from typing import List, Dict, Any, Optional
from datetime import datetime
import tiktoken
from .response import AgentRequest, AgentResponse


class ConversationExchange:
    """Represents a single query-response exchange"""
    def __init__(self, request: AgentRequest, response: AgentResponse, timestamp: datetime = None):
        self.request = request
        self.response = response
        self.timestamp = timestamp or datetime.now()
        self.metadata = {}
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "query": self.request.query,
            "answer": self.response.answer,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata
        }


class AgentMemory:
    """Manages conversation history and context for agents"""
    
    def __init__(self, max_tokens: int = 8000, model_name: str = "gpt-4"):
        self.max_tokens = max_tokens
        self.conversation_history: List[ConversationExchange] = []
        self.session_data: Dict[str, Any] = {}
        
        # Initialize tokenizer based on model
        try:
            self.tokenizer = tiktoken.encoding_for_model(model_name)
        except KeyError:
            # Fallback to a common encoding
            self.tokenizer = tiktoken.get_encoding("cl100k_base")
    
    def add_exchange(self, request: AgentRequest, response: AgentResponse) -> None:
        """Add a new query-response exchange to memory"""
        exchange = ConversationExchange(request, response)
        
        # Add the exchange
        self.conversation_history.append(exchange)
        
        # Trim if necessary
        self._trim_to_fit()
    
    def get_context_string(self) -> str:
        """Get conversation history as a formatted string"""
        if not self.conversation_history:
            return ""
        
        context_parts = []
        for exchange in self.conversation_history:
            context_parts.append(f"Human: {exchange.request.query}")
            context_parts.append(f"Assistant: {exchange.response.answer}")
        
        return "\n\n".join(context_parts)
    
    def get_recent_exchanges(self, count: int = 5) -> List[ConversationExchange]:
        """Get the most recent exchanges"""
        return self.conversation_history[-count:] if self.conversation_history else []
    
    def _count_tokens(self, text: str) -> int:
        """Count tokens in a text string"""
        return len(self.tokenizer.encode(text))
    
    def _trim_to_fit(self) -> None:
        """Remove oldest exchanges to stay within token limit"""
        while self.conversation_history and self._get_total_tokens() > self.max_tokens:
            removed = self.conversation_history.pop(0)
            print(f"Trimmed conversation exchange from {removed.timestamp}")
    
    def _get_total_tokens(self) -> int:
        """Calculate total tokens in conversation history"""
        context_string = self.get_context_string()
        return self._count_tokens(context_string)
    
    def clear(self) -> None:
        """Clear all conversation history"""
        self.conversation_history.clear()
        self.session_data.clear()
    
    def set_session_data(self, key: str, value: Any) -> None:
        """Store session-specific data"""
        self.session_data[key] = value
    
    def get_session_data(self, key: str, default: Any = None) -> Any:
        """Retrieve session-specific data"""
        return self.session_data.get(key, default)