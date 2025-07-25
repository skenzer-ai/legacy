import os
from typing import Dict, Any, Optional
from pathlib import Path


class PromptTemplate:
    """Manages prompt templates for the agent"""
    
    def __init__(self, template_name: str = "default"):
        self.template_name = template_name
        self.template_dir = Path(__file__).parent / "templates"
        self.template_content = self._load_template()
    
    def _load_template(self) -> str:
        """Load template from file"""
        template_file = self.template_dir / f"{self.template_name}.txt"
        
        if template_file.exists():
            return template_file.read_text()
        else:
            # Return default template if file doesn't exist
            return self._get_default_template()
    
    def _get_default_template(self) -> str:
        """Default system prompt template"""
        return """You are an AI assistant specialized in Infraon ITSM platform support.

Your role is to help users understand and work with the Infraon platform by:
1. Answering questions about platform features and functionality
2. Providing guidance on ITSM workflows (incidents, requests, changes, problems, releases)
3. Explaining API usage and integration
4. Offering best practices for ITSM processes

Context Information:
{knowledge_base}

Conversation History:
{conversation_history}

Current Query: {query}

Instructions:
- Provide accurate, helpful responses based on the Infraon documentation
- If you're unsure about something, acknowledge the uncertainty
- Include relevant source references when possible
- Focus on practical, actionable guidance
- Use clear, professional language appropriate for IT professionals

Response:"""
    
    def format(
        self,
        query: str,
        knowledge_base: str = "",
        conversation_history: str = "",
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """Format the template with provided data"""
        
        # Prepare context data
        format_data = {
            "query": query,
            "knowledge_base": knowledge_base or "No specific documentation found.",
            "conversation_history": conversation_history or "No previous conversation.",
        }
        
        # Add any additional context
        if context:
            format_data.update(context)
        
        # Format the template
        try:
            return self.template_content.format(**format_data)
        except KeyError as e:
            # Handle missing template variables gracefully
            print(f"Warning: Template variable {e} not provided, using default")
            return self._get_fallback_prompt(query, knowledge_base, conversation_history)
    
    def _get_fallback_prompt(self, query: str, knowledge_base: str, conversation_history: str) -> str:
        """Fallback prompt if template formatting fails"""
        return f"""You are an AI assistant for the Infraon ITSM platform.

Knowledge Base: {knowledge_base}
Previous Conversation: {conversation_history}
User Query: {query}

Please provide a helpful response based on the available information."""


class PromptManager:
    """Manages multiple prompt templates"""
    
    def __init__(self):
        self.templates: Dict[str, PromptTemplate] = {}
    
    def get_template(self, template_name: str = "default") -> PromptTemplate:
        """Get or create a template"""
        if template_name not in self.templates:
            self.templates[template_name] = PromptTemplate(template_name)
        return self.templates[template_name]
    
    def list_available_templates(self) -> list[str]:
        """List all available template files"""
        template_dir = Path(__file__).parent / "templates"
        if template_dir.exists():
            return [f.stem for f in template_dir.glob("*.txt")]
        return ["default"]
    
    def reload_template(self, template_name: str) -> None:
        """Reload a template from file"""
        if template_name in self.templates:
            del self.templates[template_name]
        # Next access will reload from file