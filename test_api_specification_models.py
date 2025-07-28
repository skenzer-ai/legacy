#!/usr/bin/env python3
"""
Test script for Man-O-Man API specification data models.
Tests model validation, CRUD detection, and specification parsing.
"""

import sys
sys.path.append('/home/heramb/source/augment/legacy/backend')

from datetime import datetime
from backend.app.core.manoman.models.api_specification import (
    SpecificationFormat,
    ClassificationStatus,
    HTTPMethod,
    ParameterLocation,
    APIParameter,
    APIResponse,
    APIRequestBody,
    RawAPIEndpoint,
    APISpecification
)


def test_enums():
    """Test enum types"""
    print("🧪 Testing enum types...")
    
    # Test SpecificationFormat
    assert SpecificationFormat.OPENAPI_3 == "openapi_3"
    assert SpecificationFormat.SWAGGER_2 == "swagger_2"
    assert SpecificationFormat.INFRAON_CUSTOM == "infraon_custom"
    
    # Test ClassificationStatus
    assert ClassificationStatus.PENDING == "pending"
    assert ClassificationStatus.PROCESSING == "processing"
    assert ClassificationStatus.COMPLETED == "completed"
    assert ClassificationStatus.FAILED == "failed"
    
    # Test HTTPMethod
    assert HTTPMethod.GET == "GET"
    assert HTTPMethod.POST == "POST"
    assert HTTPMethod.PUT == "PUT"
    assert HTTPMethod.DELETE == "DELETE"
    
    # Test ParameterLocation
    assert ParameterLocation.QUERY == "query"
    assert ParameterLocation.PATH == "path"
    assert ParameterLocation.HEADER == "header"
    
    print("✅ Enum types tests passed!")


def test_api_parameter():
    """Test APIParameter model"""
    print("🧪 Testing APIParameter model...")
    
    # Test query parameter
    query_param = APIParameter(
        name="limit",
        location=ParameterLocation.QUERY,
        type="integer",
        required=False,
        description="Maximum number of results",
        default_value=10
    )
    
    assert query_param.name == "limit"
    assert query_param.location == ParameterLocation.QUERY
    assert query_param.type == "integer"
    assert query_param.required == False
    assert query_param.default_value == 10
    
    # Test path parameter
    path_param = APIParameter(
        name="id",
        location=ParameterLocation.PATH,
        type="string",
        required=True,
        description="Resource ID"
    )
    
    assert path_param.name == "id"
    assert path_param.location == ParameterLocation.PATH
    assert path_param.required == True
    
    print("✅ APIParameter model tests passed!")
    return query_param, path_param


def test_api_response():
    """Test APIResponse model"""
    print("🧪 Testing APIResponse model...")
    
    response = APIResponse(
        status_code="200",
        description="Successful response",
        response_schema={"type": "object", "properties": {"id": {"type": "string"}}},
        examples={"application/json": {"id": "123", "name": "Test"}}
    )
    
    assert response.status_code == "200"
    assert response.description == "Successful response"
    assert "id" in response.response_schema["properties"]
    assert "application/json" in response.examples
    
    print("✅ APIResponse model tests passed!")
    return response


def test_api_request_body():
    """Test APIRequestBody model"""
    print("🧪 Testing APIRequestBody model...")
    
    request_body = APIRequestBody(
        description="Business rule creation data",
        required=True,
        content_type="application/json",
        body_schema={
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "conditions": {"type": "array"}
            },
            "required": ["name"]
        }
    )
    
    assert request_body.description == "Business rule creation data"
    assert request_body.required == True
    assert request_body.content_type == "application/json"
    assert "name" in request_body.body_schema["properties"]
    
    print("✅ APIRequestBody model tests passed!")
    return request_body


