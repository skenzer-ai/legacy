"""
API Specification Data Models

Pydantic models for parsing and handling raw API specifications from
uploaded files (OpenAPI 3.0, Swagger 2.0, Infraon custom formats).
"""

from pydantic import BaseModel, Field, validator
from typing import List, Dict, Optional, Any, Union
from datetime import datetime
from enum import Enum


class SpecificationFormat(str, Enum):
    """Supported API specification formats"""
    OPENAPI_3 = "openapi_3"
    SWAGGER_2 = "swagger_2"
    INFRAON_CUSTOM = "infraon_custom"
    UNKNOWN = "unknown"


class ClassificationStatus(str, Enum):
    """API specification processing status"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class HTTPMethod(str, Enum):
    """Supported HTTP methods"""
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    DELETE = "DELETE"
    PATCH = "PATCH"
    HEAD = "HEAD"
    OPTIONS = "OPTIONS"


class ParameterLocation(str, Enum):
    """Parameter location in request"""
    QUERY = "query"
    PATH = "path"
    HEADER = "header"
    BODY = "body"
    FORM = "formData"


class APIParameter(BaseModel):
    """Structured API parameter definition"""
    name: str = Field(..., description="Parameter name")
    location: ParameterLocation = Field(..., description="Parameter location (query, path, etc.)")
    type: str = Field(default="string", description="Parameter data type")
    required: bool = Field(default=False, description="Whether parameter is required")
    description: Optional[str] = Field(None, description="Parameter description")
    default_value: Optional[Any] = Field(None, description="Default parameter value")
    enum_values: Optional[List[Any]] = Field(None, description="Allowed enum values")
    format: Optional[str] = Field(None, description="Parameter format (date, email, etc.)")
    
    class Config:
        extra = "forbid"


class APIResponse(BaseModel):
    """API response definition"""
    status_code: str = Field(..., description="HTTP status code")
    description: str = Field(..., description="Response description")
    response_schema: Optional[Dict[str, Any]] = Field(None, description="Response schema")
    examples: Optional[Dict[str, Any]] = Field(None, description="Response examples")
    headers: Optional[Dict[str, str]] = Field(None, description="Response headers")
    
    class Config:
        extra = "forbid"


class APIRequestBody(BaseModel):
    """API request body definition"""
    description: Optional[str] = Field(None, description="Request body description")
    required: bool = Field(default=False, description="Whether request body is required")
    content_type: str = Field(default="application/json", description="Content type")
    body_schema: Optional[Dict[str, Any]] = Field(None, description="Request body schema")
    examples: Optional[Dict[str, Any]] = Field(None, description="Request body examples")
    
    class Config:
        extra = "forbid"


class RawAPIEndpoint(BaseModel):
    """Raw API endpoint parsed from specification file"""
    path: str = Field(..., description="API endpoint path")
    method: HTTPMethod = Field(..., description="HTTP method")
    operation_id: str = Field(..., description="Unique operation identifier")
    summary: Optional[str] = Field(None, description="Brief operation summary")
    description: Optional[str] = Field(None, description="Detailed operation description")
    tags: List[str] = Field(default_factory=list, description="Operation tags/categories")
    parameters: List[APIParameter] = Field(default_factory=list, description="Operation parameters")
    request_body: Optional[APIRequestBody] = Field(None, description="Request body definition")
    responses: Dict[str, APIResponse] = Field(default_factory=dict, description="Response definitions")
    deprecated: bool = Field(default=False, description="Whether operation is deprecated")
    security: Optional[List[Dict[str, List[str]]]] = Field(None, description="Security requirements")
    
    class Config:
        extra = "forbid"
    
    @validator('path')
    def validate_path(cls, v):
        """Ensure path starts with /"""
        if not v.startswith('/'):
            v = '/' + v
        return v
    
    @validator('operation_id')
    def validate_operation_id(cls, v):
        """Ensure operation_id is valid identifier"""
        if not v:
            raise ValueError('operation_id cannot be empty')
        if not v.strip():
            raise ValueError('operation_id cannot be whitespace only')
        # Allow alphanumeric, underscore, and hyphen only
        if not v.replace('_', '').replace('-', '').isalnum():
            raise ValueError('operation_id must contain only alphanumeric characters, underscores, and hyphens')
        return v
    
    def get_path_parameters(self) -> List[APIParameter]:
        """Get parameters that are in the path"""
        return [p for p in self.parameters if p.location == ParameterLocation.PATH]
    
    def get_query_parameters(self) -> List[APIParameter]:
        """Get query parameters"""
        return [p for p in self.parameters if p.location == ParameterLocation.QUERY]
    
    def get_required_parameters(self) -> List[APIParameter]:
        """Get all required parameters"""
        return [p for p in self.parameters if p.required]
    
    def has_request_body(self) -> bool:
        """Check if endpoint accepts request body"""
        return self.request_body is not None
    
    def get_success_response(self) -> Optional[APIResponse]:
        """Get the first successful response (2xx status code)"""
        for status_code, response in self.responses.items():
            if status_code.startswith('2'):
                return response
        return None
    
    def is_crud_operation(self) -> Optional[str]:
        """Determine if this is a CRUD operation and return type"""
        path_lower = self.path.lower()
        method = self.method.value
        
        # Pattern matching for CRUD operations
        if method == "GET":
            if path_lower.endswith('{id}') or path_lower.endswith('}'):
                return "get_by_id"
            else:
                return "list"
        elif method == "POST":
            return "create"
        elif method == "PUT" or method == "PATCH":
            return "update"
        elif method == "DELETE":
            return "delete"
        
        return None


class APISpecification(BaseModel):
    """Complete API specification from uploaded file"""
    source_file: str = Field(..., description="Original filename")
    file_format: SpecificationFormat = Field(..., description="Detected specification format")
    title: Optional[str] = Field(None, description="API title from specification")
    version: Optional[str] = Field(None, description="API version")
    description: Optional[str] = Field(None, description="API description")
    base_url: Optional[str] = Field(None, description="Base URL for API")
    total_endpoints: int = Field(..., description="Total number of endpoints parsed")
    endpoints: List[RawAPIEndpoint] = Field(..., description="Parsed API endpoints")
    parsing_errors: List[str] = Field(default_factory=list, description="Errors encountered during parsing")
    parsed_at: datetime = Field(default_factory=datetime.utcnow, description="When parsing was completed")
    classification_status: ClassificationStatus = Field(
        default=ClassificationStatus.PENDING, 
        description="Current processing status"
    )
    classification_started_at: Optional[datetime] = Field(None, description="When classification started")
    classification_completed_at: Optional[datetime] = Field(None, description="When classification completed")
    
    class Config:
        extra = "forbid"
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
    
    @validator('total_endpoints')
    def validate_endpoint_count(cls, v, values):
        """Ensure total_endpoints matches actual endpoint count"""
        if 'endpoints' in values:
            actual_count = len(values['endpoints'])
            if v != actual_count:
                raise ValueError(f'total_endpoints ({v}) does not match actual count ({actual_count})')
        return v
    
    def update_status(self, status: ClassificationStatus):
        """Update classification status with timestamp"""
        self.classification_status = status
        
        if status == ClassificationStatus.PROCESSING:
            self.classification_started_at = datetime.utcnow()
        elif status in [ClassificationStatus.COMPLETED, ClassificationStatus.FAILED]:
            self.classification_completed_at = datetime.utcnow()
    
    def get_endpoints_by_method(self, method: HTTPMethod) -> List[RawAPIEndpoint]:
        """Get all endpoints using specific HTTP method"""
        return [ep for ep in self.endpoints if ep.method == method]
    
    def get_endpoints_by_tag(self, tag: str) -> List[RawAPIEndpoint]:
        """Get all endpoints with specific tag"""
        return [ep for ep in self.endpoints if tag in ep.tags]
    
    def get_crud_endpoints(self) -> Dict[str, List[RawAPIEndpoint]]:
        """Group endpoints by CRUD operation type"""
        crud_groups = {}
        for endpoint in self.endpoints:
            crud_type = endpoint.is_crud_operation()
            if crud_type:
                if crud_type not in crud_groups:
                    crud_groups[crud_type] = []
                crud_groups[crud_type].append(endpoint)
        return crud_groups
    
    def get_unique_tags(self) -> List[str]:
        """Get all unique tags across endpoints"""
        tags = set()
        for endpoint in self.endpoints:
            tags.update(endpoint.tags)
        return sorted(list(tags))
    
    def get_path_patterns(self) -> Dict[str, List[RawAPIEndpoint]]:
        """Group endpoints by path patterns"""
        patterns = {}
        for endpoint in self.endpoints:
            # Extract base path (remove parameters)
            base_path = endpoint.path.split('{')[0].rstrip('/')
            if not base_path:
                base_path = '/'
                
            if base_path not in patterns:
                patterns[base_path] = []
            patterns[base_path].append(endpoint)
        
        return patterns
    
    def get_specification_stats(self) -> Dict[str, Any]:
        """Get comprehensive statistics about the API specification"""
        crud_endpoints = self.get_crud_endpoints()
        methods = {}
        
        for endpoint in self.endpoints:
            method = endpoint.method.value
            methods[method] = methods.get(method, 0) + 1
        
        return {
            "total_endpoints": self.total_endpoints,
            "methods": methods,
            "crud_operations": {k: len(v) for k, v in crud_endpoints.items()},
            "unique_tags": len(self.get_unique_tags()),
            "path_patterns": len(self.get_path_patterns()),
            "has_request_bodies": len([ep for ep in self.endpoints if ep.has_request_body()]),
            "deprecated_endpoints": len([ep for ep in self.endpoints if ep.deprecated]),
            "parsing_errors": len(self.parsing_errors),
            "format": self.file_format.value,
            "classification_status": self.classification_status.value
        }