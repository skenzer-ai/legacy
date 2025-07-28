"""
Modern task queue system using Redis and asyncio.
Lightweight alternative to Celery for our use case.
"""
import asyncio
import json
import uuid
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Union
import redis.asyncio as redis
from pydantic import BaseModel

from app.core.config import settings


class TaskStatus(str, Enum):
    """Task execution status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TaskInfo(BaseModel):
    """Task information model."""
    id: str
    name: str
    status: TaskStatus
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    result: Optional[Any] = None
    error: Optional[str] = None
    progress: int = 0  # 0-100
    metadata: Dict[str, Any] = {}


class TaskQueue:
    """Modern async task queue using Redis."""
    
    def __init__(self, redis_url: str = None):
        self.redis_url = redis_url or settings.redis_url
        self.redis: Optional[redis.Redis] = None
        self.workers: Dict[str, asyncio.Task] = {}
        self.task_registry: Dict[str, Callable] = {}
        
    async def connect(self):
        """Connect to Redis."""
        if not self.redis:
            self.redis = redis.from_url(
                self.redis_url,
                encoding="utf-8",
                decode_responses=True
            )
            
    async def disconnect(self):
        """Disconnect from Redis."""
        if self.redis:
            await self.redis.close()
            
    def register_task(self, name: str):
        """Decorator to register a task function."""
        def decorator(func: Callable):
            self.task_registry[name] = func
            return func
        return decorator
        
    async def enqueue_task(
        self,
        task_name: str,
        args: List[Any] = None,
        kwargs: Dict[str, Any] = None,
        priority: int = 0,
        delay: Optional[timedelta] = None,
        metadata: Dict[str, Any] = None
    ) -> str:
        """Enqueue a task for execution."""
        await self.connect()
        
        task_id = str(uuid.uuid4())
        now = datetime.utcnow()
        execute_at = now + delay if delay else now
        
        task_data = {
            "id": task_id,
            "name": task_name,
            "args": args or [],
            "kwargs": kwargs or {},
            "created_at": now.isoformat(),
            "execute_at": execute_at.isoformat(),
            "priority": priority,
            "metadata": metadata or {}
        }
        
        # Store task info
        task_info = TaskInfo(
            id=task_id,
            name=task_name,
            status=TaskStatus.PENDING,
            created_at=now,
            metadata=metadata or {}
        )
        
        await self.redis.hset(
            f"task:{task_id}",
            mapping={
                "info": task_info.model_dump_json(),
                "data": json.dumps(task_data)
            }
        )
        
        # Add to priority queue
        score = priority * 1000000 + int(execute_at.timestamp())
        await self.redis.zadd("task_queue", {task_id: score})
        
        return task_id
        
    async def get_task_info(self, task_id: str) -> Optional[TaskInfo]:
        """Get task information."""
        await self.connect()
        
        info_data = await self.redis.hget(f"task:{task_id}", "info")
        if info_data:
            return TaskInfo.model_validate_json(info_data)
        return None
        
    async def update_task_status(
        self,
        task_id: str,
        status: TaskStatus,
        result: Any = None,
        error: str = None,
        progress: int = None
    ):
        """Update task status and result."""
        await self.connect()
        
        task_info = await self.get_task_info(task_id)
        if not task_info:
            return
            
        task_info.status = status
        if result is not None:
            task_info.result = result
        if error:
            task_info.error = error
        if progress is not None:
            task_info.progress = progress
            
        now = datetime.utcnow()
        if status == TaskStatus.RUNNING and not task_info.started_at:
            task_info.started_at = now
        elif status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED]:
            task_info.completed_at = now
            
        await self.redis.hset(
            f"task:{task_id}",
            "info",
            task_info.model_dump_json()
        )
        
    async def cancel_task(self, task_id: str) -> bool:
        """Cancel a pending task."""
        await self.connect()
        
        # Remove from queue
        removed = await self.redis.zrem("task_queue", task_id)
        if removed:
            await self.update_task_status(task_id, TaskStatus.CANCELLED)
            return True
        return False
        
    async def start_worker(self, worker_name: str = None):
        """Start a background worker."""
        worker_name = worker_name or f"worker-{uuid.uuid4().hex[:8]}"
        
        async def worker():
            await self.connect()
            print(f"🚀 Task worker '{worker_name}' started")
            
            while True:
                try:
                    # Get next task
                    now = int(datetime.utcnow().timestamp())
                    result = await self.redis.zrangebyscore(
                        "task_queue", 
                        min=0, 
                        max=now * 1000000 + 999999,
                        start=0, 
                        num=1,
                        withscores=True
                    )
                    
                    if not result:
                        await asyncio.sleep(1)
                        continue
                        
                    task_id, score = result[0]
                    
                    # Remove from queue
                    removed = await self.redis.zrem("task_queue", task_id)
                    if not removed:
                        continue
                        
                    # Execute task
                    await self._execute_task(task_id, worker_name)
                    
                except Exception as e:
                    print(f"❌ Worker '{worker_name}' error: {e}")
                    await asyncio.sleep(5)
                    
        # Start worker task
        task = asyncio.create_task(worker())
        self.workers[worker_name] = task
        return worker_name
        
    async def _execute_task(self, task_id: str, worker_name: str):
        """Execute a single task."""
        try:
            # Get task data
            task_data_str = await self.redis.hget(f"task:{task_id}", "data")
            if not task_data_str:
                return
                
            task_data = json.loads(task_data_str)
            task_name = task_data["name"]
            
            # Check if task is registered
            if task_name not in self.task_registry:
                await self.update_task_status(
                    task_id, 
                    TaskStatus.FAILED, 
                    error=f"Task '{task_name}' not registered"
                )
                return
                
            print(f"🔄 Worker '{worker_name}' executing task '{task_name}' ({task_id})")
            
            # Update status to running
            await self.update_task_status(task_id, TaskStatus.RUNNING)
            
            # Execute task function
            task_func = self.task_registry[task_name]
            args = task_data["args"]
            kwargs = task_data["kwargs"]
            
            if asyncio.iscoroutinefunction(task_func):
                result = await task_func(*args, **kwargs)
            else:
                result = task_func(*args, **kwargs)
                
            # Update status to completed
            await self.update_task_status(task_id, TaskStatus.COMPLETED, result=result)
            print(f"✅ Task '{task_name}' ({task_id}) completed successfully")
            
        except Exception as e:
            await self.update_task_status(
                task_id, 
                TaskStatus.FAILED, 
                error=str(e)
            )
            print(f"❌ Task '{task_id}' failed: {e}")
            
    async def stop_worker(self, worker_name: str):
        """Stop a specific worker."""
        if worker_name in self.workers:
            self.workers[worker_name].cancel()
            del self.workers[worker_name]
            print(f"🛑 Worker '{worker_name}' stopped")
            
    async def stop_all_workers(self):
        """Stop all workers."""
        for worker_name in list(self.workers.keys()):
            await self.stop_worker(worker_name)
            
    async def get_queue_stats(self) -> Dict[str, Any]:
        """Get queue statistics."""
        await self.connect()
        
        pending_count = await self.redis.zcard("task_queue")
        
        # Get task counts by status
        status_counts = {}
        for status in TaskStatus:
            # This is a simplified count - in production you'd want to use Redis patterns
            status_counts[status.value] = 0  # Would require scanning all task keys
            
        return {
            "pending_tasks": pending_count,
            "active_workers": len(self.workers),
            "status_counts": status_counts
        }


# Global task queue instance
task_queue = TaskQueue()