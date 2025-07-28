"""
Progress tracking and notification system for Augment AI Platform.

This module provides comprehensive progress tracking for long-running operations,
with real-time updates, notifications, and detailed progress analytics.
"""

from typing import Dict, Any, Optional, List, Callable, Union
from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import uuid
import asyncio
from contextlib import asynccontextmanager

from pydantic import BaseModel, Field
from sqlalchemy import Column, String, DateTime, Text, Integer, Float, Boolean
from sqlalchemy.dialects.postgresql import UUID, JSON

from app.core.database import Base
from app.core.cache import cache_manager
from app.core.events import event_publisher, EventType, Event
from app.core.websocket import websocket_manager, WebSocketMessage, MessageType


class ProgressStatus(Enum):
    """Progress status enumeration."""
    PENDING = "pending"
    STARTING = "starting"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ProgressType(Enum):
    """Types of progress tracking."""
    PERCENTAGE = "percentage"  # 0-100%
    STEPS = "steps"           # X of Y steps
    BYTES = "bytes"           # Data transfer progress
    ITEMS = "items"           # Processing items
    TIME = "time"             # Time-based progress
    CUSTOM = "custom"         # Custom progress metrics


@dataclass
class ProgressStep:
    """Represents a single step in a progress sequence."""
    id: str
    name: str
    description: Optional[str] = None
    weight: float = 1.0  # Relative weight for calculating overall progress
    status: ProgressStatus = ProgressStatus.PENDING
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    progress: float = 0.0  # 0-100 for this step
    metadata: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None


@dataclass
class ProgressMetrics:
    """Progress metrics and statistics."""
    total_progress: float = 0.0  # Overall progress 0-100
    current_step: Optional[str] = None
    steps_completed: int = 0
    steps_total: int = 0
    estimated_completion: Optional[datetime] = None
    elapsed_time: Optional[timedelta] = None
    remaining_time: Optional[timedelta] = None
    throughput: Optional[float] = None  # Items/bytes per second
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "total_progress": self.total_progress,
            "current_step": self.current_step,
            "steps_completed": self.steps_completed,
            "steps_total": self.steps_total,
            "estimated_completion": self.estimated_completion.isoformat() if self.estimated_completion else None,
            "elapsed_time": self.elapsed_time.total_seconds() if self.elapsed_time else None,
            "remaining_time": self.remaining_time.total_seconds() if self.remaining_time else None,
            "throughput": self.throughput
        }


class ProgressRecord(Base):
    """SQLAlchemy model for progress tracking persistence."""
    __tablename__ = "progress_records"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    operation_id = Column(String(255), nullable=False, unique=True)
    operation_name = Column(String(255), nullable=False)
    operation_type = Column(String(100), nullable=False)
    
    status = Column(String(50), nullable=False, default=ProgressStatus.PENDING.value)
    progress_type = Column(String(50), nullable=False, default=ProgressType.PERCENTAGE.value)
    total_progress = Column(Float, default=0.0)
    
    steps = Column(JSON, nullable=False, default=list)
    operation_metadata = Column(JSON, nullable=False, default=dict)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    user_id = Column(UUID(as_uuid=True), nullable=True)
    session_id = Column(String(100), nullable=True)
    
    error_message = Column(Text, nullable=True)
    result = Column(JSON, nullable=True)


