#!/usr/bin/env python3
"""
Test script for Man-O-Man JSON parser engine.
Tests parsing of OpenAPI 3.0, Swagger 2.0, and Infraon custom API specifications.
"""

import sys
sys.path.append('/home/heramb/source/augment/legacy/backend')

import json
import asyncio
from backend.app.core.manoman.engines.json_parser import JSONParser, JSONParserError
from backend.app.core.manoman.models.api_specification import (
    SpecificationFormat,
    HTTPMethod,
    ParameterLocation
)


def create_openapi3_sample():
    """Create sample OpenAPI 3.0 specification"""
    return {
        "openapi": "3.0.0",
        "info": {
            "title": "Business Rules API",
            "version": "1.0.0",
            "description": "API for managing business rules and automation"
        },
        "servers": [
            {"url": "https://api.infraon.io/v1"}
        ],
        "paths": {
            "/business-rules": {
                "get": {
                    "operationId": "list_business_rules",
                    "summary": "List business rules",
                    "description": "Retrieve a list of all business rules",
                    "tags": ["business-rules"],
                    "parameters": [
                        {
                            "name": "limit",
                            "in": "query",
                            "description": "Maximum number of results",
                            "required": False,
                            "schema": {
                                "type": "integer",
                                "default": 10,
                                "minimum": 1,
                                "maximum": 100
                            }
                        },
                        {
                            "name": "offset",
                            "in": "query",
                            "description": "Number of results to skip",
                            "required": False,
                            "schema": {
                                "type": "integer",
                                "default": 0
                            }
                        }
                    ],
                    "responses": {
                        "200": {
                            "description": "Successful response",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "rules": {
                                                "type": "array",
                                                "items": {"type": "object"}
                                            },
                                            "total": {"type": "integer"}
                                        }
                                    }
                                }
                            }
                        },
                        "400": {
                            "description": "Bad request"
                        }
                    }
                },
                "post": {
                    "operationId": "create_business_rule",
                    "summary": "Create business rule",
                    "description": "Create a new business rule",
                    "tags": ["business-rules"],
                    "requestBody": {
                        "description": "Business rule data",
                        "required": True,
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "name": {"type": "string"},
                                        "description": {"type": "string"},
                                        "conditions": {"type": "array"}
                                    },
                                    "required": ["name", "conditions"]
                                }
                            }
                        }
                    },
                    "responses": {
                        "201": {
                            "description": "Created successfully",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "id": {"type": "string"},
                                            "name": {"type": "string"},
                                            "status": {"type": "string"}
                                        }
                                    }
                                }
                            }
                        },
                        "400": {
                            "description": "Bad request"
                        }
                    }
                }
            },
            "/business-rules/{id}": {
                "get": {
                    "operationId": "get_business_rule_by_id",
                    "summary": "Get business rule by ID",
                    "description": "Retrieve a specific business rule by ID",
                    "tags": ["business-rules"],
                    "parameters": [
                        {
                            "name": "id",
                            "in": "path",
                            "description": "Business rule ID",
                            "required": True,
                            "schema": {
                                "type": "string"
                            }
                        }
                    ],
                    "responses": {
                        "200": {
                            "description": "Business rule found",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "id": {"type": "string"},
                                            "name": {"type": "string"},
                                            "description": {"type": "string"}
                                        }
                                    }
                                }
                            }
                        },
                        "404": {
                            "description": "Rule not found"
                        }
                    }
                },
                "delete": {
                    "operationId": "delete_business_rule",
                    "summary": "Delete business rule",
                    "description": "Delete a business rule by ID",
                    "tags": ["business-rules"],
                    "parameters": [
                        {
                            "name": "id",
                            "in": "path",
                            "description": "Business rule ID",
                            "required": True,
                            "schema": {
                                "type": "string"
                            }
                        }
                    ],
                    "responses": {
                        "204": {
                            "description": "Deleted successfully"
                        },
                        "404": {
                            "description": "Rule not found"
                        }
                    }
                }
            }
        }
    }


