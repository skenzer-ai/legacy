"""
Classification API Endpoints

FastAPI endpoints for managing service classification results and operations.
Provides endpoints for getting classified services, merging services, and splitting services.
"""

import json
import logging
import uuid
from datetime import datetime
from typing import Optional, Dict, List, Any

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field

from ..engines.service_classifier import ServiceClassifier
from ..engines.conflict_detector import ConflictDetector
from ..storage.registry_manager import RegistryManager
from ..models.service_registry import ServiceDefinition, ServiceOperation
from ..models.api_specification import APISpecification
from .upload import upload_status_store  # Access to upload data

logger = logging.getLogger(__name__)

# Create router (tags will be overridden by main router)
router = APIRouter()

# In-memory storage for classification results (in production, use Redis or database)
classification_store: Dict[str, Dict[str, Any]] = {}


class ClassificationSummary(BaseModel):
    """Summary of classification results"""
    high_confidence: int
    medium_confidence: int
    needs_review: int


class ServiceSummary(BaseModel):
    """Summary of a classified service"""
    service_name: str
    endpoint_count: int
    suggested_description: str
    tier1_operations: int
    tier2_operations: int
    confidence_score: float
    needs_review: bool
    keywords: List[str] = Field(default_factory=list)
    synonyms: List[str] = Field(default_factory=list)


class ClassificationResponse(BaseModel):
    """Response model for service classification"""
    upload_id: str
    total_services: int
    services: List[ServiceSummary]
    classification_summary: ClassificationSummary


class ServiceMergeRequest(BaseModel):
    """Request model for merging services"""
    source_services: List[str] = Field(..., description="List of service names to merge")
    new_service_name: str = Field(..., description="Name for the merged service")
    merge_strategy: str = Field(default="combine_all", description="Merge strategy: combine_all, prefer_first")


class ServiceSplitRequest(BaseModel):
    """Request model for splitting services"""
    source_service: str = Field(..., description="Service name to split")
    split_config: Dict[str, List[str]] = Field(..., description="Map of new service names to operation IDs")


class ServiceMergeResponse(BaseModel):
    """Response model for service merge operation"""
    success: bool
    new_service_name: str
    merged_services: List[str]
    total_operations: int
    message: str


class ServiceSplitResponse(BaseModel):
    """Response model for service split operation"""
    success: bool
    original_service: str
    new_services: List[str]
    message: str