def test_raw_api_endpoint():
    """Test RawAPIEndpoint model"""
    print("🧪 Testing RawAPIEndpoint model...")
    
    query_param, path_param = test_api_parameter()
    response = test_api_response()
    request_body = test_api_request_body()
    
    # Test CREATE endpoint (POST)
    create_endpoint = RawAPIEndpoint(
        path="/api/v1/business-rules",
        method=HTTPMethod.POST,
        operation_id="create_business_rule",
        summary="Create business rule",
        description="Create a new business rule for automation",
        tags=["business-rules", "automation"],
        parameters=[query_param],
        request_body=request_body,
        responses={"200": response, "400": APIResponse(status_code="400", description="Bad request")}
    )
    
    assert create_endpoint.path == "/api/v1/business-rules"
    assert create_endpoint.method == HTTPMethod.POST
    assert create_endpoint.operation_id == "create_business_rule"
    assert len(create_endpoint.tags) == 2
    assert "business-rules" in create_endpoint.tags
    
    # Test helper methods
    assert create_endpoint.has_request_body() == True
    assert len(create_endpoint.get_query_parameters()) == 1
    assert len(create_endpoint.get_path_parameters()) == 0
    assert len(create_endpoint.get_required_parameters()) == 0  # query param is not required
    
    success_response = create_endpoint.get_success_response()
    assert success_response is not None
    assert success_response.status_code == "200"
    
    # Test CRUD detection
    crud_type = create_endpoint.is_crud_operation()
    assert crud_type == "create"
    
    # Test GET by ID endpoint
    get_endpoint = RawAPIEndpoint(
        path="/api/v1/business-rules/{id}",
        method=HTTPMethod.GET,
        operation_id="get_business_rule_by_id",
        summary="Get business rule by ID",
        tags=["business-rules", "automation"],
        parameters=[path_param],
        responses={"200": response}
    )
    
    assert get_endpoint.is_crud_operation() == "get_by_id"
    assert len(get_endpoint.get_path_parameters()) == 1
    
    # Test LIST endpoint
    list_endpoint = RawAPIEndpoint(
        path="/api/v1/business-rules",
        method=HTTPMethod.GET,
        operation_id="list_business_rules",
        summary="List business rules",
        tags=["business-rules", "automation"],
        responses={"200": response}
    )
    
    assert list_endpoint.is_crud_operation() == "list"
    
    # Test UPDATE endpoint
    update_endpoint = RawAPIEndpoint(
        path="/api/v1/business-rules/{id}",
        method=HTTPMethod.PUT,
        operation_id="update_business_rule",
        summary="Update business rule",
        tags=["business-rules", "automation"],
        parameters=[path_param],
        request_body=request_body,
        responses={"200": response}
    )
    
    assert update_endpoint.is_crud_operation() == "update"
    
    # Test DELETE endpoint
    delete_endpoint = RawAPIEndpoint(
        path="/api/v1/business-rules/{id}",
        method=HTTPMethod.DELETE,
        operation_id="delete_business_rule",
        summary="Delete business rule",
        tags=["business-rules", "automation"],
        parameters=[path_param],
        responses={"204": APIResponse(status_code="204", description="No content")}
    )
    
    assert delete_endpoint.is_crud_operation() == "delete"
    
    print("✅ RawAPIEndpoint model tests passed!")
    return [create_endpoint, get_endpoint, list_endpoint, update_endpoint, delete_endpoint]


