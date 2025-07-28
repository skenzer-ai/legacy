#!/usr/bin/env python3
"""
Test the working Phase 2 systems using correct imports.
"""

import asyncio
import sys
import os
import uuid
from datetime import datetime

# Add backend to Python path
sys.path.insert(0, os.path.dirname(__file__))

# Import from the working modules directly
from app.core.cache import cache_manager
from app.core.tasks.queue import task_queue


async def test_basic_phase2_systems():
    """Test the core Phase 2 systems that are actually working."""
    print("🧪 TESTING WORKING PHASE 2 SYSTEMS")
    print("="*60)
    
    results = {"passed": 0, "failed": 0}
    
    # Test 1: Redis Cache Manager
    print("\n🗄️ Testing Redis Cache Manager...")
    try:
        await cache_manager.connect()
        
        # Test basic operations
        test_data = {"message": "Phase 2 test", "timestamp": datetime.utcnow().isoformat()}
        await cache_manager.set("test_key", test_data, expire=60)
        retrieved = await cache_manager.get("test_key")
        
        if retrieved == test_data:
            print("✅ Cache set/get operations working")
            results["passed"] += 1
        else:
            print("❌ Cache operations failed")
            results["failed"] += 1
            
        # Test session management
        session_id = str(uuid.uuid4())
        session_data = {"user_id": "test-user", "role": "admin"}
        await cache_manager.set_session(session_id, session_data)
        retrieved_session = await cache_manager.get_session(session_id)
        
        if retrieved_session == session_data:
            print("✅ Session management working")
            results["passed"] += 1
        else:
            print("❌ Session management failed")
            results["failed"] += 1
            
        # Test rate limiting
        rate_result = await cache_manager.check_rate_limit("test_user", 5, 60)
        if rate_result["allowed"]:
            print("✅ Rate limiting working")
            results["passed"] += 1
        else:
            print("❌ Rate limiting failed")
            results["failed"] += 1
            
    except Exception as e:
        print(f"❌ Cache manager test failed: {e}")
        results["failed"] += 1
    
    # Test 2: Task Queue System
    print("\n📋 Testing Task Queue System...")
    try:
        await task_queue.connect()
        
        # Register test task
        @task_queue.register_task("phase2_test")
        async def test_task(message: str) -> str:
            await asyncio.sleep(0.5)
            return f"Processed: {message}"
        
        # Start worker
        worker_id = await task_queue.start_worker("test-worker")
        if worker_id:
            print("✅ Task worker started")
            results["passed"] += 1
        else:
            print("❌ Task worker failed")
            results["failed"] += 1
            
        # Enqueue task
        task_id = await task_queue.enqueue_task(
            "phase2_test",
            args=["Hello Phase 2"],
            metadata={"test": True}
        )
        
        if task_id:
            print("✅ Task enqueued successfully")
            results["passed"] += 1
            
            # Wait and check result
            await asyncio.sleep(2)
            task_info = await task_queue.get_task_info(task_id)
            if task_info and task_info.status.value in ["completed"]:
                print("✅ Task completed successfully")
                print(f"   Result: {task_info.result}")
                results["passed"] += 1
            else:
                print("❌ Task did not complete properly")
                results["failed"] += 1
        else:
            print("❌ Task enqueue failed")
            results["failed"] += 1
            
        # Stop worker
        await task_queue.stop_worker(worker_id)
        
    except Exception as e:
        print(f"❌ Task queue test failed: {e}")
        results["failed"] += 1
    
    # Test 3: System Integration
    print("\n🔧 Testing System Integration...")
    try:
        # Test that cache and task queue work together
        integration_key = f"task_result_{uuid.uuid4()}"
        
        @task_queue.register_task("cache_integration_test")
        async def cache_integration_task(cache_key: str, data: dict) -> str:
            # Task stores result in cache
            await cache_manager.set(cache_key, data, expire=300)
            return f"Stored data in cache with key: {cache_key}"
        
        # Start worker for integration test
        worker_id = await task_queue.start_worker("integration-worker")
        
        # Enqueue integration task
        test_data = {"integration": "success", "timestamp": datetime.utcnow().isoformat()}
        task_id = await task_queue.enqueue_task(
            "cache_integration_test",
            args=[integration_key, test_data]
        )
        
        # Wait for completion
        await asyncio.sleep(2)
        
        # Check if data was stored in cache by the task
        cached_data = await cache_manager.get(integration_key)
        if cached_data == test_data:
            print("✅ Cache + Task queue integration working")
            results["passed"] += 1
        else:
            print("❌ Integration test failed")
            results["failed"] += 1
            
        await task_queue.stop_worker(worker_id)
        
    except Exception as e:
        print(f"❌ Integration test failed: {e}")
        results["failed"] += 1
    
    # Test 4: Check System Stats
    print("\n📊 Testing System Statistics...")
    try:
        # Cache stats
        cache_stats = await cache_manager.get_cache_stats()
        if cache_stats and "redis_version" in cache_stats:
            print(f"✅ Cache stats: Redis {cache_stats['redis_version']}")
            print(f"   Used memory: {cache_stats.get('used_memory', 'unknown')}")
            results["passed"] += 1
        else:
            print("❌ Cache stats failed")
            results["failed"] += 1
            
        # Queue stats
        queue_stats = await task_queue.get_queue_stats()
        if queue_stats:
            print(f"✅ Queue stats: {queue_stats}")
            results["passed"] += 1
        else:
            print("❌ Queue stats failed")
            results["failed"] += 1
            
    except Exception as e:
        print(f"❌ Stats test failed: {e}")
        results["failed"] += 1
    
    # Cleanup
    try:
        await task_queue.disconnect()
        await cache_manager.disconnect()
    except Exception as e:
        print(f"⚠️  Cleanup warning: {e}")
    
    # Summary
    print("\n" + "="*60)
    print("📊 PHASE 2 SYSTEMS TEST RESULTS")
    print("="*60)
    total = results["passed"] + results["failed"]
    print(f"Total Tests: {total}")
    print(f"Passed: {results['passed']}")
    print(f"Failed: {results['failed']}")
    
    if results["failed"] == 0:
        print("\n🎉 ALL PHASE 2 CORE SYSTEMS ARE WORKING!")
        print("✅ Redis cache manager: OPERATIONAL")
        print("✅ Background task queue: OPERATIONAL")
        print("✅ Session management: OPERATIONAL") 
        print("✅ Rate limiting: OPERATIONAL")
        print("✅ System integration: OPERATIONAL")
        print("\n🚀 Ready to proceed to Phase 3!")
    else:
        print(f"\n⚠️  {results['failed']} tests failed")
        print("❌ Some systems need attention")
    
    print("="*60)
    
    return results["failed"] == 0


if __name__ == "__main__":
    success = asyncio.run(test_basic_phase2_systems())
    sys.exit(0 if success else 1)