@router.get("/classification/{upload_id}/services", response_model=ClassificationResponse)
async def get_classified_services(upload_id: str):
    """
    Get auto-classified services for an uploaded API specification
    
    Returns the results of automatic service classification including
    service groupings, confidence scores, and recommendations.
    """
    try:
        # Check if upload exists
        if upload_id not in upload_status_store:
            raise HTTPException(status_code=404, detail=f"Upload ID {upload_id} not found")
        
        upload_data = upload_status_store[upload_id]
        
        # Check if upload is ready for classification
        if upload_data["status"] != "completed":
            raise HTTPException(
                status_code=400, 
                detail=f"Upload {upload_id} is not ready for classification. Status: {upload_data['status']}"
            )
        
        # Check if already classified
        if upload_id in classification_store:
            logger.info(f"Returning cached classification results for {upload_id}")
            return ClassificationResponse.parse_obj(classification_store[upload_id])
        
        # Get parsed specification
        if "parsed_specification" not in upload_data:
            raise HTTPException(
                status_code=400, 
                detail=f"No parsed specification found for upload {upload_id}"
            )
        
        spec_data = upload_data["parsed_specification"]
        api_spec = APISpecification.parse_obj(spec_data)
        
        # Perform classification
        logger.info(f"Starting classification for upload {upload_id} with {api_spec.total_endpoints} endpoints")
        
        classifier = ServiceClassifier()
        service_groups = await classifier.classify_services(api_spec)
        
        # Convert to service summaries
        services = []
        high_confidence = 0
        medium_confidence = 0
        needs_review = 0
        
        for service_name, service_group in service_groups.items():
            # Use the data from ServiceGroup object
            tier1_count = len(service_group.tier1_operations)
            tier2_count = len(service_group.tier2_operations)
            
            # Determine confidence category
            if service_group.confidence_score >= 0.8:
                high_confidence += 1
                needs_review_flag = False
            elif service_group.confidence_score >= 0.6:
                medium_confidence += 1
                needs_review_flag = False
            else:
                needs_review += 1
                needs_review_flag = True
            
            service_summary = ServiceSummary(
                service_name=service_group.service_name,
                endpoint_count=len(service_group.endpoints),
                suggested_description=service_group.suggested_description,
                tier1_operations=tier1_count,
                tier2_operations=tier2_count,
                confidence_score=service_group.confidence_score,
                needs_review=needs_review_flag,
                keywords=service_group.keywords,
                synonyms=service_group.synonyms
            )
            
            services.append(service_summary)
        
        # Sort services by confidence score (highest first)
        services.sort(key=lambda x: x.confidence_score, reverse=True)
        
        # Create classification summary
        classification_summary = ClassificationSummary(
            high_confidence=high_confidence,
            medium_confidence=medium_confidence,
            needs_review=needs_review
        )
        
        # Create response
        response = ClassificationResponse(
            upload_id=upload_id,
            total_services=len(services),
            services=services,
            classification_summary=classification_summary
        )
        
        # Cache the results
        classification_store[upload_id] = response.dict()
        
        logger.info(f"Classification completed for {upload_id}: {len(services)} services identified")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Classification failed for upload {upload_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Classification failed: {str(e)}")


@router.post("/classification/{upload_id}/services/merge", response_model=ServiceMergeResponse)
async def merge_services(upload_id: str, merge_request: ServiceMergeRequest):
    """
    Merge multiple services into one
    
    Combines the specified services into a single service using the chosen merge strategy.
    """
    try:
        # Check if classification exists
        if upload_id not in classification_store:
            raise HTTPException(
                status_code=404, 
                detail=f"No classification results found for upload {upload_id}. Run classification first."
            )
        
        classification_data = classification_store[upload_id]
        
        # Validate source services exist
        existing_services = {s["service_name"] for s in classification_data["services"]}
        for service_name in merge_request.source_services:
            if service_name not in existing_services:
                raise HTTPException(
                    status_code=400,
                    detail=f"Service '{service_name}' not found in classification results"
                )
        
        # Check if new service name conflicts
        if (merge_request.new_service_name in existing_services and 
            merge_request.new_service_name not in merge_request.source_services):
            raise HTTPException(
                status_code=400,
                detail=f"Target service name '{merge_request.new_service_name}' already exists"
            )
        
        # Perform merge operation
        services_to_merge = [
            s for s in classification_data["services"] 
            if s["service_name"] in merge_request.source_services
        ]
        
        # Calculate merged service properties
        total_endpoints = sum(s["endpoint_count"] for s in services_to_merge)
        total_tier1 = sum(s["tier1_operations"] for s in services_to_merge)
        total_tier2 = sum(s["tier2_operations"] for s in services_to_merge)
        
        # Create merged service based on strategy
        if merge_request.merge_strategy == "prefer_first":
            base_service = services_to_merge[0]
            merged_description = base_service["suggested_description"]
            merged_keywords = base_service["keywords"].copy()
            merged_synonyms = base_service["synonyms"].copy()
            
            # Add keywords and synonyms from other services
            for service in services_to_merge[1:]:
                merged_keywords.extend(service["keywords"])
                merged_synonyms.extend(service["synonyms"])
        
        else:  # combine_all strategy
            all_descriptions = [s["suggested_description"] for s in services_to_merge]
            merged_description = f"Merged service combining: {', '.join(all_descriptions)}"
            
            merged_keywords = []
            merged_synonyms = []
            for service in services_to_merge:
                merged_keywords.extend(service["keywords"])
                merged_synonyms.extend(service["synonyms"])
        
        # Remove duplicates
        merged_keywords = list(set(merged_keywords))
        merged_synonyms = list(set(merged_synonyms))
        
        # Calculate average confidence
        avg_confidence = sum(s["confidence_score"] for s in services_to_merge) / len(services_to_merge)
        
        # Create merged service summary
        merged_service = ServiceSummary(
            service_name=merge_request.new_service_name,
            endpoint_count=total_endpoints,
            suggested_description=merged_description,
            tier1_operations=total_tier1,
            tier2_operations=total_tier2,
            confidence_score=avg_confidence,
            needs_review=avg_confidence < 0.6,
            keywords=merged_keywords,
            synonyms=merged_synonyms
        )
        
        # Update classification data
        # Remove merged services
        updated_services = [
            s for s in classification_data["services"] 
            if s["service_name"] not in merge_request.source_services
        ]
        
        # Add merged service
        updated_services.append(merged_service.dict())
        
        # Update classification store
        classification_data["services"] = updated_services
        classification_data["total_services"] = len(updated_services)
        
        # Recalculate summary
        high_confidence = sum(1 for s in updated_services if s["confidence_score"] >= 0.8)
        medium_confidence = sum(1 for s in updated_services if 0.6 <= s["confidence_score"] < 0.8)
        needs_review = sum(1 for s in updated_services if s["confidence_score"] < 0.6)
        
        classification_data["classification_summary"] = {
            "high_confidence": high_confidence,
            "medium_confidence": medium_confidence,
            "needs_review": needs_review
        }
        
        classification_store[upload_id] = classification_data
        
        logger.info(f"Merged {len(merge_request.source_services)} services into '{merge_request.new_service_name}'")
        
        return ServiceMergeResponse(
            success=True,
            new_service_name=merge_request.new_service_name,
            merged_services=merge_request.source_services,
            total_operations=total_tier1 + total_tier2,
            message=f"Successfully merged {len(merge_request.source_services)} services into '{merge_request.new_service_name}'"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Service merge failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Service merge failed: {str(e)}")


@router.post("/classification/{upload_id}/services/split", response_model=ServiceSplitResponse)
async def split_service(upload_id: str, split_request: ServiceSplitRequest):
    """
    Split a service into multiple services
    
    Divides the specified service into multiple services based on the split configuration.
    """
    try:
        # Check if classification exists
        if upload_id not in classification_store:
            raise HTTPException(
                status_code=404, 
                detail=f"No classification results found for upload {upload_id}. Run classification first."
            )
        
        classification_data = classification_store[upload_id]
        
        # Find the service to split
        source_service = None
        for service in classification_data["services"]:
            if service["service_name"] == split_request.source_service:
                source_service = service
                break
        
        if not source_service:
            raise HTTPException(
                status_code=404,
                detail=f"Service '{split_request.source_service}' not found in classification results"
            )
        
        # Validate split configuration
        total_operations = source_service["tier1_operations"] + source_service["tier2_operations"]
        split_operations_count = sum(len(ops) for ops in split_request.split_config.values())
        
        if split_operations_count != total_operations:
            raise HTTPException(
                status_code=400,
                detail=f"Split configuration mismatch: source has {total_operations} operations, "
                       f"split config has {split_operations_count} operations"
            )
        
        # Check for new service name conflicts
        existing_services = {s["service_name"] for s in classification_data["services"]}
        for new_service_name in split_request.split_config.keys():
            if new_service_name in existing_services and new_service_name != split_request.source_service:
                raise HTTPException(
                    status_code=400,
                    detail=f"New service name '{new_service_name}' already exists"
                )
        
        # Create new services from split
        new_services = []
        for new_service_name, operation_count in split_request.split_config.items():
            # Estimate tier distribution (simple heuristic)
            estimated_tier1 = int(len(operation_count) * 0.7)  # Assume 70% tier1
            estimated_tier2 = len(operation_count) - estimated_tier1
            
            # Inherit properties from original service
            new_service = ServiceSummary(
                service_name=new_service_name,
                endpoint_count=len(operation_count),
                suggested_description=f"Split from {split_request.source_service} - handles {new_service_name} operations",
                tier1_operations=estimated_tier1,
                tier2_operations=estimated_tier2,
                confidence_score=source_service["confidence_score"] * 0.9,  # Slightly lower confidence
                needs_review=source_service["confidence_score"] * 0.9 < 0.6,
                keywords=source_service["keywords"].copy(),  # Inherit keywords
                synonyms=source_service["synonyms"].copy()   # Inherit synonyms
            )
            
            new_services.append(new_service)
        
        # Update classification data
        # Remove original service
        updated_services = [
            s for s in classification_data["services"] 
            if s["service_name"] != split_request.source_service
        ]
        
        # Add new services
        for service in new_services:
            updated_services.append(service.dict())
        
        # Update classification store
        classification_data["services"] = updated_services
        classification_data["total_services"] = len(updated_services)
        
        # Recalculate summary
        high_confidence = sum(1 for s in updated_services if s["confidence_score"] >= 0.8)
        medium_confidence = sum(1 for s in updated_services if 0.6 <= s["confidence_score"] < 0.8)
        needs_review = sum(1 for s in updated_services if s["confidence_score"] < 0.6)
        
        classification_data["classification_summary"] = {
            "high_confidence": high_confidence,
            "medium_confidence": medium_confidence,
            "needs_review": needs_review
        }
        
        classification_store[upload_id] = classification_data
        
        new_service_names = list(split_request.split_config.keys())
        logger.info(f"Split service '{split_request.source_service}' into {len(new_service_names)} services")
        
        return ServiceSplitResponse(
            success=True,
            original_service=split_request.source_service,
            new_services=new_service_names,
            message=f"Successfully split '{split_request.source_service}' into {len(new_service_names)} services: {', '.join(new_service_names)}"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Service split failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Service split failed: {str(e)}")


@router.get("/classification/{upload_id}/conflicts")
async def get_classification_conflicts(upload_id: str):
    """
    Get potential conflicts in the current classification
    
    Analyzes the classified services for keyword conflicts and other issues.
    """
    try:
        # Check if classification exists
        if upload_id not in classification_store:
            raise HTTPException(
                status_code=404, 
                detail=f"No classification results found for upload {upload_id}. Run classification first."
            )
        
        classification_data = classification_store[upload_id]
        
        # Create temporary service definitions for conflict detection
        temp_services = {}
        for service_data in classification_data["services"]:
            # Create minimal service definition for conflict analysis
            temp_service = ServiceDefinition(
                service_name=service_data["service_name"],
                service_description=service_data["suggested_description"],
                business_context=f"Service for {service_data['service_name']} operations",
                keywords=service_data.get("keywords", []),
                synonyms=service_data.get("synonyms", []),
                tier1_operations={},  # Empty for conflict analysis
                tier2_operations={}   # Empty for conflict analysis
            )
            temp_services[service_data["service_name"]] = temp_service
        
        # Run conflict detection
        conflict_detector = ConflictDetector()
        conflicts = await conflict_detector.detect_conflicts_in_services(temp_services)
        
        # Format conflicts for response
        formatted_conflicts = []
        for conflict in conflicts:
            formatted_conflicts.append({
                "conflict_type": conflict.conflict_type.value,
                "severity": conflict.severity.value,
                "affected_services": conflict.affected_services,
                "description": conflict.description,
                "suggested_resolutions": conflict.suggested_resolutions,
                "auto_resolvable": conflict.auto_resolvable,
                "detection_timestamp": conflict.detection_timestamp
            })
        
        return {
            "upload_id": upload_id,
            "total_conflicts": len(formatted_conflicts),
            "conflicts": formatted_conflicts,
            "high_severity_count": sum(1 for c in formatted_conflicts if c["severity"] == "high"),
            "medium_severity_count": sum(1 for c in formatted_conflicts if c["severity"] == "medium"),
            "low_severity_count": sum(1 for c in formatted_conflicts if c["severity"] == "low")
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Conflict detection failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Conflict detection failed: {str(e)}")


@router.delete("/classification/{upload_id}")
async def clear_classification(upload_id: str):
    """
    Clear classification results for an upload
    
    Removes the cached classification data, allowing for re-classification.
    """
    try:
        if upload_id not in classification_store:
            raise HTTPException(
                status_code=404, 
                detail=f"No classification results found for upload {upload_id}"
            )
        
        del classification_store[upload_id]
        
        logger.info(f"Cleared classification results for upload {upload_id}")
        
        return {
            "message": f"Classification results cleared for upload {upload_id}",
            "upload_id": upload_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to clear classification: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to clear classification: {str(e)}")


# Cleanup function (should be called periodically)
async def cleanup_old_classifications(max_age_hours: int = 24):
    """
    Clean up old classification records to prevent memory bloat
    
    Args:
        max_age_hours: Maximum age of classifications to keep in hours
    """
    try:
        current_time = datetime.utcnow()
        cutoff_time = current_time.timestamp() - (max_age_hours * 3600)
        
        classifications_to_remove = []
        for upload_id in classification_store.keys():
            # Check if corresponding upload still exists and is recent
            if upload_id not in upload_status_store:
                classifications_to_remove.append(upload_id)
                continue
            
            upload_data = upload_status_store[upload_id]
            created_at = datetime.fromisoformat(upload_data["created_at"])
            if created_at.timestamp() < cutoff_time:
                classifications_to_remove.append(upload_id)
        
        for upload_id in classifications_to_remove:
            del classification_store[upload_id]
        
        if classifications_to_remove:
            logger.info(f"Cleaned up {len(classifications_to_remove)} old classification records")
            
    except Exception as e:
        logger.error(f"Classification cleanup failed: {str(e)}")