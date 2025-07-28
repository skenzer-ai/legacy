"""
Service Registry Data Models

Pydantic models for Man-O-Man service registry management system.
Defines the core schema for service definitions, operations, and registry structure.
"""

from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any
from enum import Enum
from datetime import datetime


class OperationType(str, Enum):
    """Standard CRUD operation types for Tier 1 classification"""
    LIST = "list"
    GET_BY_ID = "get_by_id" 
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"


class TierLevel(str, Enum):
    """Service operation tier classification"""
    TIER1 = "tier1"  # Universal CRUD operations
    TIER2 = "tier2"  # Specialized operations


class ConflictType(str, Enum):
    """Types of conflicts that can be detected between services"""
    KEYWORD_OVERLAP = "keyword_overlap"
    SYNONYM_OVERLAP = "synonym_overlap"
    INTENT_AMBIGUITY = "intent_ambiguity"
    BUSINESS_CONTEXT_OVERLAP = "business_context_overlap"
    UNKNOWN = "unknown"


class ConflictSeverity(str, Enum):
    """Severity levels for detected conflicts"""
    HIGH = "high"
    MEDIUM = "medium" 
    LOW = "low"


class APIEndpoint(BaseModel):
    """Standardized API endpoint representation"""
    path: str = Field(..., description="API endpoint path")
    method: str = Field(..., description="HTTP method (GET, POST, PUT, DELETE)")
    operation_id: str = Field(..., description="Unique operation identifier")
    description: Optional[str] = Field(None, description="Endpoint description")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Endpoint parameters")
    
    class Config:
        extra = "forbid"
        

class ServiceOperation(BaseModel):
    """Individual service operation with intent mapping"""
    endpoint: Optional[APIEndpoint] = Field(None, description="Associated API endpoint")
    intent_verbs: List[str] = Field(default_factory=list, description="Action verbs that trigger this operation")
    intent_objects: List[str] = Field(default_factory=list, description="Object types this operation handles")
    intent_indicators: List[str] = Field(default_factory=list, description="Additional intent indicators")
    description: str = Field(..., description="Human-readable operation description")
    confidence_score: float = Field(default=0.8, ge=0.0, le=1.0, description="Classification confidence")
    
    class Config:
        extra = "forbid"


class ServiceDefinition(BaseModel):
    """Complete service definition with metadata and operations"""
    service_name: str = Field(..., description="Unique service identifier")
    service_description: str = Field(..., description="Service purpose and functionality")
    business_context: str = Field(..., description="Business domain and use cases")
    keywords: List[str] = Field(default_factory=list, description="Primary keywords for service identification")
    synonyms: List[str] = Field(default_factory=list, description="Alternative terms and synonyms")
    tier1_operations: Dict[str, ServiceOperation] = Field(
        default_factory=dict, 
        description="CRUD operations (list, get_by_id, create, update, delete)"
    )
    tier2_operations: Dict[str, ServiceOperation] = Field(
        default_factory=dict,
        description="Specialized operations (bulk, analytics, etc.)"
    )
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Creation timestamp")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Last update timestamp")
    version: str = Field(default="1.0", description="Service definition version")
    
    class Config:
        extra = "forbid"
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
    
    def update_timestamp(self):
        """Update the last modified timestamp"""
        self.updated_at = datetime.utcnow()
    
    def get_all_operations(self) -> Dict[str, ServiceOperation]:
        """Get all operations (Tier 1 + Tier 2) combined"""
        return {**self.tier1_operations, **self.tier2_operations}
    
    def get_operation_count(self) -> Dict[str, int]:
        """Get count of operations by tier"""
        return {
            "tier1": len(self.tier1_operations),
            "tier2": len(self.tier2_operations),
            "total": len(self.tier1_operations) + len(self.tier2_operations)
        }
    
    def has_crud_operations(self) -> Dict[str, bool]:
        """Check which CRUD operations are available"""
        crud_check = {}
        for op_type in OperationType:
            crud_check[op_type.value] = op_type.value in self.tier1_operations
        return crud_check


