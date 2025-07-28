"""
WebSocket manager for real-time communication in Augment AI Platform.

This module provides a comprehensive WebSocket system for real-time updates,
live agent responses, workflow progress tracking, and collaborative features.
"""

from typing import Dict, Any, Optional, List, Set, Union
from enum import Enum
import uuid
import asyncio
import json
from datetime import datetime, timedelta
from dataclasses import dataclass, field

from fastapi import WebSocket, WebSocketDisconnect, WebSocketException
from pydantic import BaseModel, Field
import jwt

from app.core.cache import cache_manager
from app.core.events import event_publisher, EventType, Event


class MessageType(Enum):
    """WebSocket message types."""
    # Connection management
    PING = "ping"
    PONG = "pong"
    AUTH = "auth"
    AUTH_SUCCESS = "auth_success"
    AUTH_FAILURE = "auth_failure"
    
    # Subscriptions
    SUBSCRIBE = "subscribe"
    UNSUBSCRIBE = "unsubscribe"
    SUBSCRIPTION_SUCCESS = "subscription_success"
    SUBSCRIPTION_ERROR = "subscription_error"
    
    # Agent communication
    AGENT_QUERY = "agent_query"
    AGENT_RESPONSE = "agent_response"
    AGENT_THINKING = "agent_thinking"
    AGENT_ERROR = "agent_error"
    
    # Workflow updates
    WORKFLOW_STATUS = "workflow_status"
    WORKFLOW_PROGRESS = "workflow_progress"
    WORKFLOW_STEP = "workflow_step"
    
    # System notifications
    NOTIFICATION = "notification"
    SYSTEM_UPDATE = "system_update"
    ERROR = "error"
    
    # Collaborative features
    USER_JOINED = "user_joined"
    USER_LEFT = "user_left"
    USER_ACTIVITY = "user_activity"
    
    # Custom messages
    CUSTOM = "custom"


class SubscriptionType(Enum):
    """Types of subscriptions available."""
    EVENTS = "events"
    WORKFLOW = "workflow"
    AGENT = "agent"
    USER_ACTIVITY = "user_activity"
    SYSTEM = "system"
    ALL = "all"


