#!/usr/bin/env python3
"""
Test script for the AugmentAgent to ensure it initializes and functions correctly.
"""
import sys
import os
import asyncio
from unittest.mock import Mock, patch

# Add the backend directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'app'))


class TestAugmentAgentConfiguration:
    """Test AugmentAgent configuration and initialization"""
    
    def test_augment_config_creation(self):
        """Test AugmentConfig creation with defaults"""
        from app.core.agents.augment.config import AugmentConfig
        
        config = AugmentConfig()
        
        assert config.strategy == "direct"
        assert config.max_reasoning_loops == 5
        assert config.system_prompt_template == "default"
        assert config.retrieval_top_k == 10
        assert config.itsm_context_enabled is True
        assert config.model_name == "gpt-4"  # Inherited from BaseAgentConfig
    
    def test_augment_config_custom_values(self):
        """Test AugmentConfig with custom values"""
        from app.core.agents.augment.config import AugmentConfig
        
        config = AugmentConfig(
            strategy="react",
            max_reasoning_loops=3,
            system_prompt_template="technical",
            model_name="gpt-3.5-turbo"
        )
        
        assert config.strategy == "react"
        assert config.max_reasoning_loops == 3
        assert config.system_prompt_template == "technical"
        assert config.model_name == "gpt-3.5-turbo"


class TestPromptManagement:
    """Test prompt template management"""
    
    def test_prompt_template_creation(self):
        """Test PromptTemplate creation and formatting"""
        from app.core.agents.augment.prompts.manager import PromptTemplate
        
        template = PromptTemplate("default")
        
        formatted = template.format(
            query="How do I create an incident?",
            knowledge_base="Sample knowledge base content",
            conversation_history="Previous conversation"
        )
        
        assert "How do I create an incident?" in formatted
        assert "Sample knowledge base content" in formatted
        assert "Previous conversation" in formatted
    
    def test_prompt_manager(self):
        """Test PromptManager functionality"""
        from app.core.agents.augment.prompts.manager import PromptManager
        
        manager = PromptManager()
        
        # Test getting default template
        template = manager.get_template("default")
        assert template.template_name == "default"
        
        # Test getting technical template
        tech_template = manager.get_template("technical")
        assert tech_template.template_name == "technical"
        
        # Test list available templates
        available = manager.list_available_templates()
        assert isinstance(available, list)
        assert len(available) > 0


class TestDirectStrategy:
    """Test DirectStrategy implementation"""
    
    def test_direct_strategy_creation(self):
        """Test DirectStrategy initialization"""
        from app.core.agents.augment.strategies.direct import DirectStrategy
        
        config = {
            "system_prompt_template": "default",
            "max_response_length": 2000
        }
        
        strategy = DirectStrategy(config)
        assert strategy.get_strategy_name() == "direct"
        assert strategy.template_name == "default"
    
    def test_direct_strategy_execution_without_tools(self):
        """Test DirectStrategy execution without retrieval tools"""
        from app.core.agents.augment.strategies.direct import DirectStrategy
        
        async def run_test():
            config = {"system_prompt_template": "default"}
            strategy = DirectStrategy(config)
            
            response = await strategy.execute(
                query="What is an incident?",
                context={"user_role": "admin"},
                tools=[],
                memory_context=""
            )
            
            assert response.answer is not None
            assert len(response.answer) > 0
            assert response.metadata["strategy"] == "direct"
            assert len(response.reasoning_chain) > 0
            return True
        
        # Run the async test
        result = asyncio.run(run_test())
        assert result is True
    
    def test_direct_strategy_with_mock_retrieval(self):
        """Test DirectStrategy with mock retrieval tool"""
        from app.core.agents.augment.strategies.direct import DirectStrategy
        
        async def run_test():
            config = {"system_prompt_template": "default"}
            strategy = DirectStrategy(config)
            
            # Create mock retrieval tool
            mock_tool = Mock()
            mock_tool.name = "knowledge_retriever"
            mock_tool.retrieve = Mock(return_value=[
                {
                    "page_content": "An incident is an unplanned interruption to an IT service...",
                    "metadata": {"source": "user_guide.md"}
                }
            ])
            
            response = await strategy.execute(
                query="What is an incident?",
                context=None,
                tools=[mock_tool],
                memory_context=""
            )
            
            assert response.answer is not None
            assert len(response.sources) > 0
            assert response.sources[0].type == "document"
            assert "incident" in response.sources[0].content.lower()
            return True
        
        result = asyncio.run(run_test())
        assert result is True


