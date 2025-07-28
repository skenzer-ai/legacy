"""
Service Definition Agent

This module contains the ServiceDefinitionAgent, a conversational agent that
guides users through defining comprehensive service metadata including
descriptions, keywords, and operation classifications.
"""

import uuid
from typing import List, Dict, Any, Optional
import json

from ..models.api_specification import RawAPIEndpoint
from ..models.service_registry import ServiceDefinition, ServiceOperation, APIEndpoint
from ....core.agents.base.llm_service import LLMService

class ServiceDefinitionAgent:
    """
    Conversational agent for interactive service definition.
    """

    def __init__(self, llm_service: LLMService):
        """
        Initialize the agent with an LLM service.
        """
        self.llm_service = llm_service
        self.conversation_memory: Dict[str, Any] = {}
        self.system_prompt = self._build_system_prompt()

    async def start_definition_session(self, service_name: str, initial_endpoints: List[RawAPIEndpoint]) -> str:
        """
        Start an interactive session for defining a service.

        Args:
            service_name: The name of the service to define.
            initial_endpoints: The list of raw API endpoints for the service.

        Returns:
            A session ID for tracking the conversation.
        """
        session_id = str(uuid.uuid4())
        self.conversation_memory[session_id] = {
            "service_name": service_name,
            "endpoints": initial_endpoints,
            "current_step": "description",
            "data_collected": {},
            "history": []
        }
        
        # Generate initial question using LLM
        initial_question = await self._generate_intelligent_question(
            session_id, "description", service_name, initial_endpoints
        )
        
        self.conversation_memory[session_id]["history"].append({"agent": initial_question})
        
        return session_id

    async def process_user_response(self, session_id: str, user_input: str) -> Dict[str, Any]:
        """
        Process a user's response and continue the conversation.

        Args:
            session_id: The ID of the conversation session.
            user_input: The user's text response.

        Returns:
            A dictionary containing the agent's response and session status.
        """
        if session_id not in self.conversation_memory:
            raise ValueError("Invalid session ID")

        session = self.conversation_memory[session_id]
        session["history"].append({"user": user_input})

        current_step = session["current_step"]
        next_question = ""
        progress = 0.2

        if current_step == "description":
            # Process description and move to keywords
            session["data_collected"]["description"] = user_input
            session["current_step"] = "keywords"
            next_question = await self._generate_intelligent_question(
                session_id, "keywords", session["service_name"], session["endpoints"]
            )
            progress = 0.4
        elif current_step == "keywords":
            # Process keywords and move to operations
            keywords = await self._extract_keywords_with_llm(user_input)
            session["data_collected"]["keywords"] = keywords
            session["current_step"] = "operations"
            next_question = await self._generate_intelligent_question(
                session_id, "operations", session["service_name"], session["endpoints"]
            )
            progress = 0.6
        elif current_step == "operations":
            # Process operation classifications
            operation_data = await self._process_operation_response(session_id, user_input)
            session["data_collected"]["operations"] = operation_data
            session["current_step"] = "review"
            next_question = await self._generate_review_summary(session_id)
            progress = 0.8
        elif current_step == "review":
            # Final confirmation
            if "confirm" in user_input.lower() or "yes" in user_input.lower():
                session["current_step"] = "completed"
                next_question = "Service definition completed successfully!"
                progress = 1.0
                response = {
                    "response": next_question,
                    "current_step": session["current_step"],
                    "progress": progress,
                    "data_collected": session["data_collected"],
                    "needs_user_input": False,
                    "completion_status": "completed",
                    "service_definition": await self._build_service_definition(session_id)
                }
                session["history"].append({"agent": next_question})
                return response
            else:
                next_question = "Which part would you like to revise? (description, keywords, or operations)"
                progress = 0.8
        else:
            next_question = "Conversation completed."
            progress = 1.0

        response = {
            "response": next_question,
            "current_step": session["current_step"],
            "progress": progress,
            "data_collected": session["data_collected"],
            "needs_user_input": True,
            "completion_status": "in_progress"
        }

        session["history"].append({"agent": next_question})

        return response


    def _build_system_prompt(self) -> str:
        """
        Build the system prompt for the LLM.
        """
        return """
You are a ServiceDefinitionAgent, an expert in API service analysis and metadata collection.
Your role is to guide users through defining comprehensive service metadata including:
- Business descriptions
- Keywords and synonyms  
- Operation tier classifications (Tier 1: CRUD vs Tier 2: Specialized)

Be conversational, intelligent, and thorough. Ask follow-up questions when needed.
Always provide clear explanations and examples.
"""

    async def _generate_intelligent_question(self, session_id: str, step: str, service_name: str, endpoints: List[RawAPIEndpoint]) -> str:
        """
        Generate intelligent questions using LLM based on context.
        """
        session = self.conversation_memory[session_id]
        endpoint_summary = self._summarize_endpoints(endpoints)
        
        if step == "description":
            prompt = f"""
Analyze this service and generate an opening question to collect a business description:

Service Name: {service_name}
Endpoint Summary: {endpoint_summary}

Generate a conversational question that:
1. Shows you've analyzed the endpoints
2. Asks for a detailed business description
3. Is engaging and professional

Return only the question text.
"""
        elif step == "keywords":
            description = session["data_collected"].get("description", "")
            prompt = f"""
Based on this service information, generate a question to collect keywords and synonyms:

Service Name: {service_name}
Description: {description}
Endpoint Summary: {endpoint_summary}

Generate a question that asks for:
1. Keywords users might search for
2. Synonyms and alternative terms
3. Domain-specific terminology

Return only the question text.
"""
        elif step == "operations":
            description = session["data_collected"].get("description", "")
            keywords = session["data_collected"].get("keywords", [])
            prompt = f"""
Now we need to classify operations. Generate a question about operation tiers:

Service: {service_name}
Description: {description}
Keywords: {', '.join(keywords)}
Operations: {endpoint_summary}

Explain Tier 1 (CRUD: GET list, GET by ID, POST create, PUT update, DELETE) vs 
Tier 2 (Specialized operations) and ask the user to help classify any ambiguous operations.

Return only the question text.
"""
        else:
            return f"Let's continue with the next step for {service_name}."
        
        try:
            response = await self.llm_service.generate_response(prompt, self.system_prompt)
            return response.strip()
        except Exception as e:
            # Fallback to static questions
            return self._get_fallback_question(step, service_name, len(endpoints))

    async def _extract_keywords_with_llm(self, user_response: str) -> List[str]:
        """
        Extract and normalize keywords using LLM.
        """
        prompt = f"""
Extract all keywords, synonyms, and relevant terms from this user response:

"{user_response}"

Return a JSON list of clean, normalized keywords. Remove duplicates and normalize case.
Focus on business terms, technical terms, and user-facing language.

Example format: ["incident", "ticket", "issue", "problem", "request"]
"""
        
        try:
            response = await self.llm_service.generate_response(prompt, self.system_prompt)
            # Try to parse as JSON
            keywords = json.loads(response.strip())
            return keywords if isinstance(keywords, list) else []
        except Exception:
            # Fallback to simple parsing
            return [kw.strip() for kw in user_response.split(',') if kw.strip()]

    def _summarize_endpoints(self, endpoints: List[RawAPIEndpoint]) -> str:
        """
        Create a concise summary of endpoints.
        """
        if not endpoints:
            return "No endpoints found"
        
        summary_lines = []
        for ep in endpoints[:10]:  # Limit to first 10 for brevity
            summary_lines.append(f"{ep.method} {ep.path} ({ep.operation_id})")
        
        if len(endpoints) > 10:
            summary_lines.append(f"... and {len(endpoints) - 10} more endpoints")
        
        return "\n".join(summary_lines)
    
    def _get_fallback_question(self, step: str, service_name: str, endpoint_count: int) -> str:
        """
        Provide fallback questions if LLM fails.
        """
        if step == "description":
            return f"I've analyzed the '{service_name}' service with {endpoint_count} endpoints. Can you provide a detailed business description for this service?"
        elif step == "keywords":
            return f"What are some keywords or synonyms users might use to refer to the '{service_name}' service?"
        elif step == "operations":
            return "Let's classify the operations into Tier 1 (CRUD) and Tier 2 (specialized). Which operations need special classification?"
        else:
            return "Let's continue with the next step."

    async def _process_operation_response(self, session_id: str, user_response: str) -> Dict[str, Any]:
        """
        Process user's operation classification response.
        """
        session = self.conversation_memory[session_id]
        endpoints = session["endpoints"]
        
        # Use LLM to understand user's classification preferences
        prompt = f"""
The user provided this response about operation classification:
"{user_response}"

For these endpoints:
{self._summarize_endpoints(endpoints)}

Analyze the response and return a JSON object with:
{{
    "tier1_operations": ["list of operation_ids that are CRUD operations"],
    "tier2_operations": ["list of operation_ids that are specialized operations"],
    "user_notes": "summary of user's classification reasoning"
}}
"""
        
        try:
            response = await self.llm_service.generate_response(prompt, self.system_prompt)
            return json.loads(response.strip())
        except Exception:
            # Fallback classification
            return self._fallback_operation_classification(endpoints)
    
    def _fallback_operation_classification(self, endpoints: List[RawAPIEndpoint]) -> Dict[str, Any]:
        """
        Fallback operation classification logic.
        """
        tier1_ops = []
        tier2_ops = []
        
        for ep in endpoints:
            if ep.method.upper() in ['GET', 'POST', 'PUT', 'DELETE'] and 'list' in ep.operation_id.lower():
                tier1_ops.append(ep.operation_id)
            else:
                tier2_ops.append(ep.operation_id)
        
        return {
            "tier1_operations": tier1_ops,
            "tier2_operations": tier2_ops,
            "user_notes": "Automatic classification based on HTTP methods"
        }
    
    async def _generate_review_summary(self, session_id: str) -> str:
        """
        Generate a review summary of collected data.
        """
        session = self.conversation_memory[session_id]
        data = session["data_collected"]
        
        summary = f"""
**Service Definition Summary**

Service: {session['service_name']}
Description: {data.get('description', 'Not provided')}
Keywords: {', '.join(data.get('keywords', []))}
Operation Classification: {len(data.get('operations', {}).get('tier1_operations', []))} Tier 1, {len(data.get('operations', {}).get('tier2_operations', []))} Tier 2

Does this look correct? Type 'confirm' to save or tell me what to revise.
"""
        return summary
    
    async def _build_service_definition(self, session_id: str) -> ServiceDefinition:
        """
        Build final ServiceDefinition object from collected data.
        """
        session = self.conversation_memory[session_id]
        data = session["data_collected"]
        
        # Separate tier 1 and tier 2 operations
        tier1_ids = set(data.get('operations', {}).get('tier1_operations', []))
        tier1_operations = {}
        tier2_operations = {}
        
        for ep in session["endpoints"]:
            # Create APIEndpoint
            api_endpoint = APIEndpoint(
                path=ep.path,
                method=ep.method,
                operation_id=ep.operation_id,
                description=f"{ep.method} {ep.path}"
            )
            
            # Create ServiceOperation
            service_op = ServiceOperation(
                endpoint=api_endpoint,
                description=f"{ep.method} operation for {ep.path}",
                intent_verbs=[ep.method.lower()],
                intent_objects=[session["service_name"].lower()]
            )
            
            # Classify into tiers
            if ep.operation_id in tier1_ids:
                tier1_operations[ep.operation_id] = service_op
            else:
                tier2_operations[ep.operation_id] = service_op
        
        return ServiceDefinition(
            service_name=session["service_name"],
            service_description=data.get('description', ''),
            business_context=data.get('description', ''),
            keywords=data.get('keywords', []),
            synonyms=[],  # Could be extracted from keywords in future
            tier1_operations=tier1_operations,
            tier2_operations=tier2_operations
        )

    def get_session_status(self, session_id: str) -> Dict[str, Any]:
        """
        Get current session status and progress.
        """
        if session_id not in self.conversation_memory:
            return {"error": "Session not found"}
        
        session = self.conversation_memory[session_id]
        return {
            "session_id": session_id,
            "service_name": session["service_name"],
            "current_step": session["current_step"],
            "data_collected": session["data_collected"],
            "conversation_length": len(session["history"])
        }
    
    def clear_session(self, session_id: str) -> bool:
        """
        Clear a session from memory.
        """
        if session_id in self.conversation_memory:
            del self.conversation_memory[session_id]
            return True
        return False