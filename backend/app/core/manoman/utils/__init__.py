"""
Man-O-Man Utilities Package

Utility modules for text processing, API client interaction, and registry management.
"""

from .text_processing import (
    TextProcessor,
    text_processor,
    normalize_text,
    clean_identifier,
    extract_keywords,
    calculate_text_similarity,
    suggest_service_name
)

from .registry_helpers import (
    RegistryHelper,
    registry_helper,
    validate_registry,
    merge_services,
    split_service,
    compare_registries,
    extract_service_statistics
)

from .infraon_api_client import (
    InfraonAPIClient,
    APIEndpoint,
    APITestResult,
    APIOperation,
    TestEntity
)

__all__ = [
    # Text Processing
    'TextProcessor',
    'text_processor',
    'normalize_text',
    'clean_identifier',
    'extract_keywords',
    'calculate_text_similarity',
    'suggest_service_name',
    
    # Registry Helpers
    'RegistryHelper',
    'registry_helper',
    'validate_registry',
    'merge_services',
    'split_service',
    'compare_registries',
    'extract_service_statistics',
    
    # API Client
    'InfraonAPIClient',
    'APIEndpoint',
    'APITestResult',
    'APIOperation',
    'TestEntity'
]