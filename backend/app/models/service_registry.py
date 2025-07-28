"""
Enhanced service registry models for the Augment platform.

These models extend the existing JSON-based service registry with 
database persistence, versioning, and enhanced metadata.
"""

from sqlalchemy import (
    Column, String, Text, Boolean, Integer, Float, DateTime, 
    ForeignKey, Enum as SQLEnum, JSON
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
from enum import Enum
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field

from ..core.database import Base


class ServiceTier(str, Enum):
    """Service tier classification."""
    TIER_1 = "tier_1"  # Universal CRUD operations
    TIER_2 = "tier_2"  # Specialized operations


class EnhancementStatus(str, Enum):
    """Enhancement status for tracking Proxie work."""
    PENDING = "pending"
    ANALYZING = "analyzing"
    TESTING = "testing"
    ENHANCING = "enhancing"
    APPROVAL_NEEDED = "approval_needed"
    COMPLETED = "completed"
    FAILED = "failed"


class ServiceRegistry(Base):
    """
    Enhanced service registry with database persistence.
    
    This model extends the existing JSON-based registry with
    additional metadata for Proxie and Augment agents.
    """
    __tablename__ = "service_registry"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    service_name = Column(String(255), unique=True, nullable=False, index=True)
    
    # Basic service information
    description = Column(Text, nullable=True)
    version = Column(String(50), nullable=True)
    tier = Column(SQLEnum(ServiceTier), nullable=True)
    
    # Enhanced metadata for Augment agent
    intent_keywords = Column(JSON, nullable=True)  # List of keywords for intent matching
    semantic_category = Column(String(255), nullable=True)
    business_actions = Column(JSON, nullable=True)  # List of business actions
    user_intent_patterns = Column(JSON, nullable=True)  # List of example user queries
    negative_examples = Column(JSON, nullable=True)  # What this service is NOT for
    
    # Quality and confidence metrics
    documentation_quality_score = Column(Float, default=0.0)
    automation_readiness_score = Column(Float, default=0.0)
    confidence_score = Column(Float, default=0.0)
    
    # Enhancement tracking
    enhancement_status = Column(SQLEnum(EnhancementStatus), default=EnhancementStatus.PENDING)
    last_enhanced = Column(DateTime(timezone=True), nullable=True)
    enhanced_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    api_endpoints = relationship("APIEndpoint", back_populates="service", cascade="all, delete-orphan")
    enhancement_history = relationship("EnhancementHistory", back_populates="service")
    enhanced_by_user = relationship("User", foreign_keys=[enhanced_by])
    
    def __repr__(self):
        return f"<ServiceRegistry {self.service_name} ({self.tier})>"


class APIEndpoint(Base):
    """
    Enhanced API endpoint model with Augment-optimized metadata.
    """
    __tablename__ = "api_endpoints"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    service_id = Column(UUID(as_uuid=True), ForeignKey("service_registry.id"), nullable=False)
    
    # Basic endpoint information
    endpoint_path = Column(String(500), nullable=False)
    http_method = Column(String(10), nullable=False)
    operation_id = Column(String(255), nullable=True)
    summary = Column(Text, nullable=True)
    description = Column(Text, nullable=True)
    
    # Enhanced descriptions
    enhanced_description = Column(Text, nullable=True)
    usage_context = Column(Text, nullable=True)
    when_to_use = Column(Text, nullable=True)
    when_not_to_use = Column(Text, nullable=True)
    
    # Augment optimization metadata
    intent_specificity = Column(Float, default=0.0)  # How specific this API is to certain intents
    parameter_complexity = Column(String(20), default="unknown")  # low, medium, high
    success_patterns = Column(JSON, nullable=True)  # Keywords that indicate success
    failure_patterns = Column(JSON, nullable=True)  # Keywords that indicate failure
    
    # Parameter guidance for LLMs
    parameter_guidance = Column(JSON, nullable=True)  # Detailed parameter help
    
    # Workflow and sequence information
    workflow_role = Column(String(100), nullable=True)  # e.g., "step_1_of_3"
    typical_sequences = Column(JSON, nullable=True)  # Common workflow sequences
    data_flow = Column(JSON, nullable=True)  # What data this API produces/consumes
    
    # Error recovery information
    error_recovery = Column(JSON, nullable=True)  # Error patterns and recovery strategies
    
    # Quality metrics
    success_rate = Column(Float, default=0.0)
    average_response_time = Column(Float, default=0.0)
    last_tested = Column(DateTime(timezone=True), nullable=True)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    service = relationship("ServiceRegistry", back_populates="api_endpoints")
    
    def __repr__(self):
        return f"<APIEndpoint {self.http_method} {self.endpoint_path}>"


class EnhancementHistory(Base):
    """
    Track enhancement history for services and APIs.
    """
    __tablename__ = "enhancement_history"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    service_id = Column(UUID(as_uuid=True), ForeignKey("service_registry.id"), nullable=False)
    
    # Enhancement details
    enhancement_type = Column(String(50), nullable=False)  # "proxie_enhancement", "manual_update", etc.
    enhancement_data = Column(JSON, nullable=True)  # Details of what was enhanced
    
    # Quality improvements
    before_quality_score = Column(Float, nullable=True)
    after_quality_score = Column(Float, nullable=True)
    
    # User interaction
    user_feedback = Column(Text, nullable=True)
    approved = Column(Boolean, default=False)
    approved_at = Column(DateTime(timezone=True), nullable=True)
    approved_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    
    # Relationships
    service = relationship("ServiceRegistry", back_populates="enhancement_history")
    approved_by_user = relationship("User", foreign_keys=[approved_by])
    created_by_user = relationship("User", foreign_keys=[created_by])
    
    def __repr__(self):
        return f"<EnhancementHistory {self.enhancement_type} for {self.service_id}>"


# Pydantic schemas for API responses
class ServiceRegistryResponse(BaseModel):
    """Response schema for service registry."""
    id: uuid.UUID
    service_name: str
    description: Optional[str] = None
    version: Optional[str] = None
    tier: Optional[ServiceTier] = None
    intent_keywords: Optional[List[str]] = None
    semantic_category: Optional[str] = None
    business_actions: Optional[List[str]] = None
    user_intent_patterns: Optional[List[str]] = None
    documentation_quality_score: float
    automation_readiness_score: float
    confidence_score: float
    enhancement_status: EnhancementStatus
    last_enhanced: Optional[str] = None
    created_at: str
    updated_at: str
    
    class Config:
        from_attributes = True


class APIEndpointResponse(BaseModel):
    """Response schema for API endpoints."""
    id: uuid.UUID
    endpoint_path: str
    http_method: str
    operation_id: Optional[str] = None
    summary: Optional[str] = None
    description: Optional[str] = None
    enhanced_description: Optional[str] = None
    usage_context: Optional[str] = None
    intent_specificity: float
    parameter_complexity: str
    success_rate: float
    average_response_time: float
    last_tested: Optional[str] = None
    created_at: str
    updated_at: str
    
    class Config:
        from_attributes = True


class ServiceRegistryCreate(BaseModel):
    """Schema for creating service registry entries."""
    service_name: str
    description: Optional[str] = None
    version: Optional[str] = None
    tier: Optional[ServiceTier] = None
    intent_keywords: Optional[List[str]] = None
    semantic_category: Optional[str] = None
    business_actions: Optional[List[str]] = None


class ServiceRegistryUpdate(BaseModel):
    """Schema for updating service registry entries."""
    description: Optional[str] = None
    version: Optional[str] = None
    tier: Optional[ServiceTier] = None
    intent_keywords: Optional[List[str]] = None
    semantic_category: Optional[str] = None
    business_actions: Optional[List[str]] = None
    user_intent_patterns: Optional[List[str]] = None
    negative_examples: Optional[List[str]] = None
    documentation_quality_score: Optional[float] = None
    automation_readiness_score: Optional[float] = None
    confidence_score: Optional[float] = None
    enhancement_status: Optional[EnhancementStatus] = None