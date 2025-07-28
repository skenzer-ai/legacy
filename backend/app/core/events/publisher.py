"""
Event-driven architecture with pub/sub system for Augment AI Platform.

This module provides a comprehensive event publishing and subscription system
for loose coupling between components, real-time notifications, and workflow coordination.
"""

from typing import Dict, Any, Optional, List, Callable, Union, Set
from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime
import uuid
import asyncio
import json
import weakref
from contextlib import asynccontextmanager

from pydantic import BaseModel, Field
from sqlalchemy import Column, String, DateTime, Text, Integer, Boolean
from sqlalchemy.dialects.postgresql import UUID, JSON

from app.core.database import Base
from app.core.cache import cache_manager


class EventType(Enum):
    """Standard event types for the platform."""
    # Workflow events
    WORKFLOW_STARTED = "workflow.started"
    WORKFLOW_COMPLETED = "workflow.completed"
    WORKFLOW_FAILED = "workflow.failed"
    WORKFLOW_PAUSED = "workflow.paused"
    WORKFLOW_RESUMED = "workflow.resumed"
    WORKFLOW_STEP_STARTED = "workflow.step.started"
    WORKFLOW_STEP_COMPLETED = "workflow.step.completed"
    WORKFLOW_STEP_FAILED = "workflow.step.failed"
    
    # User events
    USER_REGISTERED = "user.registered"
    USER_LOGIN = "user.login"
    USER_LOGOUT = "user.logout"
    USER_UPDATED = "user.updated"
    
    # Agent events
    AGENT_QUERY_STARTED = "agent.query.started"
    AGENT_QUERY_COMPLETED = "agent.query.completed"
    AGENT_REASONING_STEP = "agent.reasoning.step"
    AGENT_MEMORY_UPDATED = "agent.memory.updated"
    
    # Document events
    DOCUMENT_UPLOADED = "document.uploaded"
    DOCUMENT_PROCESSED = "document.processed"
    DOCUMENT_INDEXED = "document.indexed"
    DOCUMENT_DELETED = "document.deleted"
    
    # API events
    API_CALL_STARTED = "api.call.started"
    API_CALL_COMPLETED = "api.call.completed"
    API_CALL_FAILED = "api.call.failed"
    API_SPEC_ANALYZED = "api.spec.analyzed"
    
    # System events
    SYSTEM_STARTUP = "system.startup"
    SYSTEM_SHUTDOWN = "system.shutdown"
    SYSTEM_ERROR = "system.error"
    SYSTEM_HEALTH_CHECK = "system.health.check"
    
    # Custom events
    CUSTOM = "custom"


class EventPriority(Enum):
    """Event priority levels."""
    LOW = 0
    NORMAL = 1
    HIGH = 2
    CRITICAL = 3


