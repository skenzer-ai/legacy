from typing import List, Dict, Any, Optional
import asyncio
from datetime import datetime

from ...base.strategy import AgentStrategy, StrategyResult
from ...base.response import AgentResponse, ReasoningStep, Source, ReasoningStepType
from ...base.llm_service import LLMService, LLMServiceError
from ...base.config import BaseAgentConfig
from ..prompts.manager import PromptManager


class DirectStrategy(AgentStrategy):
    """Direct response strategy without iterative reasoning"""
    
    def __init__(self, config: Dict[str, Any], agent_config: BaseAgentConfig):
        super().__init__(config)
        self.prompt_manager = PromptManager()
        self.template_name = config.get("system_prompt_template", "default")
        self.llm_service = LLMService(agent_config)
        self.agent_config = agent_config
    
    async def execute(
        self,
        query: str,
        context: Optional[Dict[str, Any]],
        tools: List[Any],
        memory_context: str = ""
    ) -> AgentResponse:
        """Execute direct response strategy"""
        
        reasoning_steps = []
        sources = []
        
        # Step 1: Retrieve relevant knowledge
        reasoning_steps.append(ReasoningStep(
            step_type=ReasoningStepType.THOUGHT,
            content="I need to search for relevant information to answer this query."
        ))
        
        knowledge_base = ""
        if tools:
            # Use retrieval tool if available
            retrieval_tool = self._get_retrieval_tool(tools)
            if retrieval_tool:
                try:
                    retrieval_results = await self._retrieve_knowledge(retrieval_tool, query)
                    knowledge_base = self._format_retrieval_results(retrieval_results)
                    sources.extend(self._extract_sources(retrieval_results))
                    
                    reasoning_steps.append(ReasoningStep(
                        step_type=ReasoningStepType.ACTION,
                        content=f"Retrieved {len(retrieval_results)} relevant documents from knowledge base."
                    ))
                except Exception as e:
                    reasoning_steps.append(ReasoningStep(
                        step_type=ReasoningStepType.OBSERVATION,
                        content=f"Knowledge retrieval failed: {str(e)}. Proceeding with general knowledge."
                    ))
        
        # Step 2: Generate response using LLM
        reasoning_steps.append(ReasoningStep(
            step_type=ReasoningStepType.THOUGHT,
            content="Now I'll generate a comprehensive response based on the retrieved information."
        ))
        
        try:
            # Format prompt
            template = self.prompt_manager.get_template(self.template_name)
            formatted_prompt = template.format(
                query=query,
                knowledge_base=knowledge_base,
                conversation_history=memory_context,
                context=context
            )
            
            # Generate response (placeholder - would use actual LLM here)
            answer = await self._generate_llm_response(formatted_prompt, query, knowledge_base)
            
            reasoning_steps.append(ReasoningStep(
                step_type=ReasoningStepType.CONCLUSION,
                content="Generated response based on retrieved knowledge and query analysis."
            ))
            
            return AgentResponse(
                answer=answer,
                sources=sources,
                reasoning_chain=reasoning_steps,
                confidence=self._calculate_confidence(knowledge_base, sources),
                metadata={
                    "strategy": "direct",
                    "template_used": self.template_name,
                    "sources_count": len(sources),
                    "retrieval_successful": len(sources) > 0
                }
            )
            
        except Exception as e:
            reasoning_steps.append(ReasoningStep(
                step_type=ReasoningStepType.OBSERVATION,
                content=f"Response generation failed: {str(e)}"
            ))
            
            return AgentResponse(
                answer=f"I encountered an error while processing your query: {str(e)}",
                sources=sources,
                reasoning_chain=reasoning_steps,
                confidence=0.0,
                metadata={"strategy": "direct", "error": str(e)}
            )
    
    def get_strategy_name(self) -> str:
        return "direct"
    
    def _get_retrieval_tool(self, tools: List[Any]) -> Optional[Any]:
        """Find the retrieval tool from available tools"""
        for tool in tools:
            if hasattr(tool, 'retrieve') or getattr(tool, 'name', '') == 'knowledge_retriever':
                return tool
        return None
    
    async def _retrieve_knowledge(self, retrieval_tool: Any, query: str) -> List[Dict[str, Any]]:
        """Retrieve knowledge using the retrieval tool"""
        # This would interface with the actual retrieval system
        if hasattr(retrieval_tool, 'retrieve'):
            if asyncio.iscoroutinefunction(retrieval_tool.retrieve):
                return await retrieval_tool.retrieve(query)
            else:
                return retrieval_tool.retrieve(query)
        elif hasattr(retrieval_tool, 'func'):
            # For LangChain-style tools
            result = retrieval_tool.func(query)
            return result if isinstance(result, list) else [result]
        else:
            return []
    
    def _format_retrieval_results(self, results: List[Dict[str, Any]]) -> str:
        """Format retrieval results for inclusion in prompt"""
        if not results:
            return "No specific documentation found."
        
        formatted_results = []
        for i, result in enumerate(results[:5], 1):  # Limit to top 5 results
            if isinstance(result, dict):
                if 'page_content' in result:
                    # Document result
                    content = result['page_content'][:300] + "..." if len(result['page_content']) > 300 else result['page_content']
                    formatted_results.append(f"{i}. {content}")
                elif 'path' in result:
                    # API result
                    path = result.get('path', '')
                    method = result.get('method', '')
                    description = result.get('description', '')
                    formatted_results.append(f"{i}. API: {method} {path} - {description}")
                else:
                    # Generic result
                    formatted_results.append(f"{i}. {str(result)[:300]}")
            else:
                formatted_results.append(f"{i}. {str(result)[:300]}")
        
        return "\n".join(formatted_results)
    
    def _extract_sources(self, results: List[Dict[str, Any]]) -> List[Source]:
        """Extract sources from retrieval results"""
        sources = []
        for result in results:
            if isinstance(result, dict):
                if 'page_content' in result:
                    # Document source
                    sources.append(Source(
                        type="document",
                        content=result['page_content'][:200] + "..." if len(result['page_content']) > 200 else result['page_content'],
                        reference=result.get('metadata', {}).get('source', 'Unknown document'),
                        confidence=0.8
                    ))
                elif 'path' in result:
                    # API source
                    sources.append(Source(
                        type="api",
                        content=f"{result.get('method', '')} {result.get('path', '')} - {result.get('description', '')}",
                        reference=result.get('operationId', result.get('path', 'Unknown API')),
                        confidence=0.8
                    ))
        
        return sources
    
    async def _generate_llm_response(self, prompt: str, query: str, knowledge_base: str) -> str:
        """Generate LLM response using the configured LLM service"""
        try:
            if not self.llm_service.is_available():
                # Fallback response when LLM is not available
                return self._generate_fallback_response(query, knowledge_base)
            
            # Format the complete prompt using the template
            template = self.prompt_manager.get_template(self.template_name)
            formatted_prompt = template.format(
                query=query,
                knowledge_base=knowledge_base,
                conversation_history="",  # Will be provided by memory context
                context={}
            )
            
            # Generate response using LLM service
            response = await self.llm_service.generate_response(
                prompt=query,
                system_prompt=formatted_prompt,
                temperature=self.agent_config.temperature,
                max_tokens=self.agent_config.max_tokens
            )
            
            return response
            
        except LLMServiceError as e:
            # Log the error and provide fallback response
            print(f"LLM service error: {str(e)}. Providing fallback response.")
            return self._generate_fallback_response(query, knowledge_base)
        except Exception as e:
            # Handle unexpected errors
            return f"I encountered an unexpected error while processing your query: {str(e)}"
    
    def _generate_fallback_response(self, query: str, knowledge_base: str) -> str:
        """Generate a fallback response when LLM is not available"""
        if knowledge_base and knowledge_base != "No specific documentation found.":
            return f"""Based on the Infraon platform documentation, here's what I found regarding your query:

{self._create_structured_response(query, knowledge_base)}

This information is derived from the official Infraon documentation and API specifications. If you need more specific details or have follow-up questions, please let me know."""
        else:
            return f"""I understand you're asking about: {query}

However, I don't have specific documentation available for this query. For the most accurate and up-to-date information about the Infraon platform, I recommend:

1. Checking the official Infraon user guide
2. Consulting the API documentation
3. Contacting your system administrator
4. Reviewing the platform's help section

If you can provide more context or rephrase your question, I might be able to offer more targeted assistance."""
    
    def _create_structured_response(self, query: str, knowledge_base: str) -> str:
        """Create a structured response based on query and knowledge"""
        # Simple heuristic-based response formatting
        lines = knowledge_base.split('\n')
        relevant_info = []
        
        for line in lines:
            if line.strip() and any(keyword in line.lower() for keyword in query.lower().split()):
                relevant_info.append(line.strip())
        
        if relevant_info:
            return '\n'.join(relevant_info[:3])  # Top 3 most relevant pieces
        else:
            return knowledge_base[:500] + "..." if len(knowledge_base) > 500 else knowledge_base
    
    def _calculate_confidence(self, knowledge_base: str, sources: List[Source]) -> float:
        """Calculate confidence score for the response"""
        base_confidence = 0.7
        
        # Increase confidence if we have sources
        if sources:
            base_confidence += 0.2
        
        # Increase confidence if we have substantial knowledge base
        if knowledge_base and len(knowledge_base) > 100:
            base_confidence += 0.1
        
        return min(base_confidence, 1.0)