#!/usr/bin/env python3
"""
Test script for LLM integration with OpenRouter.
This script tests both fallback behavior (without API key) and actual LLM calls (with API key).
"""
import sys
import os
import asyncio
from unittest.mock import patch

# Add the backend directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'app'))


class TestLLMIntegration:
    """Test LLM integration with OpenRouter"""
    
    def test_llm_service_initialization(self):
        """Test LLM service initialization"""
        from app.core.agents.base.llm_service import LLMService
        from app.core.agents.base.config import BaseAgentConfig
        
        # Test with default config (placeholder API key)
        config = BaseAgentConfig()
        llm_service = LLMService(config)
        
        # Should initialize but not be available due to placeholder key
        assert llm_service is not None
        print("✓ LLM service initialization successful")
    
    def test_llm_service_availability(self):
        """Test LLM service availability check"""
        from app.core.agents.base.llm_service import LLMService
        from app.core.agents.base.config import BaseAgentConfig
        
        # Test with placeholder key
        config = BaseAgentConfig()
        llm_service = LLMService(config)
        
        # Should not be available with placeholder key
        available = llm_service.is_available()
        print(f"✓ LLM service availability check: {available}")
        
        # Test model info
        info = llm_service.get_model_info()
        assert "model_name" in info
        assert info["model_name"] == "google/gemma-3n-e4b-it"
        print(f"✓ Model info retrieved: {info['model_name']}")
    
    def test_llm_service_with_valid_key(self):
        """Test LLM service behavior with valid API key"""
        from app.core.agents.base.llm_service import LLMService, LLMServiceError
        from app.core.agents.base.config import BaseAgentConfig
        
        async def run_test():
            config = BaseAgentConfig()
            llm_service = LLMService(config)
            
            try:
                # This should succeed with valid API key
                response = await llm_service.generate_response("Test prompt: What is ITSM?")
                print(f"✓ Got successful response: {response[:100]}...")
                return len(response) > 0
            except Exception as e:
                print(f"✗ Unexpected error: {str(e)[:50]}...")
                return False
        
        result = asyncio.run(run_test())
        assert result, "Expected LLM service to work with valid API key"
    
    @patch('app.core.retrieval.api.retriever.ApiRetriever')
    @patch('app.core.retrieval.document.retriever.DocumentRetriever')
    @patch('app.core.retrieval.fusion.fuser.Fuser')
    def test_augment_agent_fallback_behavior(self, mock_fuser, mock_doc_retriever, mock_api_retriever):
        """Test AugmentAgent fallback behavior without valid LLM"""
        # Mock the retriever classes
        mock_api_retriever.return_value.retrieve.return_value = []
        mock_doc_retriever.return_value.retrieve.return_value = []
        mock_fuser.return_value.fuse.return_value = []
        
        async def run_test():
            from app.core.agents.augment.agent import AugmentAgent
            from app.core.agents.augment.config import AugmentConfig
            from app.core.agents.base.response import AgentRequest
            
            # Create agent with default config (invalid API key)
            config = AugmentConfig(strategy="direct")
            agent = AugmentAgent(config)
            
            # Test request
            request = AgentRequest(
                query="How do I create an incident in Infraon?",
                context={"user_role": "admin"}
            )
            
            # Should work with fallback response
            response = await agent.process(request)
            
            assert response.answer is not None
            assert len(response.answer) > 0
            assert response.metadata["strategy"] == "direct"
            
            print(f"✓ Agent fallback response length: {len(response.answer)} chars")
            print(f"✓ Reasoning chain steps: {len(response.reasoning_chain)}")
            
            return True
        
        result = asyncio.run(run_test())
        assert result, "AugmentAgent should work with fallback behavior"
    
    @patch('app.core.retrieval.api.retriever.ApiRetriever')
    @patch('app.core.retrieval.document.retriever.DocumentRetriever')
    @patch('app.core.retrieval.fusion.fuser.Fuser')
    def test_react_strategy_fallback(self, mock_fuser, mock_doc_retriever, mock_api_retriever):
        """Test ReAct strategy fallback behavior"""
        # Mock the retriever classes
        mock_api_retriever.return_value.retrieve.return_value = [
            {
                "page_content": "An incident is an unplanned interruption to an IT service...",
                "metadata": {"source": "user_guide.md"}
            }
        ]
        mock_doc_retriever.return_value.retrieve.return_value = []
        mock_fuser.return_value.fuse.return_value = [
            {
                "page_content": "An incident is an unplanned interruption to an IT service...",
                "metadata": {"source": "user_guide.md"}
            }
        ]
        
        async def run_test():
            from app.core.agents.augment.agent import AugmentAgent
            from app.core.agents.augment.config import AugmentConfig
            from app.core.agents.base.response import AgentRequest
            
            # Create agent with ReAct strategy
            config = AugmentConfig(strategy="react", max_reasoning_loops=2)
            agent = AugmentAgent(config)
            
            # Test request
            request = AgentRequest(
                query="What is an incident in ITSM?",
                context={"user_role": "admin"}
            )
            
            # Should work with fallback ReAct behavior
            response = await agent.process(request)
            
            assert response.answer is not None
            assert len(response.answer) > 0
            assert response.metadata["strategy"] == "react"
            assert "iterations" in response.metadata
            
            print(f"✓ ReAct fallback response length: {len(response.answer)} chars")
            print(f"✓ ReAct reasoning iterations: {response.metadata['iterations']}")
            print(f"✓ ReAct reasoning chain steps: {len(response.reasoning_chain)}")
            
            return True
        
        result = asyncio.run(run_test())
        assert result, "ReAct strategy should work with fallback behavior"
    
    def test_config_loading_from_env(self):
        """Test configuration loading from environment"""
        from app.core.agents.base.config import BaseAgentConfig
        
        # Should load from .env file
        config = BaseAgentConfig()
        
        assert config.model_provider == "openrouter"
        assert config.model_name == "google/gemma-3n-e4b-it"
        assert config.openrouter_base_url == "https://openrouter.ai/api/v1"
        assert config.temperature == 0.7
        assert config.max_tokens == 2048
        
        print("✓ Configuration loaded correctly from .env file")
    
    def test_prompt_template_integration(self):
        """Test prompt template system integration"""
        from app.core.agents.augment.prompts.manager import PromptManager
        
        manager = PromptManager()
        
        # Test default template
        template = manager.get_template("default")
        formatted = template.format(
            query="Test query",
            knowledge_base="Test knowledge",
            conversation_history="Test history"
        )
        
        assert "Test query" in formatted
        assert "Test knowledge" in formatted
        print("✓ Prompt template integration working")
    
    def test_llm_service_with_valid_key_simulation(self):
        """Test LLM service behavior with simulated valid key"""
        from app.core.agents.base.llm_service import LLMService
        from app.core.agents.base.config import BaseAgentConfig
        
        # Create config with simulated valid key
        config = BaseAgentConfig()
        config.openrouter_api_key = "sk-or-v1-simulated-key-for-testing"
        
        llm_service = LLMService(config)
        
        # Should be marked as available
        assert llm_service.is_available()
        print("✓ LLM service shows available with simulated valid key")


