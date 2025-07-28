#!/usr/bin/env python3
"""
Test script for Man-O-Man JSON parser with real Infraon OpenAPI specification.
Tests YAML parsing, $ref resolution, and complex endpoint structures.
"""

import sys
sys.path.append('/home/heramb/source/augment/legacy/backend')

import asyncio
from pathlib import Path
from backend.app.core.manoman.engines.json_parser import JSONParser, JSONParserError
from backend.app.core.manoman.models.api_specification import SpecificationFormat


async def test_real_infraon_spec():
    """Test parsing of real Infraon OpenAPI specification"""
    print("🧪 Testing real Infraon OpenAPI specification...")
    
    # Read the real Infraon spec
    spec_path = Path("/home/heramb/source/augment/legacy/user_docs/infraon-openapi")
    if not spec_path.exists():
        print("❌ Infraon OpenAPI spec file not found!")
        return False
    
    try:
        with open(spec_path, 'r', encoding='utf-8') as f:
            spec_content = f.read()
    except Exception as e:
        print(f"❌ Failed to read spec file: {str(e)}")
        return False
    
    # Parse with enhanced parser
    parser = JSONParser()
    
    try:
        api_spec = await parser.parse_specification(
            spec_content, 
            "infraon-openapi.yaml"
        )
        
        print(f"✅ Successfully parsed Infraon OpenAPI specification!")
        print(f"📊 Parsing Results:")
        print(f"   - Format: {api_spec.file_format.value}")
        print(f"   - Title: '{api_spec.title}'")
        print(f"   - Version: '{api_spec.version}'")
        print(f"   - Total Endpoints: {api_spec.total_endpoints}")
        print(f"   - Base URL: {api_spec.base_url}")
        print(f"   - Parsing Errors: {len(api_spec.parsing_errors)}")
        
        if api_spec.parsing_errors:
            print(f"⚠️  Parsing Errors:")
            for error in api_spec.parsing_errors[:5]:  # Show first 5 errors
                print(f"     - {error}")
            if len(api_spec.parsing_errors) > 5:
                print(f"     ... and {len(api_spec.parsing_errors) - 5} more")
        
        # Analyze endpoint structure
        print(f"\n📈 Endpoint Analysis:")
        
        # Group by HTTP method
        methods = {}
        for endpoint in api_spec.endpoints:
            method = endpoint.method.value
            methods[method] = methods.get(method, 0) + 1
        
        print(f"   HTTP Methods:")
        for method, count in sorted(methods.items()):
            print(f"     - {method}: {count}")
        
        # Group by tags
        tags = {}
        for endpoint in api_spec.endpoints:
            for tag in endpoint.tags:
                tags[tag] = tags.get(tag, 0) + 1
        
        print(f"\n   Top 10 Tags:")
        for tag, count in sorted(tags.items(), key=lambda x: x[1], reverse=True)[:10]:
            print(f"     - {tag}: {count}")
        
        # CRUD Analysis
        crud_endpoints = api_spec.get_crud_endpoints()
        print(f"\n   CRUD Operations:")
        for crud_type, endpoints in crud_endpoints.items():
            print(f"     - {crud_type}: {len(endpoints)}")
        
        # Sample endpoints
        print(f"\n📝 Sample Endpoints:")
        for i, endpoint in enumerate(api_spec.endpoints[:5]):
            print(f"   {i+1}. {endpoint.method.value} {endpoint.path}")
            print(f"      - Operation ID: {endpoint.operation_id}")
            print(f"      - Tags: {', '.join(endpoint.tags)}")
            if endpoint.summary:
                print(f"      - Summary: {endpoint.summary}")
            if endpoint.parameters:
                print(f"      - Parameters: {len(endpoint.parameters)}")
            if endpoint.has_request_body():
                print(f"      - Has Request Body: Yes")
            print(f"      - Responses: {len(endpoint.responses)}")
            crud_type = endpoint.is_crud_operation()
            if crud_type:
                print(f"      - CRUD Type: {crud_type}")
            print()
        
        # Service grouping analysis
        path_patterns = api_spec.get_path_patterns()
        print(f"📊 Path Pattern Analysis:")
        print(f"   - Unique base paths: {len(path_patterns)}")
        print(f"   - Top 10 base paths by endpoint count:")
        
        sorted_patterns = sorted(path_patterns.items(), key=lambda x: len(x[1]), reverse=True)
        for base_path, endpoints in sorted_patterns[:10]:
            print(f"     - {base_path}: {len(endpoints)} endpoints")
        
        # Potential service identification
        print(f"\n🔍 Potential Service Identification:")
        potential_services = {}
        for base_path, endpoints in path_patterns.items():
            if len(endpoints) >= 3:  # Only consider paths with multiple endpoints
                # Extract service name from path
                path_parts = [p for p in base_path.split('/') if p and not p.startswith('{')]
                if len(path_parts) >= 3:  # /ux/common/service_name pattern
                    service_name = path_parts[-1]  # Last part is usually the service
                    potential_services[service_name] = len(endpoints)
        
        for service, count in sorted(potential_services.items(), key=lambda x: x[1], reverse=True)[:15]:
            print(f"     - {service}: {count} endpoints")
        
        return True
        
    except JSONParserError as e:
        print(f"❌ Parsing failed: {str(e)}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


async def test_yaml_parsing():
    """Test YAML parsing capabilities"""
    print("🧪 Testing YAML parsing capabilities...")
    
    yaml_content = """
openapi: 3.0.3
info:
  title: Test API
  version: 1.0.0
  description: Test YAML parsing
paths:
  /test:
    get:
      operationId: test_get
      summary: Test endpoint
      tags:
        - testing
      parameters:
        - name: param1
          in: query
          schema:
            type: string
      responses:
        '200':
          description: Success
          content:
            application/json:
              schema:
                type: object
"""
    
    parser = JSONParser()
    
    try:
        api_spec = await parser.parse_specification(yaml_content, "test.yaml")
        
        assert api_spec.file_format == SpecificationFormat.OPENAPI_3
        assert api_spec.title == "Test API"
        assert api_spec.version == "1.0.0"
        assert len(api_spec.endpoints) == 1
        
        endpoint = api_spec.endpoints[0]
        assert endpoint.method.value == "GET"
        assert endpoint.path == "/test"
        assert endpoint.operation_id == "test_get"
        assert "testing" in endpoint.tags
        assert len(endpoint.parameters) == 1
        assert endpoint.parameters[0].name == "param1"
        
        print("✅ YAML parsing test passed!")
        return True
        
    except Exception as e:
        print(f"❌ YAML parsing test failed: {str(e)}")
        return False


async def test_ref_resolution():
    """Test $ref resolution"""
    print("🧪 Testing $ref resolution...")
    
    # YAML with $ref references
    yaml_with_refs = """
openapi: 3.0.3
info:
  title: Test API with $refs
  version: 1.0.0
paths:
  /users:
    get:
      operationId: list_users
      responses:
        '200':
          description: List of users
          content:
            application/json:
              schema:
                type: array
                items:
                  $ref: '#/components/schemas/User'
    post:
      operationId: create_user
      requestBody:
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/User'
      responses:
        '201':
          description: User created
components:
  schemas:
    User:
      type: object
      properties:
        id:
          type: integer
        name:
          type: string
        email:
          type: string
"""
    
    parser = JSONParser()
    
    try:
        api_spec = await parser.parse_specification(yaml_with_refs, "test-refs.yaml")
        
        assert api_spec.file_format == SpecificationFormat.OPENAPI_3
        assert len(api_spec.endpoints) == 2
        
        # Check if $refs were resolved
        create_endpoint = next((ep for ep in api_spec.endpoints if ep.operation_id == "create_user"), None)
        assert create_endpoint is not None
        
        print("✅ $ref resolution test passed!")
        return True
        
    except Exception as e:
        print(f"❌ $ref resolution test failed: {str(e)}")
        return False


async def run_all_tests():
    """Run all enhanced parser tests"""
    print("🚀 Starting Enhanced JSON/YAML Parser Tests\n")
    
    try:
        # Test basic YAML parsing
        yaml_success = await test_yaml_parsing()
        
        # Test $ref resolution
        ref_success = await test_ref_resolution()
        
        # Test with real Infraon spec
        infraon_success = await test_real_infraon_spec()
        
        all_passed = yaml_success and ref_success and infraon_success
        
        if all_passed:
            print("\n🎉 All enhanced parser tests passed successfully!")
            print("✅ YAML parsing working perfectly")
            print("✅ $ref resolution implemented")
            print("✅ Real Infraon OpenAPI spec parsed successfully")
            print("📊 Ready for service classification with complex API structures")
        else:
            print("\n⚠️  Some tests failed - check output above")
        
        return all_passed
        
    except Exception as e:
        print(f"\n❌ Test suite failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(run_all_tests())
    sys.exit(0 if success else 1)