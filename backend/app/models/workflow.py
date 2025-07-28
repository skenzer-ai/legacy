"""
Workflow models for tracking complex multi-step processes.

These models support the workflow engine that coordinates
Proxie enhancements, API testing sequences, and user workflows.
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
from pydantic import BaseModel

from ..core.database import Base


class WorkflowType(str, Enum):
    """Types of workflows supported by the system."""
    SERVICE_ENHANCEMENT = "service_enhancement"  # Proxie enhancement workflow
    API_TESTING = "api_testing"  # Automated API testing workflow
    USER_TASK = "user_task"  # User-initiated workflow
    SYSTEM_MAINTENANCE = "system_maintenance"  # Background maintenance tasks


class WorkflowStatus(str, Enum):
    """Workflow execution status."""
    PENDING = "pending"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class StepStatus(str, Enum):
    """Individual step execution status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class Workflow(Base):
    """
    Workflow model for tracking complex multi-step processes.
    """
    __tablename__ = "workflows"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Basic workflow information
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    workflow_type = Column(SQLEnum(WorkflowType), nullable=False)
    status = Column(SQLEnum(WorkflowStatus), default=WorkflowStatus.PENDING)
    
    # Configuration and context
    configuration = Column(JSON, nullable=True)  # Workflow-specific configuration
    context = Column(JSON, nullable=True)  # Runtime context and variables
    
    # Progress tracking
    total_steps = Column(Integer, default=0)
    completed_steps = Column(Integer, default=0)
    current_step_index = Column(Integer, default=0)
    progress_percentage = Column(Float, default=0.0)
    
    # Timing information
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    estimated_duration = Column(Integer, nullable=True)  # Estimated duration in seconds
    actual_duration = Column(Integer, nullable=True)  # Actual duration in seconds
    
    # Error handling
    error_message = Column(Text, nullable=True)
    retry_count = Column(Integer, default=0)
    max_retries = Column(Integer, default=3)
    
    # User association
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    assigned_to = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    steps = relationship("WorkflowStep", back_populates="workflow", cascade="all, delete-orphan", order_by="WorkflowStep.step_order")
    executions = relationship("WorkflowExecution", back_populates="workflow")
    created_by_user = relationship("User", foreign_keys=[created_by])
    assigned_to_user = relationship("User", foreign_keys=[assigned_to])
    
    def __repr__(self):
        return f"<Workflow {self.name} ({self.status})>"


class WorkflowStep(Base):
    """
    Individual step within a workflow.
    """
    __tablename__ = "workflow_steps"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    workflow_id = Column(UUID(as_uuid=True), ForeignKey("workflows.id"), nullable=False)
    
    # Step information
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    step_type = Column(String(100), nullable=False)  # e.g., "api_call", "user_approval", "data_processing"
    step_order = Column(Integer, nullable=False)
    
    # Step configuration
    configuration = Column(JSON, nullable=True)  # Step-specific configuration
    input_schema = Column(JSON, nullable=True)  # Expected input schema
    output_schema = Column(JSON, nullable=True)  # Expected output schema
    
    # Execution information
    status = Column(SQLEnum(StepStatus), default=StepStatus.PENDING)
    input_data = Column(JSON, nullable=True)  # Actual input data
    output_data = Column(JSON, nullable=True)  # Actual output data
    error_message = Column(Text, nullable=True)
    
    # Conditional execution
    condition = Column(Text, nullable=True)  # Condition for step execution (Python expression)
    skip_on_failure = Column(Boolean, default=False)
    
    # Timing
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    duration = Column(Integer, nullable=True)  # Duration in seconds
    
    # Dependencies
    depends_on = Column(JSON, nullable=True)  # List of step IDs this step depends on
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    workflow = relationship("Workflow", back_populates="steps")
    
    def __repr__(self):
        return f"<WorkflowStep {self.name} ({self.status})>"


class WorkflowExecution(Base):
    """
    Track individual workflow executions with detailed logs.
    """
    __tablename__ = "workflow_executions"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    workflow_id = Column(UUID(as_uuid=True), ForeignKey("workflows.id"), nullable=False)
    
    # Execution information
    execution_number = Column(Integer, nullable=False)  # Incremental execution number
    status = Column(SQLEnum(WorkflowStatus), default=WorkflowStatus.PENDING)
    
    # Execution context
    initial_context = Column(JSON, nullable=True)  # Starting context
    final_context = Column(JSON, nullable=True)  # Final context after execution
    
    # Results
    result = Column(JSON, nullable=True)  # Execution result
    error_message = Column(Text, nullable=True)
    
    # Timing
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    duration = Column(Integer, nullable=True)  # Duration in seconds
    
    # Execution logs
    logs = Column(JSON, nullable=True)  # Detailed execution logs
    
    # User association
    executed_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    workflow = relationship("Workflow", back_populates="executions")
    executed_by_user = relationship("User", foreign_keys=[executed_by])
    
    def __repr__(self):
        return f"<WorkflowExecution {self.execution_number} for {self.workflow_id}>"


# Pydantic schemas for API responses
class WorkflowResponse(BaseModel):
    """Response schema for workflows."""
    id: uuid.UUID
    name: str
    description: Optional[str] = None
    workflow_type: WorkflowType
    status: WorkflowStatus
    total_steps: int
    completed_steps: int
    progress_percentage: float
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    estimated_duration: Optional[int] = None
    actual_duration: Optional[int] = None
    error_message: Optional[str] = None
    created_at: str
    updated_at: str
    
    class Config:
        from_attributes = True


class WorkflowStepResponse(BaseModel):
    """Response schema for workflow steps."""
    id: uuid.UUID
    name: str
    description: Optional[str] = None
    step_type: str
    step_order: int
    status: StepStatus
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    duration: Optional[int] = None
    error_message: Optional[str] = None
    
    class Config:
        from_attributes = True


class WorkflowCreate(BaseModel):
    """Schema for creating workflows."""
    name: str
    description: Optional[str] = None
    workflow_type: WorkflowType
    configuration: Optional[Dict[str, Any]] = None
    estimated_duration: Optional[int] = None


class WorkflowUpdate(BaseModel):
    """Schema for updating workflows."""
    name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[WorkflowStatus] = None
    configuration: Optional[Dict[str, Any]] = None
    context: Optional[Dict[str, Any]] = None