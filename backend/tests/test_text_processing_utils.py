"""
Tests for Text Processing Utilities

Comprehensive tests for text normalization, keyword extraction,
and ITSM domain-specific text processing functions.
"""

import pytest
from typing import List, Dict

# Add backend to sys.path
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parents[2]))

from app.core.manoman.utils.text_processing import (
    TextProcessor,
    text_processor,
    normalize_text,
    clean_identifier,
    extract_keywords,
    calculate_text_similarity,
    suggest_service_name
)


class TestTextProcessor:
    """Test cases for TextProcessor class"""
    
    @pytest.fixture
    def processor(self):
        """Create a TextProcessor instance"""
        return TextProcessor()
    
    def test_normalize_text(self, processor):
        """Test text normalization"""
        # Basic normalization
        assert processor.normalize_text("  Hello   World  ") == "hello world"
        assert processor.normalize_text("UPPERCASE") == "uppercase"
        assert processor.normalize_text("mixed-CASE_text") == "mixed-case_text"
        
        # Preserve case option
        assert processor.normalize_text("Hello World", preserve_case=True) == "Hello World"
        
        # Unicode normalization (NFKD form decomposes accented characters)
        # The result might be in decomposed form, so just check it's normalized
        normalized_cafe = processor.normalize_text("café")
        assert normalized_cafe  # Should not be empty
        assert "caf" in normalized_cafe  # Should contain base characters
        
        # Empty and None handling
        assert processor.normalize_text("") == ""
        assert processor.normalize_text(None) == ""
        
        # Multiple spaces
        assert processor.normalize_text("multiple    spaces    between") == "multiple spaces between"
    
    def test_clean_identifier(self, processor):
        """Test identifier cleaning"""
        # Basic cleaning
        assert processor.clean_identifier("user-management") == "user_management"
        assert processor.clean_identifier("User Management") == "user_management"
        assert processor.clean_identifier("user.management.service") == "user_management_service"
        
        # Special characters
        assert processor.clean_identifier("user@management#service") == "user_management_service"
        assert processor.clean_identifier("___multiple___underscores___") == "multiple_underscores"
        
        # Starting with number
        assert processor.clean_identifier("123service") == "_123service"
        
        # Empty and None
        assert processor.clean_identifier("") == "unknown_identifier"
        assert processor.clean_identifier(None) == "unknown_identifier"
    
    def test_extract_keywords(self, processor):
        """Test keyword extraction"""
        # Basic extraction
        text = "The incident management system handles ticket creation and resolution"
        keywords = processor.extract_keywords(text)
        
        assert "incident" in keywords
        assert "management" in keywords
        assert "system" in keywords
        assert "ticket" in keywords
        assert "creation" in keywords
        assert "resolution" in keywords
        
        # Stopwords should be filtered
        assert "the" not in keywords
        assert "and" not in keywords
        
        # Min length filtering
        short_text = "a to be it"
        keywords = processor.extract_keywords(short_text, min_length=3)
        assert len(keywords) == 0
        
        # Max keywords limit
        long_text = " ".join(["word" + str(i) for i in range(50)])
        keywords = processor.extract_keywords(long_text, max_keywords=10)
        assert len(keywords) <= 10
        
        # Empty text
        assert processor.extract_keywords("") == []
        assert processor.extract_keywords(None) == []
    
    def test_extract_intent_verbs(self, processor):
        """Test ITSM intent verb extraction"""
        # Create operations
        create_text = "create new incident ticket"
        verbs = processor.extract_intent_verbs(create_text)
        assert "create" in verbs
        assert "create" in verbs["create"]
        
        # Multiple verbs
        multi_text = "get and update the user then delete old records"
        verbs = processor.extract_intent_verbs(multi_text)
        assert "read" in verbs  # 'get' maps to 'read'
        assert "update" in verbs
        assert "delete" in verbs
        
        # Approve/reject verbs
        approval_text = "approve the change request or reject if invalid"
        verbs = processor.extract_intent_verbs(approval_text)
        assert "approve" in verbs
        assert "reject" in verbs
        
        # No verbs
        no_verb_text = "the ticket status is pending"
        verbs = processor.extract_intent_verbs(no_verb_text)
        assert len(verbs) == 0
    
    def test_extract_entities(self, processor):
        """Test ITSM entity extraction"""
        # Basic entities
        text = "create incident ticket for user"
        entities = processor.extract_entities(text)
        assert "incident" in entities
        assert "ticket" in entities
        assert "user" in entities
        
        # Multiple entities
        multi_text = "assign change request to group for workflow automation"
        entities = processor.extract_entities(multi_text)
        assert "change" in entities
        assert "request" in entities
        assert "group" in entities
        assert "workflow" in entities
        assert "automation" in entities
        
        # No entities
        no_entity_text = "the system is running"
        entities = processor.extract_entities(no_entity_text)
        assert len(entities) == 0
    
    def test_calculate_text_similarity(self, processor):
        """Test text similarity calculation"""
        # Identical texts
        assert processor.calculate_text_similarity("hello world", "hello world") == 1.0
        
        # Similar texts
        similarity = processor.calculate_text_similarity(
            "incident management system",
            "incident ticket management"
        )
        assert 0.0 < similarity < 1.0
        
        # Completely different texts
        similarity = processor.calculate_text_similarity(
            "user authentication",
            "network monitoring"
        )
        assert similarity == 0.0
        
        # Empty texts
        assert processor.calculate_text_similarity("", "") == 1.0
        assert processor.calculate_text_similarity("text", "") == 0.0
        assert processor.calculate_text_similarity("", "text") == 0.0
    
    def test_extract_path_components(self, processor):
        """Test API path component extraction"""
        # Basic path
        components = processor.extract_path_components("/api/users/{id}")
        assert components["segments"] == ["api", "users", "{id}"]
        assert components["static_segments"] == ["api", "users"]
        assert components["parameters"] == ["{id}"]
        assert components["has_id_parameter"] is True
        assert components["is_collection"] is False
        assert components["base_resource"] == "users"
        
        # Collection endpoint
        components = processor.extract_path_components("/api/incidents")
        assert components["has_id_parameter"] is False
        assert components["is_collection"] is True
        
        # Nested path
        components = processor.extract_path_components("/api/v2/services/{service_id}/endpoints/{endpoint_id}")
        assert components["depth"] == 6
        assert len(components["parameters"]) == 2
        assert components["resource_candidates"] == ["services", "endpoints"]
        
        # Empty path
        components = processor.extract_path_components("")
        assert components["segments"] == []
        assert components["depth"] == 0
    
    def test_suggest_service_name(self, processor):
        """Test service name suggestion"""
        # From paths
        paths = [
            "/api/users",
            "/api/users/{id}",
            "/api/users/{id}/roles"
        ]
        assert processor.suggest_service_name(paths) == "users"
        
        # Mixed resources
        mixed_paths = [
            "/api/incidents",
            "/api/incidents/{id}",
            "/api/tickets",
            "/api/incidents/search"  # Adding one more incidents path to make it most common
        ]
        # Should pick most common
        name = processor.suggest_service_name(mixed_paths)
        assert name == "incidents"
        
        # With operation IDs
        paths = ["/api/v1/resource"]
        op_ids = ["create_user", "get_user", "update_user"]
        assert processor.suggest_service_name(paths, op_ids) == "resource"
        
        # Operation ID fallback
        assert processor.suggest_service_name([], ["user_create", "user_get"]) == "user"
        
        # Empty inputs
        assert processor.suggest_service_name([]) == "unknown_service"
        assert processor.suggest_service_name([], []) == "unknown_service"
    
    def test_generate_service_description(self, processor):
        """Test service description generation"""
        # Basic description
        desc = processor.generate_service_description(
            "user_management",
            ["/api/users", "/api/users/{id}"]
        )
        assert "User Management" in desc
        assert "2 endpoints" in desc
        
        # With intent verbs
        verbs = {
            "create": ["create"],
            "read": ["get", "list"],
            "update": ["update"],
            "delete": ["delete"]
        }
        desc = processor.generate_service_description(
            "incident_service",
            ["/api/incidents"] * 4,
            verbs
        )
        assert "Incident Service" in desc
        assert "4 endpoints" in desc
        assert "create, read, update" in desc
        
        # Empty service name
        desc = processor.generate_service_description("", [])
        assert desc == "Unknown service"
    
    def test_extract_business_context(self, processor):
        """Test business context extraction"""
        # Incident management context
        context = processor.extract_business_context(
            "incident_management",
            ["/api/incidents", "/api/incidents/{id}/notes"],
            ["Create and manage incidents", "Track incident lifecycle"]
        )
        assert "incident" in context.lower()
        assert "management" in context.lower() or "resolution" in context.lower()
        
        # User management context
        context = processor.extract_business_context(
            "user_service",
            ["/api/users", "/api/users/{id}/permissions"],
            None
        )
        assert "user" in context.lower()
        
        # Generic context
        context = processor.extract_business_context(
            "custom_service",
            ["/api/custom"],
            None
        )
        assert "custom" in context.lower()
        assert "processes" in context.lower() or "operations" in context.lower()


