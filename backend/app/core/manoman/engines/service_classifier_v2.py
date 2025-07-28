"""
Service Classifier Engine V2

Improved classification logic that uses tags as primary classification,
then identifies CRUD sets and splits by path when needed.
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
class CRUDSet:
    """Represents a complete CRUD set of operations"""
    base_path: str
    list_op: Optional[RawAPIEndpoint] = None
    get_by_id_op: Optional[RawAPIEndpoint] = None
    create_op: Optional[RawAPIEndpoint] = None
    update_op: Optional[RawAPIEndpoint] = None
    delete_op: Optional[RawAPIEndpoint] = None
    
    def is_complete(self) -> bool:
        """Check if this is a complete CRUD set"""
        return all([self.list_op, self.get_by_id_op, self.create_op, 
                   self.update_op, self.delete_op])
    
    def get_operations(self) -> List[RawAPIEndpoint]:
        """Get all non-null operations"""
        ops = []
        for op in [self.list_op, self.get_by_id_op, self.create_op, 
                   self.update_op, self.delete_op]:
            if op:
                ops.append(op)
        return ops


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
    tags: List[str]  # Original API tags


class ServiceClassifierV2:
    """
    Improved service classifier that uses tags as primary classification
    and intelligently splits services when multiple CRUD sets are detected.
    """
    
    def __init__(self):
        # CRUD patterns for identifying operations
        self.crud_patterns = {
            "list": {
                "method": "GET",
                "path_pattern": r"^(.+?)/?$",  # No ID parameter
                "operation_keywords": ["list", "get_all", "fetch_all", "index"]
            },
            "get_by_id": {
                "method": "GET",
                "path_pattern": r"^(.+?)/\{[^}]+\}/?$",  # Has ID parameter
                "operation_keywords": ["get", "fetch", "retrieve", "show", "detail"]
            },
            "create": {
                "method": "POST",
                "path_pattern": r"^(.+?)/?$",  # No ID parameter
                "operation_keywords": ["create", "add", "new", "insert", "post"]
            },
            "update": {
                "method": ["PUT", "PATCH"],
                "path_pattern": r"^(.+?)/\{[^}]+\}/?$",  # Has ID parameter
                "operation_keywords": ["update", "edit", "modify", "patch", "put"]
            },
            "delete": {
                "method": "DELETE",
                "path_pattern": r"^(.+?)/\{[^}]+\}/?$",  # Has ID parameter
                "operation_keywords": ["delete", "remove", "destroy"]
            }
        }
        
        # Known ITSM domain keywords for better descriptions
        self.itsm_keywords = {
            "incident": ["incident", "ticket", "issue"],
            "request": ["request", "service_request", "sr"],
            "change": ["change", "change_request", "cr"],
            "problem": ["problem", "problem_record"],
            "user": ["user", "person", "account"],
            "asset": ["asset", "ci", "configuration_item"],
            "business_rule": ["business_rule", "rule", "workflow"],
            "purchase_order": ["purchase_order", "po", "procurement"],
            "cmdb": ["cmdb", "configuration", "item_classification"]
        }
    
    async def classify_services(self, api_spec: APISpecification) -> Dict[str, ServiceGroup]:
        """
        Classify API endpoints into logical services using improved logic:
        1. Group by tags (primary classification)
        2. Identify CRUD sets within each tag
        3. Split by path when multiple CRUD sets exist
        
        Args:
            api_spec: Parsed API specification with endpoints
            
        Returns:
            Dictionary mapping service names to ServiceGroup objects
        """
        logger.info(f"Starting service classification V2 for {len(api_spec.endpoints)} endpoints")
        
        # Step 1: Group endpoints by tags
        tag_groups = self._group_by_tags(api_spec.endpoints)
        logger.info(f"Found {len(tag_groups)} tag groups")
        
        # Step 2: Process each tag group
        all_services = {}
        
        for tag_name, endpoints in tag_groups.items():
            logger.info(f"Processing tag '{tag_name}' with {len(endpoints)} endpoints")
            
            # Find CRUD sets in this tag
            crud_sets = self._identify_crud_sets(endpoints)
            remaining_endpoints = self._get_remaining_endpoints(endpoints, crud_sets)
            
            if len(crud_sets) == 0:
                # No CRUD sets found, create single service from all endpoints
                service_name = self._normalize_service_name(tag_name)
                service = self._create_service_group(
                    service_name, endpoints, tag_name, [], endpoints
                )
                all_services[service_name] = service
                
            elif len(crud_sets) == 1:
                # Single CRUD set - all endpoints belong to one service
                service_name = self._normalize_service_name(tag_name)
                tier1_ops = crud_sets[0].get_operations()
                service = self._create_service_group(
                    service_name, endpoints, tag_name, tier1_ops, remaining_endpoints
                )
                all_services[service_name] = service
                
            else:
                # Multiple CRUD sets - need to split by path
                services = self._split_by_crud_sets(tag_name, crud_sets, remaining_endpoints)
                all_services.update(services)
        
        logger.info(f"Classification complete: {len(all_services)} services created")
        return all_services
    
    def _group_by_tags(self, endpoints: List[RawAPIEndpoint]) -> Dict[str, List[RawAPIEndpoint]]:
        """Group endpoints by their tags"""
        tag_groups = defaultdict(list)
        untagged = []
        
        for endpoint in endpoints:
            if endpoint.tags:
                # Use first tag as primary classification
                primary_tag = endpoint.tags[0]
                tag_groups[primary_tag].append(endpoint)
            else:
                untagged.append(endpoint)
        
        # Handle untagged endpoints
        if untagged:
            # Try to group by base path
            path_groups = self._group_untagged_by_path(untagged)
            tag_groups.update(path_groups)
        
        return dict(tag_groups)
    
    def _group_untagged_by_path(self, endpoints: List[RawAPIEndpoint]) -> Dict[str, List[RawAPIEndpoint]]:
        """Group untagged endpoints by their base path"""
        path_groups = defaultdict(list)
        
        for endpoint in endpoints:
            # Extract first meaningful path segment
            path_parts = endpoint.path.strip('/').split('/')
            if path_parts and path_parts[0]:
                # Skip common prefixes like 'ux', 'api', 'v1'
                skip_prefixes = ['ux', 'api', 'v1', 'v2']
                base_parts = []
                
                for part in path_parts:
                    if part.lower() not in skip_prefixes and not part.startswith('{'):
                        base_parts.append(part)
                        if len(base_parts) >= 2:  # Use first 2 meaningful parts
                            break
                
                if base_parts:
                    group_name = '_'.join(base_parts)
                    path_groups[f"untagged_{group_name}"].append(endpoint)
                else:
                    path_groups["untagged_misc"].append(endpoint)
            else:
                path_groups["untagged_root"].append(endpoint)
        
        return dict(path_groups)
    
    def _identify_crud_sets(self, endpoints: List[RawAPIEndpoint]) -> List[CRUDSet]:
        """Identify complete or partial CRUD sets in a group of endpoints"""
        # Group endpoints by their base path (without ID parameters)
        path_groups = defaultdict(list)
        
        for endpoint in endpoints:
            base_path = self._extract_crud_base_path(endpoint.path)
            path_groups[base_path].append(endpoint)
        
        # Build CRUD sets for each path group
        crud_sets = []
        
        for base_path, path_endpoints in path_groups.items():
            crud_set = CRUDSet(base_path=base_path)
            
            for endpoint in path_endpoints:
                crud_type = self._identify_crud_operation(endpoint)
                
                if crud_type == "list" and not crud_set.list_op:
                    crud_set.list_op = endpoint
                elif crud_type == "get_by_id" and not crud_set.get_by_id_op:
                    crud_set.get_by_id_op = endpoint
                elif crud_type == "create" and not crud_set.create_op:
                    crud_set.create_op = endpoint
                elif crud_type == "update" and not crud_set.update_op:
                    crud_set.update_op = endpoint
                elif crud_type == "delete" and not crud_set.delete_op:
                    crud_set.delete_op = endpoint
            
            # Only include sets that have at least 3 CRUD operations
            if len(crud_set.get_operations()) >= 3:
                crud_sets.append(crud_set)
        
        return crud_sets
    
    def _extract_crud_base_path(self, path: str) -> str:
        """Extract base path for CRUD grouping (removes ID parameters)"""
        # Remove trailing slash
        path = path.rstrip('/')
        
        # Remove ID parameters (anything in {})
        path = re.sub(r'/\{[^}]+\}', '', path)
        
        # Remove special endpoints like /create-csv, /options, etc.
        parts = path.split('/')
        cleaned_parts = []
        
        for part in parts:
            # Skip special operation suffixes
            if not any(suffix in part for suffix in ['-csv', 'options', 'count', 'delete', 'upload']):
                cleaned_parts.append(part)
        
        return '/'.join(cleaned_parts)
    
    def _identify_crud_operation(self, endpoint: RawAPIEndpoint) -> Optional[str]:
        """Identify the CRUD operation type of an endpoint"""
        method = endpoint.method.value
        path = endpoint.path
        operation_id = (endpoint.operation_id or "").lower()
        
        # Check each CRUD pattern
        for crud_type, pattern in self.crud_patterns.items():
            # Check HTTP method
            pattern_methods = pattern["method"]
            if isinstance(pattern_methods, str):
                pattern_methods = [pattern_methods]
            
            if method not in pattern_methods:
                continue
            
            # Check path pattern
            if not re.match(pattern["path_pattern"], path):
                continue
            
            # Check operation keywords
            if any(keyword in operation_id for keyword in pattern["operation_keywords"]):
                return crud_type
            
            # For simple cases, method + path pattern is enough
            if crud_type == "list" and method == "GET" and not "{" in path:
                return "list"
            elif crud_type == "get_by_id" and method == "GET" and "{" in path:
                return "get_by_id"
            elif crud_type == "create" and method == "POST" and not "{" in path:
                # Exclude special operations
                if not any(kw in path.lower() for kw in ['csv', 'upload', 'delete', 'options']):
                    return "create"
            elif crud_type == "delete" and method == "DELETE":
                return "delete"
            elif crud_type == "update" and method in ["PUT", "PATCH"]:
                return "update"
        
        return None
    
    def _get_remaining_endpoints(self, all_endpoints: List[RawAPIEndpoint], 
                                crud_sets: List[CRUDSet]) -> List[RawAPIEndpoint]:
        """Get endpoints that are not part of any CRUD set (Tier 2 operations)"""
        crud_endpoints = set()
        
        for crud_set in crud_sets:
            for op in crud_set.get_operations():
                crud_endpoints.add(op.operation_id)
        
        remaining = []
        for endpoint in all_endpoints:
            if endpoint.operation_id not in crud_endpoints:
                remaining.append(endpoint)
        
        return remaining
    
    def _split_by_crud_sets(self, tag_name: str, crud_sets: List[CRUDSet], 
                           remaining_endpoints: List[RawAPIEndpoint]) -> Dict[str, ServiceGroup]:
        """Split a tag into multiple services based on CRUD sets"""
        services = {}
        
        # Assign remaining endpoints to the closest CRUD set
        endpoint_assignments = defaultdict(list)
        
        for endpoint in remaining_endpoints:
            best_match = self._find_best_crud_set_match(endpoint, crud_sets)
            if best_match:
                endpoint_assignments[best_match.base_path].append(endpoint)
        
        # Create service for each CRUD set
        for crud_set in crud_sets:
            # Extract service name from path
            service_name = self._extract_service_name_from_path(crud_set.base_path, tag_name)
            
            # Get all endpoints for this service
            tier1_ops = crud_set.get_operations()
            tier2_ops = endpoint_assignments.get(crud_set.base_path, [])
            all_ops = tier1_ops + tier2_ops
            
            service = self._create_service_group(
                service_name, all_ops, tag_name, tier1_ops, tier2_ops
            )
            services[service_name] = service
        
        return services
    
    def _find_best_crud_set_match(self, endpoint: RawAPIEndpoint, 
                                  crud_sets: List[CRUDSet]) -> Optional[CRUDSet]:
        """Find the best matching CRUD set for an endpoint based on path similarity"""
        endpoint_path = endpoint.path.lower()
        best_match = None
        best_score = 0
        
        for crud_set in crud_sets:
            # Calculate path similarity
            base_path = crud_set.base_path.lower()
            
            # Check if endpoint path starts with CRUD set base path
            if endpoint_path.startswith(base_path):
                score = len(base_path)  # Longer matches are better
                if score > best_score:
                    best_score = score
                    best_match = crud_set
        
        return best_match
    
    def _extract_service_name_from_path(self, base_path: str, tag_name: str) -> str:
        """Extract a meaningful service name from the base path"""
        # Remove common prefixes
        path = base_path.strip('/')
        parts = path.split('/')
        
        # Skip common prefixes
        skip_prefixes = ['ux', 'api', 'v1', 'v2', 'common']
        meaningful_parts = []
        
        for part in parts:
            if part.lower() not in skip_prefixes:
                meaningful_parts.append(part)
        
        if meaningful_parts:
            # Use the last meaningful part(s)
            if len(meaningful_parts) >= 2:
                # For paths like /cmdb/item-classification
                service_name = '_'.join(meaningful_parts[-2:])
            else:
                service_name = meaningful_parts[-1]
        else:
            # Fallback to tag name
            service_name = tag_name
        
        return self._normalize_service_name(service_name)
    
    def _normalize_service_name(self, name: str) -> str:
        """Normalize service name to valid identifier"""
        # Replace hyphens and spaces with underscores
        name = name.replace('-', '_').replace(' ', '_')
        
        # Remove special characters
        name = re.sub(r'[^a-zA-Z0-9_]', '', name)
        
        # Convert to lowercase
        name = name.lower()
        
        # Remove duplicate underscores
        name = re.sub(r'_+', '_', name)
        
        # Remove leading/trailing underscores
        name = name.strip('_')
        
        return name or "unknown_service"
    
    def _create_service_group(self, service_name: str, all_endpoints: List[RawAPIEndpoint],
                             tag_name: str, tier1_ops: List[RawAPIEndpoint], 
                             tier2_ops: List[RawAPIEndpoint]) -> ServiceGroup:
        """Create a ServiceGroup with metadata"""
        # Calculate base path
        base_path = self._calculate_common_base_path(all_endpoints)
        
        # Generate description
        description = self._generate_service_description(service_name, all_endpoints, tag_name)
        
        # Extract keywords
        keywords = self._extract_keywords(service_name, all_endpoints, tag_name)
        
        # Get synonyms
        synonyms = self._get_synonyms(service_name)
        
        # Calculate confidence
        confidence = self._calculate_confidence(all_endpoints, tier1_ops, tier2_ops)
        
        # Get all tags
        all_tags = set()
        for endpoint in all_endpoints:
            if endpoint.tags:
                all_tags.update(endpoint.tags)
        
        return ServiceGroup(
            service_name=service_name,
            endpoints=all_endpoints,
            base_path=base_path,
            confidence_score=confidence,
            tier1_operations=tier1_ops,
            tier2_operations=tier2_ops,
            suggested_description=description,
            keywords=keywords,
            synonyms=synonyms,
            tags=list(all_tags)
        )
    
    def _calculate_common_base_path(self, endpoints: List[RawAPIEndpoint]) -> str:
        """Calculate the common base path for a set of endpoints"""
        if not endpoints:
            return "/"
        
        paths = [ep.path for ep in endpoints]
        
        # Find common prefix
        common_prefix = paths[0]
        for path in paths[1:]:
            # Find common characters
            i = 0
            while i < len(common_prefix) and i < len(path) and common_prefix[i] == path[i]:
                i += 1
            common_prefix = common_prefix[:i]
        
        # Clean to end at path boundary
        if common_prefix and not common_prefix.endswith('/'):
            last_slash = common_prefix.rfind('/')
            if last_slash > 0:
                common_prefix = common_prefix[:last_slash + 1]
        
        return common_prefix or "/"
    
    def _generate_service_description(self, service_name: str, endpoints: List[RawAPIEndpoint],
                                     tag_name: str) -> str:
        """Generate a meaningful description for the service"""
        # Check for ITSM domain match
        for domain, keywords in self.itsm_keywords.items():
            if service_name in keywords or any(kw in service_name for kw in keywords):
                return f"Manages {domain} operations including CRUD and specialized workflows"
        
        # Extract operations from endpoints
        operations = set()
        for endpoint in endpoints:
            if endpoint.summary:
                # Extract first few words as operation
                words = endpoint.summary.split()[:3]
                operations.add(' '.join(words).lower())
        
        if operations:
            ops_summary = ', '.join(list(operations)[:5])
            return f"Service for {service_name} with operations: {ops_summary}"
        
        return f"Service for managing {service_name} resources and operations"
    
    def _extract_keywords(self, service_name: str, endpoints: List[RawAPIEndpoint],
                         tag_name: str) -> List[str]:
        """Extract relevant keywords for the service"""
        keywords = set()
        
        # Add service name parts
        name_parts = service_name.split('_')
        keywords.update(name_parts)
        
        # Add tag name parts
        tag_parts = tag_name.lower().replace('-', '_').split('_')
        keywords.update(tag_parts)
        
        # Add from endpoint paths
        for endpoint in endpoints[:10]:  # Sample first 10
            path_parts = endpoint.path.strip('/').split('/')
            for part in path_parts:
                if not part.startswith('{') and len(part) > 2:
                    keywords.add(part.replace('-', '_').lower())
        
        # Add from summaries
        for endpoint in endpoints[:10]:
            if endpoint.summary:
                words = re.findall(r'\b\w+\b', endpoint.summary.lower())
                keywords.update([w for w in words if len(w) > 3][:5])
        
        # Remove common words
        common = {'get', 'post', 'put', 'delete', 'list', 'create', 'update', 'the', 'with', 'for', 'and'}
        keywords = keywords - common
        
        return sorted(list(keywords))[:15]  # Return top 15 keywords
    
    def _get_synonyms(self, service_name: str) -> List[str]:
        """Get synonyms for the service based on ITSM domain knowledge"""
        synonyms = []
        
        for domain, keywords in self.itsm_keywords.items():
            if service_name in keywords or any(kw in service_name for kw in keywords):
                # Add other keywords from same domain as synonyms
                synonyms = [kw for kw in keywords if kw != service_name]
                break
        
        return synonyms
    
    def _calculate_confidence(self, all_endpoints: List[RawAPIEndpoint],
                             tier1_ops: List[RawAPIEndpoint], 
                             tier2_ops: List[RawAPIEndpoint]) -> float:
        """Calculate confidence score for the service classification"""
        score = 0.5  # Base score
        
        # Bonus for having complete CRUD set
        if len(tier1_ops) >= 5:
            score += 0.2
        elif len(tier1_ops) >= 3:
            score += 0.1
        
        # Bonus for having tier 2 operations
        if tier2_ops:
            score += 0.1
        
        # Bonus for good endpoint count
        if 5 <= len(all_endpoints) <= 50:
            score += 0.1
        
        # Penalty for too few or too many endpoints
        if len(all_endpoints) < 3:
            score -= 0.2
        elif len(all_endpoints) > 100:
            score -= 0.1
        
        return max(0.1, min(1.0, score))