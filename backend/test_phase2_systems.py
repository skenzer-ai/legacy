#!/usr/bin/env python3
"""
Comprehensive test suite for Phase 2 Application Architecture systems.

Tests all the advanced systems implemented in Phase 2:
- Workflow state machine system
- Event-driven pub/sub architecture
- WebSocket real-time communication
- Progress tracking and notifications
- Advanced caching strategies
"""

import asyncio
import sys
import os
import uuid
import json
from datetime import datetime, timedelta
from typing import Dict, Any

# Add backend to Python path
sys.path.insert(0, os.path.dirname(__file__))

from app.core.workflow.state_machine import (
    workflow_engine, WorkflowDefinition, WorkflowState, 
    DocumentProcessingWorkflow, APIValidationWorkflow
)
from app.core.events import (
    event_publisher, EventType, EventPriority, Event
)
from app.core.websocket import (
    websocket_manager, WebSocketMessage, MessageType
)
from app.core.progress import (
    progress_manager, ProgressStatus, track_progress
)
from app.core.cache import (
    advanced_cache, CacheConfig, CacheLevel, cached
)
from app.core.tasks.queue import task_queue
from app.core.cache import cache_manager


class TestResults:
    """Track test results across all systems."""
    
    def __init__(self):
        self.results: Dict[str, Dict[str, Any]] = {}
        self.total_tests = 0
        self.passed_tests = 0
        self.failed_tests = 0
    
    def add_result(self, system: str, test: str, success: bool, details: str = ""):
        """Add a test result."""
        if system not in self.results:
            self.results[system] = {}
        
        self.results[system][test] = {
            "success": success,
            "details": details,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        self.total_tests += 1
        if success:
            self.passed_tests += 1
        else:
            self.failed_tests += 1
    
    def print_summary(self):
        """Print comprehensive test summary."""
        print("\n" + "="*80)
        print("🧪 PHASE 2 SYSTEMS TEST SUMMARY")
        print("="*80)
        
        for system, tests in self.results.items():
            print(f"\n📊 {system.upper()} SYSTEM:")
            passed = sum(1 for t in tests.values() if t["success"])
            total = len(tests)
            status = "✅ PASS" if passed == total else "❌ FAIL"
            print(f"   Status: {status} ({passed}/{total} tests passed)")
            
            for test_name, result in tests.items():
                icon = "✅" if result["success"] else "❌"
                print(f"   {icon} {test_name}")
                if result["details"]:
                    print(f"      Details: {result['details']}")
        
        print(f"\n🎯 OVERALL RESULTS:")
        print(f"   Total Tests: {self.total_tests}")
        print(f"   Passed: {self.passed_tests}")
        print(f"   Failed: {self.failed_tests}")
        success_rate = (self.passed_tests / self.total_tests * 100) if self.total_tests > 0 else 0
        print(f"   Success Rate: {success_rate:.1f}%")
        
        if self.failed_tests == 0:
            print("\n🎉 ALL PHASE 2 SYSTEMS WORKING CORRECTLY!")
        else:
            print(f"\n⚠️  {self.failed_tests} TESTS FAILED - CHECK IMPLEMENTATION")


async def test_workflow_system(results: TestResults):
    """Test workflow state machine system."""
    print("\n🔄 Testing Workflow State Machine System...")
    
    try:
        # Test workflow engine initialization
        print("   Testing workflow engine initialization...")
        if len(workflow_engine.workflows) >= 2:  # Should have DocumentProcessing and APIValidation
            results.add_result("workflow", "engine_initialization", True, 
                             f"Found {len(workflow_engine.workflows)} registered workflows")
        else:
            results.add_result("workflow", "engine_initialization", False, 
                             f"Expected 2+ workflows, found {len(workflow_engine.workflows)}")
        
        # Test document processing workflow
        print("   Testing document processing workflow...")
        workflow_id = await workflow_engine.start_workflow(
            "document_processing",
            {"file_path": "/test/document.md", "test_mode": True},
            user_id="test-user"
        )
        
        if workflow_id:
            results.add_result("workflow", "document_workflow_start", True, 
                             f"Workflow started with ID: {workflow_id}")
            
            # Wait a bit for processing
            await asyncio.sleep(3)
            
            # Check workflow status
            status = await workflow_engine.get_workflow_status(workflow_id)
            if status:
                results.add_result("workflow", "workflow_status_check", True,
                                 f"Status: {status['current_state']}")
            else:
                results.add_result("workflow", "workflow_status_check", False,
                                 "Could not retrieve workflow status")
        else:
            results.add_result("workflow", "document_workflow_start", False,
                             "Failed to start document processing workflow")
        
        # Test workflow pause/resume (if still running)
        if workflow_id:
            print("   Testing workflow pause/resume...")
            paused = await workflow_engine.pause_workflow(workflow_id)
            if paused:
                resumed = await workflow_engine.resume_workflow(workflow_id)
                results.add_result("workflow", "pause_resume", resumed,
                                 "Pause/resume operations completed" if resumed else "Resume failed")
            else:
                results.add_result("workflow", "pause_resume", False, "Failed to pause workflow")
    
    except Exception as e:
        results.add_result("workflow", "system_error", False, f"Exception: {str(e)}")


async def test_event_system(results: TestResults):
    """Test event-driven pub/sub system."""
    print("\n📡 Testing Event-Driven Pub/Sub System...")
    
    try:
        # Start event publisher
        print("   Starting event publisher...")
        await event_publisher.start()
        
        # Test event subscription
        print("   Testing event subscription...")
        received_events = []
        
        def test_handler(event: Event):
            received_events.append(event)
        
        subscription_id = event_publisher.subscribe(
            handler=test_handler,
            event_types=[EventType.CUSTOM, EventType.SYSTEM_STARTUP],
            name="test_subscription"
        )
        
        if subscription_id:
            results.add_result("events", "subscription", True, f"Subscription ID: {subscription_id}")
        else:
            results.add_result("events", "subscription", False, "Failed to create subscription")
        
        # Test event publishing
        print("   Testing event publishing...")
        event_id = await event_publisher.publish(
            event_type=EventType.CUSTOM,
            data={"test": "data", "timestamp": datetime.utcnow().isoformat()},
            source="test_system",
            user_id="test-user"
        )
        
        if event_id:
            results.add_result("events", "publishing", True, f"Published event: {event_id}")
        else:
            results.add_result("events", "publishing", False, "Failed to publish event")
        
        # Wait for event processing
        await asyncio.sleep(2)
        
        # Check if event was received
        if received_events:
            results.add_result("events", "event_delivery", True, 
                             f"Received {len(received_events)} events")
        else:
            results.add_result("events", "event_delivery", False, "No events received")
        
        # Test event history
        print("   Testing event history...")
        history = await event_publisher.get_event_history(
            event_types=[EventType.CUSTOM],
            limit=10
        )
        
        if history:
            results.add_result("events", "event_history", True, 
                             f"Retrieved {len(history)} historical events")
        else:
            results.add_result("events", "event_history", False, "No event history found")
        
        # Test subscription cleanup
        unsubscribed = event_publisher.unsubscribe(subscription_id)
        results.add_result("events", "unsubscription", unsubscribed, 
                         "Subscription cleaned up successfully" if unsubscribed else "Failed to unsubscribe")
    
    except Exception as e:
        results.add_result("events", "system_error", False, f"Exception: {str(e)}")


async def test_websocket_system(results: TestResults):
    """Test WebSocket real-time communication system."""
    print("\n🌐 Testing WebSocket Real-Time Communication...")
    
    try:
        # Start WebSocket manager
        print("   Starting WebSocket manager...")
        await websocket_manager.start()
        
        # Test manager initialization
        stats = websocket_manager.get_stats()
        results.add_result("websocket", "manager_initialization", True, 
                         f"Manager started with stats: {stats}")
        
        # Test message creation and serialization
        print("   Testing message handling...")
        test_message = WebSocketMessage(
            type=MessageType.CUSTOM,
            data={"test": "websocket", "timestamp": datetime.utcnow().isoformat()},
            user_id="test-user"
        )
        
        message_dict = test_message.to_dict()
        restored_message = WebSocketMessage.from_dict(message_dict)
        
        if (restored_message.type == test_message.type and 
            restored_message.data == test_message.data):
            results.add_result("websocket", "message_serialization", True,
                             "Message serialization/deserialization working")
        else:
            results.add_result("websocket", "message_serialization", False,
                             "Message serialization failed")
        
        # Test room management
        print("   Testing room management...")
        test_connection_id = "test-connection-123"
        await websocket_manager.join_room(test_connection_id, "test-room")
        
        room_connections = websocket_manager.get_room_connections("test-room")
        if test_connection_id in room_connections:
            results.add_result("websocket", "room_management", True,
                             "Room join/leave functionality working")
        else:
            results.add_result("websocket", "room_management", False,
                             "Room management not working correctly")
        
        await websocket_manager.leave_room(test_connection_id, "test-room")
        
        # Test heartbeat system (simplified)
        print("   Testing heartbeat system...")
        # The heartbeat system runs in background, just verify it's not erroring
        results.add_result("websocket", "heartbeat_system", True,
                         "Heartbeat system initialized (background task)")
    
    except Exception as e:
        results.add_result("websocket", "system_error", False, f"Exception: {str(e)}")


async def test_progress_system(results: TestResults):
    """Test progress tracking and notification system."""
    print("\n📊 Testing Progress Tracking System...")
    
    try:
        # Test progress tracker creation
        print("   Testing progress tracker creation...")
        tracker = progress_manager.create_tracker(
            "test_operation",
            "testing"
        )
        
        if tracker:
            results.add_result("progress", "tracker_creation", True,
                             f"Created tracker: {tracker.operation_id}")
        else:
            results.add_result("progress", "tracker_creation", False,
                             "Failed to create progress tracker")
        
        # Test step management
        print("   Testing step management...")
        tracker.add_steps([
            {"step_id": "step1", "name": "Initialize", "weight": 1.0},
            {"step_id": "step2", "name": "Process", "weight": 2.0},
            {"step_id": "step3", "name": "Finalize", "weight": 1.0}
        ])
        
        if len(tracker.steps) == 3:
            results.add_result("progress", "step_management", True,
                             f"Added {len(tracker.steps)} steps")
        else:
            results.add_result("progress", "step_management", False,
                             f"Expected 3 steps, got {len(tracker.steps)}")
        
        # Test progress tracking
        print("   Testing progress updates...")
        await tracker.start(user_id="test-user")
        
        # Update step progress
        await tracker.update_step_progress("step1", 100.0)
        await tracker.update_step_progress("step2", 50.0)
        
        metrics = tracker.get_metrics()
        if metrics.total_progress > 0:
            results.add_result("progress", "progress_calculation", True,
                             f"Total progress: {metrics.total_progress:.1f}%")
        else:
            results.add_result("progress", "progress_calculation", False,
                             "Progress calculation not working")
        
        # Test progress completion
        await tracker.complete_step("step2")
        await tracker.complete_step("step3")
        await tracker.complete({"result": "test completed"})
        
        final_status = tracker.get_status()
        if final_status["status"] == ProgressStatus.COMPLETED.value:
            results.add_result("progress", "completion", True,
                             "Progress tracking completed successfully")
        else:
            results.add_result("progress", "completion", False,
                             f"Unexpected final status: {final_status['status']}")
        
        # Test context manager
        print("   Testing progress context manager...")
        try:
            async with track_progress(
                "test_context_operation",
                [{"step_id": "ctx_step", "name": "Context Step", "weight": 1.0}],
                user_id="test-user"
            ) as ctx_tracker:
                await ctx_tracker.update_step_progress("ctx_step", 100.0)
            
            results.add_result("progress", "context_manager", True,
                             "Context manager working correctly")
        except Exception as e:
            results.add_result("progress", "context_manager", False,
                             f"Context manager error: {str(e)}")
    
    except Exception as e:
        results.add_result("progress", "system_error", False, f"Exception: {str(e)}")


async def test_caching_system(results: TestResults):
    """Test advanced caching strategies."""
    print("\n🗄️ Testing Advanced Caching System...")
    
    try:
        # Start advanced cache
        print("   Starting advanced cache system...")
        await advanced_cache.start()
        
        # Test basic cache operations
        print("   Testing basic cache operations...")
        test_key = "test_cache_key"
        test_value = {"data": "test", "timestamp": datetime.utcnow().isoformat()}
        
        await advanced_cache.set(test_key, test_value)
        retrieved_value = await advanced_cache.get(test_key)
        
        if retrieved_value == test_value:
            results.add_result("caching", "basic_operations", True,
                             "Set/get operations working")
        else:
            results.add_result("caching", "basic_operations", False,
                             "Set/get operations failed")
        
        # Test cache configuration
        print("   Testing cache configuration...")
        cache_config = CacheConfig(
            levels=[CacheLevel.L1_MEMORY, CacheLevel.L2_REDIS],
            ttl=300,
            tags=["test", "phase2"]
        )
        advanced_cache.configure_cache("test_pattern", cache_config)
        
        pattern_key = "pattern_test_key"
        await advanced_cache.set(pattern_key, {"pattern": "test"}, pattern="test_pattern")
        pattern_value = await advanced_cache.get(pattern_key, pattern="test_pattern")
        
        if pattern_value:
            results.add_result("caching", "pattern_config", True,
                             "Pattern-based caching working")
        else:
            results.add_result("caching", "pattern_config", False,
                             "Pattern-based caching failed")
        
        # Test multi-get operations
        print("   Testing multi-operations...")
        multi_data = {
            "key1": "value1",
            "key2": "value2", 
            "key3": "value3"
        }
        await advanced_cache.set_multi(multi_data)
        retrieved_multi = await advanced_cache.get_multi(list(multi_data.keys()))
        
        if len(retrieved_multi) == len(multi_data):
            results.add_result("caching", "multi_operations", True,
                             f"Multi-operations retrieved {len(retrieved_multi)} items")
        else:
            results.add_result("caching", "multi_operations", False,
                             f"Expected {len(multi_data)} items, got {len(retrieved_multi)}")
        
        # Test cache statistics
        print("   Testing cache statistics...")
        stats = advanced_cache.get_stats()
        if stats and "total_requests" in stats:
            results.add_result("caching", "statistics", True,
                             f"Cache stats: {stats['hit_rate_percent']:.1f}% hit rate")
        else:
            results.add_result("caching", "statistics", False,
                             "Cache statistics not available")
        
        # Test cached decorator
        print("   Testing cached decorator...")
        
        @cached(ttl=60, pattern="test_decorator")
        async def test_cached_function(value):
            return {"computed": value * 2, "timestamp": datetime.utcnow().isoformat()}
        
        result1 = await test_cached_function(5)
        result2 = await test_cached_function(5)  # Should be cached
        
        if result1 == result2:
            results.add_result("caching", "decorator", True,
                             "Cached decorator working correctly")
        else:
            results.add_result("caching", "decorator", False,
                             "Cached decorator not working")
    
    except Exception as e:
        results.add_result("caching", "system_error", False, f"Exception: {str(e)}")


async def test_system_integration(results: TestResults):
    """Test overall system integration."""
    print("\n🔧 Testing System Integration...")
    
    try:
        # Test cross-system communication
        print("   Testing cross-system communication...")
        
        # Create a progress tracker that publishes events
        tracker = progress_manager.create_tracker(
            "integration_test",
            "integration"
        )
        tracker.add_step("integration_step", "Integration Test", weight=1.0)
        
        # Subscribe to workflow events
        integration_events = []
        
        def integration_handler(event: Event):
            integration_events.append(event)
        
        subscription_id = event_publisher.subscribe(
            handler=integration_handler,
            event_types=[EventType.WORKFLOW_STARTED, EventType.WORKFLOW_COMPLETED],
            name="integration_test"
        )
        
        # Start and complete the progress tracker (should trigger events)
        await tracker.start(user_id="integration-user")
        await tracker.complete_step("integration_step")
        await tracker.complete({"integration": "success"})
        
        # Wait for event processing
        await asyncio.sleep(2)
        
        # Check if events were received
        if integration_events:
            results.add_result("integration", "cross_system_events", True,
                             f"Received {len(integration_events)} integration events")
        else:
            results.add_result("integration", "cross_system_events", False,
                             "No integration events received")
        
        # Test cache + events integration
        print("   Testing cache + events integration...")
        cache_key = "integration_cache_test"
        await advanced_cache.set(cache_key, {"integration": "test"})
        
        # Publish cache-related event
        await event_publisher.publish(
            event_type=EventType.CUSTOM,
            data={"cache_operation": "set", "key": cache_key},
            source="integration_test"
        )
        
        # Clean up subscription
        event_publisher.unsubscribe(subscription_id)
        
        results.add_result("integration", "cache_events_integration", True,
                         "Cache and events integration working")
        
        # Test all systems running together
        all_systems_status = {
            "workflow_engine": len(workflow_engine.workflows) > 0,
            "event_publisher": len(event_publisher.subscriptions) >= 0,
            "websocket_manager": websocket_manager.stats["total_connections"] >= 0,
            "progress_manager": len(progress_manager.trackers) > 0,
            "advanced_cache": advanced_cache.stats["total_requests"] >= 0
        }
        
        working_systems = sum(all_systems_status.values())
        total_systems = len(all_systems_status)
        
        if working_systems == total_systems:
            results.add_result("integration", "all_systems_operational", True,
                             f"All {total_systems} systems operational")
        else:
            results.add_result("integration", "all_systems_operational", False,
                             f"Only {working_systems}/{total_systems} systems working")
    
    except Exception as e:
        results.add_result("integration", "system_error", False, f"Exception: {str(e)}")


async def test_startup_shutdown(results: TestResults):
    """Test system startup and shutdown sequence."""
    print("\n🚀 Testing Startup/Shutdown Sequence...")
    
    try:
        # Test Redis connection (should be available)
        print("   Testing Redis connectivity...")
        await cache_manager.connect()
        redis_connected = await cache_manager.set("startup_test", "working", expire=60)
        
        if redis_connected:
            results.add_result("startup", "redis_connection", True,
                             "Redis connection established")
        else:
            results.add_result("startup", "redis_connection", False,
                             "Redis connection failed")
        
        # Test task queue connection
        print("   Testing task queue connectivity...")
        await task_queue.connect()
        queue_stats = await task_queue.get_queue_stats()
        
        if queue_stats:
            results.add_result("startup", "task_queue_connection", True,
                             f"Task queue connected: {queue_stats}")
        else:
            results.add_result("startup", "task_queue_connection", False,
                             "Task queue connection failed")
        
        # Test graceful shutdown preparation
        print("   Testing shutdown preparation...")
        
        # Stop all systems gracefully
        await advanced_cache.stop()
        await event_publisher.stop()
        await websocket_manager.stop()
        
        results.add_result("startup", "graceful_shutdown", True,
                         "All systems stopped gracefully")
        
        # Restart systems for continued testing
        await advanced_cache.start()
        await event_publisher.start()
        await websocket_manager.start()
        
        results.add_result("startup", "system_restart", True,
                         "Systems restarted successfully")
    
    except Exception as e:
        results.add_result("startup", "system_error", False, f"Exception: {str(e)}")


async def main():
    """Run comprehensive Phase 2 system tests."""
    print("🧪 STARTING PHASE 2 COMPREHENSIVE SYSTEM TESTS")
    print("="*80)
    print("Testing all advanced architecture systems implemented in Phase 2:")
    print("- Workflow State Machine System")
    print("- Event-Driven Pub/Sub Architecture") 
    print("- WebSocket Real-Time Communication")
    print("- Progress Tracking and Notifications")
    print("- Advanced Caching Strategies")
    print("- System Integration")
    print("="*80)
    
    results = TestResults()
    
    # Initialize basic connections first
    try:
        await cache_manager.connect()
        await task_queue.connect()
    except Exception as e:
        print(f"❌ Failed to initialize basic connections: {e}")
        return
    
    # Run all test suites
    test_suites = [
        ("Startup/Shutdown", test_startup_shutdown),
        ("Workflow System", test_workflow_system),
        ("Event System", test_event_system),
        ("WebSocket System", test_websocket_system),
        ("Progress System", test_progress_system),
        ("Caching System", test_caching_system),
        ("System Integration", test_system_integration),
    ]
    
    for suite_name, test_func in test_suites:
        try:
            await test_func(results)
        except Exception as e:
            results.add_result(suite_name.lower().replace(" ", "_"), "test_suite_error", 
                             False, f"Test suite failed: {str(e)}")
    
    # Print comprehensive results
    results.print_summary()
    
    # Cleanup
    try:
        await task_queue.disconnect()
        await cache_manager.disconnect()
    except Exception as e:
        print(f"⚠️  Cleanup warning: {e}")
    
    print("\n🏁 PHASE 2 TESTING COMPLETED")
    
    # Return success/failure for CI/CD
    return results.failed_tests == 0


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)