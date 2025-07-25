#!/usr/bin/env python3
"""
Test script for the agent framework to ensure imports and basic functionality work.
"""
import sys
import os
from datetime import datetime
import pytest

# Add the backend directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'app'))


class TestAgentFrameworkImports:
    """Test all imports work correctly"""
    
    def test_response_models_import(self):
        """Test response model imports"""
        from app.core.agents.base.response import (
            AgentResponse, AgentRequest, ReasoningStep, 
            Source, ReasoningStepType
        )
        assert True  # If we get here, import succeeded
    
    def test_config_import(self):
        """Test configuration imports"""
        from app.core.agents.base.config import BaseAgentConfig
        assert True
    
    def test_memory_import(self):
        """Test memory management imports"""
        from app.core.agents.base.memory import AgentMemory, ConversationExchange
        assert True
    
    def test_strategy_import(self):
        """Test strategy pattern imports"""
        from app.core.agents.base.strategy import AgentStrategy, StrategyResult
        assert True
    
    def test_base_agent_import(self):
        """Test base agent import"""
        from app.core.agents.base.agent import BaseAgent
        assert True
    
    def test_augment_config_import(self):
        """Test augment config import"""
        from app.core.agents.augment.config import AugmentConfig, augment_config
        assert True


class TestResponseModels:
    """Test response model creation and functionality"""
    
    def test_reasoning_step_creation(self):
        """Test ReasoningStep model creation"""
        from app.core.agents.base.response import ReasoningStep, ReasoningStepType
        
        step = ReasoningStep(
            step_type=ReasoningStepType.THOUGHT,
            content="I need to search for information about incidents.",
            confidence=0.9
        )
        
        assert step.step_type == ReasoningStepType.THOUGHT
        assert step.content == "I need to search for information about incidents."
        assert step.confidence == 0.9
        assert isinstance(step.timestamp, datetime)
    
    def test_source_creation(self):
        """Test Source model creation"""
        from app.core.agents.base.response import Source
        
        source = Source(
            type="document",
            content="Information about creating incidents...",
            reference="user_docs/infraon_user_guide.md",
            confidence=0.8
        )
        
        assert source.type == "document"
        assert source.content == "Information about creating incidents..."
        assert source.reference == "user_docs/infraon_user_guide.md"
        assert source.confidence == 0.8
    
    def test_agent_response_creation(self):
        """Test AgentResponse model creation"""
        from app.core.agents.base.response import (
            AgentResponse, ReasoningStep, Source, ReasoningStepType
        )
        
        step = ReasoningStep(
            step_type=ReasoningStepType.THOUGHT,
            content="Thinking about the query..."
        )
        
        source = Source(
            type="document",
            content="Relevant information...",
            confidence=0.8
        )
        
        response = AgentResponse(
            answer="To create an incident in Infraon, you need to...",
            sources=[source],
            reasoning_chain=[step],
            confidence=0.85
        )
        
        assert response.answer == "To create an incident in Infraon, you need to..."
        assert len(response.sources) == 1
        assert len(response.reasoning_chain) == 1
        assert response.confidence == 0.85
    
    def test_agent_request_creation(self):
        """Test AgentRequest model creation"""
        from app.core.agents.base.response import AgentRequest
        
        request = AgentRequest(
            query="How do I create an incident?",
            context={"user_role": "admin"},
            session_id="test-session-123"
        )
        
        assert request.query == "How do I create an incident?"
        assert request.context == {"user_role": "admin"}
        assert request.session_id == "test-session-123"


class TestConfiguration:
    """Test configuration loading and validation"""
    
    def test_base_config_defaults(self):
        """Test base configuration defaults"""
        from app.core.agents.base.config import BaseAgentConfig
        
        config = BaseAgentConfig()
        
        assert config.model_provider == "openai"
        assert config.model_name == "gpt-4"
        assert config.temperature == 0.7
        assert config.max_context_tokens == 8000
        assert config.enable_memory is True
        assert config.retrieval_enabled is True
    
    def test_augment_config_defaults(self):
        """Test augment configuration defaults"""
        from app.core.agents.augment.config import AugmentConfig
        
        config = AugmentConfig()
        
        assert config.strategy == "direct"
        assert config.max_reasoning_loops == 5
        assert config.system_prompt_template == "default"
        assert config.retrieval_top_k == 10
        assert config.itsm_context_enabled is True


