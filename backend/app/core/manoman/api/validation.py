"""
Validation API Endpoints for Man-O-Man System

FastAPI endpoints that expose the procedural testing capabilities including:
- Start/manage procedural testing sessions
- Get testing progress and results
- Schema discovery and validation
- Test entity cleanup and management
- Accuracy testing and reporting
"""

import logging
from typing import Dict, Any, Optional, List
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel, Field

from ..agents.testing_agent import TestingAgent, TestPhase
from ..models.service_registry import ServiceRegistry
from ..models.validation_models import TestSuite, TestResults, ProceduralTestResults
from ..utils.infraon_api_client import InfraonAPIClient
from ....core.agents.base.llm_service import LLMService
from ..engines.query_classifier import QueryClassifier
from ..storage.registry_manager import RegistryManager

logger = logging.getLogger(__name__)

router = APIRouter()

# Request/Response Models
class StartProceduralTestingRequest(BaseModel):
    """Request to start procedural testing"""
    registry_id: str = Field(..., description="Registry ID to test")
    services_to_test: Optional[List[str]] = Field(None, description="Specific services to test (None for all)")
    max_concurrent_services: int = Field(default=3, ge=1, le=10, description="Maximum concurrent service tests")
    api_base_url: Optional[str] = Field(None, description="Base URL for live API testing")
    api_credentials: Optional[Dict[str, str]] = Field(None, description="API authentication credentials")

class StartProceduralTestingResponse(BaseModel):
    """Response when starting procedural testing"""
    session_id: str = Field(..., description="Testing session ID")
    message: str = Field(..., description="Status message")
    services_count: int = Field(..., description="Number of services to test")
    estimated_duration_minutes: int = Field(..., description="Estimated testing duration")

class TestingProgressResponse(BaseModel):
    """Response for testing progress"""
    session_id: str = Field(..., description="Testing session ID")
    phase: str = Field(..., description="Current testing phase")
    services_total: int = Field(..., description="Total services to test")
    services_completed: int = Field(..., description="Services completed")
    progress_percentage: float = Field(..., description="Overall progress percentage")
    current_service: Optional[str] = Field(None, description="Currently testing service")
    start_time: str = Field(..., description="Session start time")
    elapsed_minutes: float = Field(..., description="Elapsed time in minutes")
    services_tested: Optional[int] = Field(None, description="Services tested so far")
    successful_services: Optional[int] = Field(None, description="Successfully tested services")
    failed_services: Optional[int] = Field(None, description="Failed services")
    success_rate: Optional[float] = Field(None, description="Success rate")

class TestingResultsResponse(BaseModel):
    """Response for complete testing results"""
    session_id: str = Field(..., description="Testing session ID")
    status: str = Field(..., description="Testing status")
    start_time: str = Field(..., description="Session start time")
    services_total: int = Field(..., description="Total services tested")
    services_tested: int = Field(..., description="Services tested")
    successful_services: int = Field(..., description="Successfully tested services")
    failed_services: int = Field(..., description="Failed services")
    results_by_service: Dict[str, Any] = Field(..., description="Detailed results by service")
    schema_discrepancies: List[Dict[str, Any]] = Field(..., description="Schema validation discrepancies")
    cleanup_summary: Dict[str, Any] = Field(..., description="Test entity cleanup summary")
    performance_metrics: Dict[str, Any] = Field(..., description="Performance metrics")

class GenerateTestSuiteRequest(BaseModel):
    """Request to generate test suite"""
    registry_id: str = Field(..., description="Registry ID to generate tests for")

class RunAccuracyTestsRequest(BaseModel):
    """Request to run accuracy tests"""
    registry_id: str = Field(..., description="Registry ID to test")
    test_suite_id: Optional[str] = Field(None, description="Specific test suite ID (generates new if None)")

class CleanupTestEntitiesRequest(BaseModel):
    """Request to cleanup test entities"""
    session_id: Optional[str] = Field(None, description="Specific session to cleanup (all if None)")
    api_base_url: Optional[str] = Field(None, description="Base URL for cleanup operations")
    api_credentials: Optional[Dict[str, str]] = Field(None, description="API authentication credentials")

class SchemaDiscoveryRequest(BaseModel):
    """Request for schema discovery"""
    registry_id: str = Field(..., description="Registry ID")
    service_name: str = Field(..., description="Service to discover schema for")
    api_base_url: str = Field(..., description="Base URL for schema discovery")
    api_credentials: Optional[Dict[str, str]] = Field(None, description="API authentication credentials")


