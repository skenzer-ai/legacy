#!/usr/bin/env python3
"""
Test core systems directly without complex imports.
"""

import asyncio
import sys
import os
import uuid
import json
from datetime import datetime, timedelta

# Add backend to Python path
sys.path.insert(0, os.path.dirname(__file__))

# Import directly from the cache.py file to avoid circular imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app', 'core'))
from cache import CacheManager
from config import settings

# Import task queue components directly
from tasks.queue import TaskQueue, TaskStatus


async def test_cache_manager():
    """Test cache manager functionality."""
    print("🗄️ Testing Cache Manager...")
    
    cache = CacheManager()
    
    try:
        # Test connection
        await cache.connect()
        print("✅ Cache connection established")
        
        # Test basic operations
        test_data = {"message": "Hello Phase 2", "timestamp": datetime.utcnow().isoformat()}
        
        # Set
        set_result = await cache.set("test_key", test_data, expire=60)
        if set_result:
            print("✅ Cache set operation working")
        else:
            print("❌ Cache set operation failed")
            return False
            
        # Get
        retrieved = await cache.get("test_key")
        if retrieved == test_data:
            print("✅ Cache get operation working")
        else:
            print("❌ Cache get operation failed")
            return False
            
        # Exists
        exists = await cache.exists("test_key")
        if exists:
            print("✅ Cache exists check working")
        else:
            print("❌ Cache exists check failed")
            return False
            
        # Delete
        deleted = await cache.delete("test_key")
        if deleted:
            print("✅ Cache delete operation working")
        else:
            print("❌ Cache delete operation failed")
            
        # Test session operations
        session_id = str(uuid.uuid4())
        session_data = {"user_id": "test-user", "role": "admin"}
        
        await cache.set_session(session_id, session_data)
        retrieved_session = await cache.get_session(session_id)
        
        if retrieved_session == session_data:
            print("✅ Session management working")
        else:
            print("❌ Session management failed")
            
        # Test rate limiting
        rate_result = await cache.check_rate_limit("test_user", 5, 60)
        if rate_result["allowed"] and rate_result["count"] == 1:
            print("✅ Rate limiting working")
        else:
            print("❌ Rate limiting failed")
            
        # Cleanup
        await cache.disconnect()
        print("✅ Cache manager tests completed successfully")
        return True
        
    except Exception as e:
        print(f"❌ Cache manager test failed: {e}")
        return False


async def test_task_queue():
    """Test task queue functionality."""
    print("📋 Testing Task Queue...")
    
    queue = TaskQueue()
    
    try:
        # Connect
        await queue.connect()
        print("✅ Task queue connection established")
        
        # Register a test task
        @queue.register_task("simple_test")
        async def simple_test_task(message: str) -> str:
            await asyncio.sleep(0.5)  # Simulate work
            return f"Processed: {message}"
        
        print("✅ Test task registered")
        
        # Start worker
        worker_id = await queue.start_worker("test-worker")
        if worker_id:
            print("✅ Worker started successfully")
        else:
            print("❌ Worker failed to start")
            return False
            
        # Enqueue task
        task_id = await queue.enqueue_task(
            "simple_test",
            args=["Hello from test"],
            metadata={"test": True}
        )
        
        if task_id:
            print("✅ Task enqueued successfully")
        else:
            print("❌ Task enqueue failed")
            return False
            
        # Wait for processing
        await asyncio.sleep(2)
        
        # Check task status
        task_info = await queue.get_task_info(task_id)
        if task_info:
            print(f"✅ Task status: {task_info.status.value}")
            if task_info.result:
                print(f"   Result: {task_info.result}")
        else:
            print("❌ Could not get task info")
            
        # Get queue stats
        stats = await queue.get_queue_stats()
        if stats:
            print("✅ Queue statistics retrieved")
            print(f"   Stats: {stats}")
        else:
            print("❌ Could not get queue stats")
            
        # Stop worker
        await queue.stop_worker(worker_id)
        print("✅ Worker stopped")
        
        # Cleanup
        await queue.disconnect()
        print("✅ Task queue tests completed successfully")
        return True
        
    except Exception as e:
        print(f"❌ Task queue test failed: {e}")
        return False


async def test_redis_connectivity():
    """Test Redis connectivity directly."""
    print("🔗 Testing Redis Connectivity...")
    
    try:
        import redis.asyncio as redis
        
        # Create Redis connection
        redis_client = redis.from_url(
            settings.redis_url,
            encoding="utf-8",
            decode_responses=True
        )
        
        # Test ping
        pong = await redis_client.ping()
        if pong:
            print("✅ Redis ping successful")
        else:
            print("❌ Redis ping failed")
            return False
            
        # Test set/get
        await redis_client.set("direct_test", "working", ex=60)
        value = await redis_client.get("direct_test")
        
        if value == "working":
            print("✅ Direct Redis operations working")
        else:
            print("❌ Direct Redis operations failed")
            return False
            
        # Test info
        info = await redis_client.info()
        if info:
            print("✅ Redis info retrieved")
            print(f"   Redis version: {info.get('redis_version', 'unknown')}")
            print(f"   Used memory: {info.get('used_memory_human', 'unknown')}")
        else:
            print("❌ Redis info failed")
            
        # Cleanup
        await redis_client.delete("direct_test")
        await redis_client.close()
        
        print("✅ Redis connectivity tests completed successfully")
        return True
        
    except Exception as e:
        print(f"❌ Redis connectivity test failed: {e}")
        return False


async def test_configuration():
    """Test configuration loading."""
    print("⚙️ Testing Configuration...")
    
    try:
        # Check that settings are loaded
        if hasattr(settings, 'redis_url') and settings.redis_url:
            print("✅ Redis URL configured")
        else:
            print("❌ Redis URL not configured")
            return False
            
        if hasattr(settings, 'database_url') and settings.database_url:
            print("✅ Database URL configured")
        else:
            print("❌ Database URL not configured")
            return False
            
        if hasattr(settings, 'secret_key') and settings.secret_key:
            print("✅ Secret key configured")
        else:
            print("❌ Secret key not configured")
            return False
            
        print("✅ Configuration tests completed successfully")
        return True
        
    except Exception as e:
        print(f"❌ Configuration test failed: {e}")
        return False


async def main():
    """Run all core system tests."""
    print("🧪 CORE SYSTEMS TEST")
    print("="*50)
    print("Testing fundamental Phase 2 components")
    print("="*50)
    
    tests = [
        ("Configuration", test_configuration),
        ("Redis Connectivity", test_redis_connectivity),
        ("Cache Manager", test_cache_manager),
        ("Task Queue", test_task_queue),
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
            import traceback
            traceback.print_exc()
    
    print("\n" + "="*50)
    print("📊 CORE SYSTEMS TEST SUMMARY")
    print("="*50)
    print(f"Total Tests: {passed + failed}")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    
    if failed == 0:
        print("🎉 ALL CORE SYSTEMS WORKING!")
        print("✅ Phase 2 foundation is solid")
    else:
        print(f"⚠️  {failed} tests failed")
        print("❌ Phase 2 foundation needs attention")
    
    print("="*50)
    
    return failed == 0


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)