class TestMemoryManagement:
    """Test memory management functionality"""
    
    def test_memory_initialization(self):
        """Test memory initialization"""
        from app.core.agents.base.memory import AgentMemory
        
        memory = AgentMemory(max_tokens=1000, model_name="gpt-4")
        
        assert memory.max_tokens == 1000
        assert len(memory.conversation_history) == 0
        assert memory.tokenizer is not None
    
    def test_add_exchange(self):
        """Test adding conversation exchanges"""
        from app.core.agents.base.memory import AgentMemory
        from app.core.agents.base.response import AgentRequest, AgentResponse
        
        memory = AgentMemory(max_tokens=1000, model_name="gpt-4")
        
        request = AgentRequest(query="What is an incident?")
        response = AgentResponse(answer="An incident is an unplanned interruption...")
        
        memory.add_exchange(request, response)
        
        assert len(memory.conversation_history) == 1
        assert memory.conversation_history[0].request.query == "What is an incident?"
        assert "unplanned interruption" in memory.conversation_history[0].response.answer
    
    def test_context_string_generation(self):
        """Test context string generation"""
        from app.core.agents.base.memory import AgentMemory
        from app.core.agents.base.response import AgentRequest, AgentResponse
        
        memory = AgentMemory(max_tokens=1000, model_name="gpt-4")
        
        # Add first exchange
        request1 = AgentRequest(query="What is an incident?")
        response1 = AgentResponse(answer="An incident is an unplanned interruption...")
        memory.add_exchange(request1, response1)
        
        # Add second exchange
        request2 = AgentRequest(query="How do I create one?")
        response2 = AgentResponse(answer="To create an incident, you need to...")
        memory.add_exchange(request2, response2)
        
        context = memory.get_context_string()
        
        assert "Human: What is an incident?" in context
        assert "Assistant: An incident is an unplanned interruption" in context
        assert "Human: How do I create one?" in context
        assert "Assistant: To create an incident, you need to" in context
    
    def test_recent_exchanges(self):
        """Test recent exchanges retrieval"""
        from app.core.agents.base.memory import AgentMemory
        from app.core.agents.base.response import AgentRequest, AgentResponse
        
        memory = AgentMemory(max_tokens=1000, model_name="gpt-4")
        
        # Add multiple exchanges
        for i in range(5):
            request = AgentRequest(query=f"Question {i}")
            response = AgentResponse(answer=f"Answer {i}")
            memory.add_exchange(request, response)
        
        recent = memory.get_recent_exchanges(3)
        assert len(recent) == 3
        assert recent[0].request.query == "Question 2"  # Should be the 3rd from end
        assert recent[2].request.query == "Question 4"  # Should be the last one
    
    def test_session_data(self):
        """Test session data storage and retrieval"""
        from app.core.agents.base.memory import AgentMemory
        
        memory = AgentMemory(max_tokens=1000, model_name="gpt-4")
        
        memory.set_session_data("user_role", "admin")
        memory.set_session_data("preferences", {"theme": "dark"})
        
        assert memory.get_session_data("user_role") == "admin"
        assert memory.get_session_data("preferences") == {"theme": "dark"}
        assert memory.get_session_data("nonexistent", "default") == "default"


if __name__ == "__main__":
    # Run tests with pytest if available, otherwise run basic tests
    try:
        pytest.main([__file__, "-v"])
    except ImportError:
        print("pytest not available, running basic tests...")
        
        # Manual test running
        test_classes = [
            TestAgentFrameworkImports,
            TestResponseModels,
            TestConfiguration,
            TestMemoryManagement
        ]
        
        total_tests = 0
        passed_tests = 0
        
        for test_class in test_classes:
            instance = test_class()
            methods = [method for method in dir(instance) if method.startswith('test_')]
            
            print(f"\n=== {test_class.__name__} ===")
            
            for method_name in methods:
                total_tests += 1
                try:
                    method = getattr(instance, method_name)
                    method()
                    print(f"✓ {method_name}")
                    passed_tests += 1
                except Exception as e:
                    print(f"✗ {method_name}: {e}")
        
        print(f"\n=== Results: {passed_tests}/{total_tests} tests passed ===")
        
        if passed_tests == total_tests:
            print("🎉 All tests passed!")
        else:
            print("❌ Some tests failed.")