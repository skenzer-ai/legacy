"""
Workflow State Machine System for Augment AI Platform.

This module provides a comprehensive state machine framework for managing
complex multi-step workflows across the platform, including agent orchestration,
document processing, and API validation workflows.
"""

from typing import Dict, Any, Optional, List, Callable, TypeVar, Generic
from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import uuid
import asyncio
import json
from contextlib import asynccontextmanager

from pydantic import BaseModel, Field
from sqlalchemy import Column, String, DateTime, Text, Integer, Boolean
from sqlalchemy.dialects.postgresql import UUID, JSON

from app.core.database import Base
from app.core.cache import cache_manager
from app.core.tasks.queue import task_queue

T = TypeVar('T')


class WorkflowState(Enum):
    """Standard workflow states."""
    PENDING = "pending"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"


class TransitionCondition(Enum):
    """Conditions for state transitions."""
    ALWAYS = "always"
    ON_SUCCESS = "on_success"
    ON_FAILURE = "on_failure"
    ON_TIMEOUT = "on_timeout"
    ON_USER_INPUT = "on_user_input"
    CONDITIONAL = "conditional"


@dataclass
class StateTransition:
    """Defines a state transition with conditions and actions."""
    from_state: WorkflowState
    to_state: WorkflowState
    condition: TransitionCondition
    condition_func: Optional[Callable[[Dict[str, Any]], bool]] = None
    action: Optional[Callable[[Dict[str, Any]], Dict[str, Any]]] = None
    timeout: Optional[timedelta] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class WorkflowStep:
    """Defines a workflow step with execution logic."""
    name: str
    state: WorkflowState
    action: Callable[[Dict[str, Any]], Any]
    timeout: Optional[timedelta] = timedelta(minutes=10)
    retry_count: int = 3
    retry_delay: timedelta = timedelta(seconds=30)
    parallel: bool = False
    dependencies: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


