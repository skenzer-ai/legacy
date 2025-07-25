#!/usr/bin/env python3
"""
Test script for the ReAct strategy implementation.
"""
import sys
import os
import asyncio
from unittest.mock import Mock

# Add the backend directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'app'))


class TestReActStrategy:
    """Test ReAct strategy implementation"""
    
    def test_react_strategy_creation(self):
        """Test ReActStrategy initialization"""
        from app.core.agents.augment.strategies.react import ReActStrategy
        
        config = {
            "system_prompt_template": "default",
            "max_reasoning_loops": 3,
            "confidence_threshold": 0.7
        }
        
        strategy = ReActStrategy(config)
        assert strategy.get_strategy_name() == "react"
        assert strategy.max_loops == 3
        assert strategy.confidence_threshold == 0.7
    
    def test_react_strategy_tool_descriptions(self):
        """Test tool description generation"""
        from app.core.agents.augment.strategies.react import ReActStrategy
        
        config = {"max_reasoning_loops": 3}
        strategy = ReActStrategy(config)
        
        # Create mock tools
        mock_tools = [
            type('Tool', (), {
                'name': 'knowledge_retriever',
                'description': 'Search Infraon documentation'
            })(),
            type('Tool', (), {
                'name': 'calculator',
                'description': 'Perform mathematical calculations'
            })()
        ]
        
        descriptions = strategy._get_tool_descriptions(mock_tools)
        assert "knowledge_retriever" in descriptions
        assert "calculator" in descriptions
        assert "Search Infraon documentation" in descriptions
    
    def test_react_strategy_action_analysis(self):
        """Test action need analysis"""
        from app.core.agents.augment.strategies.react import ReActStrategy
        
        config = {"max_reasoning_loops": 3}
        strategy = ReActStrategy(config)
        
        # Create mock tools including calculator
        mock_tools = [
            type('Tool', (), {'name': 'calculator'})(),
            type('Tool', (), {'name': 'knowledge_retriever'})()
        ]
        
        # Test calculation detection
        calc_thought = "I need to calculate the average response time"
        action = strategy._analyze_action_needed(calc_thought, [], mock_tools)
        assert action == "calculate"
        
        # Test conclusion detection
        conclude_thought = "I have enough information to provide a comprehensive answer"
        action = strategy._analyze_action_needed(conclude_thought, ["some observation"], mock_tools)
        assert action == "conclude"
        
        # Test default search
        search_thought = "I need more information about incidents"
        action = strategy._analyze_action_needed(search_thought, [], mock_tools)
        assert action == "search"
    
    def test_react_strategy_should_conclude(self):
        """Test conclusion decision logic"""
        from app.core.agents.augment.strategies.react import ReActStrategy
        
        config = {"max_reasoning_loops": 3}
        strategy = ReActStrategy(config)
        
        # Should not conclude with no observations
        assert not strategy._should_conclude([], "test query")
        
        # Should conclude with relevant information
        good_obs = ["Found relevant information:\n1. API endpoint details"]
        assert strategy._should_conclude(good_obs, "test query")
        
        # Should conclude after multiple attempts
        many_obs = ["obs1", "obs2", "obs3", "obs4"]
        assert strategy._should_conclude(many_obs, "test query")
    
    def test_react_strategy_search_results_processing(self):
        """Test search results processing"""
        from app.core.agents.augment.strategies.react import ReActStrategy
        
        config = {"max_reasoning_loops": 3}
        strategy = ReActStrategy(config)
        
        # Test with document results
        doc_results = [
            {
                "page_content": "This is information about creating incidents in Infraon platform",
                "metadata": {"source": "user_guide.md"}
            }
        ]
        
        observation = strategy._process_search_results(doc_results)
        assert "Found relevant information" in observation
        assert "creating incidents" in observation
        
        # Test with API results
        api_results = [
            {
                "path": "/api/incidents",
                "method": "POST",
                "description": "Create a new incident",
                "operationId": "createIncident"
            }
        ]
        
        observation = strategy._process_search_results(api_results)
        assert "Found relevant information" in observation
        assert "POST /api/incidents" in observation
        
        # Test with no results
        observation = strategy._process_search_results([])
        assert "No relevant information found" in observation
    
    def test_react_strategy_execution_simple(self):
        """Test ReAct strategy execution with simple scenario"""
        from app.core.agents.augment.strategies.react import ReActStrategy
        
        async def run_test():
            config = {
                "system_prompt_template": "default",
                "max_reasoning_loops": 2
            }
            strategy = ReActStrategy(config)
            
            # Create mock retrieval tool
            mock_tool = Mock()
            mock_tool.name = "knowledge_retriever"
            mock_tool.retrieve = Mock(return_value=[
                {
                    "page_content": "An incident is an unplanned interruption to an IT service",
                    "metadata": {"source": "user_guide.md"}
                }
            ])
            
            response = await strategy.execute(
                query="What is an incident?",
                context={"user_role": "admin"},
                tools=[mock_tool],
                memory_context=""
            )
            
            assert response.answer is not None
            assert len(response.answer) > 0
            assert response.metadata["strategy"] == "react"
            assert len(response.reasoning_chain) > 3  # Should have multiple reasoning steps
            assert len(response.sources) > 0
            
            # Check for different types of reasoning steps
            step_types = [step.step_type for step in response.reasoning_chain]
            assert "thought" in step_types
            assert "action" in step_types
            assert "observation" in step_types
            
            return True
        
        result = asyncio.run(run_test())
        assert result is True
    
    def test_react_strategy_with_calculation(self):
        """Test ReAct strategy with calculation tool"""
        from app.core.agents.augment.strategies.react import ReActStrategy
        
        async def run_test():
            config = {
                "system_prompt_template": "default",
                "max_reasoning_loops": 3
            }
            strategy = ReActStrategy(config)
            
            # Create mock tools
            mock_calc_tool = Mock()
            mock_calc_tool.name = "calculator"
            mock_calc_tool.func = Mock(return_value="42")
            
            mock_retrieval_tool = Mock()
            mock_retrieval_tool.name = "knowledge_retriever"
            mock_retrieval_tool.retrieve = Mock(return_value=[
                {
                    "page_content": "Average response time calculations",
                    "metadata": {"source": "metrics.md"}
                }
            ])
            
            response = await strategy.execute(
                query="What is the average response time calculation?",
                context=None,
                tools=[mock_calc_tool, mock_retrieval_tool],
                memory_context=""
            )
            
            assert response.answer is not None
            assert response.metadata["strategy"] == "react"
            assert response.metadata["iterations"] > 0
            
            return True
        
        result = asyncio.run(run_test())
        assert result is True
    
    def test_react_strategy_max_loops(self):
        """Test ReAct strategy respects max loops"""
        from app.core.agents.augment.strategies.react import ReActStrategy
        
        async def run_test():
            config = {
                "system_prompt_template": "default",
                "max_reasoning_loops": 1  # Very low to test limit
            }
            strategy = ReActStrategy(config)
            
            # Create mock tool that always returns empty results
            mock_tool = Mock()
            mock_tool.name = "knowledge_retriever"
            mock_tool.retrieve = Mock(return_value=[])
            
            response = await strategy.execute(
                query="Complex query that would need many iterations",
                context=None,
                tools=[mock_tool],
                memory_context=""
            )
            
            assert response.answer is not None
            assert response.metadata["strategy"] == "react"
            # Should respect the max loops limit
            assert response.metadata["iterations"] <= 1
            
            return True
        
        result = asyncio.run(run_test())
        assert result is True


