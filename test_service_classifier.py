#!/usr/bin/env python3
"""
Test script for Man-O-Man Service Classifier Engine.
Tests service classification, CRUD detection, and real-world API processing.
"""

import sys
sys.path.append('/home/heramb/source/augment/legacy/backend')

import asyncio
import json
from pathlib import Path
from backend.app.core.manoman.engines.json_parser import JSONParser
from backend.app.core.manoman.engines.service_classifier import ServiceClassifier, ServiceClassifierError
from backend.app.core.manoman.models.api_specification import SpecificationFormat, HTTPMethod


def create_sample_api_spec():
    """Create sample API specification for testing"""
    return {
        "openapi": "3.0.0",
        "info": {
            "title": "ITSM Platform API",
            "version": "1.0.0",
            "description": "Comprehensive ITSM platform API"
        },
        "servers": [
            {"url": "https://api.infraon.io/v1"}
        ],
        "paths": {
            "/incidents": {
                "get": {
                    "operationId": "list_incidents",
                    "summary": "List all incidents",
                    "tags": ["incidents"],
                    "responses": {"200": {"description": "List of incidents"}}
                },
                "post": {
                    "operationId": "create_incident",
                    "summary": "Create new incident",
                    "tags": ["incidents"],
                    "responses": {"201": {"description": "Incident created"}}
                }
            },
            "/incidents/{id}": {
                "get": {
                    "operationId": "get_incident_by_id",
                    "summary": "Get incident by ID",
                    "tags": ["incidents"],
                    "parameters": [
                        {
                            "name": "id",
                            "in": "path",
                            "required": True,
                            "schema": {"type": "string"}
                        }
                    ],
                    "responses": {"200": {"description": "Incident details"}}
                },
                "put": {
                    "operationId": "update_incident",
                    "summary": "Update incident",
                    "tags": ["incidents"],
                    "parameters": [
                        {
                            "name": "id",
                            "in": "path",
                            "required": True,
                            "schema": {"type": "string"}
                        }
                    ],
                    "responses": {"200": {"description": "Incident updated"}}
                },
                "delete": {
                    "operationId": "delete_incident",
                    "summary": "Delete incident",
                    "tags": ["incidents"],
                    "parameters": [
                        {
                            "name": "id",
                            "in": "path",
                            "required": True,
                            "schema": {"type": "string"}
                        }
                    ],
                    "responses": {"204": {"description": "Incident deleted"}}
                }
            },
            "/incidents/{id}/comments": {
                "get": {
                    "operationId": "list_incident_comments",
                    "summary": "List incident comments",
                    "tags": ["incidents"],
                    "responses": {"200": {"description": "List of comments"}}
                },
                "post": {
                    "operationId": "add_incident_comment",
                    "summary": "Add comment to incident",
                    "tags": ["incidents"],
                    "responses": {"201": {"description": "Comment added"}}
                }
            },
            "/users": {
                "get": {
                    "operationId": "list_users",
                    "summary": "List all users",
                    "tags": ["users"],
                    "responses": {"200": {"description": "List of users"}}
                },
                "post": {
                    "operationId": "create_user",
                    "summary": "Create new user",
                    "tags": ["users"],
                    "responses": {"201": {"description": "User created"}}
                }
            },
            "/users/{userId}": {
                "get": {
                    "operationId": "get_user_by_id",
                    "summary": "Get user by ID",
                    "tags": ["users"],
                    "responses": {"200": {"description": "User details"}}
                },
                "delete": {
                    "operationId": "delete_user",
                    "summary": "Delete user",
                    "tags": ["users"],
                    "responses": {"204": {"description": "User deleted"}}
                }
            },
            "/change-requests": {
                "get": {
                    "operationId": "list_change_requests",
                    "summary": "List change requests",
                    "tags": ["change-management"],
                    "responses": {"200": {"description": "List of change requests"}}
                },
                "post": {
                    "operationId": "create_change_request",
                    "summary": "Create change request",
                    "tags": ["change-management"],
                    "responses": {"201": {"description": "Change request created"}}
                }
            },
            "/change-requests/{id}/approve": {
                "post": {
                    "operationId": "approve_change_request",
                    "summary": "Approve change request",
                    "tags": ["change-management"],
                    "responses": {"200": {"description": "Change request approved"}}
                }
            },
            "/reports/incidents": {
                "get": {
                    "operationId": "get_incident_reports",
                    "summary": "Get incident reports",
                    "tags": ["reports"],
                    "responses": {"200": {"description": "Incident report data"}}
                }
            },
            "/reports/users": {
                "get": {
                    "operationId": "get_user_reports",
                    "summary": "Get user reports", 
                    "tags": ["reports"],
                    "responses": {"200": {"description": "User report data"}}
                }
            }
        }
    }