class ConflictReport(BaseModel):
    """Report of detected conflicts between services"""
    conflict_id: str = Field(..., description="Unique conflict identifier")
    conflict_type: ConflictType = Field(..., description="Type of conflict detected")
    severity: ConflictSeverity = Field(..., description="Conflict severity level")
    affected_services: List[str] = Field(..., description="List of services affected by the conflict")
    description: str = Field(..., description="Human-readable conflict description")
    suggested_resolutions: List[str] = Field(default_factory=list, description="Suggested ways to resolve the conflict")
    detection_timestamp: str = Field(..., description="When the conflict was detected")
    auto_resolvable: bool = Field(default=False, description="Whether conflict can be automatically resolved")
    
    class Config:
        extra = "forbid"


class ServiceRegistry(BaseModel):
    """Complete service registry with versioning and metadata"""
    registry_id: str = Field(..., description="Unique registry identifier")
    version: str = Field(..., description="Registry version")
    created_timestamp: str = Field(..., description="Registry creation timestamp")
    last_updated: str = Field(..., description="Last update timestamp")
    services: Dict[str, ServiceDefinition] = Field(
        default_factory=dict,
        description="Service definitions mapped by service name"
    )
    total_services: int = Field(default=0, description="Total number of services")
    confidence_threshold: float = Field(default=0.7, ge=0.0, le=1.0, description="Minimum confidence threshold")
    global_keywords: Dict[str, List[str]] = Field(
        default_factory=dict,
        description="Global keyword tracking for conflict detection"
    )
    classification_rules: Dict[str, Any] = Field(
        default_factory=dict,
        description="Classification rules and configurations"
    )
    
    class Config:
        extra = "forbid"
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
    
    def update_timestamp(self):
        """Update the last modified timestamp"""
        self.last_updated = datetime.utcnow().isoformat()
    
    def add_service(self, service_name: str, service_def: ServiceDefinition) -> bool:
        """Add a new service to the registry"""
        if service_name in self.services:
            return False
        
        self.services[service_name] = service_def
        self._update_global_keywords(service_name, service_def)
        self.update_timestamp()
        return True
    
    def update_service(self, service_name: str, service_def: ServiceDefinition) -> bool:
        """Update an existing service definition"""
        if service_name not in self.services:
            return False
        
        # Remove old keywords
        old_service = self.services[service_name]
        self._remove_global_keywords(service_name, old_service)
        
        # Add new service and keywords
        service_def.update_timestamp()
        self.services[service_name] = service_def
        self._update_global_keywords(service_name, service_def)
        self.update_timestamp()
        return True
    
    def remove_service(self, service_name: str) -> bool:
        """Remove a service from the registry"""
        if service_name not in self.services:
            return False
        
        service_def = self.services[service_name]
        self._remove_global_keywords(service_name, service_def)
        del self.services[service_name]
        self.update_timestamp()
        return True
    
    def get_service_count(self) -> int:
        """Get total number of services in registry"""
        return len(self.services)
    
    def get_total_operations(self) -> int:
        """Get total number of operations across all services"""
        total = 0
        for service in self.services.values():
            total += len(service.get_all_operations())
        return total
    
    def get_registry_stats(self) -> Dict[str, Any]:
        """Get comprehensive registry statistics"""
        tier1_count = 0
        tier2_count = 0
        
        for service in self.services.values():
            counts = service.get_operation_count()
            tier1_count += counts["tier1"]
            tier2_count += counts["tier2"]
        
        return {
            "total_services": self.get_service_count(),
            "total_operations": tier1_count + tier2_count,
            "tier1_operations": tier1_count,
            "tier2_operations": tier2_count,
            "total_keywords": len(self.global_keywords),
            "version": self.version,
            "last_updated": self.updated_at
        }
    
    def _update_global_keywords(self, service_name: str, service_def: ServiceDefinition):
        """Update global keyword tracking"""
        all_keywords = service_def.keywords + service_def.synonyms
        for keyword in all_keywords:
            if keyword not in self.global_keywords:
                self.global_keywords[keyword] = []
            if service_name not in self.global_keywords[keyword]:
                self.global_keywords[keyword].append(service_name)
    
    def _remove_global_keywords(self, service_name: str, service_def: ServiceDefinition):
        """Remove service from global keyword tracking"""
        all_keywords = service_def.keywords + service_def.synonyms
        for keyword in all_keywords:
            if keyword in self.global_keywords:
                if service_name in self.global_keywords[keyword]:
                    self.global_keywords[keyword].remove(service_name)
                if not self.global_keywords[keyword]:
                    del self.global_keywords[keyword]