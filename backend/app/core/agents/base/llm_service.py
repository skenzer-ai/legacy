import asyncio
import logging
from typing import Optional, Dict, Any, List
from openai import AsyncOpenAI
import json

from .config import BaseAgentConfig

logger = logging.getLogger(__name__)


class LLMServiceError(Exception):
    """Custom exception for LLM service errors"""
    pass


class LLMService:
    """Service for handling LLM API calls through OpenRouter"""
    
    def __init__(self, config: BaseAgentConfig):
        self.config = config
        self.client = None
        self._initialize_client()
    
    def _initialize_client(self) -> None:
        """Initialize the OpenAI client for OpenRouter"""
        if not self.config.openrouter_api_key:
            logger.warning("No OpenRouter API key provided. LLM calls will fail.")
            return
        
        try:
            self.client = AsyncOpenAI(
                api_key=self.config.openrouter_api_key,
                base_url=self.config.openrouter_base_url,
                default_headers={
                    "HTTP-Referer": "https://github.com/your-org/infraon-itsm-agent",
                    "X-Title": self.config.openrouter_app_name,
                }
            )
            logger.info(f"LLM client initialized for model: {self.config.model_name}")
        except Exception as e:
            logger.error(f"Failed to initialize LLM client: {e}")
            raise LLMServiceError(f"Failed to initialize LLM client: {e}")
    
    async def generate_response(
        self, 
        prompt: str, 
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ) -> str:
        """Generate a response from the LLM"""
        
        if not self.client:
            raise LLMServiceError("LLM client not initialized. Check your OpenRouter API key.")
        
        try:
            # Prepare messages
            messages = []
            
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            
            messages.append({"role": "user", "content": prompt})
            
            # Use config defaults if not specified
            temperature = temperature if temperature is not None else self.config.temperature
            max_tokens = max_tokens if max_tokens is not None else self.config.max_tokens
            
            logger.debug(f"Generating response with model: {self.config.model_name}")
            
            # Make API call
            response = await self.client.chat.completions.create(
                model=self.config.model_name,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                stream=False
            )
            
            # Extract response content
            if response.choices and len(response.choices) > 0:
                content = response.choices[0].message.content
                if content:
                    logger.debug(f"Generated response length: {len(content)} characters")
                    return content.strip()
                else:
                    logger.warning("LLM returned empty response")
                    return "I apologize, but I was unable to generate a response to your query."
            else:
                logger.warning("LLM returned no choices")
                return "I apologize, but I was unable to generate a response to your query."
                
        except Exception as e:
            logger.error(f"Error generating LLM response: {e}")
            raise LLMServiceError(f"Failed to generate response: {e}")
    
    async def generate_structured_response(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        response_format: Optional[Dict[str, Any]] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ) -> Dict[str, Any]:
        """Generate a structured response (JSON) from the LLM"""
        
        if not self.client:
            raise LLMServiceError("LLM client not initialized. Check your OpenRouter API key.")
        
        try:
            # Prepare messages
            messages = []
            
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            
            # Add JSON format instruction to prompt
            json_instruction = ""
            if response_format:
                json_instruction = f"\n\nPlease respond with a valid JSON object matching this format:\n{json.dumps(response_format, indent=2)}"
            else:
                json_instruction = "\n\nPlease respond with a valid JSON object."
            
            messages.append({"role": "user", "content": prompt + json_instruction})
            
            # Use config defaults if not specified
            temperature = temperature if temperature is not None else self.config.temperature
            max_tokens = max_tokens if max_tokens is not None else self.config.max_tokens
            
            logger.debug(f"Generating structured response with model: {self.config.model_name}")
            
            # Make API call
            response = await self.client.chat.completions.create(
                model=self.config.model_name,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                stream=False
            )
            
            # Extract and parse response content
            if response.choices and len(response.choices) > 0:
                content = response.choices[0].message.content
                if content:
                    try:
                        # Try to parse as JSON
                        parsed_response = json.loads(content.strip())
                        logger.debug("Successfully parsed structured response")
                        return parsed_response
                    except json.JSONDecodeError:
                        logger.warning("LLM response was not valid JSON, returning as text")
                        return {"response": content.strip(), "error": "Response was not valid JSON"}
                else:
                    logger.warning("LLM returned empty response")
                    return {"error": "Empty response from LLM"}
            else:
                logger.warning("LLM returned no choices")
                return {"error": "No response choices from LLM"}
                
        except Exception as e:
            logger.error(f"Error generating structured LLM response: {e}")
            raise LLMServiceError(f"Failed to generate structured response: {e}")
    
    async def generate_chat_response(
        self,
        messages: List[Dict[str, str]],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ) -> str:
        """Generate a response from a conversation history"""
        
        if not self.client:
            raise LLMServiceError("LLM client not initialized. Check your OpenRouter API key.")
        
        try:
            # Use config defaults if not specified
            temperature = temperature if temperature is not None else self.config.temperature
            max_tokens = max_tokens if max_tokens is not None else self.config.max_tokens
            
            logger.debug(f"Generating chat response with {len(messages)} messages")
            
            # Make API call
            response = await self.client.chat.completions.create(
                model=self.config.model_name,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                stream=False
            )
            
            # Extract response content
            if response.choices and len(response.choices) > 0:
                content = response.choices[0].message.content
                if content:
                    logger.debug(f"Generated chat response length: {len(content)} characters")
                    return content.strip()
                else:
                    logger.warning("LLM returned empty chat response")
                    return "I apologize, but I was unable to generate a response."
            else:
                logger.warning("LLM returned no choices for chat")
                return "I apologize, but I was unable to generate a response."
                
        except Exception as e:
            logger.error(f"Error generating chat response: {e}")
            raise LLMServiceError(f"Failed to generate chat response: {e}")
    
    def is_available(self) -> bool:
        """Check if the LLM service is available"""
        return self.client is not None and bool(self.config.openrouter_api_key)
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the current model configuration"""
        return {
            "provider": self.config.model_provider,
            "model_name": self.config.model_name,
            "temperature": self.config.temperature,
            "max_tokens": self.config.max_tokens,
            "base_url": self.config.openrouter_base_url,
            "available": self.is_available()
        }