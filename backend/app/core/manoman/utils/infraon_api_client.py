"""
InfraonAPIClient - Live API Interaction Client

Provides functionality to interact with live Infraon API endpoints for
procedural testing, schema discovery, and validation.

This client handles:
- Dynamic API endpoint discovery
- Authentication and session management
- Request/response validation
- Schema discovery through live testing
- Entity lifecycle testing (Create-Read-Delete)
"""

import asyncio
import logging
import uuid
from datetime import datetime
from typing import Dict, Any, Optional, List, Tuple, Union
from dataclasses import dataclass
from enum import Enum

import aiohttp
import json
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class APIOperation(Enum):
    """API operations for testing"""
    CREATE = "create"
    READ = "read"
    UPDATE = "update"
    DELETE = "delete"
    LIST = "list"


@dataclass
class APIEndpoint:
    """API endpoint information for testing"""
    path: str
    method: str
    operation_id: str
    parameters: Dict[str, Any]
    request_body_schema: Optional[Dict[str, Any]] = None
    response_schema: Optional[Dict[str, Any]] = None
    authentication_required: bool = True


@dataclass
class APITestResult:
    """Result of a single API test"""
    endpoint: APIEndpoint
    operation: APIOperation
    success: bool
    response_status: Optional[int] = None
    response_data: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    execution_time_ms: Optional[float] = None
    discovered_schema: Optional[Dict[str, Any]] = None


@dataclass
class TestEntity:
    """Test entity created during procedural testing"""
    entity_id: str
    service_name: str
    entity_type: str
    created_via_endpoint: str
    creation_response: Dict[str, Any]
    cleanup_endpoint: Optional[str] = None
    cleanup_attempted: bool = False
    cleanup_successful: bool = False


