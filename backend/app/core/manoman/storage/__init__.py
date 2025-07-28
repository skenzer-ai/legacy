"""
Man-O-Man Storage Management

Contains storage and persistence components for the service registry:
- Registry Manager: CRUD operations and versioning for service registry
- Version Control: Registry versioning and history management
"""

from .registry_manager import RegistryManager, RegistryManagerError

__all__ = [
    "RegistryManager",
    "RegistryManagerError"
]