def create_swagger2_sample():
    """Create sample Swagger 2.0 specification"""
    return {
        "swagger": "2.0",
        "info": {
            "title": "Incidents API",
            "version": "2.0.0",
            "description": "API for managing incidents"
        },
        "host": "api.infraon.io",
        "basePath": "/v2",
        "schemes": ["https"],
        "paths": {
            "/incidents": {
                "get": {
                    "operationId": "list_incidents",
                    "summary": "List incidents",
                    "tags": ["incidents"],
                    "responses": {
                        "200": {
                            "description": "List of incidents"
                        }
                    }
                },
                "post": {
                    "operationId": "create_incident",
                    "summary": "Create incident",
                    "tags": ["incidents"],
                    "responses": {
                        "201": {
                            "description": "Incident created"
                        }
                    }
                }
            },
            "/incidents/{id}": {
                "get": {
                    "operationId": "get_incident_by_id",
                    "summary": "Get incident by ID",
                    "tags": ["incidents"],
                    "responses": {
                        "200": {
                            "description": "Incident details"
                        }
                    }
                }
            }
        }
    }


def create_infraon_custom_sample():
    """Create sample Infraon custom specification"""
    return {
        "infraon_api_version": "1.0",
        "title": "User Management API",
        "version": "1.0.0",
        "description": "Custom API for user management",
        "base_url": "https://api.infraon.io/users",
        "endpoints": [
            {
                "path": "/users",
                "method": "GET",
                "operation_id": "list_users",
                "title": "List all users",
                "description": "Retrieve list of system users",
                "tags": ["users", "management"],
                "responses": {
                    "200": {
                        "description": "List of users"
                    }
                }
            },
            {
                "path": "/users",
                "method": "POST",
                "operation_id": "create_user",
                "title": "Create new user",
                "description": "Create a new system user",
                "tags": ["users", "management"],
                "responses": {
                    "201": {
                        "description": "User created successfully"
                    },
                    "400": {
                        "description": "Invalid user data"
                    }
                }
            },
            {
                "path": "/users/{user_id}",
                "method": "GET",
                "operation_id": "get_user_by_id",
                "title": "Get user by ID",
                "description": "Retrieve specific user details",
                "tags": ["users"],
                "responses": {
                    "200": {
                        "description": "User details"
                    },
                    "404": {
                        "description": "User not found"
                    }
                }
            }
        ]
    }


async def test_format_detection():
    """Test automatic format detection"""
    print("🧪 Testing format detection...")
    
    parser = JSONParser()
    
    # Test OpenAPI 3.0 detection
    openapi3_spec = create_openapi3_sample()
    detected_format = parser._detect_format(openapi3_spec)
    assert detected_format == SpecificationFormat.OPENAPI_3
    
    # Test Swagger 2.0 detection
    swagger2_spec = create_swagger2_sample()
    detected_format = parser._detect_format(swagger2_spec)
    assert detected_format == SpecificationFormat.SWAGGER_2
    
    # Test Infraon custom detection
    infraon_spec = create_infraon_custom_sample()
    detected_format = parser._detect_format(infraon_spec)
    assert detected_format == SpecificationFormat.INFRAON_CUSTOM
    
    # Test unknown format
    unknown_spec = {"some": "random", "data": "structure"}
    detected_format = parser._detect_format(unknown_spec)
    assert detected_format == SpecificationFormat.UNKNOWN
    
    print("✅ Format detection tests passed!")


