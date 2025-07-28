"""
Upload API Endpoints

FastAPI endpoints for uploading API specification files for processing.
Supports multipart file uploads with format detection and parsing.
"""

import json
import logging
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any

from fastapi import APIRouter, File, UploadFile, HTTPException, Form, BackgroundTasks
from pydantic import BaseModel

from ..engines.json_parser import JSONParser
from ..models.api_specification import APISpecification

logger = logging.getLogger(__name__)

# Create router (tags will be overridden by main router)
router = APIRouter()

# In-memory storage for upload status (in production, use Redis or database)
upload_status_store: Dict[str, Dict[str, Any]] = {}


class UploadResponse(BaseModel):
    """Response model for file upload"""
    upload_id: str
    filename: str
    total_endpoints: int
    parsing_status: str
    classification_status: str
    estimated_services: int
    next_step: str
    message: str


class UploadStatusResponse(BaseModel):
    """Response model for upload status check"""
    upload_id: str
    status: str
    progress: float
    current_step: str
    services_identified: int
    services_remaining: int
    estimated_completion: Optional[str] = None
    error_message: Optional[str] = None


@router.post("/upload", response_model=UploadResponse)
async def upload_api_specification(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(..., description="API specification file (JSON/YAML)"),
    format_hint: Optional[str] = Form(None, description="Optional format hint (openapi_3, swagger_2, infraon_custom)")
):
    """
    Upload API specification file for processing
    
    Accepts JSON or YAML files containing API specifications in various formats:
    - OpenAPI 3.0
    - Swagger 2.0  
    - Infraon custom format
    
    The file is parsed immediately and prepared for classification.
    """
    try:
        # Generate unique upload ID
        upload_id = str(uuid.uuid4())
        
        # Validate file
        if not file.filename:
            raise HTTPException(status_code=400, detail="No filename provided")
        
        # Check file extension
        file_ext = Path(file.filename).suffix.lower()
        if file_ext not in ['.json', '.yaml', '.yml']:
            raise HTTPException(
                status_code=400, 
                detail=f"Unsupported file format: {file_ext}. Supported formats: .json, .yaml, .yml"
            )
        
        # Read file content
        try:
            file_content = await file.read()
            content_str = file_content.decode('utf-8')
        except UnicodeDecodeError:
            raise HTTPException(status_code=400, detail="File must be UTF-8 encoded")
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Failed to read file: {str(e)}")
        
        # Initialize upload status
        upload_status_store[upload_id] = {
            "upload_id": upload_id,
            "filename": file.filename,
            "status": "processing",
            "progress": 0.1,
            "current_step": "parsing",
            "services_identified": 0,
            "services_remaining": 0,
            "estimated_completion": None,
            "error_message": None,
            "created_at": datetime.utcnow().isoformat(),
            "file_content": content_str,
            "format_hint": format_hint
        }
        
        # Start background processing
        background_tasks.add_task(process_uploaded_file, upload_id, content_str, format_hint)
        
        # Return immediate response
        return UploadResponse(
            upload_id=upload_id,
            filename=file.filename,
            total_endpoints=0,  # Will be updated during processing
            parsing_status="processing",
            classification_status="pending",
            estimated_services=0,  # Will be estimated during processing
            next_step="parsing",
            message=f"File '{file.filename}' uploaded successfully. Processing started."
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Upload failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")


@router.get("/upload/{upload_id}/status", response_model=UploadStatusResponse)
async def get_upload_status(upload_id: str):
    """
    Check upload processing status
    
    Returns current processing status, progress, and any error information.
    """
    try:
        if upload_id not in upload_status_store:
            raise HTTPException(status_code=404, detail=f"Upload ID {upload_id} not found")
        
        status_data = upload_status_store[upload_id]
        
        return UploadStatusResponse(
            upload_id=upload_id,
            status=status_data["status"],
            progress=status_data["progress"],
            current_step=status_data["current_step"],
            services_identified=status_data["services_identified"],
            services_remaining=status_data["services_remaining"],
            estimated_completion=status_data.get("estimated_completion"),
            error_message=status_data.get("error_message")
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get upload status: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get upload status: {str(e)}")


@router.delete("/upload/{upload_id}")
async def cancel_upload(upload_id: str):
    """
    Cancel upload processing and clean up resources
    """
    try:
        if upload_id not in upload_status_store:
            raise HTTPException(status_code=404, detail=f"Upload ID {upload_id} not found")
        
        # Mark as cancelled
        upload_status_store[upload_id]["status"] = "cancelled"
        upload_status_store[upload_id]["current_step"] = "cancelled"
        upload_status_store[upload_id]["error_message"] = "Processing cancelled by user"
        
        return {"message": f"Upload {upload_id} cancelled successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to cancel upload: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to cancel upload: {str(e)}")


@router.get("/uploads")
async def list_uploads(limit: int = 10, status: Optional[str] = None):
    """
    List recent uploads with optional status filtering
    
    Args:
        limit: Maximum number of uploads to return
        status: Filter by status (processing, completed, failed, cancelled)
    """
    try:
        uploads = list(upload_status_store.values())
        
        # Filter by status if provided
        if status:
            uploads = [u for u in uploads if u["status"] == status]
        
        # Sort by creation time (newest first)
        uploads.sort(key=lambda x: x["created_at"], reverse=True)
        
        # Apply limit
        uploads = uploads[:limit]
        
        # Remove file content from response (too large)
        for upload in uploads:
            if "file_content" in upload:
                del upload["file_content"]
        
        return {
            "uploads": uploads,
            "total": len(upload_status_store),
            "filtered": len(uploads)
        }
        
    except Exception as e:
        logger.error(f"Failed to list uploads: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to list uploads: {str(e)}")


async def process_uploaded_file(upload_id: str, content: str, format_hint: Optional[str]):
    """
    Background task to process uploaded API specification file
    
    This function runs asynchronously to parse the file and prepare it for classification.
    Updates the upload status throughout the process.
    """
    try:
        logger.info(f"Starting processing for upload {upload_id}")
        
        # Update status: Starting parsing
        upload_status_store[upload_id].update({
            "status": "processing",
            "progress": 0.2,
            "current_step": "parsing_file"
        })
        
        # Initialize parser
        parser = JSONParser()
        
        # Parse the specification
        try:
            # Get filename from upload status
            filename = upload_status_store[upload_id]["filename"]
            api_spec = await parser.parse_specification(content, filename, format_hint)
            
            # Update status: Parsing completed
            upload_status_store[upload_id].update({
                "progress": 0.6,
                "current_step": "analyzing_endpoints",
                "total_endpoints": api_spec.total_endpoints
            })
            
        except Exception as e:
            logger.error(f"Parsing failed for upload {upload_id}: {str(e)}")
            upload_status_store[upload_id].update({
                "status": "failed",
                "current_step": "parsing_failed",
                "error_message": f"Failed to parse API specification: {str(e)}"
            })
            return
        
        # Estimate number of services based on endpoint analysis
        try:
            estimated_services = estimate_service_count(api_spec)
            
            # Update status: Analysis completed
            upload_status_store[upload_id].update({
                "progress": 0.8,
                "current_step": "preparing_classification",
                "estimated_services": estimated_services,
                "services_remaining": estimated_services
            })
            
        except Exception as e:
            logger.warning(f"Service estimation failed for upload {upload_id}: {str(e)}")
            estimated_services = 0
        
        # Store parsed specification for later use
        upload_status_store[upload_id]["parsed_specification"] = api_spec.dict()
        
        # Update status: Ready for classification
        upload_status_store[upload_id].update({
            "status": "completed",
            "progress": 1.0,
            "current_step": "ready_for_classification",
            "estimated_completion": datetime.utcnow().isoformat()
        })
        
        logger.info(f"Processing completed for upload {upload_id}: {api_spec.total_endpoints} endpoints, ~{estimated_services} services")
        
    except Exception as e:
        logger.error(f"Unexpected error processing upload {upload_id}: {str(e)}")
        upload_status_store[upload_id].update({
            "status": "failed",
            "current_step": "processing_failed",
            "error_message": f"Unexpected processing error: {str(e)}"
        })


def estimate_service_count(api_spec: APISpecification) -> int:
    """
    Estimate the number of services based on endpoint analysis
    
    Uses simple heuristics:
    - Group endpoints by common path segments
    - Count unique tags if available
    - Use path pattern analysis
    """
    try:
        # Method 1: Count unique tags
        unique_tags = set()
        for endpoint in api_spec.endpoints:
            unique_tags.update(endpoint.tags)
        
        if unique_tags:
            return len(unique_tags)
        
        # Method 2: Group by path segments
        path_segments = set()
        for endpoint in api_spec.endpoints:
            path_parts = [part for part in endpoint.path.split('/') if part and not part.startswith('{')]
            if path_parts:
                path_segments.add(path_parts[0])  # Use first segment as service indicator
        
        # Method 3: Default estimation based on endpoint count
        endpoint_count = len(api_spec.endpoints)
        if endpoint_count < 50:
            return max(1, endpoint_count // 10)
        elif endpoint_count < 200:
            return max(5, endpoint_count // 15)
        else:
            return max(10, endpoint_count // 20)
        
    except Exception as e:
        logger.warning(f"Service count estimation failed: {str(e)}")
        return 1


# Cleanup function (should be called periodically)
async def cleanup_old_uploads(max_age_hours: int = 24):
    """
    Clean up old upload records to prevent memory bloat
    
    Args:
        max_age_hours: Maximum age of uploads to keep in hours
    """
    try:
        current_time = datetime.utcnow()
        cutoff_time = current_time.timestamp() - (max_age_hours * 3600)
        
        uploads_to_remove = []
        for upload_id, upload_data in upload_status_store.items():
            created_at = datetime.fromisoformat(upload_data["created_at"])
            if created_at.timestamp() < cutoff_time:
                uploads_to_remove.append(upload_id)
        
        for upload_id in uploads_to_remove:
            del upload_status_store[upload_id]
        
        if uploads_to_remove:
            logger.info(f"Cleaned up {len(uploads_to_remove)} old upload records")
            
    except Exception as e:
        logger.error(f"Upload cleanup failed: {str(e)}")