class ProgressTracker:
    """
    Comprehensive progress tracking system.
    
    Features:
    - Multi-step progress tracking with weights
    - Real-time progress updates via WebSocket
    - Progress estimation and ETA calculation
    - Persistent progress storage
    - Event-driven progress notifications
    - Throughput and performance metrics
    - Hierarchical progress (nested operations)
    """
    
    def __init__(self, operation_id: str, operation_name: str, operation_type: str = "generic"):
        self.operation_id = operation_id
        self.operation_name = operation_name
        self.operation_type = operation_type
        self.status = ProgressStatus.PENDING
        self.progress_type = ProgressType.PERCENTAGE
        
        self.steps: Dict[str, ProgressStep] = {}
        self.step_order: List[str] = []
        self.current_step_id: Optional[str] = None
        
        self.started_at: Optional[datetime] = None
        self.completed_at: Optional[datetime] = None
        self.user_id: Optional[str] = None
        self.session_id: Optional[str] = None
        
        self.metadata: Dict[str, Any] = {}
        self.result: Optional[Dict[str, Any]] = None
        self.error_message: Optional[str] = None
        
        # Callbacks
        self.on_progress_callbacks: List[Callable[[ProgressMetrics], Any]] = []
        self.on_status_change_callbacks: List[Callable[[ProgressStatus], Any]] = []
        
        # Performance tracking
        self.throughput_samples: List[tuple[datetime, float]] = []
        self.throughput_window = timedelta(minutes=1)
    
    def add_step(
        self,
        step_id: str,
        name: str,
        description: Optional[str] = None,
        weight: float = 1.0
    ):
        """Add a progress step."""
        step = ProgressStep(
            id=step_id,
            name=name,
            description=description,
            weight=weight
        )
        self.steps[step_id] = step
        self.step_order.append(step_id)
    
    def add_steps(self, steps: List[Dict[str, Any]]):
        """Add multiple steps at once."""
        for step_data in steps:
            self.add_step(**step_data)
    
    async def start(self, user_id: Optional[str] = None, session_id: Optional[str] = None):
        """Start progress tracking."""
        self.status = ProgressStatus.STARTING
        self.started_at = datetime.utcnow()
        self.user_id = user_id
        self.session_id = session_id
        
        # Persist to database
        await self._persist()
        
        # Emit start event
        await event_publisher.publish(
            event_type=EventType.WORKFLOW_STARTED,
            data={
                "operation_id": self.operation_id,
                "operation_name": self.operation_name,
                "operation_type": self.operation_type,
                "steps_total": len(self.steps)
            },
            source="progress_tracker",
            user_id=self.user_id,
            session_id=self.session_id
        )
        
        # Update status to running
        self.status = ProgressStatus.RUNNING
        await self._notify_status_change()
    
    async def update_step_progress(
        self,
        step_id: str,
        progress: float,
        status: Optional[ProgressStatus] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Update progress for a specific step."""
        if step_id not in self.steps:
            raise ValueError(f"Step {step_id} not found")
        
        step = self.steps[step_id]
        
        # Update step progress
        step.progress = max(0, min(100, progress))
        if status:
            step.status = status
        if metadata:
            step.metadata.update(metadata)
        
        # Update timing
        if step.status == ProgressStatus.RUNNING and not step.start_time:
            step.start_time = datetime.utcnow()
        elif step.status in [ProgressStatus.COMPLETED, ProgressStatus.FAILED, ProgressStatus.CANCELLED]:
            step.end_time = datetime.utcnow()
        
        # Set as current step if running
        if step.status == ProgressStatus.RUNNING:
            self.current_step_id = step_id
        
        # Calculate overall progress
        await self._calculate_overall_progress()
        
        # Notify progress update
        await self._notify_progress_update()
        
        # Check if operation is complete
        await self._check_completion()
    
    async def complete_step(self, step_id: str, result: Optional[Dict[str, Any]] = None):
        """Mark a step as completed."""
        await self.update_step_progress(
            step_id=step_id,
            progress=100.0,
            status=ProgressStatus.COMPLETED,
            metadata={"result": result} if result else None
        )
    
    async def fail_step(self, step_id: str, error: str):
        """Mark a step as failed."""
        if step_id in self.steps:
            self.steps[step_id].error = error
        
        await self.update_step_progress(
            step_id=step_id,
            progress=0.0,
            status=ProgressStatus.FAILED,
            metadata={"error": error}
        )
    
    async def pause(self):
        """Pause progress tracking."""
        self.status = ProgressStatus.PAUSED
        await self._notify_status_change()
        await self._persist()
    
    async def resume(self):
        """Resume progress tracking."""
        self.status = ProgressStatus.RUNNING
        await self._notify_status_change()
        await self._persist()
    
    async def complete(self, result: Optional[Dict[str, Any]] = None):
        """Complete the operation."""
        self.status = ProgressStatus.COMPLETED
        self.completed_at = datetime.utcnow()
        self.result = result
        
        # Mark all incomplete steps as completed
        for step in self.steps.values():
            if step.status not in [ProgressStatus.COMPLETED, ProgressStatus.FAILED, ProgressStatus.CANCELLED]:
                step.status = ProgressStatus.COMPLETED
                step.progress = 100.0
                if not step.end_time:
                    step.end_time = datetime.utcnow()
        
        await self._calculate_overall_progress()
        await self._notify_status_change()
        await self._notify_progress_update()
        await self._persist()
        
        # Emit completion event
        await event_publisher.publish(
            event_type=EventType.WORKFLOW_COMPLETED,
            data={
                "operation_id": self.operation_id,
                "operation_name": self.operation_name,
                "result": self.result,
                "elapsed_time": (self.completed_at - self.started_at).total_seconds() if self.started_at else None
            },
            source="progress_tracker",
            user_id=self.user_id,
            session_id=self.session_id
        )
    
    async def fail(self, error: str):
        """Fail the operation."""
        self.status = ProgressStatus.FAILED
        self.completed_at = datetime.utcnow()
        self.error_message = error
        
        await self._notify_status_change()
        await self._persist()
        
        # Emit failure event
        await event_publisher.publish(
            event_type=EventType.WORKFLOW_FAILED,
            data={
                "operation_id": self.operation_id,
                "operation_name": self.operation_name,
                "error": error
            },
            source="progress_tracker",
            user_id=self.user_id,
            session_id=self.session_id
        )
    
    async def cancel(self):
        """Cancel the operation."""
        self.status = ProgressStatus.CANCELLED
        self.completed_at = datetime.utcnow()
        
        await self._notify_status_change()
        await self._persist()
    
    def add_progress_callback(self, callback: Callable[[ProgressMetrics], Any]):
        """Add a progress update callback."""
        self.on_progress_callbacks.append(callback)
    
    def add_status_callback(self, callback: Callable[[ProgressStatus], Any]):
        """Add a status change callback."""
        self.on_status_change_callbacks.append(callback)
    
    def get_metrics(self) -> ProgressMetrics:
        """Get current progress metrics."""
        metrics = ProgressMetrics()
        
        # Calculate overall progress
        if self.steps:
            total_weight = sum(step.weight for step in self.steps.values())
            if total_weight > 0:
                weighted_progress = sum(
                    (step.progress / 100.0) * step.weight
                    for step in self.steps.values()
                )
                metrics.total_progress = (weighted_progress / total_weight) * 100
        
        # Current step
        metrics.current_step = self.current_step_id
        
        # Step counts
        metrics.steps_completed = len([s for s in self.steps.values() if s.status == ProgressStatus.COMPLETED])
        metrics.steps_total = len(self.steps)
        
        # Time calculations
        if self.started_at:
            metrics.elapsed_time = datetime.utcnow() - self.started_at
            
            # Estimate completion time
            if metrics.total_progress > 0 and self.status == ProgressStatus.RUNNING:
                estimated_total_time = metrics.elapsed_time * (100 / metrics.total_progress)
                metrics.remaining_time = estimated_total_time - metrics.elapsed_time
                metrics.estimated_completion = datetime.utcnow() + metrics.remaining_time
        
        # Throughput calculation
        metrics.throughput = self._calculate_throughput()
        
        return metrics
    
    def get_status(self) -> Dict[str, Any]:
        """Get current status and metrics."""
        metrics = self.get_metrics()
        
        return {
            "operation_id": self.operation_id,
            "operation_name": self.operation_name,
            "operation_type": self.operation_type,
            "status": self.status.value,
            "progress_type": self.progress_type.value,
            "metrics": metrics.to_dict(),
            "steps": [
                {
                    "id": step.id,
                    "name": step.name,
                    "description": step.description,
                    "status": step.status.value,
                    "progress": step.progress,
                    "weight": step.weight,
                    "start_time": step.start_time.isoformat() if step.start_time else None,
                    "end_time": step.end_time.isoformat() if step.end_time else None,
                    "metadata": step.metadata,
                    "error": step.error
                }
                for step in [self.steps[step_id] for step_id in self.step_order]
            ],
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "user_id": self.user_id,
            "session_id": self.session_id,
            "metadata": self.metadata,
            "result": self.result,
            "error_message": self.error_message
        }
    
    async def _calculate_overall_progress(self):
        """Calculate overall progress based on step weights."""
        if not self.steps:
            return
        
        total_weight = sum(step.weight for step in self.steps.values())
        if total_weight == 0:
            return
        
        weighted_progress = sum(
            (step.progress / 100.0) * step.weight
            for step in self.steps.values()
        )
        
        overall_progress = (weighted_progress / total_weight) * 100
        self.metadata["total_progress"] = overall_progress
    
    async def _notify_progress_update(self):
        """Notify subscribers of progress updates."""
        metrics = self.get_metrics()
        
        # Call registered callbacks
        for callback in self.on_progress_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(metrics)
                else:
                    callback(metrics)
            except Exception as e:
                print(f"Error in progress callback: {e}")
        
        # Send WebSocket updates
        if self.user_id:
            message = WebSocketMessage(
                type=MessageType.WORKFLOW_PROGRESS,
                data={
                    "operation_id": self.operation_id,
                    "metrics": metrics.to_dict(),
                    "current_step": self.current_step_id
                },
                user_id=self.user_id
            )
            await websocket_manager.send_to_user(self.user_id, message)
        
        # Cache latest progress for polling clients
        await cache_manager.set(
            f"progress:{self.operation_id}",
            self.get_status(),
            expire=3600
        )
    
    async def _notify_status_change(self):
        """Notify subscribers of status changes."""
        # Call registered callbacks
        for callback in self.on_status_change_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(self.status)
                else:
                    callback(self.status)
            except Exception as e:
                print(f"Error in status callback: {e}")
        
        # Send WebSocket updates
        if self.user_id:
            message = WebSocketMessage(
                type=MessageType.WORKFLOW_STATUS,
                data={
                    "operation_id": self.operation_id,
                    "status": self.status.value,
                    "timestamp": datetime.utcnow().isoformat()
                },
                user_id=self.user_id
            )
            await websocket_manager.send_to_user(self.user_id, message)
    
    async def _check_completion(self):
        """Check if all steps are complete."""
        if self.status != ProgressStatus.RUNNING:
            return
        
        incomplete_steps = [
            step for step in self.steps.values()
            if step.status not in [ProgressStatus.COMPLETED, ProgressStatus.FAILED, ProgressStatus.CANCELLED]
        ]
        
        if not incomplete_steps:
            # Check if any steps failed
            failed_steps = [step for step in self.steps.values() if step.status == ProgressStatus.FAILED]
            if failed_steps:
                error_messages = [step.error for step in failed_steps if step.error]
                await self.fail(f"Steps failed: {', '.join(error_messages)}")
            else:
                await self.complete()
    
    async def _persist(self):
        """Persist progress to database."""
        from app.core.database import async_session_maker
        
        async with async_session_maker() as session:
            try:
                # Check if record exists
                existing = await session.get(ProgressRecord, self.operation_id)
                
                if existing:
                    # Update existing record
                    existing.status = self.status.value
                    existing.total_progress = self.metadata.get("total_progress", 0.0)
                    existing.steps = [
                        {
                            "id": step.id,
                            "name": step.name,
                            "description": step.description,
                            "status": step.status.value,
                            "progress": step.progress,
                            "weight": step.weight,
                            "start_time": step.start_time.isoformat() if step.start_time else None,
                            "end_time": step.end_time.isoformat() if step.end_time else None,
                            "metadata": step.metadata,
                            "error": step.error
                        }
                        for step in [self.steps[step_id] for step_id in self.step_order]
                    ]
                    existing.operation_metadata = self.metadata
                    existing.started_at = self.started_at
                    existing.completed_at = self.completed_at
                    existing.user_id = self.user_id
                    existing.session_id = self.session_id
                    existing.error_message = self.error_message
                    existing.result = self.result
                    existing.updated_at = datetime.utcnow()
                else:
                    # Create new record
                    record = ProgressRecord(
                        operation_id=self.operation_id,
                        operation_name=self.operation_name,
                        operation_type=self.operation_type,
                        status=self.status.value,
                        progress_type=self.progress_type.value,
                        total_progress=self.metadata.get("total_progress", 0.0),
                        steps=[
                            {
                                "id": step.id,
                                "name": step.name,
                                "description": step.description,
                                "status": step.status.value,
                                "progress": step.progress,
                                "weight": step.weight,
                                "start_time": step.start_time.isoformat() if step.start_time else None,
                                "end_time": step.end_time.isoformat() if step.end_time else None,
                                "metadata": step.metadata,
                                "error": step.error
                            }
                            for step in [self.steps[step_id] for step_id in self.step_order]
                        ],
                        operation_metadata=self.metadata,
                        started_at=self.started_at,
                        completed_at=self.completed_at,
                        user_id=self.user_id,
                        session_id=self.session_id,
                        error_message=self.error_message,
                        result=self.result
                    )
                    session.add(record)
                
                await session.commit()
                
            except Exception as e:
                print(f"Error persisting progress: {e}")
                await session.rollback()
    
    def _calculate_throughput(self) -> Optional[float]:
        """Calculate current throughput."""
        if len(self.throughput_samples) < 2:
            return None
        
        # Filter samples within window
        now = datetime.utcnow()
        recent_samples = [
            (timestamp, value) for timestamp, value in self.throughput_samples
            if now - timestamp <= self.throughput_window
        ]
        
        if len(recent_samples) < 2:
            return None
        
        # Calculate rate of change
        first_time, first_value = recent_samples[0]
        last_time, last_value = recent_samples[-1]
        
        time_diff = (last_time - first_time).total_seconds()
        if time_diff > 0:
            return (last_value - first_value) / time_diff
        
        return None
    
    def add_throughput_sample(self, value: float):
        """Add a throughput sample."""
        self.throughput_samples.append((datetime.utcnow(), value))
        
        # Keep only recent samples
        cutoff = datetime.utcnow() - self.throughput_window
        self.throughput_samples = [
            (timestamp, value) for timestamp, value in self.throughput_samples
            if timestamp >= cutoff
        ]


class ProgressManager:
    """Global progress manager for tracking multiple operations."""
    
    def __init__(self):
        self.trackers: Dict[str, ProgressTracker] = {}
    
    def create_tracker(
        self,
        operation_name: str,
        operation_type: str = "generic",
        operation_id: Optional[str] = None
    ) -> ProgressTracker:
        """Create a new progress tracker."""
        if not operation_id:
            operation_id = str(uuid.uuid4())
        
        tracker = ProgressTracker(operation_id, operation_name, operation_type)
        self.trackers[operation_id] = tracker
        return tracker
    
    def get_tracker(self, operation_id: str) -> Optional[ProgressTracker]:
        """Get existing progress tracker."""
        return self.trackers.get(operation_id)
    
    def remove_tracker(self, operation_id: str) -> bool:
        """Remove progress tracker."""
        if operation_id in self.trackers:
            del self.trackers[operation_id]
            return True
        return False
    
    def list_trackers(self) -> List[Dict[str, Any]]:
        """List all active trackers."""
        return [
            {
                "operation_id": tracker.operation_id,
                "operation_name": tracker.operation_name,
                "operation_type": tracker.operation_type,
                "status": tracker.status.value,
                "progress": tracker.get_metrics().total_progress,
                "started_at": tracker.started_at.isoformat() if tracker.started_at else None,
                "user_id": tracker.user_id
            }
            for tracker in self.trackers.values()
        ]
    
    async def get_progress_status(self, operation_id: str) -> Optional[Dict[str, Any]]:
        """Get progress status for an operation."""
        # Try memory first
        if operation_id in self.trackers:
            return self.trackers[operation_id].get_status()
        
        # Try cache
        cached_status = await cache_manager.get(f"progress:{operation_id}")
        if cached_status:
            return cached_status
        
        # Try database
        from app.core.database import async_session_maker
        async with async_session_maker() as session:
            record = await session.get(ProgressRecord, operation_id)
            if record:
                return {
                    "operation_id": record.operation_id,
                    "operation_name": record.operation_name,
                    "operation_type": record.operation_type,
                    "status": record.status,
                    "progress_type": record.progress_type,
                    "total_progress": record.total_progress,
                    "steps": record.steps,
                    "metadata": record.operation_metadata,
                    "started_at": record.started_at.isoformat() if record.started_at else None,
                    "completed_at": record.completed_at.isoformat() if record.completed_at else None,
                    "user_id": str(record.user_id) if record.user_id else None,
                    "session_id": record.session_id,
                    "error_message": record.error_message,
                    "result": record.result
                }
        
        return None


# Global progress manager instance
progress_manager = ProgressManager()


# Utility context manager for automatic progress tracking
@asynccontextmanager
async def track_progress(
    operation_name: str,
    steps: List[Dict[str, Any]],
    operation_type: str = "generic",
    user_id: Optional[str] = None,
    session_id: Optional[str] = None
):
    """Context manager for automatic progress tracking."""
    tracker = progress_manager.create_tracker(operation_name, operation_type)
    tracker.add_steps(steps)
    
    try:
        await tracker.start(user_id, session_id)
        yield tracker
        await tracker.complete()
    except Exception as e:
        await tracker.fail(str(e))
        raise
    finally:
        # Keep tracker for a while for status queries
        asyncio.create_task(_cleanup_tracker(tracker.operation_id))