class TestEndToEndIntegration:
    """End-to-end integration tests"""
    
    def test_full_agent_pipeline_without_llm(self):
        """Test complete agent pipeline without actual LLM calls"""
        from fastapi.testclient import TestClient
        from unittest.mock import patch
        
        @patch('app.core.retrieval.api.retriever.ApiRetriever')
        @patch('app.core.retrieval.document.retriever.DocumentRetriever')
        @patch('app.core.retrieval.fusion.fuser.Fuser')
        def run_test(mock_fuser, mock_doc_retriever, mock_api_retriever):
            # Mock the retriever classes
            mock_api_retriever.return_value.retrieve.return_value = [
                {
                    "page_content": "To create an incident in Infraon, follow these steps...",
                    "metadata": {"source": "user_guide.md"}
                }
            ]
            mock_doc_retriever.return_value.retrieve.return_value = []
            mock_fuser.return_value.fuse.return_value = [
                {
                    "page_content": "To create an incident in Infraon, follow these steps...",
                    "metadata": {"source": "user_guide.md"}
                }
            ]
            
            from app.main import app
            client = TestClient(app)
            
            # Test API endpoint
            response = client.post(
                "/api/v1/agents/augment",
                json={
                    "query": "How do I create an incident ticket?",
                    "context": {"user_role": "admin"}
                }
            )
            
            assert response.status_code == 200
            data = response.json()
            
            assert "answer" in data
            assert "sources" in data
            assert "reasoning_chain" in data
            assert len(data["answer"]) > 0
            
            print("✓ Full API pipeline test successful")
            print(f"✓ Response length: {len(data['answer'])} chars")
            print(f"✓ Sources found: {len(data['sources'])}")
            
            return True
        
        result = run_test()
        assert result, "Full pipeline test should succeed"


if __name__ == "__main__":
    print("=== LLM Integration Testing ===\n")
    
    # Test classes
    test_classes = [TestLLMIntegration, TestEndToEndIntegration]
    
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
        print("🎉 All LLM integration tests passed!")
        print("\n📋 Next Steps:")
        print("1. Add your OpenRouter API key to backend/.env")
        print("2. Start the server: cd backend && pyenv activate augment-env && uvicorn app.main:app --reload")
        print("3. Test with real LLM: curl -X POST 'http://localhost:8000/api/v1/agents/augment' -H 'Content-Type: application/json' -d '{\"query\": \"How do I create an incident?\"}'")
    else:
        print("❌ Some tests failed. Please check the implementation.")