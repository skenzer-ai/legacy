"""
Application lifespan management for FastAPI.
Handles startup and shutdown events for background services.
"""
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI

from app.core.tasks.queue import task_queue
from app.core.tasks import tasks  # Import to register tasks
from app.core.cache import cache_manager, advanced_cache
from app.core.events import event_publisher
from app.core.websocket import websocket_manager
from app.core.progress import progress_manager
from app.core.database import create_db_and_tables


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.
    Handles startup and shutdown events.
    """
    print("🚀 Starting Augment AI Platform...")
    
    # Startup
    try:
        # Initialize database
        print("📊 Initializing database...")
        await create_db_and_tables()
        
        # Connect to Redis
        print("🔗 Connecting to Redis...")
        await cache_manager.connect()
        await task_queue.connect()
        
        # Start advanced cache system
        print("🚀 Starting advanced cache system...")
        await advanced_cache.start()
        
        # Start event publisher
        print("📡 Starting event publisher...")
        await event_publisher.start()
        
        # Start WebSocket manager
        print("🌐 Starting WebSocket manager...")
        await websocket_manager.start()
        
        # Start background workers
        print("👷 Starting background workers...")
        worker1_id = await task_queue.start_worker("primary-worker")
        worker2_id = await task_queue.start_worker("secondary-worker")
        
        print(f"✅ Workers started: {worker1_id}, {worker2_id}")
        
        # Schedule periodic tasks
        print("⏰ Scheduling periodic maintenance tasks...")
        await tasks.schedule_periodic_tasks()
        
        # Cache startup timestamp
        from datetime import datetime
        await cache_manager.set(
            "system:startup_time",
            datetime.utcnow().isoformat(),
            expire=86400  # 24 hours
        )
        
        print("✅ Augment AI Platform started successfully!")
        print("📊 Available endpoints:")
        print("   - Authentication: /api/v1/auth/*")
        print("   - User Management: /api/v1/users/*") 
        print("   - Task Management: /api/v1/tasks/*")
        print("   - Agent Services: /api/v1/agents/*")
        print("   - WebSocket: /ws")
        print("   - Progress Tracking: /api/v1/progress/*")
        print("   - Event History: /api/v1/events/*")
        print("   - API Documentation: /docs")
        print("🎯 Advanced features enabled:")
        print("   - Multi-level caching with intelligent invalidation")
        print("   - Event-driven architecture with pub/sub")
        print("   - Real-time WebSocket communication")
        print("   - Workflow state machine orchestration")
        print("   - Comprehensive progress tracking")
        
        yield
        
    except Exception as e:
        print(f"❌ Startup failed: {e}")
        raise
        
    # Shutdown
    print("🛑 Shutting down Augment AI Platform...")
    
    try:
        # Stop background workers
        print("👷 Stopping background workers...")
        await task_queue.stop_all_workers()
        
        # Stop advanced systems
        print("🛑 Stopping advanced systems...")
        await websocket_manager.stop()
        await event_publisher.stop()
        await advanced_cache.stop()
        
        # Disconnect from Redis
        print("🔗 Disconnecting from Redis...")
        await task_queue.disconnect()
        await cache_manager.disconnect()
        
        print("✅ Augment AI Platform shut down gracefully")
        
    except Exception as e:
        print(f"❌ Shutdown error: {e}")
        # Don't re-raise during shutdown