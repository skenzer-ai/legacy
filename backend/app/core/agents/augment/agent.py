from typing import List, Any, Optional
import logging

from ..base.agent import BaseAgent
from ..base.strategy import AgentStrategy
from .config import AugmentConfig
from .strategies.direct import DirectStrategy
from .strategies.react import ReActStrategy


logger = logging.getLogger(__name__)


class AugmentAgent(BaseAgent):
    """Intelligent Q&A agent for Infraon ITSM platform"""
    
    def __init__(self, config: Optional[AugmentConfig] = None):
        self.augment_config = config or AugmentConfig()
        super().__init__(self.augment_config)
        logger.info(f"AugmentAgent initialized with strategy: {self.augment_config.strategy}")
    
    def _initialize_retriever(self) -> Any:
        """Initialize the retrieval component using existing fusion system"""
        try:
            from ...retrieval.fusion.fuser import Fuser
            from ...retrieval.api.retriever import ApiRetriever
            from ...retrieval.document.retriever import DocumentRetriever
            
            # Create retriever instances
            api_retriever = ApiRetriever()
            doc_retriever = DocumentRetriever()
            fuser = Fuser()
            
            # Create a wrapper that mimics the expected interface
            class RetrievalWrapper:
                def __init__(self, api_ret, doc_ret, fusion, top_k=10):
                    self.api_retriever = api_ret
                    self.doc_retriever = doc_ret
                    self.fuser = fusion
                    self.top_k = top_k
                
                def retrieve(self, query: str) -> List[dict]:
                    """Retrieve using fusion of API and document results"""
                    try:
                        api_results = self.api_retriever.retrieve(query)
                        doc_results = self.doc_retriever.retrieve(query)
                        fused_results = self.fuser.fuse([api_results, doc_results])
                        return fused_results[:self.top_k]
                    except Exception as e:
                        logger.error(f"Retrieval failed: {e}")
                        return []
            
            return RetrievalWrapper(api_retriever, doc_retriever, fuser, self.augment_config.retrieval_top_k)
            
        except ImportError as e:
            logger.warning(f"Could not initialize retrieval system: {e}")
            return None
    
    def _initialize_tools(self) -> List[Any]:
        """Initialize tools available to the agent"""
        tools = []
        
        # Add retrieval tool if available
        if self.retriever:
            retrieval_tool = type('Tool', (), {
                'name': 'knowledge_retriever',
                'description': 'Search Infraon documentation and APIs',
                'func': self.retriever.retrieve
            })()
            tools.append(retrieval_tool)
        
        # Add calculator tool for numerical computations
        def calculate(expression: str) -> str:
            """Simple calculator for basic math operations"""
            try:
                # Basic safety check - only allow specific characters
                allowed_chars = set('0123456789+-*/.() ')
                if not all(c in allowed_chars for c in expression):
                    return "Error: Invalid characters in expression"
                
                result = eval(expression)
                return str(result)
            except Exception as e:
                return f"Error: {str(e)}"
        
        calculator_tool = type('Tool', (), {
            'name': 'calculator',
            'description': 'Perform mathematical calculations',
            'func': calculate
        })()
        tools.append(calculator_tool)
        
        logger.info(f"Initialized {len(tools)} tools for AugmentAgent")
        return tools
    
    def _initialize_strategy(self) -> AgentStrategy:
        """Initialize the reasoning strategy based on configuration"""
        strategy_name = self.augment_config.strategy.lower()
        
        strategy_config = {
            "max_reasoning_loops": self.augment_config.max_reasoning_loops,
            "system_prompt_template": self.augment_config.system_prompt_template,
            "confidence_threshold": self.augment_config.retrieval_confidence_threshold,
            "enable_itsm_context": self.augment_config.enable_itsm_context,
            "max_response_length": self.augment_config.max_response_length
        }
        
        if strategy_name == "direct":
            return DirectStrategy(strategy_config, self.augment_config)
        elif strategy_name == "react":
            return ReActStrategy(strategy_config, self.augment_config)
        else:
            logger.warning(f"Unknown strategy '{strategy_name}', using Direct strategy")
            return DirectStrategy(strategy_config, self.augment_config)
    
    def get_agent_info(self) -> dict:
        """Get information about the agent configuration"""
        return {
            "agent_type": "AugmentAgent",
            "strategy": self.augment_config.strategy,
            "model": self.augment_config.model_name,
            "retrieval_enabled": self.augment_config.retrieval_enabled,
            "memory_enabled": self.augment_config.enable_memory,
            "max_context_tokens": self.augment_config.max_context_tokens,
            "tools_count": len(self.tools),
            "prompt_template": self.augment_config.system_prompt_template
        }
    
    def update_config(self, **kwargs) -> None:
        """Update agent configuration dynamically"""
        for key, value in kwargs.items():
            if hasattr(self.augment_config, key):
                setattr(self.augment_config, key, value)
                logger.info(f"Updated config: {key} = {value}")
            else:
                logger.warning(f"Unknown config parameter: {key}")
        
        # Reinitialize strategy if strategy changed
        if 'strategy' in kwargs:
            self.strategy = self._initialize_strategy()
            logger.info(f"Strategy updated to: {self.augment_config.strategy}")


# Convenience function for creating agent instances
def create_augment_agent(
    strategy: str = "direct",
    model_name: str = "gpt-4",
    template: str = "default",
    **kwargs
) -> AugmentAgent:
    """Create an AugmentAgent with specified configuration"""
    
    config = AugmentConfig(
        strategy=strategy,
        model_name=model_name,
        system_prompt_template=template,
        **kwargs
    )
    
    return AugmentAgent(config)