def test_api_specification():
    """Test APISpecification model"""
    print("🧪 Testing APISpecification model...")
    
    endpoints = test_raw_api_endpoint()
    
    api_spec = APISpecification(
        source_file="infraon-api.json",
        file_format=SpecificationFormat.OPENAPI_3,
        title="Infraon ITSM Platform API",
        version="2.0.0",
        description="Complete API specification for Infraon ITSM platform",
        base_url="https://api.infraon.io/v1",
        total_endpoints=5,
        endpoints=endpoints
    )
    
    assert api_spec.source_file == "infraon-api.json"
    assert api_spec.file_format == SpecificationFormat.OPENAPI_3
    assert api_spec.title == "Infraon ITSM Platform API"
    assert api_spec.total_endpoints == 5
    assert len(api_spec.endpoints) == 5
    
    # Test status update
    api_spec.update_status(ClassificationStatus.PROCESSING)
    assert api_spec.classification_status == ClassificationStatus.PROCESSING
    assert api_spec.classification_started_at is not None
    
    api_spec.update_status(ClassificationStatus.COMPLETED)
    assert api_spec.classification_status == ClassificationStatus.COMPLETED
    assert api_spec.classification_completed_at is not None
    
    # Test helper methods
    get_endpoints = api_spec.get_endpoints_by_method(HTTPMethod.GET)
    assert len(get_endpoints) == 2  # list + get_by_id
    
    post_endpoints = api_spec.get_endpoints_by_method(HTTPMethod.POST)
    assert len(post_endpoints) == 1  # create
    
    tagged_endpoints = api_spec.get_endpoints_by_tag("business-rules")
    assert len(tagged_endpoints) == 5  # All endpoints have this tag
    
    # Test CRUD grouping
    crud_endpoints = api_spec.get_crud_endpoints()
    assert "create" in crud_endpoints
    assert "list" in crud_endpoints
    assert "get_by_id" in crud_endpoints
    assert "update" in crud_endpoints
    assert "delete" in crud_endpoints
    assert len(crud_endpoints["create"]) == 1
    assert len(crud_endpoints["list"]) == 1
    
    # Test unique tags
    unique_tags = api_spec.get_unique_tags()
    assert "business-rules" in unique_tags
    assert "automation" in unique_tags
    
    # Test path patterns
    path_patterns = api_spec.get_path_patterns()
    assert "/api/v1/business-rules" in path_patterns
    assert len(path_patterns["/api/v1/business-rules"]) == 5  # All endpoints have same base path
    
    # Test statistics
    stats = api_spec.get_specification_stats()
    assert stats["total_endpoints"] == 5
    assert stats["methods"]["GET"] == 2
    assert stats["methods"]["POST"] == 1
    assert stats["methods"]["PUT"] == 1
    assert stats["methods"]["DELETE"] == 1
    assert stats["crud_operations"]["create"] == 1
    assert stats["crud_operations"]["list"] == 1
    assert stats["has_request_bodies"] == 2  # POST and PUT
    assert stats["format"] == "openapi_3"
    assert stats["classification_status"] == "completed"
    
    print("✅ APISpecification model tests passed!")
    return api_spec


def test_model_validation():
    """Test model validation"""
    print("🧪 Testing model validation...")
    
    # Test path validation (should add leading slash)
    endpoint = RawAPIEndpoint(
        path="api/v1/test",  # No leading slash
        method=HTTPMethod.GET,
        operation_id="test_endpoint"
    )
    assert endpoint.path == "/api/v1/test"  # Should be corrected
    
    # Test operation_id validation works (valid IDs should pass)
    valid_endpoint = RawAPIEndpoint(
        path="/api/v1/test",
        method=HTTPMethod.GET,
        operation_id="valid_operation_id"
    )
    assert valid_endpoint.operation_id == "valid_operation_id"
    
    # Test endpoint count validation (count should match)
    valid_spec = APISpecification(
        source_file="test.json",
        file_format=SpecificationFormat.OPENAPI_3,
        total_endpoints=1,  # Matches actual count
        endpoints=[endpoint]  # 1 endpoint
    )
    assert valid_spec.total_endpoints == 1
    assert len(valid_spec.endpoints) == 1
    
    print("✅ Model validation tests passed!")


def test_model_serialization():
    """Test JSON serialization/deserialization"""
    print("🧪 Testing model serialization...")
    
    api_spec = test_api_specification()
    
    # Test serialization
    json_data = api_spec.model_dump()
    assert "source_file" in json_data
    assert "endpoints" in json_data
    assert "total_endpoints" in json_data
    assert json_data["total_endpoints"] == 5
    
    # Test deserialization
    new_spec = APISpecification(**json_data)
    assert new_spec.source_file == api_spec.source_file
    assert new_spec.total_endpoints == api_spec.total_endpoints
    assert len(new_spec.endpoints) == len(api_spec.endpoints)
    assert new_spec.classification_status == api_spec.classification_status
    
    print("✅ Model serialization tests passed!")


def run_all_tests():
    """Run all tests"""
    print("🚀 Starting Man-O-Man API Specification Model Tests\n")
    
    try:
        test_enums()
        test_api_parameter()
        test_api_response()
        test_api_request_body()
        test_raw_api_endpoint()
        test_api_specification()
        test_model_validation()
        test_model_serialization()
        
        print("\n🎉 All API specification model tests passed successfully!")
        print("✅ Models are ready for JSON parser integration")
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)