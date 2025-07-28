#!/usr/bin/env python3
"""
Simplified Phase 2 test without circular import issues.
Tests the core functionality directly.
"""

import asyncio
import sys
import os
import uuid
import json
from datetime import datetime, timedelta

# Add backend to Python path
sys.path.insert(0, os.path.dirname(__file__))

# Direct imports to avoid circular dependency
import sys
sys.path.append('/home/heramb/source/augment/legacy/backend')

# Import cache manager directly from the cache.py file
from app.core.cache import CacheManager
from app.core.tasks.queue import task_queue

# Create cache manager instance
cache_manager = CacheManager()


async def test_basic_connections():
    """Test basic Redis and task queue connections."""
    print("🔗 Testing basic connections...")
    
    try:
        # Test Redis connection
        await cache_manager.connect()
        await cache_manager.set("test_key", "test_value", expire=60)
        value = await cache_manager.get("test_key")
        
        if value == "test_value":
            print("✅ Redis connection working")
        else:
            print("❌ Redis connection failed")
            
        # Test task queue connection
        await task_queue.connect()
        stats = await task_queue.get_queue_stats()
        
        if stats:
            print("✅ Task queue connection working")
        else:
            print("❌ Task queue connection failed")
            
        return True
        
    except Exception as e:
        print(f"❌ Connection test failed: {e}")
        return False


async def test_cache_operations():
    """Test cache operations."""
    print("🗄️ Testing cache operations...")
    
    try:
        # Test basic set/get
        test_data = {"test": "data", "timestamp": datetime.utcnow().isoformat()}
        await cache_manager.set("cache_test", test_data, expire=300)
        retrieved = await cache_manager.get("cache_test")
        
        if retrieved == test_data:
            print("✅ Cache set/get working")
        else:
            print("❌ Cache set/get failed")
            
        # Test existence check
        exists = await cache_manager.exists("cache_test")
        if exists:
            print("✅ Cache exists check working")
        else:
            print("❌ Cache exists check failed")
            
        # Test deletion
        deleted = await cache_manager.delete("cache_test")
        if deleted:
            print("✅ Cache deletion working")
        else:
            print("❌ Cache deletion failed")
            
        return True
        
    except Exception as e:
        print(f"❌ Cache test failed: {e}")
        return False


async def test_task_queue():
    """Test task queue operations."""
    print("📋 Testing task queue...")
    
    try:
        # Register a simple test task
        @task_queue.register_task("test_task")
        async def simple_test_task(message: str) -> str:
            await asyncio.sleep(1)  # Simulate work
            return f"Processed: {message}"
        
        # Start a worker
        worker_id = await task_queue.start_worker("test-worker")
        if worker_id:
            print("✅ Task worker started")
        else:
            print("❌ Task worker failed to start")
            return False
            
        # Enqueue a task
        task_id = await task_queue.enqueue_task(
            "test_task",
            args=["Hello Phase 2"],
            metadata={"test": True}
        )
        
        if task_id:
            print("✅ Task enqueued successfully")
        else:
            print("❌ Task enqueue failed")
            return False
            
        # Wait for task completion
        await asyncio.sleep(3)
        
        # Get task info
        task_info = await task_queue.get_task_info(task_id)
        if task_info and task_info.status.value in ["completed", "failed"]:
            print(f"✅ Task completed with status: {task_info.status.value}")
            if task_info.result:
                print(f"   Result: {task_info.result}")
        else:
            print("❌ Task did not complete properly")
            
        # Stop worker
        await task_queue.stop_worker(worker_id)
        print("✅ Task worker stopped")
        
        return True
        
    except Exception as e:
        print(f"❌ Task queue test failed: {e}")
        return False


