"""
JSON/YAML Parser Engine

Parses various API specification formats (OpenAPI 3.0, Swagger 2.0, Infraon custom)
from JSON or YAML files with $ref resolution and converts them into standardized 
RawAPIEndpoint objects for further processing.
"""

import json
import yaml
import logging
import jsonref
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
from pathlib import Path

from ..models.api_specification import (
    SpecificationFormat,
    HTTPMethod,
    ParameterLocation,
    APIParameter,
    APIResponse,
    APIRequestBody,
    RawAPIEndpoint,
    APISpecification
)

logger = logging.getLogger(__name__)


class JSONParserError(Exception):
    """Custom exception for JSON parsing errors"""
    pass


class JSONParser:
    """
    Parses various API specification formats (JSON/YAML) and converts them into
    standardized RawAPIEndpoint objects for service classification.
    Supports $ref resolution and complex OpenAPI structures.
    """
    
    def __init__(self):
        self.supported_formats = [
            SpecificationFormat.OPENAPI_3,
            SpecificationFormat.SWAGGER_2,
            SpecificationFormat.INFRAON_CUSTOM
        ]
        self.parsing_errors = []
        self.resolved_spec = None  # Store resolved spec with $refs
    
    async def parse_specification(self, file_content: str, filename: str, format_hint: Optional[str] = None) -> APISpecification:
        """
        Parse API specification from JSON or YAML string with $ref resolution
        
        Args:
            file_content: Raw JSON/YAML string from uploaded file
            filename: Original filename for reference
            format_hint: Optional format hint to skip auto-detection
            
        Returns:
            APISpecification object with parsed endpoints
            
        Raises:
            JSONParserError: If parsing fails
        """
        self.parsing_errors = []
        
        try:
            # Try to parse as YAML first (handles both YAML and JSON)
            try:
                spec_data = yaml.safe_load(file_content)
            except yaml.YAMLError:
                # Fallback to JSON parsing
                spec_data = json.loads(file_content)
        except (json.JSONDecodeError, yaml.YAMLError) as e:
            raise JSONParserError(f"Invalid JSON/YAML format: {str(e)}")
        
        if not isinstance(spec_data, dict):
            raise JSONParserError("Specification must be a JSON/YAML object")
        
        # Resolve $ref references
        try:
            self.resolved_spec = jsonref.JsonRef.replace_refs(spec_data)
        except Exception as e:
            self.parsing_errors.append(f"$ref resolution failed: {str(e)}")
            self.resolved_spec = spec_data  # Use unresolved spec as fallback
        
        # Detect format if not provided
        if format_hint:
            detected_format = SpecificationFormat(format_hint)
        else:
            detected_format = self._detect_format(self.resolved_spec)
        
        # Extract basic metadata (use resolved spec for $ref resolution)
        title = self._extract_title(self.resolved_spec, detected_format)
        version = self._extract_version(self.resolved_spec, detected_format)
        description = self._extract_description(self.resolved_spec, detected_format)
        base_url = self._extract_base_url(self.resolved_spec, detected_format)
        
        # Parse endpoints based on format (use resolved spec)
        endpoints = []
        try:
            if detected_format == SpecificationFormat.OPENAPI_3:
                endpoints = self._extract_endpoints_openapi3(self.resolved_spec)
            elif detected_format == SpecificationFormat.SWAGGER_2:
                endpoints = self._extract_endpoints_swagger2(self.resolved_spec)
            elif detected_format == SpecificationFormat.INFRAON_CUSTOM:
                endpoints = self._extract_endpoints_infraon(self.resolved_spec)
            else:
                raise JSONParserError(f"Unsupported format: {detected_format}")
        except Exception as e:
            self.parsing_errors.append(f"Endpoint parsing failed: {str(e)}")
            logger.error(f"Endpoint parsing failed for {filename}: {str(e)}")
        
        # Create API specification
        api_spec = APISpecification(
            source_file=filename,
            file_format=detected_format,
            title=title or "Unknown API",  # Provide default for empty titles
            version=version or "1.0.0",    # Provide default for empty versions
            description=description,
            base_url=base_url,
            total_endpoints=len(endpoints),
            endpoints=endpoints,
            parsing_errors=self.parsing_errors.copy()
        )
        
        logger.info(f"Successfully parsed {filename}: {len(endpoints)} endpoints, format: {detected_format.value}")
        return api_spec
    
    def _detect_format(self, spec_data: Dict[str, Any]) -> SpecificationFormat:
        """Auto-detect API specification format"""
        try:
            # Check for OpenAPI 3.0
            if "openapi" in spec_data:
                openapi_version = spec_data["openapi"]
                if isinstance(openapi_version, str) and openapi_version.startswith("3."):
                    return SpecificationFormat.OPENAPI_3
            
            # Check for Swagger 2.0
            if "swagger" in spec_data:
                swagger_version = spec_data["swagger"]
                if isinstance(swagger_version, str) and swagger_version.startswith("2."):
                    return SpecificationFormat.SWAGGER_2
            
            # Check for Infraon custom format
            if "infraon_api_version" in spec_data or "infraon" in spec_data:
                return SpecificationFormat.INFRAON_CUSTOM
            
            # Check for custom structure patterns
            if "endpoints" in spec_data and "services" in spec_data:
                return SpecificationFormat.INFRAON_CUSTOM
            
            # Default to unknown if no clear indicators
            self.parsing_errors.append("Could not detect API specification format")
            return SpecificationFormat.UNKNOWN
            
        except Exception as e:
            self.parsing_errors.append(f"Format detection failed: {str(e)}")
            return SpecificationFormat.UNKNOWN
    
    def _extract_title(self, spec_data: Dict[str, Any], format_type: SpecificationFormat) -> Optional[str]:
        """Extract API title based on format"""
        try:
            if format_type in [SpecificationFormat.OPENAPI_3, SpecificationFormat.SWAGGER_2]:
                return spec_data.get("info", {}).get("title")
            elif format_type == SpecificationFormat.INFRAON_CUSTOM:
                return spec_data.get("title") or spec_data.get("name")
        except Exception:
            pass
        return None
    
    def _extract_version(self, spec_data: Dict[str, Any], format_type: SpecificationFormat) -> Optional[str]:
        """Extract API version based on format"""
        try:
            if format_type in [SpecificationFormat.OPENAPI_3, SpecificationFormat.SWAGGER_2]:
                return spec_data.get("info", {}).get("version")
            elif format_type == SpecificationFormat.INFRAON_CUSTOM:
                return spec_data.get("version") or spec_data.get("api_version")
        except Exception:
            pass
        return None
    
    def _extract_description(self, spec_data: Dict[str, Any], format_type: SpecificationFormat) -> Optional[str]:
        """Extract API description based on format"""
        try:
            if format_type in [SpecificationFormat.OPENAPI_3, SpecificationFormat.SWAGGER_2]:
                return spec_data.get("info", {}).get("description")
            elif format_type == SpecificationFormat.INFRAON_CUSTOM:
                return spec_data.get("description")
        except Exception:
            pass
        return None
    
    def _extract_base_url(self, spec_data: Dict[str, Any], format_type: SpecificationFormat) -> Optional[str]:
        """Extract base URL based on format"""
        try:
            if format_type == SpecificationFormat.OPENAPI_3:
                servers = spec_data.get("servers", [])
                if servers and isinstance(servers, list):
                    return servers[0].get("url")
            elif format_type == SpecificationFormat.SWAGGER_2:
                host = spec_data.get("host")
                schemes = spec_data.get("schemes", ["https"])
                base_path = spec_data.get("basePath", "")
                if host:
                    scheme = schemes[0] if schemes else "https"
                    return f"{scheme}://{host}{base_path}"
            elif format_type == SpecificationFormat.INFRAON_CUSTOM:
                return spec_data.get("base_url") or spec_data.get("host")
        except Exception:
            pass
        return None
    
    def _extract_endpoints_openapi3(self, spec_data: Dict[str, Any]) -> List[RawAPIEndpoint]:
        """Extract endpoints from OpenAPI 3.0 specification"""
        endpoints = []
        paths = spec_data.get("paths", {})
        
        for path, path_item in paths.items():
            if not isinstance(path_item, dict):
                continue
                
            for method, operation in path_item.items():
                if method.upper() not in [m.value for m in HTTPMethod]:
                    continue
                
                try:
                    endpoint = self._parse_openapi3_operation(path, method.upper(), operation)
                    endpoints.append(endpoint)
                except Exception as e:
                    error_msg = f"Failed to parse {method.upper()} {path}: {str(e)}"
                    self.parsing_errors.append(error_msg)
                    logger.warning(error_msg)
                    continue
        
        return endpoints
    
    def _parse_openapi3_operation(self, path: str, method: str, operation: Dict[str, Any]) -> RawAPIEndpoint:
        """Parse individual OpenAPI 3.0 operation"""
        # Extract basic info
        operation_id = operation.get("operationId", f"{method.lower()}_{path.replace('/', '_').replace('{', '').replace('}', '')}")
        summary = operation.get("summary")
        description = operation.get("description")
        tags = operation.get("tags", [])
        deprecated = operation.get("deprecated", False)
        
        # Parse parameters
        parameters = []
        param_list = operation.get("parameters", [])
        for param in param_list:
            try:
                api_param = self._parse_openapi3_parameter(param)
                parameters.append(api_param)
            except Exception as e:
                self.parsing_errors.append(f"Failed to parse parameter in {operation_id}: {str(e)}")
        
        # Parse request body
        request_body = None
        if "requestBody" in operation:
            try:
                request_body = self._parse_openapi3_request_body(operation["requestBody"])
            except Exception as e:
                self.parsing_errors.append(f"Failed to parse request body in {operation_id}: {str(e)}")
        
        # Parse responses
        responses = {}
        response_specs = operation.get("responses", {})
        for status_code, response_spec in response_specs.items():
            try:
                api_response = self._parse_openapi3_response(status_code, response_spec)
                responses[status_code] = api_response
            except Exception as e:
                self.parsing_errors.append(f"Failed to parse response {status_code} in {operation_id}: {str(e)}")
        
        return RawAPIEndpoint(
            path=path,
            method=HTTPMethod(method),
            operation_id=operation_id,
            summary=summary,
            description=description,
            tags=tags,
            parameters=parameters,
            request_body=request_body,
            responses=responses,
            deprecated=deprecated
        )
    
    def _parse_openapi3_parameter(self, param: Dict[str, Any]) -> APIParameter:
        """Parse OpenAPI 3.0 parameter with enhanced schema handling"""
        name = param.get("name", "")
        location = param.get("in", "query")
        required = param.get("required", False)
        description = param.get("description")
        
        # Map OpenAPI location to our enum
        location_map = {
            "query": ParameterLocation.QUERY,
            "path": ParameterLocation.PATH,
            "header": ParameterLocation.HEADER,
            "cookie": ParameterLocation.HEADER  # Treat cookies as headers
        }
        param_location = location_map.get(location, ParameterLocation.QUERY)
        
        # Extract schema info (handle both direct and nested schemas)
        schema = param.get("schema", {})
        if not schema and "type" in param:
            # Handle legacy Swagger 2.0 style in OpenAPI 3.0
            schema = {
                "type": param.get("type", "string"),
                "format": param.get("format"),
                "enum": param.get("enum"),
                "default": param.get("default")
            }
        
        param_type = schema.get("type", "string")
        default_value = schema.get("default")
        enum_values = schema.get("enum")
        format_info = schema.get("format")
        
        # Handle array types
        if param_type == "array" and "items" in schema:
            items_type = schema["items"].get("type", "string")
            param_type = f"array[{items_type}]"
        
        return APIParameter(
            name=name,
            location=param_location,
            type=param_type,
            required=required,
            description=description,
            default_value=default_value,
            enum_values=enum_values,
            format=format_info
        )
    
    def _parse_openapi3_request_body(self, request_body: Dict[str, Any]) -> APIRequestBody:
        """Parse OpenAPI 3.0 request body"""
        description = request_body.get("description")
        required = request_body.get("required", False)
        
        # Extract content type and schema
        content = request_body.get("content", {})
        content_type = "application/json"  # Default
        schema = {}
        examples = {}
        
        if content:
            # Get first content type (usually application/json)
            first_content_type = list(content.keys())[0]
            content_type = first_content_type
            content_info = content[first_content_type]
            schema = content_info.get("schema", {})
            examples = content_info.get("examples", {})
        
        return APIRequestBody(
            description=description,
            required=required,
            content_type=content_type,
            body_schema=schema,
            examples=examples
        )
    
    def _parse_openapi3_response(self, status_code: str, response: Dict[str, Any]) -> APIResponse:
        """Parse OpenAPI 3.0 response"""
        description = response.get("description", f"Response {status_code}")
        headers = response.get("headers", {})
        
        # Extract content schema and examples
        content = response.get("content", {})
        schema = {}
        examples = {}
        
        if content:
            # Get first content type (usually application/json)
            first_content_type = list(content.keys())[0]
            content_info = content[first_content_type]
            schema = content_info.get("schema", {})
            examples = content_info.get("examples", {})
        
        return APIResponse(
            status_code=status_code,
            description=description,
            response_schema=schema,
            examples=examples,
            headers=headers
        )
    
    def _extract_endpoints_swagger2(self, spec_data: Dict[str, Any]) -> List[RawAPIEndpoint]:
        """Extract endpoints from Swagger 2.0 specification"""
        # Similar to OpenAPI 3.0 but with Swagger 2.0 specific parsing
        # Implementation would be similar but handle Swagger 2.0 differences
        endpoints = []
        paths = spec_data.get("paths", {})
        
        for path, path_item in paths.items():
            if not isinstance(path_item, dict):
                continue
                
            for method, operation in path_item.items():
                if method.upper() not in [m.value for m in HTTPMethod]:
                    continue
                
                try:
                    endpoint = self._parse_swagger2_operation(path, method.upper(), operation)
                    endpoints.append(endpoint)
                except Exception as e:
                    error_msg = f"Failed to parse Swagger 2.0 {method.upper()} {path}: {str(e)}"
                    self.parsing_errors.append(error_msg)
                    logger.warning(error_msg)
                    continue
        
        return endpoints
    
    def _parse_swagger2_operation(self, path: str, method: str, operation: Dict[str, Any]) -> RawAPIEndpoint:
        """Parse individual Swagger 2.0 operation (simplified implementation)"""
        operation_id = operation.get("operationId", f"{method.lower()}_{path.replace('/', '_').replace('{', '').replace('}', '')}")
        summary = operation.get("summary")
        description = operation.get("description")
        tags = operation.get("tags", [])
        deprecated = operation.get("deprecated", False)
        
        # Simplified parameter and response parsing for Swagger 2.0
        parameters = []
        responses = {}
        
        # Basic response parsing
        response_specs = operation.get("responses", {})
        for status_code, response_spec in response_specs.items():
            responses[status_code] = APIResponse(
                status_code=status_code,
                description=response_spec.get("description", f"Response {status_code}")
            )
        
        return RawAPIEndpoint(
            path=path,
            method=HTTPMethod(method),
            operation_id=operation_id,
            summary=summary,
            description=description,
            tags=tags,
            parameters=parameters,
            responses=responses,
            deprecated=deprecated
        )
    
    def _extract_endpoints_infraon(self, spec_data: Dict[str, Any]) -> List[RawAPIEndpoint]:
        """Extract endpoints from Infraon custom format"""
        endpoints = []
        
        # Handle different Infraon custom format structures
        if "endpoints" in spec_data:
            endpoint_list = spec_data["endpoints"]
        elif "paths" in spec_data:
            # Similar to OpenAPI but may have custom extensions
            return self._extract_endpoints_openapi3(spec_data)
        else:
            # Try to find endpoints in various locations
            endpoint_list = []
            for key, value in spec_data.items():
                if isinstance(value, list) and key.endswith("endpoints"):
                    endpoint_list.extend(value)
        
        for endpoint_data in endpoint_list:
            try:
                endpoint = self._parse_infraon_endpoint(endpoint_data)
                endpoints.append(endpoint)
            except Exception as e:
                error_msg = f"Failed to parse Infraon endpoint: {str(e)}"
                self.parsing_errors.append(error_msg)
                logger.warning(error_msg)
                continue
        
        return endpoints
    
    def _parse_infraon_endpoint(self, endpoint_data: Dict[str, Any]) -> RawAPIEndpoint:
        """Parse individual Infraon custom endpoint"""
        path = endpoint_data.get("path", endpoint_data.get("url", ""))
        method = endpoint_data.get("method", "GET").upper()
        operation_id = endpoint_data.get("operation_id", endpoint_data.get("id", f"{method.lower()}_{path.replace('/', '_')}"))
        summary = endpoint_data.get("summary", endpoint_data.get("title"))
        description = endpoint_data.get("description")
        tags = endpoint_data.get("tags", endpoint_data.get("categories", []))
        
        # Basic response parsing
        responses = {}
        if "responses" in endpoint_data:
            for status_code, response_data in endpoint_data["responses"].items():
                responses[status_code] = APIResponse(
                    status_code=status_code,
                    description=response_data.get("description", f"Response {status_code}")
                )
        else:
            # Default success response
            responses["200"] = APIResponse(
                status_code="200",
                description="Success"
            )
        
        return RawAPIEndpoint(
            path=path,
            method=HTTPMethod(method),
            operation_id=operation_id,
            summary=summary,
            description=description,
            tags=tags,
            responses=responses
        )
    
    def get_parsing_errors(self) -> List[str]:
        """Get list of parsing errors encountered"""
        return self.parsing_errors.copy()
    
    def get_supported_formats(self) -> List[str]:
        """Get list of supported specification formats"""
        return [fmt.value for fmt in self.supported_formats]