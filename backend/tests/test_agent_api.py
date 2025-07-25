#!/usr/bin/env python3
"""
Test script for the agent API endpoints.
"""
import sys
import os
from fastapi.testclient import TestClient
from unittest.mock import patch, Mock

# Add the backend directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'app'))


class TestAgentAPIEndpoints:
    """Test agent API endpoints"""
    
    def setup_method(self):
        """Setup test client"""
        from app.main import app
        self.client = TestClient(app)
    
    @patch('app.core.retrieval.api.retriever.ApiRetriever')
    @patch('app.core.retrieval.document.retriever.DocumentRetriever')
    @patch('app.core.retrieval.fusion.fuser.Fuser')
    def test_augment_agent_query_endpoint(self, mock_fuser, mock_doc_retriever, mock_api_retriever):
        """Test the main augment agent query endpoint"""
        # Mock the retriever classes
        mock_api_retriever.return_value.retrieve.return_value = []
        mock_doc_retriever.return_value.retrieve.return_value = []
        mock_fuser.return_value.fuse.return_value = []
        
        # Test the endpoint
        response = self.client.post(
            "/api/v1/agents/augment",
            json={
                "query": "How do I create an incident?",
                "context": {"user_role": "admin"}
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "answer" in data
        assert "sources" in data
        assert "reasoning_chain" in data
        assert "confidence" in data
        assert "metadata" in data
        
        # Check that we get a proper response structure
        assert isinstance(data["sources"], list)
        assert isinstance(data["reasoning_chain"], list)
        assert isinstance(data["metadata"], dict)
    
    @patch('app.core.retrieval.api.retriever.ApiRetriever')
    @patch('app.core.retrieval.document.retriever.DocumentRetriever')
    @patch('app.core.retrieval.fusion.fuser.Fuser')
    def test_augment_agent_info_endpoint(self, mock_fuser, mock_doc_retriever, mock_api_retriever):
        """Test the agent info endpoint"""
        # Mock the retriever classes
        mock_api_retriever.return_value.retrieve.return_value = []
        mock_doc_retriever.return_value.retrieve.return_value = []
        mock_fuser.return_value.fuse.return_value = []
        
        response = self.client.get("/api/v1/agents/augment/info")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "agent_type" in data
        assert "strategy" in data
        assert "model" in data
        assert "retrieval_enabled" in data
        assert data["agent_type"] == "AugmentAgent"
    
    @patch('app.core.retrieval.api.retriever.ApiRetriever')
    @patch('app.core.retrieval.document.retriever.DocumentRetriever')
    @patch('app.core.retrieval.fusion.fuser.Fuser')
    def test_augment_agent_config_update_endpoint(self, mock_fuser, mock_doc_retriever, mock_api_retriever):
        """Test the config update endpoint"""
        # Mock the retriever classes
        mock_api_retriever.return_value.retrieve.return_value = []
        mock_doc_retriever.return_value.retrieve.return_value = []
        mock_fuser.return_value.fuse.return_value = []
        
        # Update configuration
        response = self.client.post(
            "/api/v1/agents/augment/config",
            json={
                "strategy": "react",
                "model_name": "gpt-3.5-turbo",
                "max_reasoning_loops": 3
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "message" in data
        assert "updated_config" in data
        assert data["updated_config"]["strategy"] == "react"
        assert data["updated_config"]["model"] == "gpt-3.5-turbo"
    
    @patch('app.core.retrieval.api.retriever.ApiRetriever')
    @patch('app.core.retrieval.document.retriever.DocumentRetriever')
    @patch('app.core.retrieval.fusion.fuser.Fuser')
    def test_augment_agent_memory_endpoints(self, mock_fuser, mock_doc_retriever, mock_api_retriever):
        """Test memory management endpoints"""
        # Mock the retriever classes
        mock_api_retriever.return_value.retrieve.return_value = []
        mock_doc_retriever.return_value.retrieve.return_value = []
        mock_fuser.return_value.fuse.return_value = []
        
        # Test memory clear
        response = self.client.post("/api/v1/agents/augment/memory/clear")
        assert response.status_code == 200
        assert "message" in response.json()
        
        # Test get memory context
        response = self.client.get("/api/v1/agents/augment/memory/context")
        assert response.status_code == 200
        data = response.json()
        assert "context" in data
        assert "context_length" in data
        assert "has_memory" in data
    
    @patch('app.core.retrieval.api.retriever.ApiRetriever')
    @patch('app.core.retrieval.document.retriever.DocumentRetriever')
    @patch('app.core.retrieval.fusion.fuser.Fuser')
    def test_augment_agent_session_endpoints(self, mock_fuser, mock_doc_retriever, mock_api_retriever):
        """Test session data management endpoints"""
        # Mock the retriever classes
        mock_api_retriever.return_value.retrieve.return_value = []
        mock_doc_retriever.return_value.retrieve.return_value = []
        mock_fuser.return_value.fuse.return_value = []
        
        # Set session data
        response = self.client.post(
            "/api/v1/agents/augment/session",
            json={
                "user_role": "admin",
                "department": "IT"
            }
        )
        assert response.status_code == 200
        
        # Get session data
        response = self.client.get("/api/v1/agents/augment/session/user_role")
        assert response.status_code == 200
        data = response.json()
        assert data["key"] == "user_role"
        assert data["value"] == "admin"
        
        # Test non-existent key
        response = self.client.get("/api/v1/agents/augment/session/nonexistent")
        assert response.status_code == 404
    
    def test_augment_agent_templates_endpoint(self):
        """Test template management endpoints"""
        # List available templates
        response = self.client.get("/api/v1/agents/augment/templates")
        assert response.status_code == 200
        data = response.json()
        assert "available_templates" in data
        assert "count" in data
        assert isinstance(data["available_templates"], list)
        
        # Test template reload
        response = self.client.post("/api/v1/agents/augment/templates/default/reload")
        assert response.status_code == 200
        assert "message" in response.json()
    
    @patch('app.core.retrieval.api.retriever.ApiRetriever')
    @patch('app.core.retrieval.document.retriever.DocumentRetriever')
    @patch('app.core.retrieval.fusion.fuser.Fuser')
    def test_create_new_agent_endpoint(self, mock_fuser, mock_doc_retriever, mock_api_retriever):
        """Test creating a new agent instance"""
        # Mock the retriever classes
        mock_api_retriever.return_value.retrieve.return_value = []
        mock_doc_retriever.return_value.retrieve.return_value = []
        mock_fuser.return_value.fuse.return_value = []
        
        response = self.client.post("/api/v1/agents/augment/create")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "agent_info" in data
    
    @patch('app.core.retrieval.api.retriever.ApiRetriever')
    @patch('app.core.retrieval.document.retriever.DocumentRetriever')
    @patch('app.core.retrieval.fusion.fuser.Fuser')
    def test_augment_agent_with_react_strategy(self, mock_fuser, mock_doc_retriever, mock_api_retriever):
        """Test agent with ReAct strategy"""
        # Mock the retriever classes  
        mock_api_retriever.return_value.retrieve.return_value = [
            {
                "page_content": "An incident is an unplanned interruption...",
                "metadata": {"source": "user_guide.md"}
            }
        ]
        mock_doc_retriever.return_value.retrieve.return_value = []
        mock_fuser.return_value.fuse.return_value = [
            {
                "page_content": "An incident is an unplanned interruption...",
                "metadata": {"source": "user_guide.md"}
            }
        ]
        
        # Set strategy to ReAct
        config_response = self.client.post(
            "/api/v1/agents/augment/config",
            json={"strategy": "react", "max_reasoning_loops": 2}
        )
        assert config_response.status_code == 200
        
        # Test query with ReAct strategy
        response = self.client.post(
            "/api/v1/agents/augment",
            json={
                "query": "What is an incident in ITSM?",
                "context": {"user_role": "admin"}
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["metadata"]["strategy"] == "react"
        assert "iterations" in data["metadata"]
        assert len(data["reasoning_chain"]) > 3  # ReAct should have more reasoning steps
    
    def test_invalid_requests(self):
        """Test handling of invalid requests"""
        # Test missing query
        response = self.client.post("/api/v1/agents/augment", json={})
        assert response.status_code == 422  # Validation error
        
        # Test invalid config update
        response = self.client.post(
            "/api/v1/agents/augment/config",
            json={"invalid_field": "invalid_value"}
        )
        # Should still return 200 but log warning about unknown field
        assert response.status_code == 200


class TestAgentAPIIntegration:
    """Integration tests for agent API"""
    
    def setup_method(self):
        """Setup test client"""
        from app.main import app
        self.client = TestClient(app)
    
    @patch('app.core.retrieval.api.retriever.ApiRetriever')
    @patch('app.core.retrieval.document.retriever.DocumentRetriever')
    @patch('app.core.retrieval.fusion.fuser.Fuser')
    def test_full_conversation_flow(self, mock_fuser, mock_doc_retriever, mock_api_retriever):
        """Test a full conversation flow with memory"""
        # Mock the retriever classes
        mock_api_retriever.return_value.retrieve.return_value = []
        mock_doc_retriever.return_value.retrieve.return_value = []
        mock_fuser.return_value.fuse.return_value = []
        
        # First query
        response1 = self.client.post(
            "/api/v1/agents/augment",
            json={"query": "What is an incident?"}
        )
        assert response1.status_code == 200
        
        # Second query (should use conversation history)
        response2 = self.client.post(
            "/api/v1/agents/augment",
            json={"query": "How do I create one?"}
        )
        assert response2.status_code == 200
        
        # Check memory context
        memory_response = self.client.get("/api/v1/agents/augment/memory/context")
        assert memory_response.status_code == 200
        memory_data = memory_response.json()
        assert len(memory_data["context"]) > 0
        
        # Clear memory
        clear_response = self.client.post("/api/v1/agents/augment/memory/clear")
        assert clear_response.status_code == 200
        
        # Check memory is cleared
        memory_response2 = self.client.get("/api/v1/agents/augment/memory/context")
        assert memory_response2.status_code == 200
        memory_data2 = memory_response2.json()
        assert len(memory_data2["context"]) == 0


if __name__ == "__main__":
    # Run tests with pytest if available, otherwise run basic tests
    try:
        import pytest
        pytest.main([__file__, "-v"])
    except ImportError:
        print("pytest not available, running basic tests...")
        
        # Manual test running
        test_classes = [TestAgentAPIEndpoints, TestAgentAPIIntegration]
        
        total_tests = 0
        passed_tests = 0
        
        for test_class in test_classes:
            instance = test_class()
            methods = [method for method in dir(instance) if method.startswith('test_')]
            
            print(f"\n=== {test_class.__name__} ===")
            
            for method_name in methods:
                total_tests += 1
                try:
                    # Setup if available
                    if hasattr(instance, 'setup_method'):
                        instance.setup_method()
                    
                    method = getattr(instance, method_name)
                    method()
                    print(f"✓ {method_name}")
                    passed_tests += 1
                except Exception as e:
                    print(f"✗ {method_name}: {e}")
        
        print(f"\n=== Results: {passed_tests}/{total_tests} tests passed ===")
        
        if passed_tests == total_tests:
            print("🎉 All API tests passed!")
        else:
            print("❌ Some tests failed.")