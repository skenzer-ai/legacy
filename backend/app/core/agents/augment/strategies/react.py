from typing import List, Dict, Any, Optional
import asyncio
import re
from datetime import datetime

from ...base.strategy import AgentStrategy, StrategyResult
from ...base.response import AgentResponse, ReasoningStep, Source, ReasoningStepType
from ...base.llm_service import LLMService, LLMServiceError
from ...base.config import BaseAgentConfig
from ..prompts.manager import PromptManager


class ReActStrategy(AgentStrategy):
    """ReAct (Reasoning + Acting) strategy with iterative thought-action-observation loops"""
    
    def __init__(self, config: Dict[str, Any], agent_config: BaseAgentConfig):
        super().__init__(config)
        self.prompt_manager = PromptManager()
        self.template_name = config.get("system_prompt_template", "default")
        self.max_loops = config.get("max_reasoning_loops", 5)
        self.confidence_threshold = config.get("confidence_threshold", 0.7)
        self.llm_service = LLMService(agent_config)
        self.agent_config = agent_config
    
    async def execute(
        self,
        query: str,
        context: Optional[Dict[str, Any]],
        tools: List[Any],
        memory_context: str = ""
    ) -> AgentResponse:
        """Execute ReAct strategy with iterative reasoning"""
        
        reasoning_steps = []
        sources = []
        all_observations = []
        
        # Initial setup
        reasoning_steps.append(ReasoningStep(
            step_type=ReasoningStepType.THOUGHT,
            content=f"I need to answer the query: '{query}'. Let me think about this step by step."
        ))
        
        # Get available tools
        available_tools = self._get_tool_descriptions(tools)
        
        # ReAct loop
        for iteration in range(self.max_loops):
            reasoning_steps.append(ReasoningStep(
                step_type=ReasoningStepType.THOUGHT,
                content=f"Iteration {iteration + 1}: Analyzing what I need to do next."
            ))
            
            # Generate thought about what to do next
            thought = await self._generate_thought(
                query, all_observations, available_tools, iteration
            )
            
            reasoning_steps.append(ReasoningStep(
                step_type=ReasoningStepType.THOUGHT,
                content=thought
            ))
            
            # Decide on action based on thought
            action_needed = self._analyze_action_needed(thought, all_observations, tools)
            
            if action_needed == "search":
                # Use retrieval tool
                action_result = await self._perform_search_action(query, tools)
                reasoning_steps.append(ReasoningStep(
                    step_type=ReasoningStepType.ACTION,
                    content=f"Searching knowledge base for information about: {query}"
                ))
                
                observation = self._process_search_results(action_result)
                sources.extend(self._extract_sources_from_results(action_result))
                
            elif action_needed == "calculate":
                # Use calculation tool
                calculation_query = self._extract_calculation_from_thought(thought)
                action_result = await self._perform_calculation_action(calculation_query, tools)
                reasoning_steps.append(ReasoningStep(
                    step_type=ReasoningStepType.ACTION,
                    content=f"Performing calculation: {calculation_query}"
                ))
                
                observation = f"Calculation result: {action_result}"
                
            elif action_needed == "conclude":
                # Ready to provide final answer
                reasoning_steps.append(ReasoningStep(
                    step_type=ReasoningStepType.THOUGHT,
                    content="I have gathered sufficient information to provide a comprehensive answer."
                ))
                break
                
            else:
                # Search by default if unclear
                action_result = await self._perform_search_action(query, tools)
                reasoning_steps.append(ReasoningStep(
                    step_type=ReasoningStepType.ACTION,
                    content="Searching for relevant information to answer the query."
                ))
                
                observation = self._process_search_results(action_result)
                sources.extend(self._extract_sources_from_results(action_result))
            
            # Record observation
            reasoning_steps.append(ReasoningStep(
                step_type=ReasoningStepType.OBSERVATION,
                content=observation
            ))
            
            all_observations.append(observation)
            
            # Check if we have enough information to conclude
            if self._should_conclude(all_observations, query):
                reasoning_steps.append(ReasoningStep(
                    step_type=ReasoningStepType.THOUGHT,
                    content="I believe I have sufficient information to provide a good answer."
                ))
                break
        
        # Generate final answer based on all observations
        final_answer = await self._generate_final_answer(
            query, all_observations, memory_context, context
        )
        
        reasoning_steps.append(ReasoningStep(
            step_type=ReasoningStepType.CONCLUSION,
            content="Generated comprehensive answer based on research and reasoning."
        ))
        
        return AgentResponse(
            answer=final_answer,
            sources=sources,
            reasoning_chain=reasoning_steps,
            confidence=self._calculate_confidence(all_observations, sources),
            metadata={
                "strategy": "react",
                "iterations": len([s for s in reasoning_steps if s.step_type == ReasoningStepType.ACTION]),
                "template_used": self.template_name,
                "sources_count": len(sources),
                "observations_count": len(all_observations)
            }
        )
    
    def get_strategy_name(self) -> str:
        return "react"
    
    def _get_tool_descriptions(self, tools: List[Any]) -> str:
        """Get descriptions of available tools"""
        if not tools:
            return "No tools available."
        
        descriptions = []
        for tool in tools:
            name = getattr(tool, 'name', 'unknown_tool')
            desc = getattr(tool, 'description', 'No description available')
            descriptions.append(f"- {name}: {desc}")
        
        return "\n".join(descriptions)
    
    async def _generate_thought(
        self, 
        query: str, 
        observations: List[str], 
        available_tools: str, 
        iteration: int
    ) -> str:
        """Generate a thought about what to do next using LLM"""
        
        try:
            if not self.llm_service.is_available():
                # Fallback to heuristic-based thinking
                return self._generate_heuristic_thought(query, observations, iteration)
            
            # Prepare context for LLM
            context = f"""
You are an AI assistant helping with Infraon ITSM platform queries. You are in iteration {iteration + 1} of a reasoning process.

Original Query: {query}

Available Tools:
{available_tools}

Previous Observations:
{chr(10).join(f"{i+1}. {obs}" for i, obs in enumerate(observations)) if observations else "None yet"}

Think about what you should do next. Consider:
1. Do you have enough information to answer the query?
2. Do you need to search for more information?
3. Do you need to perform calculations?
4. Should you conclude with the available information?

Respond with a single thought about what to do next (1-2 sentences).
"""
            
            thought = await self.llm_service.generate_response(
                prompt=context,
                temperature=0.3,  # Lower temperature for more focused thinking
                max_tokens=150
            )
            
            return thought.strip()
            
        except Exception as e:
            print(f"Error generating thought: {e}")
            return self._generate_heuristic_thought(query, observations, iteration)
    
    def _generate_heuristic_thought(self, query: str, observations: List[str], iteration: int) -> str:
        """Fallback heuristic-based thought generation"""
        if iteration == 0:
            return f"I need to understand what the user is asking about: '{query}'. Let me search for relevant information first."
        
        if not observations:
            return "I don't have any information yet. I should search for relevant documentation or data."
        
        latest_observation = observations[-1] if observations else ""
        
        # Simple heuristic-based thought generation
        if "no results" in latest_observation.lower() or "not found" in latest_observation.lower():
            return "The previous search didn't yield good results. Let me try a different search approach or conclude with available information."
        
        if "calculation" in query.lower() or any(word in query.lower() for word in ["time", "average", "total", "count", "sum"]):
            return "This query might require some calculations. Let me see if I need to compute something based on the information I have."
        
        if len(observations) >= 2:
            return "I have gathered some information. Let me analyze if I have enough to provide a comprehensive answer."
        
        return "Let me gather more specific information to provide a better answer."
    
    def _analyze_action_needed(self, thought: str, observations: List[str], tools: List[Any]) -> str:
        """Analyze what action is needed based on the thought"""
        
        thought_lower = thought.lower()
        
        # Check if calculation is needed
        calc_keywords = ["calculate", "calculation", "compute", "sum", "average", "total", "count"]
        if any(keyword in thought_lower for keyword in calc_keywords):
            # Check if we have a calculator tool
            if any(getattr(tool, 'name', '') == 'calculator' for tool in tools):
                return "calculate"
        
        # Check if we should conclude
        conclude_keywords = ["enough", "sufficient", "ready", "comprehensive", "conclude"]
        if any(keyword in thought_lower for keyword in conclude_keywords) and len(observations) > 0:
            return "conclude"
        
        # Default to search
        return "search"
    
    async def _perform_search_action(self, query: str, tools: List[Any]) -> List[Dict[str, Any]]:
        """Perform search action using retrieval tools"""
        retrieval_tool = None
        for tool in tools:
            if hasattr(tool, 'retrieve') or getattr(tool, 'name', '') == 'knowledge_retriever':
                retrieval_tool = tool
                break
        
        if not retrieval_tool:
            return []
        
        try:
            if hasattr(retrieval_tool, 'retrieve'):
                if asyncio.iscoroutinefunction(retrieval_tool.retrieve):
                    return await retrieval_tool.retrieve(query)
                else:
                    return retrieval_tool.retrieve(query)
            elif hasattr(retrieval_tool, 'func'):
                result = retrieval_tool.func(query)
                return result if isinstance(result, list) else [result]
        except Exception as e:
            return [{"error": f"Search failed: {str(e)}"}]
        
        return []
    
    async def _perform_calculation_action(self, calculation: str, tools: List[Any]) -> str:
        """Perform calculation using calculator tool"""
        calc_tool = None
        for tool in tools:
            if getattr(tool, 'name', '') == 'calculator':
                calc_tool = tool
                break
        
        if not calc_tool:
            return "Calculator tool not available"
        
        try:
            if hasattr(calc_tool, 'func'):
                return calc_tool.func(calculation)
            else:
                return "Calculator tool not properly configured"
        except Exception as e:
            return f"Calculation failed: {str(e)}"
    
    def _extract_calculation_from_thought(self, thought: str) -> str:
        """Extract calculation expression from thought"""
        # Simple regex to find mathematical expressions
        calc_pattern = r'[\d+\-*/().\s]+'
        matches = re.findall(calc_pattern, thought)
        
        if matches:
            # Return the longest match that looks like a calculation
            longest_match = max(matches, key=len)
            if len(longest_match.strip()) > 3:  # Minimum reasonable calculation length
                return longest_match.strip()
        
        return "1+1"  # Default simple calculation
    
    def _process_search_results(self, results: List[Dict[str, Any]]) -> str:
        """Process search results into an observation"""
        if not results:
            return "No relevant information found in the knowledge base."
        
        if any("error" in result for result in results):
            error_msg = next((result.get("error", "") for result in results if "error" in result), "")
            return f"Search encountered an error: {error_msg}"
        
        # Format results into a readable observation
        formatted_results = []
        for i, result in enumerate(results[:3], 1):  # Limit to top 3 results
            if isinstance(result, dict):
                if 'page_content' in result:
                    content = result['page_content'][:200] + "..." if len(result['page_content']) > 200 else result['page_content']
                    formatted_results.append(f"{i}. {content}")
                elif 'path' in result:
                    path = result.get('path', '')
                    method = result.get('method', '')
                    description = result.get('description', '')
                    formatted_results.append(f"{i}. API: {method} {path} - {description}")
                else:
                    formatted_results.append(f"{i}. {str(result)[:200]}")
        
        if formatted_results:
            return f"Found relevant information:\n" + "\n".join(formatted_results)
        else:
            return "Search completed but no specific relevant information was found."
    
    def _extract_sources_from_results(self, results: List[Dict[str, Any]]) -> List[Source]:
        """Extract sources from search results"""
        sources = []
        for result in results:
            if isinstance(result, dict) and "error" not in result:
                if 'page_content' in result:
                    sources.append(Source(
                        type="document",
                        content=result['page_content'][:200] + "..." if len(result['page_content']) > 200 else result['page_content'],
                        reference=result.get('metadata', {}).get('source', 'Unknown document'),
                        confidence=0.8
                    ))
                elif 'path' in result:
                    sources.append(Source(
                        type="api",
                        content=f"{result.get('method', '')} {result.get('path', '')} - {result.get('description', '')}",
                        reference=result.get('operationId', result.get('path', 'Unknown API')),
                        confidence=0.8
                    ))
        
        return sources
    
    def _should_conclude(self, observations: List[str], query: str) -> bool:
        """Determine if we have enough information to conclude"""
        if len(observations) < 1:
            return False
        
        # If we have good information from recent observations
        latest_observation = observations[-1].lower()
        if "found relevant information" in latest_observation or "api:" in latest_observation:
            return True
        
        # If we've tried multiple times without success
        if len(observations) >= 3:
            return True
        
        return False
    
    async def _generate_final_answer(
        self, 
        query: str, 
        observations: List[str], 
        memory_context: str, 
        context: Optional[Dict[str, Any]]
    ) -> str:
        """Generate final answer based on observations using LLM"""
        
        try:
            if not self.llm_service.is_available():
                # Fallback to heuristic-based response
                return self._generate_heuristic_final_answer(query, observations, memory_context)
            
            # Combine all observations
            knowledge_base = "\n\n".join(observations) if observations else "No specific information was gathered during the search process."
            
            # Use prompt template to generate structured response
            template = self.prompt_manager.get_template(self.template_name)
            system_prompt = template.format(
                query=query,
                knowledge_base=knowledge_base,
                conversation_history=memory_context or "No previous conversation.",
                context=context or {}
            )
            
            # Create detailed prompt for final answer generation
            final_prompt = f"""
Based on my research process, I need to provide a comprehensive answer to this query: {query}

Research Results:
{knowledge_base}

Please provide a clear, helpful response that:
1. Directly answers the user's question
2. References specific information found during research
3. Acknowledges any limitations in the available information
4. Offers next steps or additional resources if appropriate

Make the response professional and specific to the Infraon ITSM platform context.
"""
            
            # Generate response using LLM service
            response = await self.llm_service.generate_response(
                prompt=final_prompt,
                system_prompt=system_prompt,
                temperature=self.agent_config.temperature,
                max_tokens=self.agent_config.max_tokens
            )
            
            return response
            
        except Exception as e:
            print(f"Error generating final answer: {e}")
            return self._generate_heuristic_final_answer(query, observations, memory_context)
    
    def _generate_heuristic_final_answer(self, query: str, observations: List[str], memory_context: str) -> str:
        """Fallback heuristic-based final answer generation"""
        if observations and any("found relevant information" in obs.lower() for obs in observations):
            return f"""Based on my research into the Infraon platform, here's what I found regarding your query:

{self._create_structured_response_from_observations(query, observations)}

This information comes from the official Infraon documentation and API specifications. The reasoning process involved {len(observations)} research steps to gather comprehensive information.

If you need more specific details or have follow-up questions, please let me know."""
        else:
            return f"""I conducted a thorough search to answer your query: "{query}"

However, I wasn't able to find specific documentation that directly addresses your question. Here's what I attempted:

{self._summarize_search_attempts(observations)}

For the most accurate and up-to-date information about the Infraon platform, I recommend:
1. Checking the official Infraon user guide
2. Consulting the API documentation
3. Contacting your system administrator
4. Reviewing the platform's help section

If you can provide more context or rephrase your question, I might be able to offer more targeted assistance."""
    
    def _create_structured_response_from_observations(self, query: str, observations: List[str]) -> str:
        """Create structured response from observations"""
        relevant_info = []
        
        for obs in observations:
            if "found relevant information" in obs.lower():
                # Extract the numbered points
                lines = obs.split('\n')
                for line in lines[1:]:  # Skip the "Found relevant information:" line
                    if line.strip() and (line.strip().startswith(('1.', '2.', '3.')) or 'API:' in line):
                        relevant_info.append(line.strip())
        
        if relevant_info:
            return '\n'.join(relevant_info)
        else:
            # Fallback to combining all observations
            return '\n'.join(obs for obs in observations if obs.strip())
    
    def _summarize_search_attempts(self, observations: List[str]) -> str:
        """Summarize the search attempts made"""
        if not observations:
            return "- No search attempts were made"
        
        attempts = []
        for i, obs in enumerate(observations, 1):
            if "no relevant information" in obs.lower() or "not found" in obs.lower():
                attempts.append(f"- Attempt {i}: No matching documentation found")
            elif "error" in obs.lower():
                attempts.append(f"- Attempt {i}: Search encountered technical issues")
            else:
                attempts.append(f"- Attempt {i}: Search completed but results were not directly relevant")
        
        return '\n'.join(attempts)
    
    def _calculate_confidence(self, observations: List[str], sources: List[Source]) -> float:
        """Calculate confidence score based on observations and sources"""
        base_confidence = 0.5
        
        # Increase confidence for successful searches
        successful_searches = sum(1 for obs in observations if "found relevant information" in obs.lower())
        base_confidence += (successful_searches * 0.2)
        
        # Increase confidence for having sources
        if sources:
            base_confidence += 0.2
        
        # Decrease confidence for failed searches
        failed_searches = sum(1 for obs in observations if any(term in obs.lower() for term in ["no relevant", "not found", "error"]))
        base_confidence -= (failed_searches * 0.1)
        
        return max(0.1, min(base_confidence, 1.0))