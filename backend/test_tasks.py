#!/usr/bin/env python3
"""
Test script for the background task system.
"""
import asyncio
import sys
import os

# Add the backend directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from app.core.tasks.queue import task_queue
from app.core.tasks import tasks  # Import to register tasks
from app.core.cache import cache_manager

async def test_task_system():
    """Test the background task system."""
    print("🧪 Testing background task system...")
    
    try:
        # Connect to Redis
        await task_queue.connect()
        await cache_manager.connect()
        
        # Start a worker
        print("👷 Starting test worker...")
        worker_id = await task_queue.start_worker("test-worker")
        print(f"✅ Worker started: {worker_id}")
        
        # Enqueue a test task
        print("📝 Enqueueing test task...")
        task_id = await task_queue.enqueue_task(
            task_name="test_task",
            args=["Hello from test!", 2],
            metadata={"test": True}
        )
        print(f"✅ Task enqueued: {task_id}")
        
        # Monitor task progress
        print("⏳ Monitoring task progress...")
        for i in range(10):
            task_info = await task_queue.get_task_info(task_id)
            if task_info:
                print(f"📊 Task {task_id}: {task_info.status}")
                if task_info.status.value in ["completed", "failed"]:
                    if task_info.result:
                        print(f"✅ Result: {task_info.result}")
                    if task_info.error:
                        print(f"❌ Error: {task_info.error}")
                    break
            await asyncio.sleep(1)
        
        # Test cache operations
        print("🗄️ Testing cache operations...")
        await cache_manager.set("test_key", {"message": "Hello Cache!"}, expire=60)
        cached_value = await cache_manager.get("test_key")
        print(f"✅ Cache test: {cached_value}")
        
        # Get queue stats
        stats = await task_queue.get_queue_stats()
        print(f"📊 Queue stats: {stats}")
        
        # Stop the worker
        print("🛑 Stopping test worker...")
        await task_queue.stop_worker(worker_id)
        
        print("✅ All tests completed successfully!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Cleanup
        await task_queue.disconnect()
        await cache_manager.disconnect()

if __name__ == "__main__":
    print("Testing Background Task System...")
    asyncio.run(test_task_system())
    print("Done!")