class InfraonAPIClient:
    """
    Client for interacting with live Infraon API endpoints.
    
    Supports authentication, dynamic endpoint discovery, and comprehensive
    testing including Create-Read-Delete cycles for schema validation.
    """
    
    def __init__(
        self, 
        base_url: str,
        api_key: Optional[str] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
        authorization: Optional[str] = None,
        csrf_token: Optional[str] = None,
        timeout: int = 30
    ):
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.username = username
        self.password = password
        self.authorization = authorization  # For Infraon-specific auth
        self.csrf_token = csrf_token        # For Infraon CSRF token
        self.timeout = timeout
        
        # Session management
        self.session: Optional[aiohttp.ClientSession] = None
        self.auth_token: Optional[str] = None
        self.auth_expires_at: Optional[datetime] = None
        
        # Test entity tracking
        self.test_entities: List[TestEntity] = []
        self.cleanup_queue: List[TestEntity] = []
        
        # Schema discovery cache
        self.discovered_schemas: Dict[str, Dict[str, Any]] = {}
        
    async def __aenter__(self):
        """Async context manager entry"""
        await self.initialize()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.cleanup()
        
    async def initialize(self):
        """Initialize the API client session"""
        if self.session is None:
            timeout = aiohttp.ClientTimeout(total=self.timeout)
            self.session = aiohttp.ClientSession(timeout=timeout)
            
        # Authenticate if credentials provided
        if self.username and self.password:
            await self._authenticate()
            
        logger.info(f"InfraonAPIClient initialized for {self.base_url}")
        
    async def cleanup(self):
        """Clean up resources and test entities"""
        # Clean up test entities before closing session
        await self.cleanup_test_entities()
        
        # Close HTTP session
        if self.session:
            await self.session.close()
            self.session = None
            
        logger.info("InfraonAPIClient cleanup completed")
        
    async def _authenticate(self) -> bool:
        """
        Authenticate with the Infraon API
        
        Returns:
            bool: True if authentication successful
        """
        try:
            # Infraon authentication endpoint (adjust based on actual API)
            auth_url = f"{self.base_url}/api/auth/login"
            
            auth_data = {
                "username": self.username,
                "password": self.password
            }
            
            async with self.session.post(auth_url, json=auth_data) as response:
                if response.status == 200:
                    auth_result = await response.json()
                    self.auth_token = auth_result.get("token") or auth_result.get("access_token")
                    
                    if self.auth_token:
                        logger.info("Authentication successful")
                        return True
                        
                logger.error(f"Authentication failed: {response.status}")
                return False
                
        except Exception as e:
            logger.error(f"Authentication error: {str(e)}")
            return False
            
    def _get_auth_headers(self) -> Dict[str, str]:
        """Get authentication headers for requests"""
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        
        # Infraon-specific authentication
        if self.authorization:
            headers["Authorization"] = self.authorization
        elif self.api_key:
            headers["X-API-Key"] = self.api_key
        elif self.auth_token:
            headers["Authorization"] = f"Bearer {self.auth_token}"
        
        # Infraon CSRF token
        if self.csrf_token:
            headers["X-CSRFToken"] = self.csrf_token
            
        return headers
        
    async def test_endpoint(
        self, 
        endpoint: APIEndpoint, 
        test_data: Optional[Dict[str, Any]] = None,
        path_params: Optional[Dict[str, Any]] = None
    ) -> APITestResult:
        """
        Test a single API endpoint
        
        Args:
            endpoint: The endpoint to test
            test_data: Data to send in request body
            path_params: Parameters to substitute in path
            
        Returns:
            APITestResult: Result of the test
        """
        start_time = datetime.now()
        
        try:
            # Build URL with path parameters
            url = self._build_url(endpoint.path, path_params)
            headers = self._get_auth_headers()
            
            # Prepare request parameters
            request_kwargs = {"headers": headers}
            if test_data and endpoint.method.upper() in ["POST", "PUT", "PATCH"]:
                request_kwargs["json"] = test_data
                
            # Make the request
            async with self.session.request(
                endpoint.method.upper(), 
                url, 
                **request_kwargs
            ) as response:
                
                execution_time = (datetime.now() - start_time).total_seconds() * 1000
                
                # Parse response
                response_data = None
                try:
                    response_data = await response.json()
                except:
                    response_data = {"raw": await response.text()}
                    
                # Discover schema from response
                discovered_schema = self._analyze_response_schema(response_data)
                
                success = 200 <= response.status < 300
                
                result = APITestResult(
                    endpoint=endpoint,
                    operation=self._classify_operation(endpoint),
                    success=success,
                    response_status=response.status,
                    response_data=response_data,
                    execution_time_ms=execution_time,
                    discovered_schema=discovered_schema
                )
                
                if not success:
                    result.error_message = f"HTTP {response.status}: {response_data}"
                    
                return result
                
        except Exception as e:
            execution_time = (datetime.now() - start_time).total_seconds() * 1000
            
            return APITestResult(
                endpoint=endpoint,
                operation=self._classify_operation(endpoint),
                success=False,
                error_message=str(e),
                execution_time_ms=execution_time
            )
            
    async def perform_crd_cycle(
        self, 
        service_name: str,
        create_endpoint: APIEndpoint,
        read_endpoint: APIEndpoint, 
        delete_endpoint: APIEndpoint,
        test_data: Dict[str, Any]
    ) -> Dict[str, APITestResult]:
        """
        Perform Create-Read-Delete cycle testing
        
        Args:
            service_name: Name of the service being tested
            create_endpoint: Endpoint for creating entities
            read_endpoint: Endpoint for reading entities
            delete_endpoint: Endpoint for deleting entities
            test_data: Test data for entity creation
            
        Returns:
            Dict containing results for each operation
        """
        results = {}
        created_entity = None
        
        # Step 1: Create
        logger.info(f"Starting CRD cycle for {service_name} - CREATE")
        create_result = await self.test_endpoint(create_endpoint, test_data)
        results["create"] = create_result
        
        if create_result.success and create_result.response_data:
            # Extract entity ID from create response
            entity_id = self._extract_entity_id(create_result.response_data)
            
            if entity_id:
                # Track test entity for cleanup
                created_entity = TestEntity(
                    entity_id=entity_id,
                    service_name=service_name,
                    entity_type=service_name,
                    created_via_endpoint=create_endpoint.path,
                    creation_response=create_result.response_data,
                    cleanup_endpoint=delete_endpoint.path
                )
                self.test_entities.append(created_entity)
                
                # Step 2: Read
                logger.info(f"CRD cycle for {service_name} - READ")
                read_path_params = {"id": entity_id}
                read_result = await self.test_endpoint(read_endpoint, path_params=read_path_params)
                results["read"] = read_result
                
                # Step 3: Delete
                logger.info(f"CRD cycle for {service_name} - DELETE")
                delete_path_params = {"id": entity_id}
                delete_result = await self.test_endpoint(delete_endpoint, path_params=delete_path_params)
                results["delete"] = delete_result
                
                # Update cleanup status
                if delete_result.success:
                    created_entity.cleanup_attempted = True
                    created_entity.cleanup_successful = True
                else:
                    # Add to cleanup queue for later
                    self.cleanup_queue.append(created_entity)
                    
            else:
                logger.warning(f"Could not extract entity ID from create response for {service_name}")
                results["read"] = APITestResult(
                    endpoint=read_endpoint,
                    operation=APIOperation.READ,
                    success=False,
                    error_message="No entity ID found in create response"
                )
                results["delete"] = APITestResult(
                    endpoint=delete_endpoint,
                    operation=APIOperation.DELETE,
                    success=False,
                    error_message="No entity ID found in create response"
                )
        else:
            logger.warning(f"Create operation failed for {service_name}, skipping read/delete")
            results["read"] = APITestResult(
                endpoint=read_endpoint,
                operation=APIOperation.READ,
                success=False,
                error_message="Create operation failed"
            )
            results["delete"] = APITestResult(
                endpoint=delete_endpoint,
                operation=APIOperation.DELETE,
                success=False,
                error_message="Create operation failed"
            )
            
        return results
        
    async def discover_service_schema(
        self, 
        service_name: str,
        endpoints: List[APIEndpoint]
    ) -> Dict[str, Any]:
        """
        Discover actual schema for a service through live testing
        
        Args:
            service_name: Name of the service
            endpoints: List of endpoints to test
            
        Returns:
            Dict containing discovered schemas for operations
        """
        discovered_schema = {
            "service_name": service_name,
            "operations": {},
            "discovery_timestamp": datetime.utcnow().isoformat(),
            "endpoints_tested": len(endpoints)
        }
        
        for endpoint in endpoints:
            operation = self._classify_operation(endpoint)
            
            # Test with minimal data first
            test_result = await self.test_endpoint(endpoint, {})
            
            if test_result.discovered_schema:
                discovered_schema["operations"][operation.value] = {
                    "endpoint": {
                        "path": endpoint.path,
                        "method": endpoint.method,
                        "operation_id": endpoint.operation_id
                    },
                    "schema": test_result.discovered_schema,
                    "success": test_result.success,
                    "response_status": test_result.response_status
                }
                
        # Cache the discovered schema
        self.discovered_schemas[service_name] = discovered_schema
        
        return discovered_schema
        
    async def cleanup_test_entities(self) -> Dict[str, Any]:
        """
        Clean up all test entities created during testing
        
        Returns:
            Dict containing cleanup summary
        """
        cleanup_summary = {
            "total_entities": len(self.test_entities),
            "cleanup_attempted": 0,
            "cleanup_successful": 0,
            "cleanup_failed": 0,
            "manual_cleanup_required": []
        }
        
        for entity in self.test_entities:
            if not entity.cleanup_attempted and entity.cleanup_endpoint:
                try:
                    # Attempt to delete the entity
                    delete_endpoint = APIEndpoint(
                        path=entity.cleanup_endpoint,
                        method="DELETE",
                        operation_id=f"delete_{entity.entity_type}",
                        parameters={}
                    )
                    
                    path_params = {"id": entity.entity_id}
                    delete_result = await self.test_endpoint(delete_endpoint, path_params=path_params)
                    
                    entity.cleanup_attempted = True
                    cleanup_summary["cleanup_attempted"] += 1
                    
                    if delete_result.success:
                        entity.cleanup_successful = True
                        cleanup_summary["cleanup_successful"] += 1
                    else:
                        cleanup_summary["cleanup_failed"] += 1
                        cleanup_summary["manual_cleanup_required"].append({
                            "entity_id": entity.entity_id,
                            "service": entity.service_name,
                            "endpoint": entity.cleanup_endpoint,
                            "error": delete_result.error_message
                        })
                        
                except Exception as e:
                    logger.error(f"Cleanup failed for entity {entity.entity_id}: {str(e)}")
                    cleanup_summary["cleanup_failed"] += 1
                    cleanup_summary["manual_cleanup_required"].append({
                        "entity_id": entity.entity_id,
                        "service": entity.service_name,
                        "endpoint": entity.cleanup_endpoint,
                        "error": str(e)
                    })
                    
        logger.info(f"Cleanup completed: {cleanup_summary['cleanup_successful']}/{cleanup_summary['total_entities']} entities cleaned")
        
        return cleanup_summary
        
    def _build_url(self, path: str, path_params: Optional[Dict[str, Any]] = None) -> str:
        """Build full URL with path parameters"""
        url = f"{self.base_url}{path}"
        
        if path_params:
            for param, value in path_params.items():
                url = url.replace(f"{{{param}}}", str(value))
                
        return url
        
    def _classify_operation(self, endpoint: APIEndpoint) -> APIOperation:
        """Classify endpoint operation type"""
        method = endpoint.method.upper()
        path = endpoint.path.lower()
        operation_id = endpoint.operation_id.lower()
        
        if method == "POST":
            return APIOperation.CREATE
        elif method == "GET":
            if "{id}" in path or "get" in operation_id:
                return APIOperation.READ
            else:
                return APIOperation.LIST
        elif method == "PUT" or method == "PATCH":
            return APIOperation.UPDATE
        elif method == "DELETE":
            return APIOperation.DELETE
        else:
            return APIOperation.READ  # Default
            
    def _extract_entity_id(self, response_data: Dict[str, Any]) -> Optional[str]:
        """Extract entity ID from API response"""
        # Common patterns for entity IDs
        id_fields = ["id", "uuid", "identifier", "entity_id", "_id"]
        
        for field in id_fields:
            if field in response_data:
                return str(response_data[field])
                
        # Check in nested data
        if "data" in response_data:
            for field in id_fields:
                if field in response_data["data"]:
                    return str(response_data["data"][field])
                    
        return None
        
    def _analyze_response_schema(self, response_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze response data to discover schema"""
        if not response_data:
            return {}
            
        schema = {
            "type": "object",
            "properties": {},
            "field_types": {},
            "required_fields": [],
            "optional_fields": []
        }
        
        def analyze_value(value):
            if isinstance(value, str):
                return "string"
            elif isinstance(value, int):
                return "integer"
            elif isinstance(value, float):
                return "number"
            elif isinstance(value, bool):
                return "boolean"
            elif isinstance(value, list):
                return "array"
            elif isinstance(value, dict):
                return "object"
            else:
                return "unknown"
                
        # Analyze top-level fields
        for field, value in response_data.items():
            field_type = analyze_value(value)
            schema["properties"][field] = {"type": field_type}
            schema["field_types"][field] = field_type
            
            # Assume all fields are required (this could be refined)
            schema["required_fields"].append(field)
            
        return schema