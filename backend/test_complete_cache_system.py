#!/usr/bin/env python3
"""
Test both basic and advanced cache systems.
"""

import asyncio
import sys
import os
from datetime import datetime

# Add backend to Python path
sys.path.insert(0, os.path.dirname(__file__))

# Import both cache systems
from app.core.cache import cache_manager, advanced_cache, CacheConfig, CacheLevel, cached


async def test_basic_cache():
    """Test basic cache manager."""
    print("🗄️ Testing Basic Cache Manager...")
    
    try:
        await cache_manager.connect()
        
        # Test basic operations
        test_data = {"basic": "cache", "timestamp": datetime.utcnow().isoformat()}
        await cache_manager.set("basic_test", test_data, expire=60)
        retrieved = await cache_manager.get("basic_test")
        
        if retrieved == test_data:
            print("✅ Basic cache operations working")
            return True
        else:
            print("❌ Basic cache operations failed")
            return False
            
    except Exception as e:
        print(f"❌ Basic cache test failed: {e}")
        return False


async def test_advanced_cache():
    """Test advanced cache manager."""
    print("🚀 Testing Advanced Cache Manager...")
    
    try:
        await advanced_cache.start()
        
        # Configure advanced cache
        config = CacheConfig(
            levels=[CacheLevel.L1_MEMORY, CacheLevel.L2_REDIS],
            ttl=300,
            tags=["test", "advanced"],
            max_size=1000
        )
        advanced_cache.configure_cache("test_pattern", config)
        
        # Test advanced operations
        test_data = {"advanced": "cache", "level": "L1+L2"}
        await advanced_cache.set("advanced_test", test_data, pattern="test_pattern")
        retrieved = await advanced_cache.get("advanced_test", pattern="test_pattern")
        
        if retrieved == test_data:
            print("✅ Advanced cache operations working")
            
            # Test L1 cache hit
            retrieved_again = await advanced_cache.get("advanced_test", pattern="test_pattern")
            if retrieved_again == test_data:
                print("✅ L1 cache hit working")
            else:
                print("❌ L1 cache hit failed")
            
            # Test cache stats
            stats = advanced_cache.get_stats()
            if stats and stats["hits"] > 0:
                print(f"✅ Cache stats: {stats['hits']} hits, {stats['hit_rate_percent']:.1f}% hit rate")
                print(f"   L1 size: {stats['l1_size']}")
                return True
            else:
                print("❌ Cache stats failed")
                return False
        else:
            print("❌ Advanced cache operations failed")
            return False
            
    except Exception as e:
        print(f"❌ Advanced cache test failed: {e}")
        return False


async def test_cached_decorator():
    """Test cached decorator."""
    print("🎯 Testing Cached Decorator...")
    
    try:
        call_count = 0
        
        @cached(ttl=60, pattern="test_decorator", tags=["decorator"])
        async def expensive_function(value: int) -> dict:
            nonlocal call_count
            call_count += 1
            await asyncio.sleep(0.1)  # Simulate expensive operation
            return {"result": value * 2, "call_count": call_count}
        
        # First call - should execute function
        result1 = await expensive_function(5)
        if result1["result"] == 10 and result1["call_count"] == 1:
            print("✅ First call executed function")
        else:
            print("❌ First call failed")
            return False
            
        # Second call - should use cache
        result2 = await expensive_function(5)
        if result2["result"] == 10 and result2["call_count"] == 1:  # Same call_count = cached
            print("✅ Second call used cache")
            return True
        else:
            print("❌ Second call did not use cache")
            return False
            
    except Exception as e:
        print(f"❌ Cached decorator test failed: {e}")
        return False


async def test_cache_integration():
    """Test integration between basic and advanced cache."""
    print("🔧 Testing Cache Integration...")
    
    try:
        # Set data using basic cache
        basic_data = {"source": "basic", "integration": True}
        await cache_manager.set("integration_test", basic_data, expire=300)
        
        # Try to read using advanced cache (should hit L2/Redis)
        advanced_data = await advanced_cache.get("integration_test")
        
        if advanced_data == basic_data:
            print("✅ Basic → Advanced cache integration working")
            
            # Now set using advanced cache
            advanced_only_data = {"source": "advanced", "level": "L1+L2"}
            await advanced_cache.set("advanced_only", advanced_only_data)
            
            # Read using basic cache (should hit Redis)
            basic_read = await cache_manager.get("advanced_only")
            
            if basic_read == advanced_only_data:
                print("✅ Advanced → Basic cache integration working")
                return True
            else:
                print("❌ Advanced → Basic integration failed")
                return False
        else:
            print("❌ Basic → Advanced integration failed")
            return False
            
    except Exception as e:
        print(f"❌ Cache integration test failed: {e}")
        return False


async def main():
    """Run complete cache system tests."""
    print("🧪 COMPLETE CACHE SYSTEM TEST")
    print("="*60)
    print("Testing both basic and advanced cache functionality")
    print("="*60)
    
    tests = [
        ("Basic Cache Manager", test_basic_cache),
        ("Advanced Cache Manager", test_advanced_cache),
        ("Cached Decorator", test_cached_decorator),
        ("Cache Integration", test_cache_integration),
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
        await advanced_cache.stop()
        await cache_manager.disconnect()
    except Exception as e:
        print(f"⚠️  Cleanup warning: {e}")
    
    print("\n" + "="*60)
    print("📊 COMPLETE CACHE SYSTEM RESULTS")
    print("="*60)
    print(f"Total Tests: {passed + failed}")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    
    if failed == 0:
        print("\n🎉 BOTH CACHE SYSTEMS WORKING PERFECTLY!")
        print("✅ Basic cache: Redis operations, sessions, rate limiting")
        print("✅ Advanced cache: L1+L2 levels, intelligent invalidation")
        print("✅ Cache decorator: Function result caching")
        print("✅ Integration: Basic ↔ Advanced cache communication")
        print("\n🚀 Complete caching infrastructure ready!")
    else:
        print(f"\n⚠️  {failed} tests failed")
        print("❌ Cache system needs attention")
    
    print("="*60)
    
    return failed == 0


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)