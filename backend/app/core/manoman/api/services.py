"""
Services API Endpoints

FastAPI endpoints for accessing and managing service data.
Provides general access to services without requiring specific upload IDs.
"""

import json
import logging
from typing import Optional, List, Any
from datetime import datetime

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from .classification import classification_store
from .upload import upload_status_store

logger = logging.getLogger(__name__)

# Create router (tags will be overridden by main router)
router = APIRouter()


class ServiceListResponse(BaseModel):
    """Response model for service list"""
    services: List[dict]
    total_services: int
    upload_id: Optional[str] = None
    upload_filename: Optional[str] = None
    last_updated: Optional[str] = None


@router.get("/services", response_model=ServiceListResponse)
async def get_all_services(
    limit: int = Query(default=100, ge=1, le=1000, description="Maximum number of services to return"),
    offset: int = Query(default=0, ge=0, description="Number of services to skip"),
    search: Optional[str] = Query(default=None, description="Search term for service names or descriptions"),
    confidence_min: Optional[float] = Query(default=None, ge=0.0, le=1.0, description="Minimum confidence score"),
    needs_review: Optional[bool] = Query(default=None, description="Filter by needs_review status")
):
    """
    Get all services from the most recent completed classification
    
    Returns services from the latest successfully processed upload.
    Supports pagination, search, and filtering.
    """
    try:
        # Find the most recent completed classification
        latest_upload_id = None
        latest_timestamp = None
        
        for upload_id, classification_data in classification_store.items():
            # Check if upload still exists and is completed
            if upload_id not in upload_status_store:
                continue
                
            upload_info = upload_status_store[upload_id]
            if upload_info["status"] != "completed":
                continue
            
            # Get timestamp for comparison
            created_at = datetime.fromisoformat(upload_info["created_at"])
            if latest_timestamp is None or created_at > latest_timestamp:
                latest_timestamp = created_at
                latest_upload_id = upload_id
        
        if not latest_upload_id:
            # No completed uploads found, return empty result
            return ServiceListResponse(
                services=[],
                total_services=0,
                upload_id=None,
                upload_filename=None,
                last_updated=None
            )
        
        # Get services from the latest classification
        classification_data = classification_store[latest_upload_id]
        all_services = classification_data["services"]
        upload_info = upload_status_store[latest_upload_id]
        
        # Apply search filter
        filtered_services = all_services
        if search:
            search_lower = search.lower()
            filtered_services = [
                service for service in filtered_services
                if (search_lower in service["service_name"].lower() or 
                    search_lower in service["suggested_description"].lower() or
                    any(search_lower in keyword.lower() for keyword in service.get("keywords", [])))
            ]
        
        # Apply confidence filter
        if confidence_min is not None:
            filtered_services = [
                service for service in filtered_services
                if service["confidence_score"] >= confidence_min
            ]
        
        # Apply needs_review filter
        if needs_review is not None:
            filtered_services = [
                service for service in filtered_services
                if service["needs_review"] == needs_review
            ]
        
        # Apply pagination
        total_filtered = len(filtered_services)
        paginated_services = filtered_services[offset:offset + limit]
        
        return ServiceListResponse(
            services=paginated_services,
            total_services=total_filtered,
            upload_id=latest_upload_id,
            upload_filename=upload_info["filename"],
            last_updated=upload_info["created_at"]
        )
        
    except Exception as e:
        logger.error(f"Failed to get services: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get services: {str(e)}")


@router.get("/services/{service_name}")
async def get_service_by_name(service_name: str):
    """
    Get detailed information about a specific service by name
    
    Returns service details from the most recent completed classification.
    """
    try:
        # Find the most recent completed classification
        latest_upload_id = None
        latest_timestamp = None
        
        for upload_id, classification_data in classification_store.items():
            if upload_id not in upload_status_store:
                continue
                
            upload_info = upload_status_store[upload_id]
            if upload_info["status"] != "completed":
                continue
            
            created_at = datetime.fromisoformat(upload_info["created_at"])
            if latest_timestamp is None or created_at > latest_timestamp:
                latest_timestamp = created_at
                latest_upload_id = upload_id
        
        if not latest_upload_id:
            raise HTTPException(status_code=404, detail="No completed classifications found")
        
        # Find the specific service
        classification_data = classification_store[latest_upload_id]
        services = classification_data["services"]
        
        for service in services:
            if service["service_name"] == service_name:
                # Add metadata
                upload_info = upload_status_store[latest_upload_id]
                service_with_metadata = service.copy()
                service_with_metadata["upload_id"] = latest_upload_id
                service_with_metadata["upload_filename"] = upload_info["filename"]
                service_with_metadata["last_updated"] = upload_info["created_at"]
                return service_with_metadata
        
        raise HTTPException(status_code=404, detail=f"Service '{service_name}' not found")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get service {service_name}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get service: {str(e)}")


@router.get("/services/stats/summary")
async def get_services_summary():
    """
    Get summary statistics about all services
    
    Returns aggregated statistics from the most recent completed classification.
    """
    try:
        # Find the most recent completed classification
        latest_upload_id = None
        latest_timestamp = None
        
        for upload_id, classification_data in classification_store.items():
            if upload_id not in upload_status_store:
                continue
                
            upload_info = upload_status_store[upload_id]
            if upload_info["status"] != "completed":
                continue
            
            created_at = datetime.fromisoformat(upload_info["created_at"])
            if latest_timestamp is None or created_at > latest_timestamp:
                latest_timestamp = created_at
                latest_upload_id = upload_id
        
        if not latest_upload_id:
            return {
                "total_services": 0,
                "total_endpoints": 0,
                "high_confidence": 0,
                "medium_confidence": 0,
                "needs_review": 0,
                "avg_confidence": 0.0,
                "largest_service": None,
                "upload_id": None,
                "last_updated": None
            }
        
        # Calculate statistics
        classification_data = classification_store[latest_upload_id]
        services = classification_data["services"]
        upload_info = upload_status_store[latest_upload_id]
        
        total_services = len(services)
        total_endpoints = sum(s["endpoint_count"] for s in services)
        high_confidence = sum(1 for s in services if s["confidence_score"] >= 0.8)
        medium_confidence = sum(1 for s in services if 0.6 <= s["confidence_score"] < 0.8)
        needs_review = sum(1 for s in services if s["needs_review"])
        avg_confidence = sum(s["confidence_score"] for s in services) / len(services) if services else 0.0
        
        # Find largest service
        largest_service = None
        if services:
            largest = max(services, key=lambda s: s["endpoint_count"])
            largest_service = {
                "name": largest["service_name"],
                "endpoint_count": largest["endpoint_count"]
            }
        
        return {
            "total_services": total_services,
            "total_endpoints": total_endpoints,
            "high_confidence": high_confidence,
            "medium_confidence": medium_confidence,
            "needs_review": needs_review,
            "avg_confidence": round(avg_confidence, 3),
            "largest_service": largest_service,
            "upload_id": latest_upload_id,
            "upload_filename": upload_info["filename"],
            "last_updated": upload_info["created_at"]
        }
        
    except Exception as e:
        logger.error(f"Failed to get services summary: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get services summary: {str(e)}")