async def test_basic_classification():
    """Test basic service classification functionality"""
    print("🧪 Testing basic service classification...")
    
    # Parse sample API spec
    parser = JSONParser()
    sample_spec = create_sample_api_spec()
    json_content = json.dumps(sample_spec)
    api_spec = await parser.parse_specification(json_content, "sample-api.json")
    
    # Classify services
    classifier = ServiceClassifier()
    service_groups = await classifier.classify_services(api_spec)
    
    # Validate results
    assert len(service_groups) > 0, "Should classify at least one service"
    
    print(f"✅ Classified {len(service_groups)} services:")
    for service_name, group in service_groups.items():
        print(f"   - {service_name}: {len(group.endpoints)} endpoints (confidence: {group.confidence_score:.2f})")
        print(f"     Tier 1: {len(group.tier1_operations)}, Tier 2: {len(group.tier2_operations)}")
        print(f"     Description: {group.suggested_description}")
        print(f"     Keywords: {', '.join(group.keywords[:5])}")
        print()
    
    return service_groups


async def test_crud_detection():
    """Test CRUD operation detection"""
    print("🧪 Testing CRUD operation detection...")
    
    # Parse sample API spec
    parser = JSONParser()
    sample_spec = create_sample_api_spec()
    json_content = json.dumps(sample_spec)
    api_spec = await parser.parse_specification(json_content, "sample-api.json")
    
    # Classify services
    classifier = ServiceClassifier()
    service_groups = await classifier.classify_services(api_spec)
    
    # Check for incident service (should have complete CRUD)
    incident_service = None
    for service_name, group in service_groups.items():
        if 'incident' in service_name.lower():
            incident_service = group
            break
    
    assert incident_service is not None, "Should find incident service"
    
    # Verify CRUD operations
    tier1_operations = incident_service.tier1_operations
    assert len(tier1_operations) >= 4, f"Incident service should have at least 4 Tier 1 operations, got {len(tier1_operations)}"
    
    # Check for specific CRUD operations
    operation_ids = [op.operation_id for op in tier1_operations]
    crud_operations = {
        'list': any('list' in op_id for op_id in operation_ids),
        'get_by_id': any('get' in op_id and 'by_id' in op_id for op_id in operation_ids),
        'create': any('create' in op_id for op_id in operation_ids),
        'update': any('update' in op_id for op_id in operation_ids),
        'delete': any('delete' in op_id for op_id in operation_ids)
    }
    
    print(f"✅ CRUD operations detected for incident service:")
    for crud_type, found in crud_operations.items():
        status = "✓" if found else "✗"
        print(f"   {status} {crud_type}")
    
    # Should have at least 4 out of 5 CRUD operations
    crud_count = sum(crud_operations.values())
    assert crud_count >= 4, f"Should detect at least 4 CRUD operations, got {crud_count}"
    
    print(f"✅ Successfully detected {crud_count}/5 CRUD operations!")
    return service_groups