class TestAugmentAgentWithReAct:
    """Test AugmentAgent using ReAct strategy"""
    
    def test_augment_agent_react_initialization(self):
        """Test AugmentAgent with ReAct strategy"""
        from app.core.agents.augment.agent import create_augment_agent
        
        agent = create_augment_agent(
            strategy="react",
            model_name="gpt-4",
            template="default",
            max_reasoning_loops=3
        )
        
        assert agent.augment_config.strategy == "react"
        assert agent.strategy.get_strategy_name() == "react"
        assert agent.augment_config.max_reasoning_loops == 3
    
    def test_augment_agent_strategy_switching(self):
        """Test dynamic strategy switching"""
        from app.core.agents.augment.agent import create_augment_agent
        
        agent = create_augment_agent(strategy="direct")
        assert agent.strategy.get_strategy_name() == "direct"
        
        # Switch to ReAct
        agent.update_config(strategy="react")
        assert agent.strategy.get_strategy_name() == "react"
        
        # Switch back to Direct
        agent.update_config(strategy="direct")
        assert agent.strategy.get_strategy_name() == "direct"


if __name__ == "__main__":
    # Run tests with pytest if available, otherwise run basic tests
    try:
        import pytest
        pytest.main([__file__, "-v"])
    except ImportError:
        print("pytest not available, running basic tests...")
        
        # Manual test running
        test_classes = [TestReActStrategy, TestAugmentAgentWithReAct]
        
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
            print("🎉 All ReAct strategy tests passed!")
        else:
            print("❌ Some tests failed.")