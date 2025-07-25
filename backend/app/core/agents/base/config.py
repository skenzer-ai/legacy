from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional, Dict, Any


class BaseAgentConfig(BaseSettings):
    """Base configuration for all agents"""
    
    # Model Configuration
    model_provider: str = Field(default="openrouter", env="AGENT_MODEL_PROVIDER")
    model_name: str = Field(default="google/gemma-3n-e4b-it", env="AGENT_MODEL_NAME")
    temperature: float = Field(default=0.7, env="AGENT_TEMPERATURE")
    max_tokens: Optional[int] = Field(default=2048, env="AGENT_MAX_TOKENS")
    
    # OpenRouter Configuration
    openrouter_api_key: Optional[str] = Field(default=None, env="OPENROUTER_API_KEY")
    openrouter_base_url: str = Field(default="https://openrouter.ai/api/v1", env="OPENROUTER_BASE_URL")
    openrouter_app_name: str = Field(default="Infraon-ITSM-Agent", env="OPENROUTER_APP_NAME")
    
    # Context Management
    max_context_tokens: int = Field(default=8000, env="AGENT_MAX_CONTEXT_TOKENS")
    enable_memory: bool = Field(default=True, env="AGENT_ENABLE_MEMORY")
    memory_trim_strategy: str = Field(default="oldest_first", env="AGENT_MEMORY_TRIM_STRATEGY")
    
    # Retrieval Configuration
    retrieval_enabled: bool = Field(default=True, env="AGENT_RETRIEVAL_ENABLED")
    retrieval_top_k: int = Field(default=10, env="AGENT_RETRIEVAL_TOP_K")
    
    # Response Configuration
    enable_reasoning_chain: bool = Field(default=True, env="AGENT_ENABLE_REASONING_CHAIN")
    enable_source_attribution: bool = Field(default=True, env="AGENT_ENABLE_SOURCE_ATTRIBUTION")
    confidence_threshold: float = Field(default=0.7, env="AGENT_CONFIDENCE_THRESHOLD")
    
    # Legacy API Keys (kept for compatibility)
    openai_api_key: Optional[str] = Field(default=None, env="OPENAI_API_KEY")
    anthropic_api_key: Optional[str] = Field(default=None, env="ANTHROPIC_API_KEY")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "allow"  # Allow additional fields for agent-specific configs