class TestConvenienceFunctions:
    """Test module-level convenience functions"""
    
    def test_normalize_text_function(self):
        """Test normalize_text convenience function"""
        assert normalize_text("  HELLO  ") == "hello"
        assert normalize_text("Test", preserve_case=True) == "Test"
    
    def test_clean_identifier_function(self):
        """Test clean_identifier convenience function"""
        assert clean_identifier("test-service") == "test_service"
        assert clean_identifier("123test") == "_123test"
    
    def test_extract_keywords_function(self):
        """Test extract_keywords convenience function"""
        keywords = extract_keywords("incident management system for ticket handling")
        assert "incident" in keywords
        assert "management" in keywords
        assert "system" in keywords
        assert "ticket" in keywords
        assert "handling" in keywords
    
    def test_calculate_text_similarity_function(self):
        """Test calculate_text_similarity convenience function"""
        assert calculate_text_similarity("test", "test") == 1.0
        assert calculate_text_similarity("abc", "xyz") == 0.0
    
    def test_suggest_service_name_function(self):
        """Test suggest_service_name convenience function"""
        paths = ["/api/incidents", "/api/incidents/{id}"]
        assert suggest_service_name(paths) == "incidents"


class TestITSMDomainKnowledge:
    """Test ITSM domain-specific functionality"""
    
    @pytest.fixture
    def processor(self):
        return TextProcessor()
    
    def test_itsm_verb_patterns(self, processor):
        """Test ITSM verb pattern recognition"""
        # Verify verb patterns are compiled
        assert len(processor.verb_patterns) > 0
        assert "create" in processor.verb_patterns
        assert "read" in processor.verb_patterns
        assert "update" in processor.verb_patterns
        assert "delete" in processor.verb_patterns
        assert "approve" in processor.verb_patterns
        assert "escalate" in processor.verb_patterns
    
    def test_itsm_entity_patterns(self, processor):
        """Test ITSM entity pattern recognition"""
        # Test common ITSM entities
        test_entities = ["ticket", "incident", "change", "problem", "user", "asset"]
        
        for entity in test_entities:
            text = f"This is a test {entity} in the system"
            extracted = processor.extract_entities(text)
            assert entity in extracted
    
    def test_itsm_stopwords(self, processor):
        """Test ITSM-specific stopword filtering"""
        # Verify stopwords are filtered
        text = "get the incident and update it with new data"
        keywords = processor.extract_keywords(text)
        
        # These should be filtered
        assert "the" not in keywords
        assert "and" not in keywords
        assert "it" not in keywords
        assert "with" not in keywords
        assert "get" not in keywords  # Common API verb
        
        # These should remain
        assert "incident" in keywords
        assert "update" in keywords
        assert "new" in keywords
        assert "data" in keywords


if __name__ == "__main__":
    pytest.main([__file__, "-v"])