class WorkflowDefinition(BaseModel):
    """Pydantic model for workflow definition."""
    name: str
    description: str
    initial_state: WorkflowState = WorkflowState.PENDING
    steps: List[str] = Field(default_factory=list)
    timeout: Optional[int] = 3600  # 1 hour default
    retry_policy: Dict[str, Any] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class WorkflowInstance(Base):
    """SQLAlchemy model for workflow instances."""
    __tablename__ = "workflow_instances"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    workflow_name = Column(String(255), nullable=False)
    current_state = Column(String(50), nullable=False, default=WorkflowState.PENDING.value)
    context = Column(JSON, nullable=False, default=dict)
    result = Column(JSON, nullable=True)
    error = Column(Text, nullable=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    
    user_id = Column(UUID(as_uuid=True), nullable=True)
    priority = Column(Integer, default=0)
    timeout_at = Column(DateTime, nullable=True)
    retry_count = Column(Integer, default=0)
    max_retries = Column(Integer, default=3)


class WorkflowEngine:
    """
    Core workflow engine for managing state machines and workflow execution.
    
    Features:
    - State machine management with custom transitions
    - Parallel and sequential step execution
    - Timeout and retry handling
    - Event-driven workflow progression
    - Persistent workflow state
    - Real-time monitoring and notifications
    """
    
    def __init__(self):
        self.workflows: Dict[str, 'WorkflowManager'] = {}
        self.running_instances: Dict[str, asyncio.Task] = {}
    
    def register_workflow(self, workflow_manager: 'WorkflowManager'):
        """Register a workflow manager with the engine."""
        self.workflows[workflow_manager.name] = workflow_manager
    
    async def start_workflow(
        self,
        workflow_name: str,
        context: Dict[str, Any],
        user_id: Optional[str] = None,
        priority: int = 0
    ) -> str:
        """Start a new workflow instance."""
        if workflow_name not in self.workflows:
            raise ValueError(f"Workflow '{workflow_name}' not registered")
        
        workflow_manager = self.workflows[workflow_name]
        instance_id = str(uuid.uuid4())
        
        # Create workflow instance
        instance = WorkflowInstance(
            id=instance_id,
            workflow_name=workflow_name,
            context=context,
            user_id=user_id,
            priority=priority,
            timeout_at=datetime.utcnow() + timedelta(seconds=workflow_manager.definition.timeout) if workflow_manager.definition.timeout else None
        )
        
        # Store in database
        from app.core.database import async_session_maker
        async with async_session_maker() as session:
            session.add(instance)
            await session.commit()
        
        # Start execution
        task = asyncio.create_task(
            self._execute_workflow(instance_id, workflow_manager)
        )
        self.running_instances[instance_id] = task
        
        return instance_id
    
    async def _execute_workflow(self, instance_id: str, workflow_manager: 'WorkflowManager'):
        """Execute a workflow instance."""
        try:
            await workflow_manager.execute(instance_id)
        except Exception as e:
            await self._handle_workflow_error(instance_id, str(e))
        finally:
            # Cleanup
            if instance_id in self.running_instances:
                del self.running_instances[instance_id]
    
    async def _handle_workflow_error(self, instance_id: str, error: str):
        """Handle workflow execution errors."""
        from app.core.database import async_session_maker
        async with async_session_maker() as session:
            instance = await session.get(WorkflowInstance, instance_id)
            if instance:
                instance.current_state = WorkflowState.FAILED.value
                instance.error = error
                instance.completed_at = datetime.utcnow()
                await session.commit()
    
    async def pause_workflow(self, instance_id: str) -> bool:
        """Pause a running workflow."""
        if instance_id in self.running_instances:
            task = self.running_instances[instance_id]
            task.cancel()
            
            # Update state
            from app.core.database import async_session_maker
            async with async_session_maker() as session:
                instance = await session.get(WorkflowInstance, instance_id)
                if instance:
                    instance.current_state = WorkflowState.PAUSED.value
                    await session.commit()
            return True
        return False
    
    async def resume_workflow(self, instance_id: str) -> bool:
        """Resume a paused workflow."""
        from app.core.database import async_session_maker
        async with async_session_maker() as session:
            instance = await session.get(WorkflowInstance, instance_id)
            if instance and instance.current_state == WorkflowState.PAUSED.value:
                workflow_manager = self.workflows.get(instance.workflow_name)
                if workflow_manager:
                    task = asyncio.create_task(
                        workflow_manager.execute(instance_id)
                    )
                    self.running_instances[instance_id] = task
                    return True
        return False
    
    async def get_workflow_status(self, instance_id: str) -> Optional[Dict[str, Any]]:
        """Get current workflow status."""
        from app.core.database import async_session_maker
        async with async_session_maker() as session:
            instance = await session.get(WorkflowInstance, instance_id)
            if instance:
                return {
                    "id": str(instance.id),
                    "workflow_name": instance.workflow_name,
                    "current_state": instance.current_state,
                    "context": instance.context,
                    "result": instance.result,
                    "error": instance.error,
                    "created_at": instance.created_at.isoformat(),
                    "updated_at": instance.updated_at.isoformat(),
                    "started_at": instance.started_at.isoformat() if instance.started_at else None,
                    "completed_at": instance.completed_at.isoformat() if instance.completed_at else None,
                    "user_id": str(instance.user_id) if instance.user_id else None,
                    "priority": instance.priority,
                    "retry_count": instance.retry_count,
                    "max_retries": instance.max_retries
                }
        return None


class WorkflowManager(Generic[T]):
    """
    Base class for managing specific workflow types.
    
    Provides state machine logic, step execution, and transition handling
    for complex multi-step processes.
    """
    
    def __init__(self, definition: WorkflowDefinition):
        self.definition = definition
        self.name = definition.name
        self.steps: Dict[str, WorkflowStep] = {}
        self.transitions: List[StateTransition] = []
        self._step_registry: Dict[WorkflowState, WorkflowStep] = {}
    
    def add_step(self, step: WorkflowStep):
        """Add a workflow step."""
        self.steps[step.name] = step
        self._step_registry[step.state] = step
    
    def add_transition(self, transition: StateTransition):
        """Add a state transition."""
        self.transitions.append(transition)
    
    async def execute(self, instance_id: str):
        """Execute workflow instance."""
        from app.core.database import async_session_maker
        
        async with async_session_maker() as session:
            instance = await session.get(WorkflowInstance, instance_id)
            if not instance:
                raise ValueError(f"Workflow instance {instance_id} not found")
            
            # Update state to running
            instance.current_state = WorkflowState.RUNNING.value
            instance.started_at = datetime.utcnow()
            await session.commit()
            
            current_state = WorkflowState(instance.current_state)
            context = instance.context.copy()
            
            try:
                while current_state not in [WorkflowState.COMPLETED, WorkflowState.FAILED, WorkflowState.CANCELLED]:
                    # Execute current step
                    if current_state in self._step_registry:
                        step = self._step_registry[current_state]
                        result = await self._execute_step(step, context)
                        context.update(result or {})
                    
                    # Find next transition
                    next_state = await self._find_next_state(current_state, context)
                    if next_state == current_state:
                        # No valid transition found
                        break
                    
                    current_state = next_state
                    
                    # Update instance
                    instance.current_state = current_state.value
                    instance.context = context
                    instance.updated_at = datetime.utcnow()
                    await session.commit()
                    
                    # Cache progress for real-time monitoring
                    await cache_manager.set(
                        f"workflow:progress:{instance_id}",
                        {
                            "state": current_state.value,
                            "context": context,
                            "updated_at": datetime.utcnow().isoformat()
                        },
                        expire=3600
                    )
                
                # Mark as completed
                if current_state == WorkflowState.COMPLETED:
                    instance.completed_at = datetime.utcnow()
                    instance.result = context.get("result")
                
                await session.commit()
                
            except Exception as e:
                instance.current_state = WorkflowState.FAILED.value
                instance.error = str(e)
                instance.completed_at = datetime.utcnow()
                await session.commit()
                raise
    
    async def _execute_step(self, step: WorkflowStep, context: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Execute a workflow step with timeout and retry logic."""
        for attempt in range(step.retry_count + 1):
            try:
                # Execute with timeout
                if step.timeout:
                    result = await asyncio.wait_for(
                        step.action(context),
                        timeout=step.timeout.total_seconds()
                    )
                else:
                    result = await step.action(context)
                
                return result
                
            except asyncio.TimeoutError:
                if attempt == step.retry_count:
                    raise Exception(f"Step '{step.name}' timed out after {step.retry_count + 1} attempts")
                await asyncio.sleep(step.retry_delay.total_seconds())
                
            except Exception as e:
                if attempt == step.retry_count:
                    raise Exception(f"Step '{step.name}' failed: {str(e)}")
                await asyncio.sleep(step.retry_delay.total_seconds())
        
        return None
    
    async def _find_next_state(self, current_state: WorkflowState, context: Dict[str, Any]) -> WorkflowState:
        """Find the next state based on transitions and conditions."""
        for transition in self.transitions:
            if transition.from_state == current_state:
                if await self._check_transition_condition(transition, context):
                    if transition.action:
                        action_result = await transition.action(context)
                        context.update(action_result or {})
                    return transition.to_state
        
        # Default behavior: if no transition found, stay in current state
        return current_state
    
    async def _check_transition_condition(self, transition: StateTransition, context: Dict[str, Any]) -> bool:
        """Check if transition condition is met."""
        if transition.condition == TransitionCondition.ALWAYS:
            return True
        elif transition.condition == TransitionCondition.ON_SUCCESS:
            return context.get("success", False)
        elif transition.condition == TransitionCondition.ON_FAILURE:
            return context.get("error") is not None
        elif transition.condition == TransitionCondition.CONDITIONAL and transition.condition_func:
            return transition.condition_func(context)
        
        return False


# Global workflow engine instance
workflow_engine = WorkflowEngine()


# Example workflow managers for common use cases

class DocumentProcessingWorkflow(WorkflowManager):
    """Workflow for document processing and indexing."""
    
    def __init__(self):
        definition = WorkflowDefinition(
            name="document_processing",
            description="Process and index documents for retrieval",
            timeout=1800  # 30 minutes
        )
        super().__init__(definition)
        
        # Define steps
        self.add_step(WorkflowStep(
            name="validate_document",
            state=WorkflowState.PENDING,
            action=self._validate_document
        ))
        
        self.add_step(WorkflowStep(
            name="extract_content",
            state=WorkflowState.RUNNING,
            action=self._extract_content
        ))
        
        # Define transitions
        self.add_transition(StateTransition(
            from_state=WorkflowState.PENDING,
            to_state=WorkflowState.RUNNING,
            condition=TransitionCondition.ON_SUCCESS
        ))
        
        self.add_transition(StateTransition(
            from_state=WorkflowState.RUNNING,
            to_state=WorkflowState.COMPLETED,
            condition=TransitionCondition.ON_SUCCESS
        ))
        
        self.add_transition(StateTransition(
            from_state=WorkflowState.RUNNING,
            to_state=WorkflowState.FAILED,
            condition=TransitionCondition.ON_FAILURE
        ))
    
    async def _validate_document(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Validate document format and accessibility."""
        file_path = context.get("file_path")
        if not file_path:
            context["error"] = "No file path provided"
            return context
        
        # Simulate validation
        await asyncio.sleep(1)
        context["success"] = True
        context["document_type"] = "markdown"
        return context
    
    async def _extract_content(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Extract and process document content."""
        # Simulate content extraction
        await asyncio.sleep(2)
        context["success"] = True
        context["result"] = {
            "content": "Extracted document content",
            "chunks": 10,
            "embeddings_created": True
        }
        return context


class APIValidationWorkflow(WorkflowManager):
    """Workflow for API specification validation and testing."""
    
    def __init__(self):
        definition = WorkflowDefinition(
            name="api_validation",
            description="Validate and test API specifications",
            timeout=2400  # 40 minutes
        )
        super().__init__(definition)
        
        # Define workflow steps and transitions
        # (Implementation similar to DocumentProcessingWorkflow)


# Register default workflows
workflow_engine.register_workflow(DocumentProcessingWorkflow())
workflow_engine.register_workflow(APIValidationWorkflow())