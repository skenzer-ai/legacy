"""
Version Control System

Enhanced versioning capabilities for service registry including change tracking,
diff generation, branch management, and comprehensive version history analysis.
Extends the basic versioning provided by RegistryManager.
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any, Set, Tuple
from datetime import datetime
from dataclasses import dataclass
from enum import Enum

from ..models.service_registry import (
    ServiceRegistry,
    ServiceDefinition,
    ServiceOperation
)

logger = logging.getLogger(__name__)


class ChangeType(str, Enum):
    """Types of changes in version control"""
    SERVICE_ADDED = "service_added"
    SERVICE_DELETED = "service_deleted"
    SERVICE_MODIFIED = "service_modified"
    OPERATION_ADDED = "operation_added"
    OPERATION_DELETED = "operation_deleted"
    OPERATION_MODIFIED = "operation_modified"
    METADATA_CHANGED = "metadata_changed"


@dataclass
class VersionChange:
    """Represents a single change in a version"""
    change_type: ChangeType
    target: str  # Service name, operation ID, etc.
    old_value: Optional[Any] = None
    new_value: Optional[Any] = None
    description: str = ""


@dataclass
class VersionInfo:
    """Comprehensive version information"""
    version: str
    timestamp: str
    changes: List[VersionChange]
    total_services: int
    total_operations: int
    author: str = "system"
    message: str = ""
    parent_version: Optional[str] = None


class VersionControlError(Exception):
    """Custom exception for version control errors"""
    pass


class VersionControl:
    """
    Enhanced version control system for service registry with change tracking,
    diff generation, and comprehensive version history management.
    """
    
    def __init__(self, storage_path: str = "processed_data/service_registry/"):
        self.storage_path = Path(storage_path)
        self.versions_path = self.storage_path / "versions"
        self.history_path = self.storage_path / "history"
        self.branches_path = self.storage_path / "branches"
        
        # Ensure directories exist
        self.history_path.mkdir(parents=True, exist_ok=True)
        self.branches_path.mkdir(parents=True, exist_ok=True)
        
        # Version control metadata
        self.history_file = self.history_path / "version_history.json"
        self.branches_file = self.branches_path / "branches.json"
        
        logger.info(f"VersionControl initialized with storage path: {self.storage_path}")
    
    async def analyze_changes(self, old_registry: ServiceRegistry, new_registry: ServiceRegistry) -> List[VersionChange]:
        """
        Analyze changes between two registry versions
        
        Args:
            old_registry: Previous version of registry
            new_registry: New version of registry
            
        Returns:
            List of detected changes
        """
        changes = []
        
        try:
            # Compare service-level changes
            old_services = set(old_registry.services.keys())
            new_services = set(new_registry.services.keys())
            
            # Detect added services
            added_services = new_services - old_services
            for service_name in added_services:
                changes.append(VersionChange(
                    change_type=ChangeType.SERVICE_ADDED,
                    target=service_name,
                    new_value=new_registry.services[service_name].dict(),
                    description=f"Added service '{service_name}'"
                ))
            
            # Detect deleted services
            deleted_services = old_services - new_services
            for service_name in deleted_services:
                changes.append(VersionChange(
                    change_type=ChangeType.SERVICE_DELETED,
                    target=service_name,
                    old_value=old_registry.services[service_name].dict(),
                    description=f"Deleted service '{service_name}'"
                ))
            
            # Detect modified services
            common_services = old_services & new_services
            for service_name in common_services:
                service_changes = self._compare_services(
                    old_registry.services[service_name],
                    new_registry.services[service_name],
                    service_name
                )
                changes.extend(service_changes)
            
            # Compare registry metadata
            metadata_changes = self._compare_metadata(old_registry, new_registry)
            changes.extend(metadata_changes)
            
            logger.info(f"Analyzed {len(changes)} changes between versions")
            return changes
            
        except Exception as e:
            error_msg = f"Failed to analyze changes: {str(e)}"
            logger.error(error_msg)
            raise VersionControlError(error_msg)
    
    async def create_version_info(self, registry: ServiceRegistry, changes: List[VersionChange], 
                                message: str = "", author: str = "system", 
                                parent_version: Optional[str] = None) -> VersionInfo:
        """
        Create comprehensive version information
        
        Args:
            registry: Registry version
            changes: List of changes in this version
            message: Commit message
            author: Version author
            parent_version: Previous version
            
        Returns:
            VersionInfo object
        """
        total_operations = sum(
            len(service.tier1_operations) + len(service.tier2_operations)
            for service in registry.services.values()
        )
        
        return VersionInfo(
            version=registry.version,
            timestamp=registry.last_updated,
            changes=changes,
            total_services=len(registry.services),
            total_operations=total_operations,
            author=author,
            message=message,
            parent_version=parent_version
        )
    
    async def save_version_history(self, version_info: VersionInfo):
        """
        Save version history to persistent storage
        
        Args:
            version_info: Version information to save
        """
        try:
            # Load existing history
            history = await self._load_version_history()
            
            # Add new version
            history[version_info.version] = {
                "timestamp": version_info.timestamp,
                "author": version_info.author,
                "message": version_info.message,
                "parent_version": version_info.parent_version,
                "total_services": version_info.total_services,
                "total_operations": version_info.total_operations,
                "change_count": len(version_info.changes),
                "changes": [
                    {
                        "change_type": change.change_type.value,
                        "target": change.target,
                        "description": change.description,
                        "old_value": change.old_value,
                        "new_value": change.new_value
                    }
                    for change in version_info.changes
                ]
            }
            
            # Save updated history
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump(history, f, indent=2, ensure_ascii=False, default=str)
            
            logger.info(f"Saved version history for {version_info.version}")
            
        except Exception as e:
            error_msg = f"Failed to save version history: {str(e)}"
            logger.error(error_msg)
            raise VersionControlError(error_msg)
    
    async def get_version_history(self, limit: Optional[int] = None) -> List[VersionInfo]:
        """
        Get version history with optional limit
        
        Args:
            limit: Maximum number of versions to return
            
        Returns:
            List of version information ordered by timestamp (newest first)
        """
        try:
            history = await self._load_version_history()
            
            # Convert to VersionInfo objects
            version_infos = []
            for version, data in history.items():
                changes = [
                    VersionChange(
                        change_type=ChangeType(change_data["change_type"]),
                        target=change_data["target"],
                        old_value=change_data.get("old_value"),
                        new_value=change_data.get("new_value"),
                        description=change_data["description"]
                    )
                    for change_data in data.get("changes", [])
                ]
                
                version_info = VersionInfo(
                    version=version,
                    timestamp=data["timestamp"],
                    changes=changes,
                    total_services=data["total_services"],
                    total_operations=data["total_operations"],
                    author=data.get("author", "system"),
                    message=data.get("message", ""),
                    parent_version=data.get("parent_version")
                )
                version_infos.append(version_info)
            
            # Sort by timestamp (newest first)
            version_infos.sort(key=lambda v: v.timestamp, reverse=True)
            
            # Apply limit if specified
            if limit:
                version_infos = version_infos[:limit]
            
            return version_infos
            
        except Exception as e:
            error_msg = f"Failed to get version history: {str(e)}"
            logger.error(error_msg)
            raise VersionControlError(error_msg)
    
    async def generate_diff_report(self, version1: str, version2: str) -> Dict[str, Any]:
        """
        Generate detailed diff report between two versions
        
        Args:
            version1: Earlier version
            version2: Later version
            
        Returns:
            Comprehensive diff report
        """
        try:
            history = await self._load_version_history()
            
            if version1 not in history or version2 not in history:
                raise VersionControlError(f"One or both versions not found: {version1}, {version2}")
            
            v1_data = history[version1]
            v2_data = history[version2]
            
            # Calculate differences
            services_diff = v2_data["total_services"] - v1_data["total_services"]
            operations_diff = v2_data["total_operations"] - v1_data["total_operations"]
            
            # Collect all changes between versions
            all_changes = []
            
            # Get version chain from v1 to v2
            version_chain = await self._get_version_chain(version1, version2, history)
            
            for version in version_chain:
                if version in history:
                    all_changes.extend(history[version].get("changes", []))
            
            # Categorize changes
            change_summary = {}
            for change in all_changes:
                change_type = change["change_type"]
                change_summary[change_type] = change_summary.get(change_type, 0) + 1
            
            return {
                "version_from": version1,
                "version_to": version2,
                "timestamp_from": v1_data["timestamp"],
                "timestamp_to": v2_data["timestamp"],
                "services_diff": services_diff,
                "operations_diff": operations_diff,
                "total_changes": len(all_changes),
                "change_summary": change_summary,
                "detailed_changes": all_changes
            }
            
        except Exception as e:
            error_msg = f"Failed to generate diff report: {str(e)}"
            logger.error(error_msg)
            raise VersionControlError(error_msg)
    
    async def get_version_statistics(self) -> Dict[str, Any]:
        """
        Get comprehensive version control statistics
        
        Returns:
            Dictionary with version control statistics
        """
        try:
            history = await self._load_version_history()
            
            if not history:
                return {
                    "total_versions": 0,
                    "earliest_version": None,
                    "latest_version": None,
                    "total_changes": 0,
                    "change_types": {},
                    "authors": {},
                    "version_frequency": {}
                }
            
            # Basic statistics
            total_versions = len(history)
            all_timestamps = [data["timestamp"] for data in history.values()]
            earliest_version = min(history.keys(), key=lambda v: history[v]["timestamp"])
            latest_version = max(history.keys(), key=lambda v: history[v]["timestamp"])
            
            # Change analysis
            total_changes = sum(data.get("change_count", 0) for data in history.values())
            change_types = {}
            authors = {}
            
            for data in history.values():
                # Author statistics
                author = data.get("author", "system")
                authors[author] = authors.get(author, 0) + 1
                
                # Change type statistics
                for change in data.get("changes", []):
                    change_type = change["change_type"]
                    change_types[change_type] = change_types.get(change_type, 0) + 1
            
            # Version frequency (by date)
            version_frequency = {}
            for data in history.values():
                date = data["timestamp"][:10]  # Extract date part
                version_frequency[date] = version_frequency.get(date, 0) + 1
            
            return {
                "total_versions": total_versions,
                "earliest_version": earliest_version,
                "latest_version": latest_version,
                "total_changes": total_changes,
                "change_types": change_types,
                "authors": authors,
                "version_frequency": version_frequency,
                "average_changes_per_version": total_changes / total_versions if total_versions > 0 else 0
            }
            
        except Exception as e:
            error_msg = f"Failed to get version statistics: {str(e)}"
            logger.error(error_msg)
            raise VersionControlError(error_msg)
    
    def _compare_services(self, old_service: ServiceDefinition, new_service: ServiceDefinition, 
                         service_name: str) -> List[VersionChange]:
        """Compare two service definitions and detect changes"""
        changes = []
        
        # Compare basic fields
        fields_to_compare = ['service_description', 'business_context', 'keywords', 'synonyms']
        
        for field in fields_to_compare:
            old_value = getattr(old_service, field)
            new_value = getattr(new_service, field)
            
            if old_value != new_value:
                changes.append(VersionChange(
                    change_type=ChangeType.SERVICE_MODIFIED,
                    target=f"{service_name}.{field}",
                    old_value=old_value,
                    new_value=new_value,
                    description=f"Modified {field} in service '{service_name}'"
                ))
        
        # Compare operations
        operation_changes = self._compare_operations(old_service, new_service, service_name)
        changes.extend(operation_changes)
        
        return changes
    
    def _compare_operations(self, old_service: ServiceDefinition, new_service: ServiceDefinition,
                           service_name: str) -> List[VersionChange]:
        """Compare operations between two service definitions"""
        changes = []
        
        # Compare tier1 operations
        old_tier1 = set(old_service.tier1_operations.keys())
        new_tier1 = set(new_service.tier1_operations.keys())
        
        # Added operations
        for op_id in new_tier1 - old_tier1:
            changes.append(VersionChange(
                change_type=ChangeType.OPERATION_ADDED,
                target=f"{service_name}.{op_id}",
                new_value=new_service.tier1_operations[op_id].dict(),
                description=f"Added tier1 operation '{op_id}' to service '{service_name}'"
            ))
        
        # Deleted operations
        for op_id in old_tier1 - new_tier1:
            changes.append(VersionChange(
                change_type=ChangeType.OPERATION_DELETED,
                target=f"{service_name}.{op_id}",
                old_value=old_service.tier1_operations[op_id].dict(),
                description=f"Deleted tier1 operation '{op_id}' from service '{service_name}'"
            ))
        
        # Modified operations
        for op_id in old_tier1 & new_tier1:
            old_op = old_service.tier1_operations[op_id]
            new_op = new_service.tier1_operations[op_id]
            
            if old_op.dict() != new_op.dict():
                changes.append(VersionChange(
                    change_type=ChangeType.OPERATION_MODIFIED,
                    target=f"{service_name}.{op_id}",
                    old_value=old_op.dict(),
                    new_value=new_op.dict(),
                    description=f"Modified tier1 operation '{op_id}' in service '{service_name}'"
                ))
        
        # Compare tier2 operations (similar logic)
        old_tier2 = set(old_service.tier2_operations.keys())
        new_tier2 = set(new_service.tier2_operations.keys())
        
        for op_id in new_tier2 - old_tier2:
            changes.append(VersionChange(
                change_type=ChangeType.OPERATION_ADDED,
                target=f"{service_name}.{op_id}",
                new_value=new_service.tier2_operations[op_id].dict(),
                description=f"Added tier2 operation '{op_id}' to service '{service_name}'"
            ))
        
        for op_id in old_tier2 - new_tier2:
            changes.append(VersionChange(
                change_type=ChangeType.OPERATION_DELETED,
                target=f"{service_name}.{op_id}",
                old_value=old_service.tier2_operations[op_id].dict(),
                description=f"Deleted tier2 operation '{op_id}' from service '{service_name}'"
            ))
        
        for op_id in old_tier2 & new_tier2:
            old_op = old_service.tier2_operations[op_id]
            new_op = new_service.tier2_operations[op_id]
            
            if old_op.dict() != new_op.dict():
                changes.append(VersionChange(
                    change_type=ChangeType.OPERATION_MODIFIED,
                    target=f"{service_name}.{op_id}",
                    old_value=old_op.dict(),
                    new_value=new_op.dict(),
                    description=f"Modified tier2 operation '{op_id}' in service '{service_name}'"
                ))
        
        return changes
    
    def _compare_metadata(self, old_registry: ServiceRegistry, new_registry: ServiceRegistry) -> List[VersionChange]:
        """Compare registry metadata"""
        changes = []
        
        metadata_fields = ['confidence_threshold']
        
        for field in metadata_fields:
            old_value = getattr(old_registry, field, None)
            new_value = getattr(new_registry, field, None)
            
            if old_value != new_value:
                changes.append(VersionChange(
                    change_type=ChangeType.METADATA_CHANGED,
                    target=f"registry.{field}",
                    old_value=old_value,
                    new_value=new_value,
                    description=f"Changed registry {field} from {old_value} to {new_value}"
                ))
        
        return changes
    
    async def _load_version_history(self) -> Dict[str, Any]:
        """Load version history from storage"""
        try:
            if not self.history_file.exists():
                return {}
            
            with open(self.history_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"Failed to load version history: {str(e)}")
            return {}
    
    async def _get_version_chain(self, version1: str, version2: str, history: Dict[str, Any]) -> List[str]:
        """Get ordered list of versions between two versions"""
        # Simple implementation - in practice, this would follow parent version chains
        # For now, return all versions between timestamps
        
        v1_timestamp = history[version1]["timestamp"]
        v2_timestamp = history[version2]["timestamp"]
        
        # Ensure v1 is earlier than v2
        if v1_timestamp > v2_timestamp:
            v1_timestamp, v2_timestamp = v2_timestamp, v1_timestamp
        
        # Find all versions in the time range
        versions_in_range = []
        for version, data in history.items():
            timestamp = data["timestamp"]
            if v1_timestamp <= timestamp <= v2_timestamp:
                versions_in_range.append(version)
        
        # Sort by timestamp
        versions_in_range.sort(key=lambda v: history[v]["timestamp"])
        
        return versions_in_range
    
    async def cleanup_old_versions(self, keep_count: int = 10):
        """
        Clean up old version history to prevent storage bloat
        
        Args:
            keep_count: Number of recent versions to keep
        """
        try:
            history = await self._load_version_history()
            
            if len(history) <= keep_count:
                return  # Nothing to clean up
            
            # Sort versions by timestamp (newest first)
            sorted_versions = sorted(
                history.items(),
                key=lambda x: x[1]["timestamp"],
                reverse=True
            )
            
            # Keep only the most recent versions
            versions_to_keep = dict(sorted_versions[:keep_count])
            
            # Save cleaned history
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump(versions_to_keep, f, indent=2, ensure_ascii=False, default=str)
            
            removed_count = len(history) - len(versions_to_keep)
            logger.info(f"Cleaned up {removed_count} old versions, keeping {keep_count} recent versions")
            
        except Exception as e:
            logger.error(f"Failed to cleanup old versions: {str(e)}")
    
    async def export_version_history(self, output_path: str, format: str = "json"):
        """
        Export version history to external file
        
        Args:
            output_path: Path to export file
            format: Export format ("json" or "csv")
        """
        try:
            history = await self._load_version_history()
            output_file = Path(output_path)
            
            if format.lower() == "json":
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(history, f, indent=2, ensure_ascii=False, default=str)
            
            elif format.lower() == "csv":
                import csv
                
                with open(output_file, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    
                    # Write header
                    writer.writerow([
                        "Version", "Timestamp", "Author", "Message", "Services", 
                        "Operations", "Changes", "Parent Version"
                    ])
                    
                    # Write data
                    for version, data in history.items():
                        writer.writerow([
                            version,
                            data["timestamp"],
                            data.get("author", "system"),
                            data.get("message", ""),
                            data["total_services"],
                            data["total_operations"],
                            data.get("change_count", 0),
                            data.get("parent_version", "")
                        ])
            
            else:
                raise VersionControlError(f"Unsupported export format: {format}")
            
            logger.info(f"Exported version history to {output_path} in {format} format")
            
        except Exception as e:
            error_msg = f"Failed to export version history: {str(e)}"
            logger.error(error_msg)
            raise VersionControlError(error_msg)