@dataclass
class Event:
    """Represents an event in the system."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    type: EventType = EventType.CUSTOM
    source: str = "system"
    timestamp: datetime = field(default_factory=datetime.utcnow)
    data: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    priority: EventPriority = EventPriority.NORMAL
    correlation_id: Optional[str] = None
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary."""
        return {
            "id": self.id,
            "type": self.type.value,
            "source": self.source,
            "timestamp": self.timestamp.isoformat(),
            "data": self.data,
            "metadata": self.metadata,
            "priority": self.priority.value,
            "correlation_id": self.correlation_id,
            "user_id": self.user_id,
            "session_id": self.session_id
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Event':
        """Create event from dictionary."""
        return cls(
            id=data.get("id", str(uuid.uuid4())),
            type=EventType(data.get("type", EventType.CUSTOM.value)),
            source=data.get("source", "system"),
            timestamp=datetime.fromisoformat(data.get("timestamp", datetime.utcnow().isoformat())),
            data=data.get("data", {}),
            metadata=data.get("metadata", {}),
            priority=EventPriority(data.get("priority", EventPriority.NORMAL.value)),
            correlation_id=data.get("correlation_id"),
            user_id=data.get("user_id"),
            session_id=data.get("session_id")
        )


class EventFilter(BaseModel):
    """Filter for event subscriptions."""
    event_types: Optional[List[EventType]] = None
    sources: Optional[List[str]] = None
    user_ids: Optional[List[str]] = None
    priorities: Optional[List[EventPriority]] = None
    custom_filter: Optional[Callable[[Event], bool]] = None


# Type aliases for event handlers
EventHandler = Callable[[Event], Any]
AsyncEventHandler = Callable[[Event], Any]


class EventSubscription:
    """Represents an event subscription."""
    
    def __init__(
        self,
        handler: Union[EventHandler, AsyncEventHandler],
        event_filter: Optional[EventFilter] = None,
        name: Optional[str] = None,
        once: bool = False
    ):
        self.id = str(uuid.uuid4())
        self.handler = handler
        self.filter = event_filter or EventFilter()
        self.name = name or f"subscription_{self.id[:8]}"
        self.once = once
        self.created_at = datetime.utcnow()
        self.call_count = 0
        self.last_called = None
        self.active = True
    
    def matches(self, event: Event) -> bool:
        """Check if event matches subscription filter."""
        if not self.active:
            return False
        
        # Check event types
        if self.filter.event_types and event.type not in self.filter.event_types:
            return False
        
        # Check sources
        if self.filter.sources and event.source not in self.filter.sources:
            return False
        
        # Check user IDs
        if self.filter.user_ids and event.user_id not in self.filter.user_ids:
            return False
        
        # Check priorities
        if self.filter.priorities and event.priority not in self.filter.priorities:
            return False
        
        # Check custom filter
        if self.filter.custom_filter and not self.filter.custom_filter(event):
            return False
        
        return True
    
    async def handle_event(self, event: Event):
        """Handle an event with this subscription."""
        if not self.active:
            return
        
        try:
            self.call_count += 1
            self.last_called = datetime.utcnow()
            
            if asyncio.iscoroutinefunction(self.handler):
                await self.handler(event)
            else:
                self.handler(event)
            
            # Deactivate if once-only subscription
            if self.once:
                self.active = False
                
        except Exception as e:
            print(f"Error in event handler {self.name}: {e}")
            # Log error but don't raise to prevent breaking other handlers


class EventHistory(Base):
    """SQLAlchemy model for persisting event history."""
    __tablename__ = "event_history"
    
    id = Column(UUID(as_uuid=True), primary_key=True)
    event_type = Column(String(100), nullable=False)
    source = Column(String(100), nullable=False)
    timestamp = Column(DateTime, nullable=False)
    data = Column(JSON, nullable=False)
    event_metadata = Column(JSON, nullable=False)
    priority = Column(Integer, nullable=False)
    correlation_id = Column(String(100), nullable=True)
    user_id = Column(UUID(as_uuid=True), nullable=True)
    session_id = Column(String(100), nullable=True)
    
    # Indexing for efficient queries
    __table_args__ = ()


class EventPublisher:
    """
    Central event publisher for the platform.
    
    Features:
    - Async event publishing and handling
    - Flexible subscription system with filters
    - Event persistence and history
    - Real-time notifications via Redis
    - Batch publishing for performance
    - Event correlation and tracing
    """
    
    def __init__(self):
        self.subscriptions: Dict[str, EventSubscription] = {}
        self.event_queue: asyncio.Queue = asyncio.Queue()
        self.processing_task: Optional[asyncio.Task] = None
        self.batch_size = 10
        self.batch_timeout = 1.0  # seconds
        self.stats = {
            "events_published": 0,
            "events_processed": 0,
            "handlers_executed": 0,
            "errors": 0
        }
    
    async def start(self):
        """Start the event processing system."""
        if not self.processing_task:
            self.processing_task = asyncio.create_task(self._process_events())
    
    async def stop(self):
        """Stop the event processing system."""
        if self.processing_task:
            self.processing_task.cancel()
            try:
                await self.processing_task
            except asyncio.CancelledError:
                pass
            self.processing_task = None
    
    async def publish(
        self,
        event_type: EventType,
        data: Dict[str, Any],
        source: str = "system",
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        correlation_id: Optional[str] = None,
        priority: EventPriority = EventPriority.NORMAL,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Publish an event."""
        event = Event(
            type=event_type,
            source=source,
            data=data,
            metadata=metadata or {},
            priority=priority,
            correlation_id=correlation_id,
            user_id=user_id,
            session_id=session_id
        )
        
        await self.event_queue.put(event)
        self.stats["events_published"] += 1
        
        return event.id
    
    async def publish_event(self, event: Event) -> str:
        """Publish a pre-created event."""
        await self.event_queue.put(event)
        self.stats["events_published"] += 1
        return event.id
    
    def subscribe(
        self,
        handler: Union[EventHandler, AsyncEventHandler],
        event_types: Optional[List[EventType]] = None,
        sources: Optional[List[str]] = None,
        user_ids: Optional[List[str]] = None,
        priorities: Optional[List[EventPriority]] = None,
        custom_filter: Optional[Callable[[Event], bool]] = None,
        name: Optional[str] = None,
        once: bool = False
    ) -> str:
        """Subscribe to events with optional filtering."""
        event_filter = EventFilter(
            event_types=event_types,
            sources=sources,
            user_ids=user_ids,
            priorities=priorities,
            custom_filter=custom_filter
        )
        
        subscription = EventSubscription(
            handler=handler,
            event_filter=event_filter,
            name=name,
            once=once
        )
        
        self.subscriptions[subscription.id] = subscription
        return subscription.id
    
    def unsubscribe(self, subscription_id: str) -> bool:
        """Unsubscribe from events."""
        if subscription_id in self.subscriptions:
            del self.subscriptions[subscription_id]
            return True
        return False
    
    def get_subscription(self, subscription_id: str) -> Optional[EventSubscription]:
        """Get subscription by ID."""
        return self.subscriptions.get(subscription_id)
    
    def list_subscriptions(self) -> List[Dict[str, Any]]:
        """List all active subscriptions."""
        return [
            {
                "id": sub.id,
                "name": sub.name,
                "filter": {
                    "event_types": [t.value for t in sub.filter.event_types] if sub.filter.event_types else None,
                    "sources": sub.filter.sources,
                    "user_ids": sub.filter.user_ids,
                    "priorities": [p.value for p in sub.filter.priorities] if sub.filter.priorities else None
                },
                "once": sub.once,
                "created_at": sub.created_at.isoformat(),
                "call_count": sub.call_count,
                "last_called": sub.last_called.isoformat() if sub.last_called else None,
                "active": sub.active
            }
            for sub in self.subscriptions.values()
        ]
    
    async def _process_events(self):
        """Process events from the queue."""
        while True:
            try:
                events = []
                
                # Collect events for batch processing
                timeout = self.batch_timeout
                for _ in range(self.batch_size):
                    try:
                        event = await asyncio.wait_for(self.event_queue.get(), timeout=timeout)
                        events.append(event)
                        timeout = 0.1  # Shorter timeout for subsequent events
                    except asyncio.TimeoutError:
                        break
                
                if events:
                    await self._handle_event_batch(events)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"Error processing events: {e}")
                self.stats["errors"] += 1
                await asyncio.sleep(1)
    
    async def _handle_event_batch(self, events: List[Event]):
        """Handle a batch of events."""
        # Persist events to database
        await self._persist_events(events)
        
        # Publish to Redis for real-time notifications
        await self._publish_to_redis(events)
        
        # Handle subscriptions
        for event in events:
            await self._handle_event(event)
            self.stats["events_processed"] += 1
    
    async def _handle_event(self, event: Event):
        """Handle a single event by dispatching to matching subscriptions."""
        matching_subscriptions = [
            sub for sub in self.subscriptions.values()
            if sub.matches(event)
        ]
        
        # Execute handlers concurrently
        if matching_subscriptions:
            handler_tasks = [
                asyncio.create_task(sub.handle_event(event))
                for sub in matching_subscriptions
            ]
            
            await asyncio.gather(*handler_tasks, return_exceptions=True)
            self.stats["handlers_executed"] += len(handler_tasks)
        
        # Clean up once-only subscriptions
        for sub in matching_subscriptions:
            if sub.once and not sub.active:
                self.unsubscribe(sub.id)
    
    async def _persist_events(self, events: List[Event]):
        """Persist events to database."""
        from app.core.database import async_session_maker
        
        async with async_session_maker() as session:
            try:
                event_records = [
                    EventHistory(
                        id=event.id,
                        event_type=event.type.value,
                        source=event.source,
                        timestamp=event.timestamp,
                        data=event.data,
                        event_metadata=event.metadata,
                        priority=event.priority.value,
                        correlation_id=event.correlation_id,
                        user_id=event.user_id,
                        session_id=event.session_id
                    )
                    for event in events
                ]
                
                session.add_all(event_records)
                await session.commit()
                
            except Exception as e:
                print(f"Error persisting events: {e}")
                await session.rollback()
    
    async def _publish_to_redis(self, events: List[Event]):
        """Publish events to Redis for real-time notifications."""
        try:
            pipeline = cache_manager.redis.pipeline()
            
            for event in events:
                # Publish to general event stream
                pipeline.xadd(
                    "events:stream",
                    event.to_dict(),
                    maxlen=10000  # Keep last 10k events
                )
                
                # Publish to type-specific channel
                pipeline.publish(
                    f"events:{event.type.value}",
                    json.dumps(event.to_dict())
                )
                
                # Publish to user-specific channel if applicable
                if event.user_id:
                    pipeline.publish(
                        f"events:user:{event.user_id}",
                        json.dumps(event.to_dict())
                    )
            
            await pipeline.execute()
            
        except Exception as e:
            print(f"Error publishing to Redis: {e}")
    
    async def get_event_history(
        self,
        event_types: Optional[List[EventType]] = None,
        sources: Optional[List[str]] = None,
        user_id: Optional[str] = None,
        correlation_id: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """Get event history with filtering."""
        from app.core.database import async_session_maker
        from sqlalchemy import and_, or_
        
        async with async_session_maker() as session:
            query = session.query(EventHistory)
            
            # Apply filters
            conditions = []
            if event_types:
                conditions.append(EventHistory.event_type.in_([t.value for t in event_types]))
            if sources:
                conditions.append(EventHistory.source.in_(sources))
            if user_id:
                conditions.append(EventHistory.user_id == user_id)
            if correlation_id:
                conditions.append(EventHistory.correlation_id == correlation_id)
            
            if conditions:
                query = query.filter(and_(*conditions))
            
            # Order by timestamp descending
            query = query.order_by(EventHistory.timestamp.desc())
            
            # Apply pagination
            query = query.offset(offset).limit(limit)
            
            result = await session.execute(query)
            events = result.scalars().all()
            
            return [
                {
                    "id": str(event.id),
                    "type": event.event_type,
                    "source": event.source,
                    "timestamp": event.timestamp.isoformat(),
                    "data": event.data,
                    "metadata": event.event_metadata,
                    "priority": event.priority,
                    "correlation_id": event.correlation_id,
                    "user_id": str(event.user_id) if event.user_id else None,
                    "session_id": event.session_id
                }
                for event in events
            ]
    
    def get_stats(self) -> Dict[str, Any]:
        """Get publisher statistics."""
        return {
            **self.stats,
            "active_subscriptions": len([s for s in self.subscriptions.values() if s.active]),
            "total_subscriptions": len(self.subscriptions),
            "queue_size": self.event_queue.qsize()
        }


# Global event publisher instance
event_publisher = EventPublisher()


# Utility decorators and context managers

def event_emitter(event_type: EventType, source: str = "system"):
    """Decorator to automatically emit events for function calls."""
    def decorator(func):
        async def async_wrapper(*args, **kwargs):
            correlation_id = str(uuid.uuid4())
            
            # Emit start event
            await event_publisher.publish(
                event_type=EventType.CUSTOM,
                data={"function": func.__name__, "args": len(args), "kwargs": list(kwargs.keys())},
                source=source,
                correlation_id=correlation_id,
                metadata={"phase": "start"}
            )
            
            try:
                result = await func(*args, **kwargs)
                
                # Emit completion event
                await event_publisher.publish(
                    event_type=event_type,
                    data={"function": func.__name__, "success": True},
                    source=source,
                    correlation_id=correlation_id,
                    metadata={"phase": "complete"}
                )
                
                return result
                
            except Exception as e:
                # Emit error event
                await event_publisher.publish(
                    event_type=EventType.SYSTEM_ERROR,
                    data={"function": func.__name__, "error": str(e)},
                    source=source,
                    correlation_id=correlation_id,
                    metadata={"phase": "error"}
                )
                raise
        
        def sync_wrapper(*args, **kwargs):
            # For sync functions, we can't emit events directly
            # Could be enhanced to queue events for later processing
            return func(*args, **kwargs)
        
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


@asynccontextmanager
async def event_context(
    event_type: EventType,
    data: Dict[str, Any],
    source: str = "system",
    user_id: Optional[str] = None
):
    """Context manager for event-wrapped operations."""
    correlation_id = str(uuid.uuid4())
    
    # Emit start event
    await event_publisher.publish(
        event_type=EventType.CUSTOM,
        data={**data, "phase": "start"},
        source=source,
        user_id=user_id,
        correlation_id=correlation_id
    )
    
    try:
        yield correlation_id
        
        # Emit success event
        await event_publisher.publish(
            event_type=event_type,
            data={**data, "phase": "complete", "success": True},
            source=source,
            user_id=user_id,
            correlation_id=correlation_id
        )
        
    except Exception as e:
        # Emit error event
        await event_publisher.publish(
            event_type=EventType.SYSTEM_ERROR,
            data={**data, "phase": "error", "error": str(e)},
            source=source,
            user_id=user_id,
            correlation_id=correlation_id
        )
        raise