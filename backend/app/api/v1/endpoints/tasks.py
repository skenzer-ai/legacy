"""
Task management API endpoints.
"""
from datetime import timedelta
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel

from app.core.auth import current_active_user, current_admin_user
from app.core.tasks.queue import task_queue, TaskInfo, TaskStatus
from app.core.tasks.tasks import test_task
from app.models.user import User

router = APIRouter()


class TaskRequest(BaseModel):
    """Request model for creating tasks."""
    task_name: str
    args: List[Any] = []
    kwargs: Dict[str, Any] = {}
    priority: int = 0
    delay_seconds: Optional[int] = None
    metadata: Dict[str, Any] = {}


class TaskResponse(BaseModel):
    """Response model for task operations."""
    task_id: str
    message: str


class QueueStatsResponse(BaseModel):
    """Queue statistics response."""
    pending_tasks: int
    active_workers: int
    status_counts: Dict[str, int]


@router.post("/enqueue", response_model=TaskResponse)
async def enqueue_task(
    task_request: TaskRequest,
    user: User = Depends(current_active_user)
):
    """Enqueue a new task for background processing."""
    try:
        # Add user info to metadata
        task_request.metadata["user_id"] = str(user.id)
        task_request.metadata["user_email"] = user.email
        
        # Convert delay to timedelta if provided
        delay = None
        if task_request.delay_seconds:
            delay = timedelta(seconds=task_request.delay_seconds)
            
        task_id = await task_queue.enqueue_task(
            task_name=task_request.task_name,
            args=task_request.args,
            kwargs=task_request.kwargs,
            priority=task_request.priority,
            delay=delay,
            metadata=task_request.metadata
        )
        
        return TaskResponse(
            task_id=task_id,
            message=f"Task '{task_request.task_name}' enqueued successfully"
        )
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/status/{task_id}", response_model=TaskInfo)
async def get_task_status(
    task_id: str,
    user: User = Depends(current_active_user)
):
    """Get the status of a specific task."""
    task_info = await task_queue.get_task_info(task_id)
    
    if not task_info:
        raise HTTPException(status_code=404, detail="Task not found")
        
    # Check if user has permission to view this task
    if (user.role != "admin" and 
        task_info.metadata.get("user_id") != str(user.id)):
        raise HTTPException(status_code=403, detail="Access denied")
        
    return task_info


@router.delete("/cancel/{task_id}")
async def cancel_task(
    task_id: str,
    user: User = Depends(current_active_user)
):
    """Cancel a pending task."""
    task_info = await task_queue.get_task_info(task_id)
    
    if not task_info:
        raise HTTPException(status_code=404, detail="Task not found")
        
    # Check if user has permission to cancel this task
    if (user.role != "admin" and 
        task_info.metadata.get("user_id") != str(user.id)):
        raise HTTPException(status_code=403, detail="Access denied")
        
    if task_info.status != TaskStatus.PENDING:
        raise HTTPException(
            status_code=400, 
            detail=f"Cannot cancel task with status '{task_info.status}'"
        )
        
    success = await task_queue.cancel_task(task_id)
    
    if success:
        return {"message": "Task cancelled successfully"}
    else:
        raise HTTPException(status_code=400, detail="Task could not be cancelled")


@router.get("/stats", response_model=QueueStatsResponse)
async def get_queue_stats(
    user: User = Depends(current_admin_user)
):
    """Get task queue statistics (Admin only)."""
    stats = await task_queue.get_queue_stats()
    return QueueStatsResponse(**stats)


@router.post("/test")
async def create_test_task(
    message: str = "Hello from background task!",
    delay: int = 1,
    user: User = Depends(current_active_user)
):
    """Create a simple test task for demonstration."""
    task_id = await task_queue.enqueue_task(
        task_name="test_task",
        args=[message, delay],
        metadata={
            "user_id": str(user.id),
            "user_email": user.email,
            "task_type": "test"
        }
    )
    
    return {
        "task_id": task_id,
        "message": "Test task created",
        "check_status": f"/api/v1/tasks/status/{task_id}"
    }


@router.post("/process-document")
async def create_document_processing_task(
    file_path: str,
    user: User = Depends(current_active_user)
):
    """Create a document processing task."""
    task_id = await task_queue.enqueue_task(
        task_name="process_document",
        kwargs={
            "file_path": file_path,
            "user_id": str(user.id)
        },
        priority=5,  # Higher priority for user-initiated tasks
        metadata={
            "user_id": str(user.id),
            "user_email": user.email,
            "task_type": "document_processing"
        }
    )
    
    return {
        "task_id": task_id,
        "message": "Document processing task created",
        "file_path": file_path,
        "check_status": f"/api/v1/tasks/status/{task_id}"
    }


@router.post("/analyze-api")
async def create_api_analysis_task(
    api_spec_path: str,
    analysis_type: str = "full",
    user: User = Depends(current_active_user)
):
    """Create an API specification analysis task."""
    task_id = await task_queue.enqueue_task(
        task_name="api_specification_analysis",
        kwargs={
            "api_spec_path": api_spec_path,
            "user_id": str(user.id),
            "analysis_type": analysis_type
        },
        priority=3,
        metadata={
            "user_id": str(user.id),
            "user_email": user.email,
            "task_type": "api_analysis"
        }
    )
    
    return {
        "task_id": task_id,
        "message": "API analysis task created",
        "api_spec_path": api_spec_path,
        "analysis_type": analysis_type,
        "check_status": f"/api/v1/tasks/status/{task_id}"
    }


@router.post("/admin/start-worker")
async def start_worker(
    worker_name: Optional[str] = None,
    user: User = Depends(current_admin_user)
):
    """Start a new background worker (Admin only)."""
    worker_id = await task_queue.start_worker(worker_name)
    return {
        "worker_id": worker_id,
        "message": "Background worker started successfully"
    }


@router.delete("/admin/stop-worker/{worker_name}")
async def stop_worker(
    worker_name: str,
    user: User = Depends(current_admin_user)
):
    """Stop a specific background worker (Admin only)."""
    await task_queue.stop_worker(worker_name)
    return {
        "message": f"Worker '{worker_name}' stopped successfully"
    }