# Dependency injection
def get_registry_manager() -> RegistryManager:
    """Get registry manager instance"""
    return RegistryManager()

def get_llm_service() -> LLMService:
    """Get LLM service instance"""
    try:
        from ....core.agents.base.llm_service import LLMService
        from ....core.agents.base.config import BaseAgentConfig
        
        # Create a default config for the LLM service
        config = BaseAgentConfig()
        return LLMService(config)
    except Exception as e:
        # Fallback: create a mock LLM service for testing
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Failed to create LLMService: {e}")
        
        # Create a simple mock LLM service
        class MockLLMService:
            def __init__(self):
                pass
            async def complete(self, *args, **kwargs):
                return "Mock response"
        
        return MockLLMService()

def get_query_classifier() -> QueryClassifier:
    """Get query classifier instance"""
    return QueryClassifier()

async def get_testing_agent(
    llm_service: LLMService = Depends(get_llm_service),
    query_classifier: QueryClassifier = Depends(get_query_classifier),
    registry_manager: RegistryManager = Depends(get_registry_manager)
) -> TestingAgent:
    """Get testing agent instance with API client"""
    # Create a default API client (will be configured per request)
    api_client = InfraonAPIClient(
        base_url="http://localhost:8080",  # Default
        timeout=30
    )
    
    return TestingAgent(
        llm_service=llm_service,
        query_classifier=query_classifier,
        api_client=api_client,
        registry_manager=registry_manager
    )

# API Endpoints
@router.post("/start-procedural-testing", response_model=StartProceduralTestingResponse)
async def start_procedural_testing(
    request: StartProceduralTestingRequest,
    background_tasks: BackgroundTasks,
    testing_agent: TestingAgent = Depends(get_testing_agent),
    registry_manager: RegistryManager = Depends(get_registry_manager)
):
    """
    Start comprehensive procedural testing for a service registry
    
    This endpoint initiates:
    - Create-Read-Delete cycle testing for all Tier 1 APIs
    - Schema discovery and validation
    - Performance metrics collection
    - Automatic test entity cleanup
    """
    try:
        # Load the registry
        registry = await registry_manager.load_registry(request.registry_id)
        if not registry:
            raise HTTPException(status_code=404, detail=f"Registry {request.registry_id} not found")
        
        # Configure API client if credentials provided
        if request.api_base_url:
            testing_agent.api_client.base_url = request.api_base_url.rstrip('/')
            
        if request.api_credentials:
            testing_agent.api_client.api_key = request.api_credentials.get("api_key")
            testing_agent.api_client.username = request.api_credentials.get("username")
            testing_agent.api_client.password = request.api_credentials.get("password")
            testing_agent.api_client.authorization = request.api_credentials.get("authorization")
            testing_agent.api_client.csrf_token = request.api_credentials.get("csrf_token")
            
        # Initialize the API client
        await testing_agent.api_client.initialize()
        
        # Start procedural testing
        session_id = await testing_agent.start_procedural_testing(
            registry=registry,
            services_to_test=request.services_to_test,
            max_concurrent_services=request.max_concurrent_services
        )
        
        # Calculate service count and estimated duration
        services_count = len(request.services_to_test) if request.services_to_test else len(registry.services)
        estimated_duration = max(5, services_count * 2)  # ~2 minutes per service minimum
        
        logger.info(f"Started procedural testing session {session_id} for registry {request.registry_id}")
        
        return StartProceduralTestingResponse(
            session_id=session_id,
            message="Procedural testing started successfully",
            services_count=services_count,
            estimated_duration_minutes=estimated_duration
        )
        
    except Exception as e:
        logger.error(f"Failed to start procedural testing: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to start testing: {str(e)}")


@router.get("/testing-progress/{session_id}", response_model=TestingProgressResponse)
async def get_testing_progress(
    session_id: str,
    testing_agent: TestingAgent = Depends(get_testing_agent)
):
    """
    Get current progress of a procedural testing session
    
    Returns detailed progress information including:
    - Current testing phase
    - Services completed vs total
    - Success/failure rates
    - Performance metrics
    """
    try:
        progress = await testing_agent.get_testing_progress(session_id)
        
        if "error" in progress:
            raise HTTPException(status_code=404, detail=progress["error"])
            
        return TestingProgressResponse(**progress)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get testing progress: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get progress: {str(e)}")