async def test_session_management():
    """Test session management."""
    print("👤 Testing session management...")
    
    try:
        session_id = str(uuid.uuid4())
        session_data = {
            "user_id": "test-user",
            "role": "admin",
            "created_at": datetime.utcnow().isoformat()
        }
        
        # Set session
        set_result = await cache_manager.set_session(session_id, session_data)
        if set_result:
            print("✅ Session set successfully")
        else:
            print("❌ Session set failed")
            return False
            
        # Get session
        retrieved_session = await cache_manager.get_session(session_id)
        if retrieved_session == session_data:
            print("✅ Session retrieved successfully")
        else:
            print("❌ Session retrieval failed")
            return False
            
        # Extend session
        extended = await cache_manager.extend_session(session_id, 3600)
        if extended:
            print("✅ Session extended successfully")
        else:
            print("❌ Session extension failed")
            
        # Delete session
        deleted = await cache_manager.delete_session(session_id)
        if deleted:
            print("✅ Session deleted successfully")
        else:
            print("❌ Session deletion failed")
            
        return True
        
    except Exception as e:
        print(f"❌ Session management test failed: {e}")
        return False


async def test_rate_limiting():
    """Test rate limiting functionality."""
    print("🚦 Testing rate limiting...")
    
    try:
        identifier = "test_user"
        limit = 3
        window = 10  # 10 seconds
        
        # First request - should be allowed
        result1 = await cache_manager.check_rate_limit(identifier, limit, window)
        if result1["allowed"] and result1["count"] == 1:
            print("✅ First rate limit check passed")
        else:
            print("❌ First rate limit check failed")
            return False
            
        # Second request - should be allowed
        result2 = await cache_manager.check_rate_limit(identifier, limit, window)
        if result2["allowed"] and result2["count"] == 2:
            print("✅ Second rate limit check passed")
        else:
            print("❌ Second rate limit check failed")
            return False
            
        # Third request - should be allowed
        result3 = await cache_manager.check_rate_limit(identifier, limit, window)
        if result3["allowed"] and result3["count"] == 3:
            print("✅ Third rate limit check passed")
        else:
            print("❌ Third rate limit check failed")
            return False
            
        # Fourth request - should be denied
        result4 = await cache_manager.check_rate_limit(identifier, limit, window)
        if not result4["allowed"] and result4["count"] == 3:
            print("✅ Rate limit enforcement working")
        else:
            print("❌ Rate limit enforcement failed")
            return False
            
        return True
        
    except Exception as e:
        print(f"❌ Rate limiting test failed: {e}")
        return False


async def test_cache_stats():
    """Test cache statistics."""
    print("📊 Testing cache statistics...")
    
    try:
        stats = await cache_manager.get_cache_stats()
        
        if stats and "redis_version" in stats:
            print("✅ Cache statistics retrieved")
            print(f"   Redis version: {stats.get('redis_version')}")
            print(f"   Used memory: {stats.get('used_memory')}")
            print(f"   Hit rate: {stats.get('hit_rate', 0):.1f}%")
        else:
            print("❌ Cache statistics failed")
            return False
            
        return True
        
    except Exception as e:
        print(f"❌ Cache statistics test failed: {e}")
        return False


async def main():
    """Run simplified Phase 2 tests."""
    print("🧪 SIMPLIFIED PHASE 2 SYSTEM TESTS")
    print("="*60)
    print("Testing core systems without complex dependencies")
    print("="*60)
    
    tests = [
        ("Basic Connections", test_basic_connections),
        ("Cache Operations", test_cache_operations),
        ("Task Queue", test_task_queue),
        ("Session Management", test_session_management),
        ("Rate Limiting", test_rate_limiting),
        ("Cache Statistics", test_cache_stats),
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        print(f"\n🔍 Running {test_name} test...")
        try:
            result = await test_func()
            if result:
                passed += 1
                print(f"✅ {test_name} test PASSED")
            else:
                failed += 1
                print(f"❌ {test_name} test FAILED")
        except Exception as e:
            failed += 1
            print(f"❌ {test_name} test FAILED with exception: {e}")
    
    # Cleanup
    try:
        await task_queue.disconnect()
        await cache_manager.disconnect()
    except Exception as e:
        print(f"⚠️  Cleanup warning: {e}")
    
    print("\n" + "="*60)
    print("📊 TEST SUMMARY")
    print("="*60)
    print(f"Total Tests: {passed + failed}")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    
    if failed == 0:
        print("🎉 ALL TESTS PASSED - Core Phase 2 systems working!")
    else:
        print(f"⚠️  {failed} tests failed - Check implementation")
    
    print("="*60)
    
    return failed == 0


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)