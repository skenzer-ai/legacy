"""
Service Classifier Engine

Analyzes parsed API endpoints and automatically groups them into logical services
based on URL patterns, operation patterns, and semantic similarity. This engine
implements the core service-centric tier classification system.
"""

import re
import logging
from typing import Dict, List, Optional, Set, Tuple, Any
from collections import defaultdict, Counter
from dataclasses import dataclass
from datetime import datetime

from ..models.api_specification import (
    APISpecification,
    RawAPIEndpoint,
    HTTPMethod
)
from ..models.service_registry import (
    ServiceDefinition,
    ServiceOperation,
    OperationType,
    TierLevel,
    APIEndpoint
)

logger = logging.getLogger(__name__)


@dataclass
class ServiceGroup:
    """Represents a classified service group with metadata"""
    service_name: str
    endpoints: List[RawAPIEndpoint]
    base_path: str
    confidence_score: float
    tier1_operations: List[RawAPIEndpoint]
    tier2_operations: List[RawAPIEndpoint]
    suggested_description: str
    keywords: List[str]
    synonyms: List[str]


class ServiceClassifierError(Exception):
    """Custom exception for service classification errors"""
    pass


# Import the V2 classifier
from .service_classifier_v2 import ServiceClassifierV2

class ServiceClassifier:
    """
    Analyzes parsed API endpoints and automatically groups them into logical services
    based on URL patterns, operation patterns, and semantic similarity.
    """
    
    def __init__(self):
        # Use the V2 classifier internally
        self._v2_classifier = ServiceClassifierV2()
        
        # Keep the original attributes for backward compatibility
        self.crud_operation_map = {
            "GET": {"list": r"^/[\w-]+/?$", "get_by_id": r"^/[\w-]+/\{[\w-]+\}/?$"},
            "POST": {"create": r"^/[\w-]+/?$"},
            "PUT": {"update": r"^/[\w-]+/\{[\w-]+\}/?$"},
            "PATCH": {"update": r"^/[\w-]+/\{[\w-]+\}/?$"},
            "DELETE": {"delete": r"^/[\w-]+/\{[\w-]+\}/?$"}
        }
        
        # Common ITSM domain keywords for better classification
        self.itsm_keywords = {
            "incident": ["incident", "ticket", "issue", "problem"],
            "request": ["request", "service_request", "sr"],
            "change": ["change", "change_request", "cr"],
            "problem": ["problem", "problem_record", "pr"],
            "release": ["release", "deployment", "rollout"],
            "user": ["user", "person", "account", "profile"],
            "asset": ["asset", "ci", "configuration_item"],
            "catalog": ["catalog", "service_catalog", "offering"],
            "workflow": ["workflow", "process", "automation"],
            "notification": ["notification", "alert", "message"],
            "report": ["report", "analytics", "dashboard"],
            "approval": ["approval", "authorize", "review"]
        }
        
        self.classification_errors = []
    
    async def classify_services(self, api_spec: APISpecification) -> Dict[str, ServiceGroup]:
        """
        Classify API endpoints into logical services using the improved V2 classifier
        
        Args:
            api_spec: Parsed API specification with endpoints
            
        Returns:
            Dictionary mapping service names to ServiceGroup objects
            
        Raises:
            ServiceClassifierError: If classification fails
        """
        # Delegate to V2 classifier
        return await self._v2_classifier.classify_services(api_spec)
    
    def _group_by_path_patterns(self, endpoints: List[RawAPIEndpoint]) -> Dict[str, List[RawAPIEndpoint]]:
        """Group endpoints by common URL path segments"""
        path_groups = defaultdict(list)
        
        for endpoint in endpoints:
            # Extract base path (remove path parameters and normalize)
            base_path = self._extract_base_path(endpoint.path)
            path_groups[base_path].append(endpoint)
        
        # Filter out groups with too few endpoints (likely not a service)
        filtered_groups = {}
        for base_path, group_endpoints in path_groups.items():
            if len(group_endpoints) >= 2:  # At least 2 endpoints to form a service
                filtered_groups[base_path] = group_endpoints
            else:
                # Add single endpoints to a "miscellaneous" group
                if "miscellaneous" not in filtered_groups:
                    filtered_groups["miscellaneous"] = []
                filtered_groups["miscellaneous"].extend(group_endpoints)
        
        return filtered_groups
    
    def _extract_base_path(self, path: str) -> str:
        """Extract base path from full endpoint path"""
        # Remove leading/trailing slashes
        clean_path = path.strip('/')
        
        if not clean_path:
            return "root"
        
        # Split path into segments
        segments = clean_path.split('/')
        
        # Remove path parameters (anything in curly braces or that looks like an ID)
        base_segments = []
        for segment in segments:
            if not (segment.startswith('{') and segment.endswith('}')):
                # Check if segment looks like an ID (numeric or UUID-like)
                if not (segment.isdigit() or self._looks_like_id(segment)):
                    base_segments.append(segment)
        
        # Take the most specific path that's not too generic
        if len(base_segments) >= 2:
            # Use last 2 segments for better service identification
            return '/'.join(base_segments[-2:])
        elif len(base_segments) == 1:
            return base_segments[0]
        else:
            return "root"
    
    def _looks_like_id(self, segment: str) -> bool:
        """Check if a path segment looks like an ID"""
        # UUID pattern
        uuid_pattern = r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
        if re.match(uuid_pattern, segment, re.IGNORECASE):
            return True
        
        # Numeric ID
        if segment.isdigit():
            return True
        
        # Mixed alphanumeric that looks like an ID
        if len(segment) > 8 and re.match(r'^[a-zA-Z0-9]+$', segment):
            return True
        
        return False
    
    def _refine_groups_by_semantics(self, path_groups: Dict[str, List[RawAPIEndpoint]]) -> Dict[str, List[RawAPIEndpoint]]:
        """Refine groupings using semantic similarity and ITSM domain knowledge"""
        refined_groups = {}
        
        for base_path, endpoints in path_groups.items():
            # Extract semantic information from paths and operation IDs
            service_name = self._suggest_service_name(base_path, endpoints)
            
            # Check if this service should be merged with an existing one
            merge_candidate = self._find_merge_candidate(service_name, refined_groups)
            
            if merge_candidate:
                # Merge with existing service
                refined_groups[merge_candidate].extend(endpoints)
                logger.debug(f"Merged '{base_path}' into existing service '{merge_candidate}'")
            else:
                # Create new service group
                refined_groups[service_name] = endpoints
                logger.debug(f"Created new service group '{service_name}' with {len(endpoints)} endpoints")
        
        return refined_groups
    
    def _suggest_service_name(self, base_path: str, endpoints: List[RawAPIEndpoint]) -> str:
        """Suggest a service name based on path and endpoint analysis"""
        # Extract potential service names from path
        path_parts = [part for part in base_path.split('/') if part]
        
        # Check for ITSM domain matches
        for part in path_parts:
            part_lower = part.lower().replace('-', '_').replace(' ', '_')
            for domain_key, keywords in self.itsm_keywords.items():
                if part_lower in keywords or part_lower.startswith(domain_key):
                    return domain_key
        
        # Check operation IDs for semantic clues
        operation_words = []
        for endpoint in endpoints:
            if endpoint.operation_id:
                # Extract words from operation_id (camelCase or snake_case)
                words = re.findall(r'[A-Z][a-z]*|[a-z]+', endpoint.operation_id)
                operation_words.extend([w.lower() for w in words])
        
        # Find most common meaningful word
        word_counts = Counter(operation_words)
        common_words = ['get', 'post', 'put', 'delete', 'list', 'create', 'update', 'by', 'id']
        
        for word, count in word_counts.most_common():
            if word not in common_words and len(word) > 2:
                # Check if it matches ITSM domain
                for domain_key, keywords in self.itsm_keywords.items():
                    if word in keywords:
                        return domain_key
                # Use the word as-is if no domain match
                return word
        
        # Fallback to path-based name
        if path_parts:
            return path_parts[-1].lower().replace('-', '_')
        
        return base_path.replace('/', '_').lower()
    
    def _find_merge_candidate(self, service_name: str, existing_groups: Dict[str, List[RawAPIEndpoint]]) -> Optional[str]:
        """Find if this service should be merged with an existing one"""
        # Check for exact matches or close semantic matches
        service_lower = service_name.lower()
        
        for existing_name in existing_groups.keys():
            existing_lower = existing_name.lower()
            
            # Exact match
            if service_lower == existing_lower:
                return existing_name
            
            # Check for semantic similarity in ITSM domain
            for domain_key, keywords in self.itsm_keywords.items():
                if (service_lower in keywords and existing_lower in keywords):
                    return existing_name
            
            # Check for substring matches (be careful not to over-merge)
            if (len(service_lower) > 4 and len(existing_lower) > 4 and
                (service_lower in existing_lower or existing_lower in service_lower)):
                return existing_name
        
        return None
    
    def _create_service_group(self, service_name: str, endpoints: List[RawAPIEndpoint]) -> ServiceGroup:
        """Create a ServiceGroup with full classification"""
        # Classify CRUD operations
        crud_classification = self._classify_crud_operations(endpoints)
        
        tier1_ops = []
        tier2_ops = []
        
        for endpoint in endpoints:
            crud_type = crud_classification.get(endpoint.operation_id)
            if crud_type in ['list', 'get_by_id', 'create', 'update', 'delete']:
                tier1_ops.append(endpoint)
            else:
                tier2_ops.append(endpoint)
        
        # Generate metadata
        base_path = self._get_common_base_path(endpoints)
        description = self._generate_service_description(service_name, endpoints)
        keywords = self._extract_keywords(service_name, endpoints)
        synonyms = self._get_domain_synonyms(service_name)
        
        # Calculate confidence score
        confidence = self._calculate_confidence_score(service_name, endpoints, tier1_ops, tier2_ops)
        
        return ServiceGroup(
            service_name=service_name,
            endpoints=endpoints,
            base_path=base_path,
            confidence_score=confidence,
            tier1_operations=tier1_ops,
            tier2_operations=tier2_ops,
            suggested_description=description,
            keywords=keywords,
            synonyms=synonyms
        )
    
    def _classify_crud_operations(self, endpoints: List[RawAPIEndpoint]) -> Dict[str, str]:
        """Classify endpoints as CRUD operations"""
        crud_map = {}
        
        for endpoint in endpoints:
            method = endpoint.method.value
            path = endpoint.path
            
            # Normalize path for pattern matching
            normalized_path = self._normalize_path_for_crud(path)
            
            crud_type = None
            if method in self.crud_operation_map:
                for operation, pattern in self.crud_operation_map[method].items():
                    if re.match(pattern, normalized_path):
                        crud_type = operation
                        break
            
            # Fallback: use operation_id hints
            if not crud_type and endpoint.operation_id:
                crud_type = self._infer_crud_from_operation_id(endpoint.operation_id)
            
            # Fallback: use method-based defaults
            if not crud_type:
                crud_type = self._get_default_crud_for_method(method)
            
            crud_map[endpoint.operation_id] = crud_type
        
        return crud_map
    
    def _normalize_path_for_crud(self, path: str) -> str:
        """Normalize path for CRUD pattern matching"""
        # Replace specific IDs with generic parameter pattern
        normalized = re.sub(r'/[^/]*\{[^}]+\}', '/{id}', path)
        # Remove trailing slash
        normalized = normalized.rstrip('/')
        # Ensure leading slash
        if not normalized.startswith('/'):
            normalized = '/' + normalized
        return normalized
    
    def _infer_crud_from_operation_id(self, operation_id: str) -> Optional[str]:
        """Infer CRUD operation from operation ID"""
        op_lower = operation_id.lower()
        
        if any(word in op_lower for word in ['list', 'get_all', 'find_all']):
            return 'list'
        elif any(word in op_lower for word in ['get_by', 'find_by', 'get_', 'fetch']):
            return 'get_by_id'
        elif any(word in op_lower for word in ['create', 'add', 'insert', 'new']):
            return 'create'
        elif any(word in op_lower for word in ['update', 'modify', 'edit', 'patch']):
            return 'update'
        elif any(word in op_lower for word in ['delete', 'remove', 'destroy']):
            return 'delete'
        
        return None
    
    def _get_default_crud_for_method(self, method: str) -> str:
        """Get default CRUD operation for HTTP method"""
        method_defaults = {
            'GET': 'list',  # Could be get_by_id, but list is more common default
            'POST': 'create',
            'PUT': 'update',
            'PATCH': 'update',
            'DELETE': 'delete'
        }
        return method_defaults.get(method, 'unknown')
    
    def _get_common_base_path(self, endpoints: List[RawAPIEndpoint]) -> str:
        """Find common base path for a group of endpoints"""
        if not endpoints:
            return "/"
        
        paths = [ep.path for ep in endpoints]
        
        # Find common prefix
        common_prefix = paths[0]
        for path in paths[1:]:
            # Find common prefix between current common_prefix and this path
            i = 0
            while (i < len(common_prefix) and i < len(path) and 
                   common_prefix[i] == path[i]):
                i += 1
            common_prefix = common_prefix[:i]
        
        # Clean up the common prefix to end at a path boundary
        if common_prefix and not common_prefix.endswith('/'):
            last_slash = common_prefix.rfind('/')
            if last_slash >= 0:
                common_prefix = common_prefix[:last_slash + 1]
        
        return common_prefix or "/"
    
    def _generate_service_description(self, service_name: str, endpoints: List[RawAPIEndpoint]) -> str:
        """Generate a description for the service"""
        # Check if it's a known ITSM domain
        for domain_key, keywords in self.itsm_keywords.items():
            if service_name.lower() in keywords:
                return f"Manages {domain_key} operations including CRUD operations and related workflows"
        
        # Extract operation verbs from endpoints
        operations = set()
        for endpoint in endpoints:
            if endpoint.summary:
                # Extract verbs from summary
                words = re.findall(r'\b\w+\b', endpoint.summary.lower())
                action_words = [w for w in words if w in ['create', 'get', 'list', 'update', 'delete', 'manage', 'process']]
                operations.update(action_words)
        
        if operations:
            ops_str = ', '.join(sorted(operations))
            return f"Service for {service_name} management with operations: {ops_str}"
        
        return f"Service for {service_name} management and related operations"
    
    def _extract_keywords(self, service_name: str, endpoints: List[RawAPIEndpoint]) -> List[str]:
        """Extract relevant keywords for the service"""
        keywords = set([service_name.lower()])
        
        # Add ITSM domain keywords if applicable
        for domain_key, domain_keywords in self.itsm_keywords.items():
            if service_name.lower() in domain_keywords:
                keywords.update(domain_keywords)
                break
        
        # Extract from endpoint paths and summaries
        for endpoint in endpoints:
            # From path
            path_words = re.findall(r'\b\w+\b', endpoint.path.lower())
            keywords.update([w for w in path_words if len(w) > 2 and w.isalpha()])
            
            # From summary and description
            for text in [endpoint.summary, endpoint.description]:
                if text:
                    text_words = re.findall(r'\b\w+\b', text.lower())
                    keywords.update([w for w in text_words if len(w) > 3 and w.isalpha()])
        
        # Filter out common words
        common_words = {'get', 'post', 'put', 'delete', 'api', 'endpoint', 'the', 'and', 'or', 'with', 'for'}
        filtered_keywords = [k for k in keywords if k not in common_words]
        
        return sorted(filtered_keywords)[:10]  # Limit to top 10 keywords
    
    def _get_domain_synonyms(self, service_name: str) -> List[str]:
        """Get domain-specific synonyms for the service"""
        service_lower = service_name.lower()
        
        for domain_key, keywords in self.itsm_keywords.items():
            if service_lower in keywords:
                # Return other keywords in the same domain as synonyms
                return [k for k in keywords if k != service_lower]
        
        return []
    
    def _calculate_confidence_score(self, service_name: str, endpoints: List[RawAPIEndpoint], 
                                   tier1_ops: List[RawAPIEndpoint], tier2_ops: List[RawAPIEndpoint]) -> float:
        """Calculate confidence score for service classification"""
        score = 0.0
        
        # Base score for having endpoints
        if endpoints:
            score += 0.3
        
        # Bonus for ITSM domain recognition
        for domain_key, keywords in self.itsm_keywords.items():
            if service_name.lower() in keywords:
                score += 0.2
                break
        
        # Bonus for having balanced CRUD operations
        if tier1_ops:
            score += 0.2
            # Extra bonus for having complete CRUD set
            crud_types = set()
            for op in tier1_ops:
                if hasattr(op, 'method'):
                    crud_types.add(op.method.value)
            
            if len(crud_types) >= 3:  # Has at least 3 different HTTP methods
                score += 0.1
        
        # Penalty for too few endpoints (might be misclassified)
        if len(endpoints) < 2:
            score -= 0.2
        
        # Bonus for consistent naming patterns
        if self._has_consistent_naming(endpoints):
            score += 0.1
        
        # Bonus for having both tier1 and tier2 operations
        if tier1_ops and tier2_ops:
            score += 0.1
        
        return min(max(score, 0.0), 1.0)  # Clamp between 0 and 1
    
    def _has_consistent_naming(self, endpoints: List[RawAPIEndpoint]) -> bool:
        """Check if endpoints have consistent naming patterns"""
        if len(endpoints) < 2:
            return True
        
        # Check if operation IDs follow similar patterns
        operation_patterns = []
        for endpoint in endpoints:
            if endpoint.operation_id:
                # Extract pattern (e.g., "get_user" -> "verb_noun")
                parts = re.findall(r'[A-Z][a-z]*|[a-z]+', endpoint.operation_id)
                if len(parts) >= 2:
                    pattern = f"{parts[0]}_{parts[-1]}"  # verb_noun pattern
                    operation_patterns.append(pattern)
        
        if not operation_patterns:
            return False
        
        # Check if most operations share the same noun
        nouns = [pattern.split('_')[-1] for pattern in operation_patterns]
        most_common_noun = Counter(nouns).most_common(1)[0][0]
        consistency_ratio = nouns.count(most_common_noun) / len(nouns)
        
        return consistency_ratio >= 0.7  # At least 70% consistency
    
    def _validate_service_groups(self, service_groups: Dict[str, ServiceGroup]) -> Dict[str, ServiceGroup]:
        """Validate and clean up service groups"""
        validated_groups = {}
        
        for service_name, group in service_groups.items():
            # Skip groups with very low confidence
            if group.confidence_score < 0.3:
                self.classification_errors.append(f"Skipping service '{service_name}' due to low confidence: {group.confidence_score}")
                continue
            
            # Ensure service name is valid
            clean_name = self._clean_service_name(service_name)
            
            # Check for duplicates
            if clean_name in validated_groups:
                # Merge with existing service
                existing = validated_groups[clean_name]
                merged_group = self._merge_service_groups(existing, group)
                validated_groups[clean_name] = merged_group
                logger.info(f"Merged duplicate service '{service_name}' into '{clean_name}'")
            else:
                validated_groups[clean_name] = group
        
        return validated_groups
    
    def _clean_service_name(self, service_name: str) -> str:
        """Clean and normalize service name"""
        # Convert to lowercase and replace special characters
        clean_name = re.sub(r'[^a-zA-Z0-9_]', '_', service_name.lower())
        # Remove multiple underscores
        clean_name = re.sub(r'_+', '_', clean_name)
        # Remove leading/trailing underscores
        clean_name = clean_name.strip('_')
        
        return clean_name or 'unknown_service'
    
    def _merge_service_groups(self, group1: ServiceGroup, group2: ServiceGroup) -> ServiceGroup:
        """Merge two service groups"""
        # Combine endpoints
        all_endpoints = group1.endpoints + group2.endpoints
        all_tier1 = group1.tier1_operations + group2.tier1_operations
        all_tier2 = group2.tier2_operations + group2.tier2_operations
        
        # Combine keywords and synonyms
        combined_keywords = list(set(group1.keywords + group2.keywords))
        combined_synonyms = list(set(group1.synonyms + group2.synonyms))
        
        # Use higher confidence score
        confidence = max(group1.confidence_score, group2.confidence_score)
        
        # Use better description
        description = group1.suggested_description if len(group1.suggested_description) > len(group2.suggested_description) else group2.suggested_description
        
        return ServiceGroup(
            service_name=group1.service_name,  # Keep first name
            endpoints=all_endpoints,
            base_path=group1.base_path,  # Keep first base path
            confidence_score=confidence,
            tier1_operations=all_tier1,
            tier2_operations=all_tier2,
            suggested_description=description,
            keywords=combined_keywords,
            synonyms=combined_synonyms
        )
    
    def get_classification_errors(self) -> List[str]:
        """Get list of classification errors encountered"""
        return self.classification_errors.copy()
    
    def get_classification_stats(self, service_groups: Dict[str, ServiceGroup]) -> Dict[str, Any]:
        """Get classification statistics"""
        if not service_groups:
            return {}
        
        total_endpoints = sum(len(group.endpoints) for group in service_groups.values())
        total_tier1 = sum(len(group.tier1_operations) for group in service_groups.values())
        total_tier2 = sum(len(group.tier2_operations) for group in service_groups.values())
        
        confidence_scores = [group.confidence_score for group in service_groups.values()]
        avg_confidence = sum(confidence_scores) / len(confidence_scores)
        
        high_confidence = len([s for s in confidence_scores if s >= 0.8])
        medium_confidence = len([s for s in confidence_scores if 0.5 <= s < 0.8])
        low_confidence = len([s for s in confidence_scores if s < 0.5])
        
        return {
            "total_services": len(service_groups),
            "total_endpoints": total_endpoints,
            "tier1_operations": total_tier1,
            "tier2_operations": total_tier2,
            "average_confidence": round(avg_confidence, 3),
            "confidence_distribution": {
                "high_confidence": high_confidence,
                "medium_confidence": medium_confidence,
                "low_confidence": low_confidence
            },
            "classification_errors": len(self.classification_errors)
        }
    
    def suggest_service_metadata(self, service_name: str, endpoints: List[RawAPIEndpoint]) -> Dict[str, Any]:
        """
        Suggest metadata for a service based on its endpoints
        
        Args:
            service_name: Name of the service
            endpoints: List of endpoints belonging to this service
            
        Returns:
            Dictionary containing suggested metadata
        """
        return {
            "description": self._generate_service_description(service_name, endpoints),
            "keywords": self._extract_keywords(service_name, endpoints),
            "synonyms": self._get_domain_synonyms(service_name),
            "base_path": self._get_common_base_path(endpoints),
            "confidence_score": self._calculate_confidence_score(service_name, endpoints, defaultdict(str))
        }
    
    def classify_operation_tier(self, endpoint: RawAPIEndpoint) -> Dict[str, Any]:
        """
        Classify an individual operation into tier 1 or tier 2
        
        Args:
            endpoint: The API endpoint to classify
            
        Returns:
            Dictionary with tier classification and confidence
        """
        # Detect CRUD operations
        crud_pattern = self._infer_crud_from_operation_id(endpoint.operation_id)
        if not crud_pattern:
            # Try to infer from method and path
            crud_pattern = self._get_default_crud_for_method(endpoint.method.value)
        
        # Tier 1: Basic CRUD operations
        tier1_operations = {"create", "read", "update", "delete", "list"}
        
        if crud_pattern and crud_pattern.lower() in tier1_operations:
            # Check for simple patterns vs complex ones
            if self._is_simple_crud(endpoint):
                return {
                    "tier": "tier1",
                    "operation_type": crud_pattern.lower(),
                    "confidence": 0.9
                }
            else:
                return {
                    "tier": "tier2",
                    "operation_type": crud_pattern.lower(),
                    "confidence": 0.8
                }
        
        # Tier 2: Everything else (bulk operations, analytics, complex workflows)
        return {
            "tier": "tier2",
            "operation_type": "specialized",
            "confidence": 0.7
        }
    
    def _is_simple_crud(self, endpoint: RawAPIEndpoint) -> bool:
        """Check if this is a simple CRUD operation vs complex one"""
        # Simple heuristics for complexity
        
        # Complex indicators in path
        complex_keywords = ["bulk", "batch", "export", "import", "search", "filter", "analytics", "report"]
        path_lower = endpoint.path.lower()
        
        if any(keyword in path_lower for keyword in complex_keywords):
            return False
        
        # Complex indicators in operation ID or summary
        operation_text = (endpoint.operation_id or "").lower()
        summary_text = (endpoint.summary or "").lower()
        
        if any(keyword in operation_text or keyword in summary_text for keyword in complex_keywords):
            return False
        
        # Simple CRUD operations typically have fewer parameters
        if len(endpoint.parameters) > 5:
            return False
        
        # Default to simple
        return True