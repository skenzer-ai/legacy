"""
Registry Helper Utilities for Man-O-Man

Provides helper functions for service registry operations, validation,
transformation, and common registry management tasks.
"""

import json
import logging
from typing import Dict, List, Optional, Set, Tuple, Any, Union
from datetime import datetime, timezone
from collections import defaultdict
import uuid

from ..models.service_registry import (
    ServiceRegistry, ServiceDefinition, ServiceOperation, APIEndpoint,
    OperationType, TierLevel, ConflictType, ConflictSeverity, ConflictReport
)
from ..models.api_specification import RawAPIEndpoint, HTTPMethod
from .text_processing import text_processor

logger = logging.getLogger(__name__)


class RegistryHelper:
    """
    Helper utilities for service registry operations
    
    Provides functions for registry validation, transformation, merging,
    comparison, and other common registry management operations.
    """
    
    @staticmethod
    def create_registry_id() -> str:
        """Generate a unique registry ID"""
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        unique_id = str(uuid.uuid4())[:8]
        return f"registry_{timestamp}_{unique_id}"
    
    @staticmethod
    def validate_registry(registry: ServiceRegistry) -> List[str]:
        """
        Validate a service registry for consistency and completeness
        
        Args:
            registry: ServiceRegistry to validate
            
        Returns:
            List of validation errors (empty if valid)
        """
        errors = []
        
        # Basic structure validation
        if not registry.registry_id:
            errors.append("Registry ID is required")
        
        if not registry.version:
            errors.append("Registry version is required")
        
        if not registry.services:
            errors.append("Registry must contain at least one service")
        
        # Service count validation
        if registry.total_services != len(registry.services):
            errors.append(f"Total services count ({registry.total_services}) doesn't match actual services ({len(registry.services)})")
        
        # Individual service validation
        for service_name, service_def in registry.services.items():
            service_errors = RegistryHelper.validate_service_definition(service_def, service_name)
            errors.extend(service_errors)
        
        # Cross-service validation
        cross_errors = RegistryHelper.validate_cross_service_consistency(registry)
        errors.extend(cross_errors)
        
        return errors
    
    @staticmethod
    def validate_service_definition(service_def: ServiceDefinition, expected_name: str = None) -> List[str]:
        """
        Validate a single service definition
        
        Args:
            service_def: ServiceDefinition to validate
            expected_name: Expected service name (optional)
            
        Returns:
            List of validation errors
        """
        errors = []
        
        # Name validation
        if expected_name and service_def.service_name != expected_name:
            errors.append(f"Service name mismatch: expected '{expected_name}', got '{service_def.service_name}'")
        
        # Required fields
        if not service_def.service_name:
            errors.append("Service name is required")
        
        if not service_def.service_description:
            errors.append(f"Service '{service_def.service_name}' missing description")
        
        # Operations validation
        if not service_def.tier1_operations and not service_def.tier2_operations:
            errors.append(f"Service '{service_def.service_name}' has no operations")
        
        # Validate individual operations
        for op_name, operation in service_def.tier1_operations.items():
            op_errors = RegistryHelper.validate_service_operation(operation, op_name, "tier1")
            errors.extend([f"Service '{service_def.service_name}': {error}" for error in op_errors])
        
        for op_name, operation in service_def.tier2_operations.items():
            op_errors = RegistryHelper.validate_service_operation(operation, op_name, "tier2")
            errors.extend([f"Service '{service_def.service_name}': {error}" for error in op_errors])
        
        return errors
    
    @staticmethod
    def validate_service_operation(operation: ServiceOperation, op_name: str = None, tier: str = None) -> List[str]:
        """
        Validate a service operation
        
        Args:
            operation: ServiceOperation to validate
            op_name: Expected operation name (optional)
            tier: Operation tier (optional)
            
        Returns:
            List of validation errors
        """
        errors = []
        
        # Endpoint validation
        if not operation.endpoint:
            errors.append(f"Operation '{op_name}' missing endpoint")
        else:
            endpoint_errors = RegistryHelper.validate_api_endpoint(operation.endpoint)
            errors.extend([f"Operation '{op_name}': {error}" for error in endpoint_errors])
        
        # Intent validation
        if not operation.intent_verbs:
            errors.append(f"Operation '{op_name}' missing intent verbs")
        
        if not operation.intent_objects:
            errors.append(f"Operation '{op_name}' missing intent objects")
        
        # Confidence score validation
        if not (0.0 <= operation.confidence_score <= 1.0):
            errors.append(f"Operation '{op_name}' has invalid confidence score: {operation.confidence_score}")
        
        return errors
    
    @staticmethod
    def validate_api_endpoint(endpoint: APIEndpoint) -> List[str]:
        """
        Validate an API endpoint
        
        Args:
            endpoint: APIEndpoint to validate
            
        Returns:
            List of validation errors
        """
        errors = []
        
        if not endpoint.path:
            errors.append("Endpoint path is required")
        
        if not endpoint.method:
            errors.append("Endpoint method is required")
        
        if not endpoint.operation_id:
            errors.append("Endpoint operation_id is required")
        
        # Path validation
        if endpoint.path and not endpoint.path.startswith('/'):
            errors.append(f"Endpoint path should start with '/': {endpoint.path}")
        
        # Method validation
        valid_methods = {'GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'HEAD', 'OPTIONS'}
        if endpoint.method and endpoint.method.upper() not in valid_methods:
            errors.append(f"Invalid HTTP method: {endpoint.method}")
        
        return errors
    
    @staticmethod
    def validate_cross_service_consistency(registry: ServiceRegistry) -> List[str]:
        """
        Validate consistency across services in a registry
        
        Args:
            registry: ServiceRegistry to validate
            
        Returns:
            List of cross-service validation errors
        """
        errors = []
        
        # Check for duplicate endpoint paths with same method
        endpoint_signatures = defaultdict(list)
        
        for service_name, service_def in registry.services.items():
            all_operations = {**service_def.tier1_operations, **service_def.tier2_operations}
            
            for op_name, operation in all_operations.items():
                if operation.endpoint:
                    signature = f"{operation.endpoint.method.upper()} {operation.endpoint.path}"
                    endpoint_signatures[signature].append((service_name, op_name))
        
        # Report duplicates
        for signature, occurrences in endpoint_signatures.items():
            if len(occurrences) > 1:
                services = [f"{service}:{op}" for service, op in occurrences]
                errors.append(f"Duplicate endpoint '{signature}' found in: {', '.join(services)}")
        
        # Check for keyword conflicts
        service_keywords = {}
        for service_name, service_def in registry.services.items():
            all_keywords = set(service_def.keywords + service_def.synonyms)
            service_keywords[service_name] = all_keywords
        
        # Find overlapping keywords
        for service1, keywords1 in service_keywords.items():
            for service2, keywords2 in service_keywords.items():
                if service1 < service2:  # Avoid duplicate comparisons
                    overlap = keywords1.intersection(keywords2)
                    if overlap:
                        errors.append(f"Keyword overlap between '{service1}' and '{service2}': {', '.join(overlap)}")
        
        return errors
    
    @staticmethod
    def merge_services(registry: ServiceRegistry, 
                      source_services: List[str], 
                      new_service_name: str,
                      new_service_description: str = None) -> ServiceRegistry:
        """
        Merge multiple services into a single service
        
        Args:
            registry: Source registry
            source_services: List of service names to merge
            new_service_name: Name for the merged service
            new_service_description: Description for the merged service
            
        Returns:
            New registry with merged service
        """
        if not source_services:
            raise ValueError("At least one source service is required")
        
        # Validate source services exist
        missing_services = [svc for svc in source_services if svc not in registry.services]
        if missing_services:
            raise ValueError(f"Services not found: {', '.join(missing_services)}")
        
        # Collect all operations and metadata
        merged_tier1 = {}
        merged_tier2 = {}
        merged_keywords = set()
        merged_synonyms = set()
        merged_contexts = []
        
        for service_name in source_services:
            service_def = registry.services[service_name]
            
            # Merge operations (handle naming conflicts)
            for op_name, operation in service_def.tier1_operations.items():
                unique_name = f"{service_name}_{op_name}" if op_name in merged_tier1 else op_name
                merged_tier1[unique_name] = operation
            
            for op_name, operation in service_def.tier2_operations.items():
                unique_name = f"{service_name}_{op_name}" if op_name in merged_tier2 else op_name
                merged_tier2[unique_name] = operation
            
            # Merge metadata
            merged_keywords.update(service_def.keywords)
            merged_synonyms.update(service_def.synonyms)
            if service_def.business_context:
                merged_contexts.append(service_def.business_context)
        
        # Create merged service definition
        merged_description = new_service_description or f"Merged service from: {', '.join(source_services)}"
        merged_context = "; ".join(merged_contexts) if merged_contexts else "Merged service operations"
        
        merged_service = ServiceDefinition(
            service_name=new_service_name,
            service_description=merged_description,
            business_context=merged_context,
            keywords=list(merged_keywords),
            synonyms=list(merged_synonyms),
            tier1_operations=merged_tier1,
            tier2_operations=merged_tier2
        )
        
        # Create new registry
        new_services = {name: service for name, service in registry.services.items() 
                       if name not in source_services}
        new_services[new_service_name] = merged_service
        
        new_registry = ServiceRegistry(
            registry_id=RegistryHelper.create_registry_id(),
            version=registry.version,  # Consider incrementing
            created_timestamp=datetime.now(timezone.utc).isoformat(),
            last_updated=datetime.now(timezone.utc).isoformat(),
            services=new_services,
            total_services=len(new_services)
        )
        
        return new_registry
    
    @staticmethod
    def split_service(registry: ServiceRegistry,
                     source_service: str,
                     split_config: Dict[str, List[str]]) -> ServiceRegistry:
        """
        Split a service into multiple services
        
        Args:
            registry: Source registry
            source_service: Name of service to split
            split_config: Dict mapping new service names to operation lists
            
        Returns:
            New registry with split services
        """
        if source_service not in registry.services:
            raise ValueError(f"Service '{source_service}' not found")
        
        source_def = registry.services[source_service]
        all_operations = {**source_def.tier1_operations, **source_def.tier2_operations}
        
        # Validate all operations are accounted for
        assigned_ops = set()
        for ops in split_config.values():
            assigned_ops.update(ops)
        
        available_ops = set(all_operations.keys())
        if assigned_ops != available_ops:
            missing = available_ops - assigned_ops
            extra = assigned_ops - available_ops
            error_msg = ""
            if missing:
                error_msg += f"Missing operations: {', '.join(missing)}. "
            if extra:
                error_msg += f"Unknown operations: {', '.join(extra)}."
            raise ValueError(error_msg.strip())
        
        # Create new services
        new_services = {name: service for name, service in registry.services.items() 
                       if name != source_service}
        
        for new_service_name, operation_names in split_config.items():
            new_tier1 = {}
            new_tier2 = {}
            
            for op_name in operation_names:
                operation = all_operations[op_name]
                
                # Determine tier based on original placement
                if op_name in source_def.tier1_operations:
                    new_tier1[op_name] = operation
                else:
                    new_tier2[op_name] = operation
            
            # Create service definition
            new_service = ServiceDefinition(
                service_name=new_service_name,
                service_description=f"Split from {source_service}: {new_service_name}",
                business_context=f"Subset of {source_service} operations",
                keywords=source_def.keywords.copy(),  # Inherit keywords
                synonyms=source_def.synonyms.copy(),   # Inherit synonyms
                tier1_operations=new_tier1,
                tier2_operations=new_tier2
            )
            
            new_services[new_service_name] = new_service
        
        # Create new registry
        new_registry = ServiceRegistry(
            registry_id=RegistryHelper.create_registry_id(),
            version=registry.version,  # Consider incrementing
            created_timestamp=datetime.now(timezone.utc).isoformat(),
            last_updated=datetime.now(timezone.utc).isoformat(),
            services=new_services,
            total_services=len(new_services)
        )
        
        return new_registry
    
    @staticmethod
    def compare_registries(registry1: ServiceRegistry, 
                          registry2: ServiceRegistry) -> Dict[str, Any]:
        """
        Compare two service registries and report differences
        
        Args:
            registry1: First registry
            registry2: Second registry
            
        Returns:
            Dictionary with comparison results
        """
        comparison = {
            'added_services': [],
            'removed_services': [],
            'modified_services': [],
            'unchanged_services': [],
            'summary': {}
        }
        
        services1 = set(registry1.services.keys())
        services2 = set(registry2.services.keys())
        
        # Find added/removed services
        comparison['added_services'] = list(services2 - services1)
        comparison['removed_services'] = list(services1 - services2)
        
        # Compare common services
        common_services = services1.intersection(services2)
        
        for service_name in common_services:
            service1 = registry1.services[service_name]
            service2 = registry2.services[service_name]
            
            if RegistryHelper._services_equal(service1, service2):
                comparison['unchanged_services'].append(service_name)
            else:
                changes = RegistryHelper._compare_services(service1, service2)
                comparison['modified_services'].append({
                    'service_name': service_name,
                    'changes': changes
                })
        
        # Summary
        comparison['summary'] = {
            'total_services_before': len(services1),
            'total_services_after': len(services2),
            'services_added': len(comparison['added_services']),
            'services_removed': len(comparison['removed_services']),
            'services_modified': len(comparison['modified_services']),
            'services_unchanged': len(comparison['unchanged_services'])
        }
        
        return comparison
    
    @staticmethod
    def _services_equal(service1: ServiceDefinition, service2: ServiceDefinition) -> bool:
        """Check if two service definitions are equal"""
        # Compare basic fields
        if (service1.service_name != service2.service_name or
            service1.service_description != service2.service_description or
            service1.business_context != service2.business_context or
            set(service1.keywords) != set(service2.keywords) or
            set(service1.synonyms) != set(service2.synonyms)):
            return False
        
        # Compare operations
        if (set(service1.tier1_operations.keys()) != set(service2.tier1_operations.keys()) or
            set(service1.tier2_operations.keys()) != set(service2.tier2_operations.keys())):
            return False
        
        # Deep comparison of operations would require more complex logic
        # For now, we'll consider services different if operation sets differ
        return True
    
    @staticmethod
    def _compare_services(service1: ServiceDefinition, service2: ServiceDefinition) -> Dict[str, Any]:
        """Compare two service definitions and return changes"""
        changes = {}
        
        if service1.service_description != service2.service_description:
            changes['description'] = {
                'before': service1.service_description,
                'after': service2.service_description
            }
        
        if service1.business_context != service2.business_context:
            changes['business_context'] = {
                'before': service1.business_context,
                'after': service2.business_context
            }
        
        keywords1 = set(service1.keywords)
        keywords2 = set(service2.keywords)
        if keywords1 != keywords2:
            changes['keywords'] = {
                'added': list(keywords2 - keywords1),
                'removed': list(keywords1 - keywords2)
            }
        
        synonyms1 = set(service1.synonyms)
        synonyms2 = set(service2.synonyms)
        if synonyms1 != synonyms2:
            changes['synonyms'] = {
                'added': list(synonyms2 - synonyms1),
                'removed': list(synonyms1 - synonyms2)
            }
        
        # Compare operations
        tier1_ops1 = set(service1.tier1_operations.keys())
        tier1_ops2 = set(service2.tier1_operations.keys())
        if tier1_ops1 != tier1_ops2:
            changes['tier1_operations'] = {
                'added': list(tier1_ops2 - tier1_ops1),
                'removed': list(tier1_ops1 - tier1_ops2)
            }
        
        tier2_ops1 = set(service1.tier2_operations.keys())
        tier2_ops2 = set(service2.tier2_operations.keys())
        if tier2_ops1 != tier2_ops2:
            changes['tier2_operations'] = {
                'added': list(tier2_ops2 - tier2_ops1),
                'removed': list(tier2_ops1 - tier2_ops2)
            }
        
        return changes
    
    @staticmethod
    def convert_raw_endpoint_to_api_endpoint(raw_endpoint: RawAPIEndpoint) -> APIEndpoint:
        """
        Convert RawAPIEndpoint to APIEndpoint
        
        Args:
            raw_endpoint: RawAPIEndpoint to convert
            
        Returns:
            Converted APIEndpoint
        """
        # Convert parameters list to dict (if parameters exist)
        param_dict = {}
        if raw_endpoint.parameters:
            for param in raw_endpoint.parameters:
                # Handle both dict and APIParameter objects
                if hasattr(param, 'name'):
                    # APIParameter object
                    param_dict[param.name] = {
                        'name': param.name,
                        'location': param.location.value if hasattr(param.location, 'value') else str(param.location),
                        'type': param.type,
                        'required': param.required,
                        'description': getattr(param, 'description', None)
                    }
                elif isinstance(param, dict) and 'name' in param:
                    # Dict format
                    param_dict[param['name']] = param
        
        return APIEndpoint(
            path=raw_endpoint.path,
            method=raw_endpoint.method.value if isinstance(raw_endpoint.method, HTTPMethod) else raw_endpoint.method,
            operation_id=raw_endpoint.operation_id,
            description=raw_endpoint.summary or raw_endpoint.operation_id,
            parameters=param_dict
        )
    
    @staticmethod
    def extract_service_statistics(registry: ServiceRegistry) -> Dict[str, Any]:
        """
        Extract comprehensive statistics from a service registry
        
        Args:
            registry: ServiceRegistry to analyze
            
        Returns:
            Dictionary with registry statistics
        """
        stats = {
            'registry_info': {
                'registry_id': registry.registry_id,
                'version': registry.version,
                'created': registry.created_timestamp,
                'last_updated': registry.last_updated,
                'total_services': registry.total_services
            },
            'service_statistics': {
                'total_services': len(registry.services),
                'total_tier1_operations': 0,
                'total_tier2_operations': 0,
                'total_operations': 0,
                'avg_operations_per_service': 0
            },
            'operation_types': defaultdict(int),
            'http_methods': defaultdict(int),
            'keywords': defaultdict(int),
            'service_details': []
        }
        
        total_tier1 = 0
        total_tier2 = 0
        
        for service_name, service_def in registry.services.items():
            tier1_count = len(service_def.tier1_operations)
            tier2_count = len(service_def.tier2_operations)
            total_ops = tier1_count + tier2_count
            
            total_tier1 += tier1_count
            total_tier2 += tier2_count
            
            # Service details
            service_detail = {
                'service_name': service_name,
                'description': service_def.service_description,
                'tier1_operations': tier1_count,
                'tier2_operations': tier2_count,
                'total_operations': total_ops,
                'keywords_count': len(service_def.keywords),
                'synonyms_count': len(service_def.synonyms)
            }
            stats['service_details'].append(service_detail)
            
            # Count keywords
            for keyword in service_def.keywords:
                stats['keywords'][keyword] += 1
            
            # Count HTTP methods and operation types
            all_operations = {**service_def.tier1_operations, **service_def.tier2_operations}
            for operation in all_operations.values():
                if operation.endpoint:
                    stats['http_methods'][operation.endpoint.method.upper()] += 1
        
        # Update totals
        stats['service_statistics']['total_tier1_operations'] = total_tier1
        stats['service_statistics']['total_tier2_operations'] = total_tier2
        stats['service_statistics']['total_operations'] = total_tier1 + total_tier2
        
        if registry.total_services > 0:
            stats['service_statistics']['avg_operations_per_service'] = (
                stats['service_statistics']['total_operations'] / registry.total_services
            )
        
        return stats


# Global instance for easy access
registry_helper = RegistryHelper()


# Convenience functions
def validate_registry(registry: ServiceRegistry) -> List[str]:
    """Validate registry using global helper"""
    return registry_helper.validate_registry(registry)


def merge_services(registry: ServiceRegistry, 
                  source_services: List[str], 
                  new_service_name: str,
                  new_service_description: str = None) -> ServiceRegistry:
    """Merge services using global helper"""
    return registry_helper.merge_services(registry, source_services, new_service_name, new_service_description)


def split_service(registry: ServiceRegistry,
                 source_service: str,
                 split_config: Dict[str, List[str]]) -> ServiceRegistry:
    """Split service using global helper"""
    return registry_helper.split_service(registry, source_service, split_config)


def compare_registries(registry1: ServiceRegistry, registry2: ServiceRegistry) -> Dict[str, Any]:
    """Compare registries using global helper"""
    return registry_helper.compare_registries(registry1, registry2)


def extract_service_statistics(registry: ServiceRegistry) -> Dict[str, Any]:
    """Extract statistics using global helper"""
    return registry_helper.extract_service_statistics(registry)