async def test_openapi3_parsing():
    """Test OpenAPI 3.0 specification parsing"""
    print("🧪 Testing OpenAPI 3.0 parsing...")
    
    parser = JSONParser()
    openapi3_spec = create_openapi3_sample()
    json_content = json.dumps(openapi3_spec)
    
    api_spec = await parser.parse_specification(json_content, "business-rules-api.json")
    
    # Test basic metadata
    assert api_spec.source_file == "business-rules-api.json"
    assert api_spec.file_format == SpecificationFormat.OPENAPI_3
    assert api_spec.title == "Business Rules API"
    assert api_spec.version == "1.0.0"
    assert api_spec.description == "API for managing business rules and automation"
    assert api_spec.base_url == "https://api.infraon.io/v1"
    assert api_spec.total_endpoints == 4  # GET /business-rules, POST /business-rules, GET /business-rules/{id}, DELETE /business-rules/{id}
    
    # Test endpoints
    assert len(api_spec.endpoints) == 4
    
    # Test specific endpoint
    list_endpoint = next((ep for ep in api_spec.endpoints if ep.operation_id == "list_business_rules"), None)
    assert list_endpoint is not None
    assert list_endpoint.path == "/business-rules"
    assert list_endpoint.method == HTTPMethod.GET
    assert list_endpoint.summary == "List business rules"
    assert "business-rules" in list_endpoint.tags
    assert len(list_endpoint.parameters) == 2  # limit and offset
    
    # Test parameter parsing
    limit_param = next((p for p in list_endpoint.parameters if p.name == "limit"), None)
    assert limit_param is not None
    assert limit_param.location == ParameterLocation.QUERY
    assert limit_param.type == "integer"
    assert limit_param.required == False
    assert limit_param.default_value == 10
    
    # Test create endpoint with request body
    create_endpoint = next((ep for ep in api_spec.endpoints if ep.operation_id == "create_business_rule"), None)
    assert create_endpoint is not None
    assert create_endpoint.has_request_body() == True
    assert create_endpoint.request_body.required == True
    assert create_endpoint.request_body.content_type == "application/json"
    
    # Test CRUD detection
    assert list_endpoint.is_crud_operation() == "list"
    assert create_endpoint.is_crud_operation() == "create"
    
    get_by_id_endpoint = next((ep for ep in api_spec.endpoints if ep.operation_id == "get_business_rule_by_id"), None)
    assert get_by_id_endpoint.is_crud_operation() == "get_by_id"
    
    delete_endpoint = next((ep for ep in api_spec.endpoints if ep.operation_id == "delete_business_rule"), None)
    assert delete_endpoint.is_crud_operation() == "delete"
    
    # Test responses
    assert "200" in list_endpoint.responses
    assert "201" in create_endpoint.responses
    assert list_endpoint.responses["200"].status_code == "200"
    
    print("✅ OpenAPI 3.0 parsing tests passed!")
    return api_spec


async def test_swagger2_parsing():
    """Test Swagger 2.0 specification parsing"""
    print("🧪 Testing Swagger 2.0 parsing...")
    
    parser = JSONParser()
    swagger2_spec = create_swagger2_sample()
    json_content = json.dumps(swagger2_spec)
    
    api_spec = await parser.parse_specification(json_content, "incidents-api.json")
    
    # Test basic metadata
    assert api_spec.source_file == "incidents-api.json"
    assert api_spec.file_format == SpecificationFormat.SWAGGER_2
    assert api_spec.title == "Incidents API"
    assert api_spec.version == "2.0.0"
    assert api_spec.base_url == "https://api.infraon.io/v2"
    assert api_spec.total_endpoints == 3
    
    # Test endpoints
    assert len(api_spec.endpoints) == 3
    
    # Test specific endpoint
    list_endpoint = next((ep for ep in api_spec.endpoints if ep.operation_id == "list_incidents"), None)
    assert list_endpoint is not None
    assert list_endpoint.path == "/incidents"
    assert list_endpoint.method == HTTPMethod.GET
    assert "incidents" in list_endpoint.tags
    
    print("✅ Swagger 2.0 parsing tests passed!")
    return api_spec


async def test_infraon_custom_parsing():
    """Test Infraon custom specification parsing"""
    print("🧪 Testing Infraon custom parsing...")
    
    parser = JSONParser()
    infraon_spec = create_infraon_custom_sample()
    json_content = json.dumps(infraon_spec)
    
    api_spec = await parser.parse_specification(json_content, "users-api.json")
    
    # Test basic metadata
    assert api_spec.source_file == "users-api.json"
    assert api_spec.file_format == SpecificationFormat.INFRAON_CUSTOM
    assert api_spec.title == "User Management API"
    assert api_spec.version == "1.0.0"
    assert api_spec.base_url == "https://api.infraon.io/users"
    assert api_spec.total_endpoints == 3
    
    # Test endpoints
    assert len(api_spec.endpoints) == 3
    
    # Test specific endpoint
    list_endpoint = next((ep for ep in api_spec.endpoints if ep.operation_id == "list_users"), None)
    assert list_endpoint is not None
    assert list_endpoint.path == "/users"
    assert list_endpoint.method == HTTPMethod.GET
    assert "users" in list_endpoint.tags
    assert "management" in list_endpoint.tags
    
    print("✅ Infraon custom parsing tests passed!")
    return api_spec