@router.get("/testing-results/{session_id}", response_model=TestingResultsResponse)
async def get_testing_results(
    session_id: str,
    testing_agent: TestingAgent = Depends(get_testing_agent)
):
    """
    Get complete results of a procedural testing session
    
    Returns comprehensive results including:
    - Per-service test results
    - Schema validation reports
    - Performance metrics
    - Test entity cleanup status
    """
    try:
        results = await testing_agent.get_testing_results(session_id)
        
        if not results:
            raise HTTPException(status_code=404, detail="Testing session not found")
            
        return TestingResultsResponse(**results)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get testing results: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get results: {str(e)}")


@router.post("/generate-test-suite")
async def generate_test_suite(
    request: GenerateTestSuiteRequest,
    testing_agent: TestingAgent = Depends(get_testing_agent),
    registry_manager: RegistryManager = Depends(get_registry_manager)
):
    """
    Generate a comprehensive test suite for accuracy testing
    
    Creates test cases for:
    - Basic CRUD operations
    - Service identification
    - Intent classification
    - Edge cases and error handling
    """
    try:
        # Load the registry
        registry = await registry_manager.load_registry(request.registry_id)
        if not registry:
            raise HTTPException(status_code=404, detail=f"Registry {request.registry_id} not found")
            
        # Generate test suite
        test_suite = await testing_agent.generate_test_suite(registry)
        
        logger.info(f"Generated test suite with {test_suite.total_tests} tests for registry {request.registry_id}")
        
        return {
            "suite_id": test_suite.suite_id,
            "registry_version": test_suite.service_registry_version,
            "total_tests": test_suite.total_tests,
            "test_categories": {
                category: len(tests) for category, tests in test_suite.test_categories.items()
            },
            "message": f"Generated {test_suite.total_tests} test cases"
        }
        
    except Exception as e:
        logger.error(f"Failed to generate test suite: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to generate test suite: {str(e)}")


@router.post("/run-accuracy-tests")
async def run_accuracy_tests(
    request: RunAccuracyTestsRequest,
    testing_agent: TestingAgent = Depends(get_testing_agent),
    registry_manager: RegistryManager = Depends(get_registry_manager)
):
    """
    Run accuracy tests against the classification system
    
    Tests the accuracy of:
    - Service identification
    - Operation classification
    - Intent mapping
    - Confidence scoring
    """
    try:
        # Load the registry
        registry = await registry_manager.load_registry(request.registry_id)
        if not registry:
            raise HTTPException(status_code=404, detail=f"Registry {request.registry_id} not found")
            
        # Generate test suite if needed
        test_suite = await testing_agent.generate_test_suite(registry)
        
        # Run accuracy tests
        test_results = await testing_agent.run_accuracy_tests(registry, test_suite)
        
        logger.info(f"Completed accuracy tests: {test_results.passed}/{test_results.total_tests} passed ({test_results.accuracy_percentage:.1f}%)")
        
        return {
            "suite_id": test_suite.suite_id,
            "total_tests": test_results.total_tests,
            "passed": test_results.passed,
            "failed": test_results.failed,
            "accuracy_percentage": test_results.accuracy_percentage,
            "execution_time_total_ms": test_results.execution_time_total_ms,
            "detailed_results": test_results.detailed_results[:10],  # First 10 for response size
            "message": f"Accuracy: {test_results.accuracy_percentage:.1f}% ({test_results.passed}/{test_results.total_tests})"
        }
        
    except Exception as e:
        logger.error(f"Failed to run accuracy tests: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to run accuracy tests: {str(e)}")


@router.post("/cleanup-test-entities")
async def cleanup_test_entities(
    request: CleanupTestEntitiesRequest,
    testing_agent: TestingAgent = Depends(get_testing_agent)
):
    """
    Clean up test entities created during procedural testing
    
    Attempts to delete all test entities created during testing sessions
    and provides a summary of cleanup results.
    """
    try:
        # Configure API client if credentials provided
        if request.api_base_url:
            testing_agent.api_client.base_url = request.api_base_url.rstrip('/')
            
        if request.api_credentials:
            testing_agent.api_client.api_key = request.api_credentials.get("api_key")
            testing_agent.api_client.username = request.api_credentials.get("username")
            testing_agent.api_client.password = request.api_credentials.get("password")
            testing_agent.api_client.authorization = request.api_credentials.get("authorization")
            testing_agent.api_client.csrf_token = request.api_credentials.get("csrf_token")
            
        # Initialize the API client
        await testing_agent.api_client.initialize()
        
        # Perform cleanup
        cleanup_summary = await testing_agent.api_client.cleanup_test_entities()
        
        logger.info(f"Test entity cleanup completed: {cleanup_summary['cleanup_successful']}/{cleanup_summary['total_entities']} entities cleaned")
        
        return {
            "cleanup_summary": cleanup_summary,
            "message": f"Cleaned {cleanup_summary['cleanup_successful']}/{cleanup_summary['total_entities']} test entities"
        }
        
    except Exception as e:
        logger.error(f"Failed to cleanup test entities: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to cleanup: {str(e)}")