class TestAugmentAgent:
    """Test AugmentAgent main functionality"""
    
    @patch('app.core.retrieval.api.retriever.ApiRetriever')
    @patch('app.core.retrieval.document.retriever.DocumentRetriever')
    @patch('app.core.retrieval.fusion.fuser.Fuser')
    def test_augment_agent_initialization(self, mock_fuser, mock_doc_retriever, mock_api_retriever):
        """Test AugmentAgent initialization with mocked retrievers"""
        from app.core.agents.augment.agent import AugmentAgent
        from app.core.agents.augment.config import AugmentConfig
        
        # Mock the retriever classes
        mock_api_retriever.return_value.retrieve.return_value = []
        mock_doc_retriever.return_value.retrieve.return_value = []
        mock_fuser.return_value.fuse.return_value = []
        
        config = AugmentConfig(strategy="direct")
        agent = AugmentAgent(config)
        
        assert agent.augment_config.strategy == "direct"
        assert agent.strategy is not None
        assert agent.strategy.get_strategy_name() == "direct"
        assert len(agent.tools) >= 1  # Should have at least calculator tool
    
    def test_augment_agent_without_retrieval(self):
        """Test AugmentAgent when retrieval system is not available"""
        from app.core.agents.augment.agent import AugmentAgent
        from app.core.agents.augment.config import AugmentConfig
        
        # Test with retrieval disabled
        config = AugmentConfig(strategy="direct", retrieval_enabled=False)
        agent = AugmentAgent(config)
        
        assert agent.augment_config.strategy == "direct"
        assert agent.strategy is not None
        assert len(agent.tools) >= 1  # Should still have calculator tool
    
    def test_augment_agent_info(self):
        """Test agent info retrieval"""
        from app.core.agents.augment.agent import AugmentAgent
        from app.core.agents.augment.config import AugmentConfig
        
        config = AugmentConfig(
            strategy="direct",
            model_name="gpt-3.5-turbo",
            system_prompt_template="technical"
        )
        agent = AugmentAgent(config)
        
        info = agent.get_agent_info()
        
        assert info["agent_type"] == "AugmentAgent"
        assert info["strategy"] == "direct"
        assert info["model"] == "gpt-3.5-turbo"
        assert info["prompt_template"] == "technical"
        assert "tools_count" in info
    
    def test_augment_agent_config_update(self):
        """Test dynamic configuration updates"""
        from app.core.agents.augment.agent import AugmentAgent
        from app.core.agents.augment.config import AugmentConfig
        
        config = AugmentConfig(strategy="direct")
        agent = AugmentAgent(config)
        
        # Update configuration
        agent.update_config(
            strategy="react",
            model_name="gpt-4",
            max_reasoning_loops=3
        )
        
        assert agent.augment_config.strategy == "react"
        assert agent.augment_config.model_name == "gpt-4"
        assert agent.augment_config.max_reasoning_loops == 3
    
    @patch('app.core.retrieval.api.retriever.ApiRetriever')
    @patch('app.core.retrieval.document.retriever.DocumentRetriever')
    @patch('app.core.retrieval.fusion.fuser.Fuser')
    def test_augment_agent_process_request(self, mock_fuser, mock_doc_retriever, mock_api_retriever):
        """Test processing a request through the agent"""
        from app.core.agents.augment.agent import AugmentAgent
        from app.core.agents.augment.config import AugmentConfig
        from app.core.agents.base.response import AgentRequest
        
        async def run_test():
            # Mock the retriever classes
            mock_api_retriever.return_value.retrieve.return_value = []
            mock_doc_retriever.return_value.retrieve.return_value = []
            mock_fuser.return_value.fuse.return_value = []
            
            config = AugmentConfig(strategy="direct", enable_memory=False)
            agent = AugmentAgent(config)
            
            request = AgentRequest(
                query="How do I create an incident ticket?",
                context={"user_role": "admin"}
            )
            
            response = await agent.process(request)
            
            assert response.answer is not None
            assert len(response.answer) > 0
            assert response.metadata["strategy"] == "direct"
            return True
        
        result = asyncio.run(run_test())
        assert result is True


class TestConvenienceFunctions:
    """Test convenience functions"""
    
    @patch('app.core.retrieval.api.retriever.ApiRetriever')
    @patch('app.core.retrieval.document.retriever.DocumentRetriever')
    @patch('app.core.retrieval.fusion.fuser.Fuser')
    def test_create_augment_agent(self, mock_fuser, mock_doc_retriever, mock_api_retriever):
        """Test convenience function for creating agents"""
        from app.core.agents.augment.agent import create_augment_agent
        
        # Mock the retriever classes
        mock_api_retriever.return_value.retrieve.return_value = []
        mock_doc_retriever.return_value.retrieve.return_value = []
        mock_fuser.return_value.fuse.return_value = []
        
        agent = create_augment_agent(
            strategy="direct",
            model_name="gpt-3.5-turbo",
            template="technical",
            max_reasoning_loops=3
        )
        
        assert agent.augment_config.strategy == "direct"
        assert agent.augment_config.model_name == "gpt-3.5-turbo"
        assert agent.augment_config.system_prompt_template == "technical"
        assert agent.augment_config.max_reasoning_loops == 3


if __name__ == "__main__":
    # Run tests with pytest if available, otherwise run basic tests
    try:
        import pytest
        pytest.main([__file__, "-v"])
    except ImportError:
        print("pytest not available, running basic tests...")
        
        # Manual test running
        test_classes = [
            TestAugmentAgentConfiguration,
            TestPromptManagement,
            TestDirectStrategy,
            TestAugmentAgent,
            TestConvenienceFunctions
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