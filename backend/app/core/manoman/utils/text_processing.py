"""
Text Processing Utilities for Man-O-Man

Provides NLP utilities for classification, keyword extraction, and text normalization
used throughout the Man-O-Man service registry management system.
"""

import re
import string
import unicodedata
from typing import List, Dict, Set, Optional, Tuple, Any
from collections import Counter
import logging

logger = logging.getLogger(__name__)


class TextProcessor:
    """
    Comprehensive text processing utilities for Man-O-Man system
    
    Handles text normalization, keyword extraction, semantic similarity,
    and ITSM domain-specific text processing operations.
    """
    
    # ITSM domain-specific stopwords
    ITSM_STOPWORDS = {
        'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with',
        'by', 'from', 'up', 'about', 'into', 'through', 'during', 'before',
        'after', 'above', 'below', 'between', 'among', 'is', 'are', 'was',
        'were', 'be', 'been', 'being', 'have', 'has', 'had', 'do', 'does',
        'did', 'will', 'would', 'should', 'could', 'can', 'may', 'might',
        'must', 'shall', 'a', 'an', 'this', 'that', 'these', 'those', 'it',
        'api', 'endpoint', 'method', 'get', 'post', 'put', 'delete', 'patch'
    }
    
    # Common ITSM verb patterns
    ITSM_VERBS = {
        'create': ['create', 'add', 'new', 'register', 'establish', 'generate', 'make'],
        'read': ['get', 'read', 'show', 'view', 'display', 'fetch', 'retrieve', 'find', 'search', 'list'],
        'update': ['update', 'modify', 'edit', 'change', 'revise', 'alter', 'patch'],
        'delete': ['delete', 'remove', 'destroy', 'cancel', 'terminate', 'drop'],
        'approve': ['approve', 'accept', 'authorize', 'confirm', 'validate'],
        'reject': ['reject', 'deny', 'decline', 'refuse'],
        'assign': ['assign', 'allocate', 'delegate', 'transfer'],
        'escalate': ['escalate', 'promote', 'raise', 'forward'],
        'close': ['close', 'complete', 'finish', 'resolve', 'end'],
        'reopen': ['reopen', 'restart', 'resume', 'activate']
    }
    
    # ITSM domain entities
    ITSM_ENTITIES = {
        'ticket', 'incident', 'request', 'change', 'problem', 'release',
        'user', 'group', 'role', 'permission', 'asset', 'configuration',
        'service', 'catalog', 'category', 'priority', 'status', 'workflow',
        'notification', 'alert', 'report', 'dashboard', 'analytics',
        'business_rule', 'automation', 'policy', 'compliance', 'audit'
    }
    
    def __init__(self):
        """Initialize text processor with domain knowledge"""
        self.verb_patterns = self._compile_verb_patterns()
        self.entity_patterns = self._compile_entity_patterns()
    
    def _compile_verb_patterns(self) -> Dict[str, re.Pattern]:
        """Compile regex patterns for ITSM verbs"""
        patterns = {}
        for action, verbs in self.ITSM_VERBS.items():
            pattern = r'\b(?:' + '|'.join(re.escape(verb) for verb in verbs) + r')\b'
            patterns[action] = re.compile(pattern, re.IGNORECASE)
        return patterns
    
    def _compile_entity_patterns(self) -> re.Pattern:
        """Compile regex pattern for ITSM entities"""
        pattern = r'\b(?:' + '|'.join(re.escape(entity) for entity in self.ITSM_ENTITIES) + r')\b'
        return re.compile(pattern, re.IGNORECASE)
    
    def normalize_text(self, text: str, preserve_case: bool = False) -> str:
        """
        Normalize text for consistent processing
        
        Args:
            text: Input text to normalize
            preserve_case: Whether to preserve original casing
            
        Returns:
            Normalized text string
        """
        if not text:
            return ""
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text.strip())
        
        # Normalize unicode characters
        text = unicodedata.normalize('NFKD', text)
        
        # Remove control characters
        text = ''.join(char for char in text if unicodedata.category(char)[0] != 'C')
        
        if not preserve_case:
            text = text.lower()
        
        return text
    
    def clean_identifier(self, identifier: str) -> str:
        """
        Clean and normalize identifiers (service names, operation IDs, etc.)
        
        Args:
            identifier: Raw identifier string
            
        Returns:
            Clean identifier suitable for programmatic use
        """
        if not identifier:
            return "unknown_identifier"
        
        # Convert to lowercase
        clean_id = identifier.lower()
        
        # Replace special characters with underscores
        clean_id = re.sub(r'[^a-zA-Z0-9_]', '_', clean_id)
        
        # Remove multiple underscores
        clean_id = re.sub(r'_+', '_', clean_id)
        
        # Remove leading/trailing underscores
        clean_id = clean_id.strip('_')
        
        # Ensure it starts with a letter or underscore
        if clean_id and clean_id[0].isdigit():
            clean_id = '_' + clean_id
        
        return clean_id or 'unknown_identifier'
    
    def extract_keywords(self, text: str, min_length: int = 2, max_keywords: int = 20) -> List[str]:
        """
        Extract meaningful keywords from text
        
        Args:
            text: Input text
            min_length: Minimum keyword length
            max_keywords: Maximum number of keywords to return
            
        Returns:
            List of extracted keywords
        """
        if not text:
            return []
        
        # Normalize text
        normalized = self.normalize_text(text)
        
        # Split into words
        words = re.findall(r'\b[a-zA-Z]{' + str(min_length) + r',}\b', normalized)
        
        # Filter out stopwords
        keywords = [word for word in words if word not in self.ITSM_STOPWORDS]
        
        # Count frequency and extract most common
        word_counts = Counter(keywords)
        top_keywords = [word for word, count in word_counts.most_common(max_keywords)]
        
        return top_keywords
    
    def extract_intent_verbs(self, text: str) -> Dict[str, List[str]]:
        """
        Extract ITSM intent verbs from text
        
        Args:
            text: Input text to analyze
            
        Returns:
            Dictionary mapping intent categories to found verbs
        """
        intent_verbs = {}
        
        for action, pattern in self.verb_patterns.items():
            matches = pattern.findall(text)
            if matches:
                intent_verbs[action] = list(set(match.lower() for match in matches))
        
        return intent_verbs
    
    def extract_entities(self, text: str) -> List[str]:
        """
        Extract ITSM domain entities from text
        
        Args:
            text: Input text to analyze
            
        Returns:
            List of found ITSM entities
        """
        matches = self.entity_patterns.findall(text)
        return list(set(match.lower() for match in matches))
    
    def calculate_text_similarity(self, text1: str, text2: str) -> float:
        """
        Calculate similarity between two text strings using Jaccard similarity
        
        Args:
            text1: First text string
            text2: Second text string
            
        Returns:
            Similarity score between 0.0 and 1.0
        """
        # Handle empty strings
        if not text1 and not text2:
            return 1.0  # Both empty strings are considered identical
        
        if not text1 or not text2:
            return 0.0
        
        # Extract keywords from both texts
        keywords1 = set(self.extract_keywords(text1))
        keywords2 = set(self.extract_keywords(text2))
        
        if not keywords1 and not keywords2:
            return 1.0
        
        if not keywords1 or not keywords2:
            return 0.0
        
        # Calculate Jaccard similarity
        intersection = len(keywords1.intersection(keywords2))
        union = len(keywords1.union(keywords2))
        
        return intersection / union if union > 0 else 0.0
    
    def extract_path_components(self, api_path: str) -> Dict[str, Any]:
        """
        Extract meaningful components from API path
        
        Args:
            api_path: API endpoint path
            
        Returns:
            Dictionary with path analysis results
        """
        if not api_path:
            return {
                'segments': [],
                'static_segments': [],
                'parameters': [],
                'resource_candidates': [],
                'depth': 0,
                'has_id_parameter': False,
                'is_collection': True,
                'base_resource': None
            }
        
        # Clean the path
        clean_path = api_path.strip('/')
        
        # Split into segments
        segments = clean_path.split('/') if clean_path else []
        
        # Identify parameters (segments with {})
        parameters = [seg for seg in segments if '{' in seg and '}' in seg]
        
        # Identify static segments (segments without {})
        static_segments = [seg for seg in segments if '{' not in seg and '}' not in seg]
        
        # Extract potential service/resource names
        resource_candidates = []
        for segment in static_segments:
            if segment and segment not in ['api', 'v1', 'v2', 'v3']:
                resource_candidates.append(segment)
        
        # Calculate path depth
        depth = len(segments)
        
        # Identify if it's a collection vs item endpoint
        has_id_parameter = any('{id}' in param or 'id}' in param for param in parameters)
        
        return {
            'segments': segments,
            'static_segments': static_segments,
            'parameters': parameters,
            'resource_candidates': resource_candidates,
            'depth': depth,
            'has_id_parameter': has_id_parameter,
            'is_collection': not has_id_parameter,
            'base_resource': resource_candidates[0] if resource_candidates else None
        }
    
    def suggest_service_name(self, endpoint_paths: List[str], operation_ids: List[str] = None) -> str:
        """
        Suggest a service name based on endpoint paths and operation IDs
        
        Args:
            endpoint_paths: List of API endpoint paths
            operation_ids: Optional list of operation IDs
            
        Returns:
            Suggested service name
        """
        # If we have paths, try to extract from them first
        if endpoint_paths:
            # Extract resource candidates from all paths
            all_resources = []
            for path in endpoint_paths:
                components = self.extract_path_components(path)
                all_resources.extend(components.get('resource_candidates', []))
            
            # Find most common resource
            if all_resources:
                resource_counts = Counter(all_resources)
                most_common_resource = resource_counts.most_common(1)[0][0]
                
                # Clean and return
                return self.clean_identifier(most_common_resource)
        
        # Fallback: try to extract from operation IDs
        if operation_ids:
            # Look for common prefixes/suffixes in operation IDs
            common_parts = []
            for op_id in operation_ids:
                if op_id:
                    parts = re.split(r'[_\-.]', op_id.lower())
                    common_parts.extend(parts)
            
            if common_parts:
                part_counts = Counter(common_parts)
                # Filter out common CRUD words
                filtered_parts = [part for part, count in part_counts.most_common() 
                                if part not in {'get', 'post', 'put', 'delete', 'create', 'update', 'list'}]
                
                if filtered_parts:
                    return self.clean_identifier(filtered_parts[0])
        
        return "unknown_service"
    
    def generate_service_description(self, 
                                   service_name: str, 
                                   endpoints: List[str], 
                                   intent_verbs: Dict[str, List[str]] = None) -> str:
        """
        Generate a descriptive service description
        
        Args:
            service_name: Name of the service
            endpoints: List of endpoint paths
            intent_verbs: Optional extracted intent verbs
            
        Returns:
            Generated service description
        """
        if not service_name:
            return "Unknown service"
        
        # Clean service name for description
        readable_name = service_name.replace('_', ' ').title()
        
        # Determine primary actions
        primary_actions = []
        if intent_verbs:
            for action, verbs in intent_verbs.items():
                if verbs:
                    primary_actions.append(action)
        
        # Count endpoints
        endpoint_count = len(endpoints) if endpoints else 0
        
        # Generate description
        if primary_actions:
            action_list = ", ".join(primary_actions[:3])
            description = f"Service for {readable_name} management with {endpoint_count} endpoints. "
            description += f"Supports {action_list} operations."
        else:
            description = f"Service for {readable_name} management with {endpoint_count} endpoints."
        
        return description
    
    def extract_business_context(self, 
                               service_name: str, 
                               endpoints: List[str],
                               descriptions: List[str] = None) -> str:
        """
        Extract business context from service information
        
        Args:
            service_name: Name of the service
            endpoints: List of endpoint paths
            descriptions: Optional endpoint descriptions
            
        Returns:
            Business context description
        """
        context_keywords = set()
        
        # Extract from service name
        service_keywords = self.extract_keywords(service_name)
        context_keywords.update(service_keywords)
        
        # Extract from endpoint paths
        for endpoint in endpoints:
            path_components = self.extract_path_components(endpoint)
            context_keywords.update(path_components.get('resource_candidates', []))
        
        # Extract from descriptions if available
        if descriptions:
            for desc in descriptions:
                if desc:
                    desc_keywords = self.extract_keywords(desc)
                    context_keywords.update(desc_keywords)
        
        # Map to business domains
        itsm_domains = {
            'incident': 'Incident management and resolution',
            'request': 'Service request fulfillment',
            'change': 'Change management and control',
            'problem': 'Problem identification and analysis',
            'release': 'Release deployment and management',
            'user': 'User account and identity management',
            'asset': 'Asset lifecycle management',
            'service': 'Service catalog and provisioning',
            'business_rule': 'Business process automation',
            'notification': 'Communication and alerting',
            'report': 'Analytics and reporting',
            'workflow': 'Process orchestration'
        }
        
        # Find matching domains
        matched_domains = []
        for keyword in context_keywords:
            for domain, description in itsm_domains.items():
                if keyword in domain or domain in keyword:
                    matched_domains.append(description)
                    break
        
        if matched_domains:
            return f"Handles {matched_domains[0].lower()}"
        else:
            # Generic business context
            if 'management' in service_name.lower():
                return f"Manages {service_name.replace('_management', '').replace('_', ' ')} operations"
            else:
                return f"Supports {service_name.replace('_', ' ')} business processes"


# Global instance for easy access
text_processor = TextProcessor()


# Convenience functions
def normalize_text(text: str, preserve_case: bool = False) -> str:
    """Normalize text using global text processor"""
    return text_processor.normalize_text(text, preserve_case)


def clean_identifier(identifier: str) -> str:
    """Clean identifier using global text processor"""
    return text_processor.clean_identifier(identifier)


def extract_keywords(text: str, min_length: int = 2, max_keywords: int = 20) -> List[str]:
    """Extract keywords using global text processor"""
    return text_processor.extract_keywords(text, min_length, max_keywords)


def calculate_text_similarity(text1: str, text2: str) -> float:
    """Calculate text similarity using global text processor"""
    return text_processor.calculate_text_similarity(text1, text2)


def suggest_service_name(endpoint_paths: List[str], operation_ids: List[str] = None) -> str:
    """Suggest service name using global text processor"""
    return text_processor.suggest_service_name(endpoint_paths, operation_ids)