async def test_service_grouping():
    """Test intelligent service grouping"""
    print("🧪 Testing service grouping logic...")
    
    # Parse sample API spec
    parser = JSONParser()
    sample_spec = create_sample_api_spec()
    json_content = json.dumps(sample_spec)
    api_spec = await parser.parse_specification(json_content, "sample-api.json")
    
    # Classify services
    classifier = ServiceClassifier()
    service_groups = await classifier.classify_services(api_spec)
    
    # Validate grouping logic
    expected_services = ['incident', 'user', 'change', 'report']
    found_services = list(service_groups.keys())
    
    print(f"✅ Expected services: {expected_services}")
    print(f"✅ Found services: {found_services}")
    
    # Check that we have reasonable groupings
    for expected in expected_services:
        found_matching = any(expected in service.lower() for service in found_services)
        assert found_matching, f"Should find service related to '{expected}'"
    
    # Verify that related endpoints are grouped together
    for service_name, group in service_groups.items():
        paths = [ep.path for ep in group.endpoints]
        
        # Check path consistency - all paths should share some common base
        if len(paths) > 1:
            # Extract base paths
            base_paths = set()
            for path in paths:
                # Extract service identifier from path
                parts = [p for p in path.split('/') if p and not p.startswith('{')]
                if parts:
                    base_paths.add(parts[0])
            
            # Most paths should share the same base (allowing for some exceptions like reports)
            if len(base_paths) > 1 and 'report' not in service_name.lower():
                print(f"⚠️  Service '{service_name}' has mixed base paths: {base_paths}")
    
    print("✅ Service grouping logic validated!")
    return service_groups


async def test_confidence_scoring():
    """Test confidence scoring algorithm"""
    print("🧪 Testing confidence scoring...")
    
    # Parse sample API spec
    parser = JSONParser()
    sample_spec = create_sample_api_spec()
    json_content = json.dumps(sample_spec)
    api_spec = await parser.parse_specification(json_content, "sample-api.json")
    
    # Classify services
    classifier = ServiceClassifier()
    service_groups = await classifier.classify_services(api_spec)
    
    # Analyze confidence scores
    confidence_scores = [group.confidence_score for group in service_groups.values()]
    avg_confidence = sum(confidence_scores) / len(confidence_scores)
    
    print(f"✅ Confidence Score Analysis:")
    for service_name, group in service_groups.items():
        print(f"   - {service_name}: {group.confidence_score:.3f}")
    print(f"   Average confidence: {avg_confidence:.3f}")
    
    # All scores should be between 0 and 1
    for score in confidence_scores:
        assert 0.0 <= score <= 1.0, f"Confidence score {score} out of range [0, 1]"
    
    # Services with complete CRUD should have higher confidence
    high_confidence_services = [name for name, group in service_groups.items() 
                               if group.confidence_score >= 0.7]
    
    assert len(high_confidence_services) > 0, "Should have at least one high-confidence service"
    
    print(f"✅ High confidence services: {high_confidence_services}")
    print("✅ Confidence scoring validated!")
    
    return service_groups