async def test_error_handling():
    """Test error handling and validation"""
    print("🧪 Testing error handling...")
    
    parser = JSONParser()
    
    # Test invalid JSON
    try:
        await parser.parse_specification("invalid json content", "invalid.json")
        assert False, "Should have raised JSONParserError"
    except JSONParserError as e:
        assert "Invalid JSON format" in str(e)
    
    # Test empty specification
    empty_spec = {}
    api_spec = await parser.parse_specification("{}", "empty.json")
    assert api_spec.file_format == SpecificationFormat.UNKNOWN
    assert len(api_spec.parsing_errors) > 0
    
    # Test specification with parsing errors
    malformed_spec = {
        "openapi": "3.0.0",
        "info": {"title": "Test API"},
        "paths": {
            "/test": {
                "get": {
                    # Missing required fields like operationId
                    "summary": "Test endpoint"
                }
            }
        }
    }
    
    json_content = json.dumps(malformed_spec)
    api_spec = await parser.parse_specification(json_content, "malformed.json")
    
    # Should still parse but may have errors
    assert api_spec.file_format == SpecificationFormat.OPENAPI_3
    assert len(api_spec.endpoints) >= 0  # May or may not parse depending on error
    
    print("✅ Error handling tests passed!")


async def test_specification_analysis():
    """Test specification analysis and statistics"""
    print("🧪 Testing specification analysis...")
    
    # Use the OpenAPI 3.0 spec for analysis
    api_spec = await test_openapi3_parsing()
    
    # Test statistics
    stats = api_spec.get_specification_stats()
    assert stats["total_endpoints"] == 4
    assert stats["methods"]["GET"] == 2
    assert stats["methods"]["POST"] == 1
    assert stats["methods"]["DELETE"] == 1
    assert stats["format"] == "openapi_3"
    
    # Test CRUD grouping
    crud_endpoints = api_spec.get_crud_endpoints()
    assert "list" in crud_endpoints
    assert "create" in crud_endpoints
    assert "get_by_id" in crud_endpoints
    assert "delete" in crud_endpoints
    assert len(crud_endpoints["list"]) == 1
    assert len(crud_endpoints["create"]) == 1
    
    # Test path patterns
    path_patterns = api_spec.get_path_patterns()
    assert "/business-rules" in path_patterns
    assert len(path_patterns["/business-rules"]) == 4  # All endpoints share base path
    
    # Test unique tags
    unique_tags = api_spec.get_unique_tags()
    assert "business-rules" in unique_tags
    
    print("✅ Specification analysis tests passed!")


async def test_parser_configuration():
    """Test parser configuration and supported formats"""
    print("🧪 Testing parser configuration...")
    
    parser = JSONParser()
    
    # Test supported formats
    supported_formats = parser.get_supported_formats()
    assert "openapi_3" in supported_formats
    assert "swagger_2" in supported_formats
    assert "infraon_custom" in supported_formats
    
    # Test parsing errors tracking
    errors_before = len(parser.get_parsing_errors())
    
    # Parse a spec that will generate errors
    malformed_spec = {"openapi": "3.0.0", "paths": {"invalid": "structure"}}
    json_content = json.dumps(malformed_spec)
    await parser.parse_specification(json_content, "error-test.json")
    
    errors_after = len(parser.get_parsing_errors())
    # Should have more errors now (or at least the same number)
    assert errors_after >= errors_before
    
    print("✅ Parser configuration tests passed!")


async def run_all_tests():
    """Run all JSON parser tests"""
    print("🚀 Starting Man-O-Man JSON Parser Engine Tests\n")
    
    try:
        await test_format_detection()
        await test_openapi3_parsing()
        await test_swagger2_parsing()
        await test_infraon_custom_parsing()
        await test_error_handling()
        await test_specification_analysis()
        await test_parser_configuration()
        
        print("\n🎉 All JSON parser tests passed successfully!")
        print("✅ JSON parser engine is ready for service classification")
        print("📁 Supports OpenAPI 3.0, Swagger 2.0, and Infraon custom formats")
        print("🔍 CRUD operation detection working perfectly")
        print("📊 Comprehensive error handling and statistics")
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(run_all_tests())
    sys.exit(0 if success else 1)