from pydantic import Field
from typing import Optional
from ..base.config import BaseAgentConfig


class AugmentConfig(BaseAgentConfig):
    """Configuration specific to the Augment Agent"""
    
    # Strategy Configuration
    strategy: str = Field(default="direct", env="AUGMENT_STRATEGY")  # "direct", "react"
    max_reasoning_loops: int = Field(default=5, env="AUGMENT_MAX_LOOPS")
    
    # Prompt Configuration
    system_prompt_template: str = Field(default="default", env="AUGMENT_PROMPT_TEMPLATE")
    enable_itsm_context: bool = Field(default=True, env="AUGMENT_ENABLE_ITSM_CONTEXT")
    
    # Retrieval Configuration
    retrieval_top_k: int = Field(default=10, env="AUGMENT_RETRIEVAL_TOP_K")
    retrieval_confidence_threshold: float = Field(default=0.3, env="AUGMENT_RETRIEVAL_CONFIDENCE")
    
    # Response Configuration
    max_response_length: int = Field(default=2000, env="AUGMENT_MAX_RESPONSE_LENGTH")
    include_source_snippets: bool = Field(default=True, env="AUGMENT_INCLUDE_SNIPPETS")
    
    # ITSM Domain Configuration
    itsm_context_enabled: bool = Field(default=True, env="AUGMENT_ITSM_CONTEXT_ENABLED")
    infraon_focus: bool = Field(default=True, env="AUGMENT_INFRAON_FOCUS")


# Global instance
augment_config = AugmentConfig()