@dataclass
class WebSocketMessage:
    """Represents a WebSocket message."""
    type: MessageType
    data: Dict[str, Any] = field(default_factory=dict)
    message_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = field(default_factory=datetime.utcnow)
    correlation_id: Optional[str] = None
    user_id: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert message to dictionary for JSON serialization."""
        return {
            "type": self.type.value,
            "data": self.data,
            "message_id": self.message_id,
            "timestamp": self.timestamp.isoformat(),
            "correlation_id": self.correlation_id,
            "user_id": self.user_id
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'WebSocketMessage':
        """Create message from dictionary."""
        return cls(
            type=MessageType(data.get("type", MessageType.CUSTOM.value)),
            data=data.get("data", {}),
            message_id=data.get("message_id", str(uuid.uuid4())),
            timestamp=datetime.fromisoformat(data.get("timestamp", datetime.utcnow().isoformat())),
            correlation_id=data.get("correlation_id"),
            user_id=data.get("user_id")
        )


@dataclass
class WebSocketConnection:
    """Represents a WebSocket connection."""
    id: str
    websocket: WebSocket
    user_id: Optional[str] = None
    authenticated: bool = False
    connected_at: datetime = field(default_factory=datetime.utcnow)
    last_ping: Optional[datetime] = None
    subscriptions: Set[str] = field(default_factory=set)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    async def send_message(self, message: WebSocketMessage):
        """Send a message to this connection."""
        try:
            await self.websocket.send_text(json.dumps(message.to_dict()))
        except Exception as e:
            print(f"Error sending message to connection {self.id}: {e}")
    
    async def send_json(self, data: Dict[str, Any]):
        """Send JSON data to this connection."""
        try:
            await self.websocket.send_json(data)
        except Exception as e:
            print(f"Error sending JSON to connection {self.id}: {e}")


class WebSocketManager:
    """
    Manages WebSocket connections and real-time communication.
    
    Features:
    - Connection lifecycle management
    - Authentication and authorization
    - Message routing and broadcasting
    - Event subscriptions and notifications
    - Heartbeat and connection health monitoring
    - User presence and activity tracking
    - Room-based communication
    """
    
    def __init__(self):
        self.connections: Dict[str, WebSocketConnection] = {}
        self.user_connections: Dict[str, Set[str]] = {}  # user_id -> connection_ids
        self.rooms: Dict[str, Set[str]] = {}  # room_name -> connection_ids
        self.heartbeat_task: Optional[asyncio.Task] = None
        self.heartbeat_interval = 30  # seconds
        self.connection_timeout = 60  # seconds
        
        # Statistics
        self.stats = {
            "total_connections": 0,
            "active_connections": 0,
            "messages_sent": 0,
            "messages_received": 0,
            "authentication_attempts": 0,
            "authentication_failures": 0
        }
    
    async def start(self):
        """Start the WebSocket manager."""
        if not self.heartbeat_task:
            self.heartbeat_task = asyncio.create_task(self._heartbeat_loop())
        
        # Subscribe to events for broadcasting
        event_publisher.subscribe(
            handler=self._handle_event,
            name="websocket_event_handler"
        )
    
    async def stop(self):
        """Stop the WebSocket manager."""
        if self.heartbeat_task:
            self.heartbeat_task.cancel()
            try:
                await self.heartbeat_task
            except asyncio.CancelledError:
                pass
            self.heartbeat_task = None
        
        # Close all connections
        for connection in list(self.connections.values()):
            await self.disconnect(connection.id)
    
    async def connect(self, websocket: WebSocket) -> str:
        """Accept a new WebSocket connection."""
        connection_id = str(uuid.uuid4())
        await websocket.accept()
        
        connection = WebSocketConnection(
            id=connection_id,
            websocket=websocket
        )
        
        self.connections[connection_id] = connection
        self.stats["total_connections"] += 1
        self.stats["active_connections"] = len(self.connections)
        
        # Send welcome message
        welcome_message = WebSocketMessage(
            type=MessageType.AUTH,
            data={
                "connection_id": connection_id,
                "message": "Connection established. Please authenticate.",
                "timestamp": datetime.utcnow().isoformat()
            }
        )
        await connection.send_message(welcome_message)
        
        return connection_id
    
    async def disconnect(self, connection_id: str):
        """Disconnect a WebSocket connection."""
        if connection_id not in self.connections:
            return
        
        connection = self.connections[connection_id]
        
        # Remove from user connections
        if connection.user_id and connection.user_id in self.user_connections:
            self.user_connections[connection.user_id].discard(connection_id)
            if not self.user_connections[connection.user_id]:
                del self.user_connections[connection.user_id]
        
        # Remove from rooms
        for room_connections in self.rooms.values():
            room_connections.discard(connection_id)
        
        # Close WebSocket
        try:
            await connection.websocket.close()
        except Exception:
            pass
        
        # Remove from connections
        del self.connections[connection_id]
        self.stats["active_connections"] = len(self.connections)
        
        # Notify other users if this was an authenticated connection
        if connection.authenticated and connection.user_id:
            await self._broadcast_user_left(connection.user_id)
    
    async def handle_message(self, connection_id: str, message_data: Dict[str, Any]):
        """Handle incoming WebSocket message."""
        if connection_id not in self.connections:
            return
        
        connection = self.connections[connection_id]
        self.stats["messages_received"] += 1
        
        try:
            message = WebSocketMessage.from_dict(message_data)
            await self._process_message(connection, message)
        except Exception as e:
            error_message = WebSocketMessage(
                type=MessageType.ERROR,
                data={"error": f"Invalid message format: {str(e)}"}
            )
            await connection.send_message(error_message)
    
    async def _process_message(self, connection: WebSocketConnection, message: WebSocketMessage):
        """Process a received message."""
        if message.type == MessageType.PING:
            await self._handle_ping(connection)
        elif message.type == MessageType.AUTH:
            await self._handle_auth(connection, message)
        elif message.type == MessageType.SUBSCRIBE:
            await self._handle_subscribe(connection, message)
        elif message.type == MessageType.UNSUBSCRIBE:
            await self._handle_unsubscribe(connection, message)
        elif message.type == MessageType.AGENT_QUERY:
            await self._handle_agent_query(connection, message)
        else:
            # Handle custom messages or unknown types
            await self._handle_custom_message(connection, message)
    
    async def _handle_ping(self, connection: WebSocketConnection):
        """Handle ping message."""
        connection.last_ping = datetime.utcnow()
        pong_message = WebSocketMessage(
            type=MessageType.PONG,
            data={"timestamp": datetime.utcnow().isoformat()}
        )
        await connection.send_message(pong_message)
    
    async def _handle_auth(self, connection: WebSocketConnection, message: WebSocketMessage):
        """Handle authentication message."""
        self.stats["authentication_attempts"] += 1
        
        token = message.data.get("token")
        if not token:
            await self._send_auth_failure(connection, "No token provided")
            return
        
        try:
            # Verify JWT token (simplified - use your actual auth system)
            from app.core.config import settings
            payload = jwt.decode(token, settings.secret_key, algorithms=["HS256"])
            user_id = payload.get("sub")
            
            if user_id:
                connection.user_id = user_id
                connection.authenticated = True
                
                # Track user connections
                if user_id not in self.user_connections:
                    self.user_connections[user_id] = set()
                self.user_connections[user_id].add(connection.id)
                
                # Send success response
                auth_success = WebSocketMessage(
                    type=MessageType.AUTH_SUCCESS,
                    data={
                        "user_id": user_id,
                        "connection_id": connection.id,
                        "timestamp": datetime.utcnow().isoformat()
                    },
                    user_id=user_id
                )
                await connection.send_message(auth_success)
                
                # Notify other users
                await self._broadcast_user_joined(user_id)
            else:
                await self._send_auth_failure(connection, "Invalid token payload")
                
        except jwt.InvalidTokenError:
            await self._send_auth_failure(connection, "Invalid token")
        except Exception as e:
            await self._send_auth_failure(connection, f"Authentication error: {str(e)}")
    
    async def _send_auth_failure(self, connection: WebSocketConnection, reason: str):
        """Send authentication failure message."""
        self.stats["authentication_failures"] += 1
        auth_failure = WebSocketMessage(
            type=MessageType.AUTH_FAILURE,
            data={"reason": reason, "timestamp": datetime.utcnow().isoformat()}
        )
        await connection.send_message(auth_failure)
    
    async def _handle_subscribe(self, connection: WebSocketConnection, message: WebSocketMessage):
        """Handle subscription message."""
        if not connection.authenticated:
            error_message = WebSocketMessage(
                type=MessageType.SUBSCRIPTION_ERROR,
                data={"error": "Authentication required for subscriptions"}
            )
            await connection.send_message(error_message)
            return
        
        subscription_type = message.data.get("subscription_type")
        filters = message.data.get("filters", {})
        
        # Create subscription ID
        subscription_id = f"{connection.id}:{subscription_type}:{uuid.uuid4()}"
        connection.subscriptions.add(subscription_id)
        
        # Store subscription details in cache
        await cache_manager.set(
            f"ws_subscription:{subscription_id}",
            {
                "connection_id": connection.id,
                "user_id": connection.user_id,
                "type": subscription_type,
                "filters": filters,
                "created_at": datetime.utcnow().isoformat()
            },
            expire=3600
        )
        
        success_message = WebSocketMessage(
            type=MessageType.SUBSCRIPTION_SUCCESS,
            data={
                "subscription_id": subscription_id,
                "subscription_type": subscription_type,
                "filters": filters
            }
        )
        await connection.send_message(success_message)
    
    async def _handle_unsubscribe(self, connection: WebSocketConnection, message: WebSocketMessage):
        """Handle unsubscribe message."""
        subscription_id = message.data.get("subscription_id")
        if subscription_id in connection.subscriptions:
            connection.subscriptions.remove(subscription_id)
            await cache_manager.delete(f"ws_subscription:{subscription_id}")
    
    async def _handle_agent_query(self, connection: WebSocketConnection, message: WebSocketMessage):
        """Handle agent query message."""
        if not connection.authenticated:
            error_message = WebSocketMessage(
                type=MessageType.ERROR,
                data={"error": "Authentication required for agent queries"}
            )
            await connection.send_message(error_message)
            return
        
        # Forward to agent system (would integrate with actual agent)
        query = message.data.get("query", "")
        agent_type = message.data.get("agent_type", "augment")
        
        # Simulate agent processing
        thinking_message = WebSocketMessage(
            type=MessageType.AGENT_THINKING,
            data={
                "query": query,
                "agent_type": agent_type,
                "status": "Processing query..."
            },
            correlation_id=message.correlation_id,
            user_id=connection.user_id
        )
        await connection.send_message(thinking_message)
        
        # This would integrate with your actual agent system
        # For now, send a mock response
        await asyncio.sleep(2)  # Simulate processing time
        
        response_message = WebSocketMessage(
            type=MessageType.AGENT_RESPONSE,
            data={
                "query": query,
                "agent_type": agent_type,
                "response": f"Mock response to: {query}",
                "reasoning": ["Step 1: Analyzed query", "Step 2: Generated response"],
                "sources": []
            },
            correlation_id=message.correlation_id,
            user_id=connection.user_id
        )
        await connection.send_message(response_message)
    
    async def _handle_custom_message(self, connection: WebSocketConnection, message: WebSocketMessage):
        """Handle custom message types."""
        # Log or process custom messages as needed
        pass
    
    async def _handle_event(self, event: Event):
        """Handle events from the event publisher."""
        # Convert event to WebSocket message
        message = WebSocketMessage(
            type=MessageType.NOTIFICATION,
            data={
                "event_type": event.type.value,
                "event_data": event.data,
                "source": event.source
            },
            correlation_id=event.correlation_id,
            user_id=event.user_id
        )
        
        # Broadcast to relevant connections
        if event.user_id:
            await self.send_to_user(event.user_id, message)
        else:
            await self.broadcast(message)
    
    async def send_to_user(self, user_id: str, message: WebSocketMessage):
        """Send message to all connections of a specific user."""
        if user_id in self.user_connections:
            for connection_id in self.user_connections[user_id]:
                if connection_id in self.connections:
                    await self.connections[connection_id].send_message(message)
                    self.stats["messages_sent"] += 1
    
    async def send_to_connection(self, connection_id: str, message: WebSocketMessage):
        """Send message to a specific connection."""
        if connection_id in self.connections:
            await self.connections[connection_id].send_message(message)
            self.stats["messages_sent"] += 1
    
    async def broadcast(self, message: WebSocketMessage, exclude_connections: Optional[Set[str]] = None):
        """Broadcast message to all authenticated connections."""
        exclude_connections = exclude_connections or set()
        
        for connection in self.connections.values():
            if connection.authenticated and connection.id not in exclude_connections:
                await connection.send_message(message)
                self.stats["messages_sent"] += 1
    
    async def broadcast_to_room(self, room_name: str, message: WebSocketMessage):
        """Broadcast message to all connections in a room."""
        if room_name in self.rooms:
            for connection_id in self.rooms[room_name]:
                if connection_id in self.connections:
                    await self.connections[connection_id].send_message(message)
                    self.stats["messages_sent"] += 1
    
    async def join_room(self, connection_id: str, room_name: str):
        """Add connection to a room."""
        if connection_id in self.connections:
            if room_name not in self.rooms:
                self.rooms[room_name] = set()
            self.rooms[room_name].add(connection_id)
    
    async def leave_room(self, connection_id: str, room_name: str):
        """Remove connection from a room."""
        if room_name in self.rooms:
            self.rooms[room_name].discard(connection_id)
            if not self.rooms[room_name]:
                del self.rooms[room_name]
    
    async def _broadcast_user_joined(self, user_id: str):
        """Broadcast user joined notification."""
        message = WebSocketMessage(
            type=MessageType.USER_JOINED,
            data={
                "user_id": user_id,
                "timestamp": datetime.utcnow().isoformat()
            }
        )
        await self.broadcast(message)
    
    async def _broadcast_user_left(self, user_id: str):
        """Broadcast user left notification."""
        message = WebSocketMessage(
            type=MessageType.USER_LEFT,
            data={
                "user_id": user_id,
                "timestamp": datetime.utcnow().isoformat()
            }
        )
        await self.broadcast(message)
    
    async def _heartbeat_loop(self):
        """Heartbeat loop to monitor connection health."""
        while True:
            try:
                current_time = datetime.utcnow()
                
                # Check for stale connections
                stale_connections = []
                for connection in self.connections.values():
                    if connection.last_ping:
                        time_since_ping = current_time - connection.last_ping
                        if time_since_ping.total_seconds() > self.connection_timeout:
                            stale_connections.append(connection.id)
                
                # Disconnect stale connections
                for connection_id in stale_connections:
                    await self.disconnect(connection_id)
                
                # Send ping to all connections
                ping_message = WebSocketMessage(
                    type=MessageType.PING,
                    data={"timestamp": current_time.isoformat()}
                )
                
                for connection in list(self.connections.values()):
                    try:
                        await connection.send_message(ping_message)
                    except Exception:
                        # Connection is broken, mark for removal
                        stale_connections.append(connection.id)
                
                # Clean up broken connections
                for connection_id in stale_connections:
                    await self.disconnect(connection_id)
                
                await asyncio.sleep(self.heartbeat_interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                print(f"Error in heartbeat loop: {e}")
                await asyncio.sleep(5)
    
    def get_stats(self) -> Dict[str, Any]:
        """Get WebSocket manager statistics."""
        return {
            **self.stats,
            "active_users": len(self.user_connections),
            "active_rooms": len(self.rooms),
            "authenticated_connections": len([c for c in self.connections.values() if c.authenticated])
        }
    
    def get_user_connections(self, user_id: str) -> List[str]:
        """Get all connection IDs for a user."""
        return list(self.user_connections.get(user_id, set()))
    
    def get_room_connections(self, room_name: str) -> List[str]:
        """Get all connection IDs in a room."""
        return list(self.rooms.get(room_name, set()))


# Global WebSocket manager instance
websocket_manager = WebSocketManager()