@router.post("/discover-service-schema")
async def discover_service_schema(
    request: SchemaDiscoveryRequest,
    testing_agent: TestingAgent = Depends(get_testing_agent),
    registry_manager: RegistryManager = Depends(get_registry_manager)
):
    """
    Discover actual schema for a service through live API interaction
    
    Tests service endpoints to discover:
    - Request/response schemas
    - Required vs optional fields
    - Data types and validation rules
    - Error responses
    """
    try:
        # Load the registry
        registry = await registry_manager.load_registry(request.registry_id)
        if not registry:
            raise HTTPException(status_code=404, detail=f"Registry {request.registry_id} not found")
            
        # Get service definition
        if request.service_name not in registry.services:
            raise HTTPException(status_code=404, detail=f"Service {request.service_name} not found in registry")
            
        service_def = registry.services[request.service_name]
        
        # Configure API client
        testing_agent.api_client.base_url = request.api_base_url.rstrip('/')
        if request.api_credentials:
            testing_agent.api_client.api_key = request.api_credentials.get("api_key")
            testing_agent.api_client.username = request.api_credentials.get("username")
            testing_agent.api_client.password = request.api_credentials.get("password")
            testing_agent.api_client.authorization = request.api_credentials.get("authorization")
            testing_agent.api_client.csrf_token = request.api_credentials.get("csrf_token")
            
        # Initialize the API client
        await testing_agent.api_client.initialize()
        
        # Convert service operations to endpoints
        endpoints = []
        for op_name, operation in service_def.get_all_operations().items():
            endpoint = testing_agent._convert_operation_to_endpoint(operation)
            if endpoint:
                endpoints.append(endpoint)
                
        # Discover schema
        discovered_schema = await testing_agent.api_client.discover_service_schema(
            service_name=request.service_name,
            endpoints=endpoints
        )
        
        logger.info(f"Schema discovery completed for {request.service_name}: {len(endpoints)} endpoints tested")
        
        return {
            "service_name": request.service_name,
            "discovered_schema": discovered_schema,
            "endpoints_tested": len(endpoints),
            "message": f"Schema discovered for {request.service_name}"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to discover service schema: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to discover schema: {str(e)}")


@router.get("/active-sessions")
async def get_active_sessions(
    testing_agent: TestingAgent = Depends(get_testing_agent)
):
    """
    Get list of all active testing sessions
    
    Returns summary information for all currently running or completed
    testing sessions.
    """
    try:
        active_sessions = []
        
        for session_id, session in testing_agent.active_sessions.items():
            session_info = {
                "session_id": session_id,
                "phase": session.phase.value,
                "registry_id": session.registry.registry_id,
                "services_total": len(session.test_plans),
                "services_completed": session.current_service_index,
                "start_time": session.start_time.isoformat(),
                "elapsed_minutes": (session.start_time.now() - session.start_time).total_seconds() / 60
            }
            active_sessions.append(session_info)
            
        return {
            "active_sessions": active_sessions,
            "total_sessions": len(active_sessions),
            "message": f"Found {len(active_sessions)} active sessions"
        }
        
    except Exception as e:
        logger.error(f"Failed to get active sessions: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get sessions: {str(e)}")


@router.delete("/session/{session_id}")
async def terminate_testing_session(
    session_id: str,
    testing_agent: TestingAgent = Depends(get_testing_agent)
):
    """
    Terminate a testing session and clean up resources
    
    Stops the testing session and performs cleanup of any test entities
    created during the session.
    """
    try:
        if session_id not in testing_agent.active_sessions:
            raise HTTPException(status_code=404, detail="Testing session not found")
            
        session = testing_agent.active_sessions[session_id]
        
        # Mark session as terminated
        session.phase = TestPhase.FAILED
        session.results["terminated"] = True
        
        # Cleanup test entities
        cleanup_summary = await testing_agent.api_client.cleanup_test_entities()
        
        # Remove session
        del testing_agent.active_sessions[session_id]
        
        logger.info(f"Terminated testing session {session_id}")
        
        return {
            "session_id": session_id,
            "message": "Testing session terminated",
            "cleanup_summary": cleanup_summary
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to terminate session: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to terminate session: {str(e)}")