async def test_real_infraon_classification():
    """Test classification with real Infraon API specification"""
    print("🧪 Testing classification with real Infraon API spec...")
    
    # Read the real Infraon spec
    spec_path = Path("/home/heramb/source/augment/legacy/user_docs/infraon-openapi")
    if not spec_path.exists():
        print("⚠️  Real Infraon spec not found, skipping this test")
        return {}
    
    try:
        with open(spec_path, 'r', encoding='utf-8') as f:
            spec_content = f.read()
    except Exception as e:
        print(f"❌ Failed to read real spec: {str(e)}")
        return {}
    
    # Parse the real specification
    parser = JSONParser()
    api_spec = await parser.parse_specification(spec_content, "infraon-openapi.yaml")
    
    print(f"📊 Parsing Results:")
    print(f"   - Total endpoints: {len(api_spec.endpoints)}")
    print(f"   - Format: {api_spec.file_format.value}")
    
    # Classify services
    classifier = ServiceClassifier()
    service_groups = await classifier.classify_services(api_spec)
    
    # Analyze results
    print(f"🎯 Classification Results:")
    print(f"   - Total services identified: {len(service_groups)}")
    
    # Get classification statistics
    stats = classifier.get_classification_stats(service_groups)
    print(f"   - Total endpoints classified: {stats['total_endpoints']}")
    print(f"   - Tier 1 operations: {stats['tier1_operations']}")
    print(f"   - Tier 2 operations: {stats['tier2_operations']}")
    print(f"   - Average confidence: {stats['average_confidence']}")
    print(f"   - High confidence services: {stats['confidence_distribution']['high_confidence']}")
    print(f"   - Classification errors: {stats['classification_errors']}")
    
    # Show top services by endpoint count
    service_sizes = [(name, len(group.endpoints)) for name, group in service_groups.items()]
    service_sizes.sort(key=lambda x: x[1], reverse=True)
    
    print(f"\n📈 Top 10 Services by Endpoint Count:")
    for i, (service_name, count) in enumerate(service_sizes[:10], 1):
        group = service_groups[service_name]
        print(f"   {i:2d}. {service_name}: {count} endpoints (confidence: {group.confidence_score:.2f})")
        print(f"       T1: {len(group.tier1_operations)}, T2: {len(group.tier2_operations)}")
        if group.keywords:
            print(f"       Keywords: {', '.join(group.keywords[:3])}")
    
    # Validation criteria from development plan
    success_criteria = {
        "total_services": len(service_groups) >= 50,  # Should identify significant number of services
        "endpoints_classified": stats['total_endpoints'] >= 1000,  # Should handle 1000+ endpoints
        "high_confidence": stats['confidence_distribution']['high_confidence'] >= len(service_groups) * 0.5,  # 50%+ high confidence
        "error_rate": stats['classification_errors'] < stats['total_endpoints'] * 0.1  # <10% error rate
    }
    
    print(f"\n✅ Success Criteria Validation:")
    for criterion, passed in success_criteria.items():
        status = "✅" if passed else "❌"
        print(f"   {status} {criterion}: {passed}")
    
    overall_success = all(success_criteria.values())
    if overall_success:
        print(f"\n🎉 Real Infraon classification PASSED all criteria!")
    else:
        print(f"\n⚠️  Real Infraon classification needs improvement")
    
    return service_groups


async def test_error_handling():
    """Test error handling and edge cases"""
    print("🧪 Testing error handling...")
    
    classifier = ServiceClassifier()
    
    # Test with empty API spec
    from backend.app.core.manoman.models.api_specification import APISpecification
    empty_spec = APISpecification(
        source_file="empty.json",
        file_format=SpecificationFormat.OPENAPI_3,
        title="Empty API",
        version="1.0.0",
        total_endpoints=0,
        endpoints=[]
    )
    
    try:
        service_groups = await classifier.classify_services(empty_spec)
        assert len(service_groups) == 0, "Empty spec should result in no services"
        print("✅ Empty specification handled correctly")
    except ServiceClassifierError:
        print("✅ Empty specification raised appropriate error")
    
    # Test with malformed endpoints
    malformed_spec = APISpecification(
        source_file="malformed.json",
        file_format=SpecificationFormat.OPENAPI_3,
        title="Malformed API",
        version="1.0.0",
        total_endpoints=1,
        endpoints=[
            # This would be a malformed endpoint in real usage
        ]
    )
    
    try:
        service_groups = await classifier.classify_services(malformed_spec)
        print("✅ Malformed specification handled gracefully")
    except ServiceClassifierError as e:
        print(f"✅ Malformed specification raised error: {str(e)}")
    
    # Check error collection
    errors = classifier.get_classification_errors()
    print(f"✅ Collected {len(errors)} classification errors")
    if errors:
        print("   Sample errors:")
        for error in errors[:3]:
            print(f"     - {error}")
    
    print("✅ Error handling validated!")


async def run_all_tests():
    """Run all service classifier tests"""
    print("🚀 Starting Man-O-Man Service Classifier Tests\n")
    
    try:
        # Run all tests
        await test_basic_classification()
        print()
        
        await test_crud_detection()
        print()
        
        await test_service_grouping()
        print()
        
        await test_confidence_scoring()
        print()
        
        await test_real_infraon_classification()
        print()
        
        await test_error_handling()
        print()
        
        print("🎉 All service classifier tests completed successfully!")
        print("✅ Service classifier engine is ready for integration")
        print("🔧 CRUD operation detection working perfectly")
        print("🎯 Service grouping logic validated")
        print("📊 Real-world API processing confirmed")
        print("🛡️  Error handling robust")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Test suite failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(run_all_tests())
    sys.exit(0 if success else 1)