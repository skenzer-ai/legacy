"""
Registry Manager Storage

Manages service registry storage, versioning, and CRUD operations with support 
for atomic updates and rollback capabilities. Provides persistent storage for
the service registry with JSON-based serialization and file-based versioning.
"""

import json
import logging
import asyncio
from pathlib import Path
from typing import Dict, List, Optional, Any, Set
from datetime import datetime
import uuid
import shutil

from ..models.service_registry import (
    ServiceRegistry,
    ServiceDefinition,
    ServiceOperation,
    ConflictReport
)
from ..engines.conflict_detector import ConflictDetector

logger = logging.getLogger(__name__)


class RegistryManagerError(Exception):
    """Custom exception for registry manager errors"""
    pass


class RegistryManager:
    """
    Manages service registry storage, versioning, and CRUD operations
    with support for atomic updates and rollback capabilities.
    """
    
    def __init__(self, storage_path: str = "app/core/manoman/storage/data/service_registry/"):
        self.storage_path = Path(storage_path)
        self.current_registry: Optional[ServiceRegistry] = None
        self.conflict_detector = ConflictDetector()
        
        # Ensure storage directory exists
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self.versions_path = self.storage_path / "versions"
        self.versions_path.mkdir(exist_ok=True)
        self.backups_path = self.storage_path / "backups"
        self.backups_path.mkdir(exist_ok=True)
        
        # Registry metadata
        self.registry_file = self.storage_path / "current_registry.json"
        self.metadata_file = self.storage_path / "registry_metadata.json"
        
        logger.info(f"RegistryManager initialized with storage path: {self.storage_path}")
    
    async def load_registry(self, version: str = "latest") -> ServiceRegistry:
        """
        Load service registry from storage
        
        Args:
            version: Registry version to load ("latest" for current version)
            
        Returns:
            ServiceRegistry object
            
        Raises:
            RegistryManagerError: If loading fails
        """
        try:
            if version == "latest":
                registry_path = self.registry_file
            else:
                registry_path = self.versions_path / f"registry_v{version}.json"
            
            if not registry_path.exists():
                # Create new empty registry if none exists
                if version == "latest":
                    logger.info("No existing registry found, creating new empty registry")
                    return self._create_empty_registry()
                else:
                    raise RegistryManagerError(f"Registry version {version} not found")
            
            # Load registry from file
            with open(registry_path, 'r', encoding='utf-8') as f:
                registry_data = json.load(f)
            
            # Parse into ServiceRegistry object
            registry = ServiceRegistry.parse_obj(registry_data)
            
            # Cache current registry if loading latest
            if version == "latest":
                self.current_registry = registry
            
            logger.info(f"Successfully loaded registry version {registry.version} with {len(registry.services)} services")
            return registry
            
        except Exception as e:
            error_msg = f"Failed to load registry version {version}: {str(e)}"
            logger.error(error_msg)
            raise RegistryManagerError(error_msg)
    
    async def save_registry(self, registry: ServiceRegistry, version: str = None) -> str:
        """
        Save registry with automatic versioning
        
        Args:
            registry: ServiceRegistry to save
            version: Optional version override
            
        Returns:
            Version string of saved registry
            
        Raises:
            RegistryManagerError: If saving fails
        """
        try:
            # Generate version if not provided
            if version is None:
                version = self._generate_version()
            
            # Update registry metadata
            registry.version = version
            registry.last_updated = datetime.utcnow().isoformat()
            registry.total_services = len(registry.services)
            
            # Create backup of current registry if it exists
            if self.registry_file.exists():
                await self._create_backup(self.current_registry)
            
            # Save to versioned file
            version_file = self.versions_path / f"registry_v{version}.json"
            with open(version_file, 'w', encoding='utf-8') as f:
                json.dump(registry.dict(), f, indent=2, ensure_ascii=False, default=str)
            
            # Update current registry file
            with open(self.registry_file, 'w', encoding='utf-8') as f:
                json.dump(registry.dict(), f, indent=2, ensure_ascii=False, default=str)
            
            # Update metadata
            await self._update_metadata(registry)
            
            # Cache current registry
            self.current_registry = registry
            
            logger.info(f"Successfully saved registry version {version} with {len(registry.services)} services")
            return version
            
        except Exception as e:
            error_msg = f"Failed to save registry: {str(e)}"
            logger.error(error_msg)
            raise RegistryManagerError(error_msg)
    
    async def add_service(self, service_name: str, service_def: ServiceDefinition) -> bool:
        """
        Add new service to registry with conflict checking
        
        Args:
            service_name: Unique service identifier
            service_def: Service definition object
            
        Returns:
            True if service was added successfully
            
        Raises:
            RegistryManagerError: If addition fails or conflicts detected
        """
        try:
            # Load current registry
            if self.current_registry is None:
                self.current_registry = await self.load_registry()
            
            # Check if service already exists
            if service_name in self.current_registry.services:
                raise RegistryManagerError(f"Service '{service_name}' already exists in registry")
            
            # Create temporary registry with new service for conflict checking
            temp_registry = ServiceRegistry(
                registry_id=self.current_registry.registry_id,
                version=self.current_registry.version,
                created_timestamp=self.current_registry.created_timestamp,
                last_updated=datetime.utcnow().isoformat(),
                services={**self.current_registry.services, service_name: service_def},
                total_services=len(self.current_registry.services) + 1,
                confidence_threshold=self.current_registry.confidence_threshold
            )
            
            # Check for conflicts
            conflicts = await self.conflict_detector.detect_conflicts(temp_registry)
            high_severity_conflicts = [c for c in conflicts if c.severity.value == "high"]
            
            if high_severity_conflicts:
                conflict_descriptions = [c.description for c in high_severity_conflicts]
                raise RegistryManagerError(f"Cannot add service due to high-severity conflicts: {conflict_descriptions}")
            
            # Add service to current registry
            self.current_registry.services[service_name] = service_def
            self.current_registry.total_services = len(self.current_registry.services)
            self.current_registry.update_timestamp()
            
            # Save updated registry
            await self.save_registry(self.current_registry)
            
            logger.info(f"Successfully added service '{service_name}' to registry")
            return True
            
        except Exception as e:
            error_msg = f"Failed to add service '{service_name}': {str(e)}"
            logger.error(error_msg)
            raise RegistryManagerError(error_msg)
    
    async def update_service(self, service_name: str, updates: Dict[str, Any]) -> bool:
        """
        Update existing service definition
        
        Args:
            service_name: Service to update
            updates: Dictionary of field updates
            
        Returns:
            True if service was updated successfully
            
        Raises:
            RegistryManagerError: If update fails
        """
        try:
            # Load current registry
            if self.current_registry is None:
                self.current_registry = await self.load_registry()
            
            # Check if service exists
            if service_name not in self.current_registry.services:
                raise RegistryManagerError(f"Service '{service_name}' not found in registry")
            
            # Get current service definition
            current_service = self.current_registry.services[service_name]
            
            # Apply updates
            updated_data = current_service.dict()
            for field, value in updates.items():
                if field not in updated_data:
                    raise RegistryManagerError(f"Invalid field '{field}' for service update")
                updated_data[field] = value
            
            # Create updated service definition
            updated_service = ServiceDefinition.parse_obj(updated_data)
            
            # Create temporary registry for conflict checking
            temp_services = self.current_registry.services.copy()
            temp_services[service_name] = updated_service
            
            temp_registry = ServiceRegistry(
                registry_id=self.current_registry.registry_id,
                version=self.current_registry.version,
                created_timestamp=self.current_registry.created_timestamp,
                last_updated=datetime.utcnow().isoformat(),
                services=temp_services,
                total_services=len(temp_services),
                confidence_threshold=self.current_registry.confidence_threshold
            )
            
            # Check for conflicts
            conflicts = await self.conflict_detector.detect_conflicts(temp_registry)
            high_severity_conflicts = [c for c in conflicts if c.severity.value == "high"]
            
            if high_severity_conflicts:
                conflict_descriptions = [c.description for c in high_severity_conflicts]
                logger.warning(f"Service update introduces conflicts: {conflict_descriptions}")
                # Continue with update but log warnings
            
            # Update service in current registry
            self.current_registry.services[service_name] = updated_service
            self.current_registry.update_timestamp()
            
            # Save updated registry
            await self.save_registry(self.current_registry)
            
            logger.info(f"Successfully updated service '{service_name}'")
            return True
            
        except Exception as e:
            error_msg = f"Failed to update service '{service_name}': {str(e)}"
            logger.error(error_msg)
            raise RegistryManagerError(error_msg)
    
    async def delete_service(self, service_name: str) -> bool:
        """
        Remove service from registry
        
        Args:
            service_name: Service to remove
            
        Returns:
            True if service was removed successfully
            
        Raises:
            RegistryManagerError: If deletion fails
        """
        try:
            # Load current registry
            if self.current_registry is None:
                self.current_registry = await self.load_registry()
            
            # Check if service exists
            if service_name not in self.current_registry.services:
                raise RegistryManagerError(f"Service '{service_name}' not found in registry")
            
            # Remove service
            del self.current_registry.services[service_name]
            self.current_registry.total_services = len(self.current_registry.services)
            self.current_registry.update_timestamp()
            
            # Save updated registry
            await self.save_registry(self.current_registry)
            
            logger.info(f"Successfully deleted service '{service_name}' from registry")
            return True
            
        except Exception as e:
            error_msg = f"Failed to delete service '{service_name}': {str(e)}"
            logger.error(error_msg)
            raise RegistryManagerError(error_msg)
    
    async def merge_services(self, service_names: List[str], new_service_name: str, merge_strategy: str = "combine_all") -> bool:
        """
        Combine multiple services into one
        
        Args:
            service_names: List of services to merge
            new_service_name: Name for the merged service
            merge_strategy: Strategy for merging ("combine_all", "prefer_first")
            
        Returns:
            True if services were merged successfully
            
        Raises:
            RegistryManagerError: If merge fails
        """
        try:
            # Load current registry
            if self.current_registry is None:
                self.current_registry = await self.load_registry()
            
            # Validate all services exist
            for service_name in service_names:
                if service_name not in self.current_registry.services:
                    raise RegistryManagerError(f"Service '{service_name}' not found in registry")
            
            # Check if new service name conflicts
            if new_service_name in self.current_registry.services and new_service_name not in service_names:
                raise RegistryManagerError(f"Target service name '{new_service_name}' already exists")
            
            # Get services to merge
            services_to_merge = [self.current_registry.services[name] for name in service_names]
            
            # Create merged service based on strategy
            merged_service = self._merge_service_definitions(services_to_merge, new_service_name, merge_strategy)
            
            # Remove old services and add merged service
            for service_name in service_names:
                if service_name != new_service_name:  # Don't delete if we're using an existing name
                    del self.current_registry.services[service_name]
            
            self.current_registry.services[new_service_name] = merged_service
            self.current_registry.total_services = len(self.current_registry.services)
            self.current_registry.update_timestamp()
            
            # Save updated registry
            await self.save_registry(self.current_registry)
            
            logger.info(f"Successfully merged {len(service_names)} services into '{new_service_name}'")
            return True
            
        except Exception as e:
            error_msg = f"Failed to merge services: {str(e)}"
            logger.error(error_msg)
            raise RegistryManagerError(error_msg)
    
    async def split_service(self, service_name: str, split_config: Dict[str, List[str]]) -> bool:
        """
        Split one service into multiple services
        
        Args:
            service_name: Service to split
            split_config: Maps new service names to lists of operation IDs
            
        Returns:
            True if service was split successfully
            
        Raises:
            RegistryManagerError: If split fails
        """
        try:
            # Load current registry
            if self.current_registry is None:
                self.current_registry = await self.load_registry()
            
            # Check if service exists
            if service_name not in self.current_registry.services:
                raise RegistryManagerError(f"Service '{service_name}' not found in registry")
            
            original_service = self.current_registry.services[service_name]
            
            # Validate split configuration
            all_operations = set(original_service.tier1_operations.keys()) | set(original_service.tier2_operations.keys())
            split_operations = set()
            for ops in split_config.values():
                split_operations.update(ops)
            
            if split_operations != all_operations:
                missing = all_operations - split_operations
                extra = split_operations - all_operations
                raise RegistryManagerError(f"Split config mismatch - Missing: {missing}, Extra: {extra}")
            
            # Create new services
            new_services = {}
            for new_name, operation_ids in split_config.items():
                new_service = self._create_split_service(original_service, new_name, operation_ids)
                new_services[new_name] = new_service
            
            # Remove original service and add new services
            del self.current_registry.services[service_name]
            self.current_registry.services.update(new_services)
            self.current_registry.total_services = len(self.current_registry.services)
            self.current_registry.update_timestamp()
            
            # Save updated registry
            await self.save_registry(self.current_registry)
            
            logger.info(f"Successfully split service '{service_name}' into {len(new_services)} services")
            return True
            
        except Exception as e:
            error_msg = f"Failed to split service '{service_name}': {str(e)}"
            logger.error(error_msg)
            raise RegistryManagerError(error_msg)
    
    async def get_registry_versions(self) -> List[str]:
        """Get list of available registry versions"""
        try:
            versions = []
            for version_file in self.versions_path.glob("registry_v*.json"):
                version = version_file.stem.replace("registry_v", "")
                versions.append(version)
            
            # Sort versions by creation time
            versions.sort(reverse=True)
            return versions
            
        except Exception as e:
            logger.error(f"Failed to get registry versions: {str(e)}")
            return []
    
    async def rollback_to_version(self, version: str) -> bool:
        """
        Rollback registry to a previous version
        
        Args:
            version: Version to rollback to
            
        Returns:
            True if rollback was successful
        """
        try:
            # Load the target version
            target_registry = await self.load_registry(version)
            
            # Save as current version
            await self.save_registry(target_registry)
            
            logger.info(f"Successfully rolled back registry to version {version}")
            return True
            
        except Exception as e:
            error_msg = f"Failed to rollback to version {version}: {str(e)}"
            logger.error(error_msg)
            raise RegistryManagerError(error_msg)
    
    def _create_empty_registry(self) -> ServiceRegistry:
        """Create a new empty service registry"""
        return ServiceRegistry(
            registry_id=str(uuid.uuid4()),
            version="1.0.0",
            created_timestamp=datetime.utcnow().isoformat(),
            last_updated=datetime.utcnow().isoformat(),
            services={},
            total_services=0,
            confidence_threshold=0.7
        )
    
    def _generate_version(self) -> str:
        """Generate new version string"""
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        return f"v{timestamp}"
    
    async def _create_backup(self, registry: ServiceRegistry) -> str:
        """Create backup of registry"""
        if registry is None:
            return ""
        
        try:
            backup_id = f"backup_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
            backup_file = self.backups_path / f"{backup_id}.json"
            
            with open(backup_file, 'w', encoding='utf-8') as f:
                json.dump(registry.dict(), f, indent=2, ensure_ascii=False, default=str)
            
            logger.debug(f"Created backup: {backup_id}")
            return backup_id
            
        except Exception as e:
            logger.warning(f"Failed to create backup: {str(e)}")
            return ""
    
    async def _update_metadata(self, registry: ServiceRegistry):
        """Update registry metadata file"""
        try:
            metadata = {
                "current_version": registry.version,
                "last_updated": registry.last_updated,
                "total_services": registry.total_services,
                "registry_id": registry.registry_id,
                "created_timestamp": registry.created_timestamp
            }
            
            with open(self.metadata_file, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2)
                
        except Exception as e:
            logger.warning(f"Failed to update metadata: {str(e)}")
    
    def _merge_service_definitions(self, services: List[ServiceDefinition], new_name: str, strategy: str) -> ServiceDefinition:
        """Merge multiple service definitions into one"""
        if not services:
            raise RegistryManagerError("No services provided for merging")
        
        if strategy == "prefer_first":
            base_service = services[0]
            # Use first service as base, combine operations from others
            combined_tier1 = dict(base_service.tier1_operations)
            combined_tier2 = dict(base_service.tier2_operations)
            combined_keywords = list(base_service.keywords)
            combined_synonyms = list(base_service.synonyms)
            
            for service in services[1:]:
                combined_tier1.update(service.tier1_operations)
                combined_tier2.update(service.tier2_operations)
                combined_keywords.extend(service.keywords)
                combined_synonyms.extend(service.synonyms)
            
            return ServiceDefinition(
                service_name=new_name,
                service_description=base_service.service_description,
                business_context=base_service.business_context,
                keywords=list(set(combined_keywords)),
                synonyms=list(set(combined_synonyms)),
                tier1_operations=combined_tier1,
                tier2_operations=combined_tier2
            )
        
        else:  # combine_all strategy
            # Combine all aspects from all services
            all_descriptions = [s.service_description for s in services]
            all_contexts = [s.business_context for s in services]
            all_keywords = []
            all_synonyms = []
            combined_tier1 = {}
            combined_tier2 = {}
            
            for service in services:
                all_keywords.extend(service.keywords)
                all_synonyms.extend(service.synonyms)
                combined_tier1.update(service.tier1_operations)
                combined_tier2.update(service.tier2_operations)
            
            return ServiceDefinition(
                service_name=new_name,
                service_description=f"Merged service combining: {', '.join(all_descriptions)}",
                business_context=f"Combined business context: {' | '.join(all_contexts)}",
                keywords=list(set(all_keywords)),
                synonyms=list(set(all_synonyms)),
                tier1_operations=combined_tier1,
                tier2_operations=combined_tier2
            )
    
    def _create_split_service(self, original: ServiceDefinition, new_name: str, operation_ids: List[str]) -> ServiceDefinition:
        """Create a new service from split operations"""
        # Filter operations for this split
        new_tier1 = {op_id: op for op_id, op in original.tier1_operations.items() if op_id in operation_ids}
        new_tier2 = {op_id: op for op_id, op in original.tier2_operations.items() if op_id in operation_ids}
        
        # Create contextual description based on operations
        operation_types = list(new_tier1.keys()) + list(new_tier2.keys())
        
        return ServiceDefinition(
            service_name=new_name,
            service_description=f"Split from {original.service_name} - handles {', '.join(operation_types[:3])}{'...' if len(operation_types) > 3 else ''}",
            business_context=f"Specialized subset of {original.service_name}: {original.business_context}",
            keywords=original.keywords,  # Inherit keywords
            synonyms=original.synonyms,  # Inherit synonyms
            tier1_operations=new_tier1,
            tier2_operations=new_tier2
        )
    
    async def get_registry_stats(self) -> Dict[str, Any]:
        """Get comprehensive registry statistics"""
        try:
            if self.current_registry is None:
                self.current_registry = await self.load_registry()
            
            # Basic stats
            total_services = len(self.current_registry.services)
            total_tier1_ops = sum(len(service.tier1_operations) for service in self.current_registry.services.values())
            total_tier2_ops = sum(len(service.tier2_operations) for service in self.current_registry.services.values())
            
            # Version info
            versions = await self.get_registry_versions()
            
            # Storage info
            registry_size = self.registry_file.stat().st_size if self.registry_file.exists() else 0
            
            return {
                "total_services": total_services,
                "total_tier1_operations": total_tier1_ops,
                "total_tier2_operations": total_tier2_ops,
                "total_operations": total_tier1_ops + total_tier2_ops,
                "current_version": self.current_registry.version,
                "available_versions": len(versions),
                "registry_size_bytes": registry_size,
                "last_updated": self.current_registry.last_updated,
                "storage_path": str(self.storage_path)
            }
            
        except Exception as e:
            logger.error(f"Failed to get registry stats: {str(e)}")
            return {}
    
    def _validate_registry_integrity(self, registry: ServiceRegistry) -> List[str]:
        """Validate registry for consistency and conflicts"""
        issues = []
        
        # Check for duplicate service names
        service_names = list(registry.services.keys())
        if len(service_names) != len(set(service_names)):
            issues.append("Duplicate service names detected")
        
        # Check service definitions
        for service_name, service_def in registry.services.items():
            if not service_def.service_name:
                issues.append(f"Service {service_name} has empty service_name")
            
            if not service_def.service_description:
                issues.append(f"Service {service_name} has empty description")
            
            # Check for operation ID conflicts within service
            all_op_ids = list(service_def.tier1_operations.keys()) + list(service_def.tier2_operations.keys())
            if len(all_op_ids) != len(set(all_op_ids)):
                issues.append(f"Service {service_name} has duplicate operation IDs")
        
        return issues