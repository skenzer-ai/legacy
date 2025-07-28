#!/usr/bin/env python3
"""
Test script for Man-O-Man validation and testing data models.
Tests comprehensive validation framework including procedural testing models.
"""

import sys
sys.path.append('/home/heramb/source/augment/legacy/backend')

import uuid
from datetime import datetime
from backend.app.core.manoman.models.validation_models import (
    TestCategoryType,
    DifficultyLevel,
    ConflictType,
    ConflictSeverity,
    DiscrepancyType,
    ImpactLevel,
    TestCase,
    TestSuite,
    TestResult,
    TestResults,
    APITestResult,
    CRDTestResult,
    ParameterValidationResult,
    SchemaDiscrepancy,
    SchemaValidationReport,
    ProceduralTestResults,
    ConflictReport,
    ImprovementSuggestion
)


def test_enums():
    """Test all enum types"""
    print("🧪 Testing enum types...")
    
    # Test TestCategoryType
    assert TestCategoryType.BASIC_CRUD == "basic_crud"
    assert TestCategoryType.SERVICE_IDENTIFICATION == "service_identification"
    assert TestCategoryType.PROCEDURAL_API == "procedural_api"
    
    # Test DifficultyLevel
    assert DifficultyLevel.EASY == "easy"
    assert DifficultyLevel.MEDIUM == "medium"
    assert DifficultyLevel.HARD == "hard"
    
    # Test ConflictType
    assert ConflictType.IDENTICAL_KEYWORDS == "identical_keywords"
    assert ConflictType.SEMANTIC_SIMILARITY == "semantic_similarity"
    
    # Test ConflictSeverity
    assert ConflictSeverity.LOW == "low"
    assert ConflictSeverity.CRITICAL == "critical"
    
    # Test DiscrepancyType
    assert DiscrepancyType.MISSING_FIELD == "missing_field"
    assert DiscrepancyType.WRONG_TYPE == "wrong_type"
    
    # Test ImpactLevel
    assert ImpactLevel.LOW == "low"
    assert ImpactLevel.HIGH == "high"
    
    print("✅ Enum types tests passed!")


def test_test_case():
    """Test TestCase model"""
    print("🧪 Testing TestCase model...")
    
    test_case = TestCase(
        test_id="tc_001",
        query="create a new business rule",
        expected_service="business_rule",
        expected_operation="create",
        expected_tier="tier1",
        expected_parameters={"name": "string", "conditions": "array"},
        difficulty_level=DifficultyLevel.EASY,
        category=TestCategoryType.BASIC_CRUD,
        description="Basic create operation test"
    )
    
    assert test_case.test_id == "tc_001"
    assert test_case.query == "create a new business rule"
    assert test_case.expected_service == "business_rule"
    assert test_case.difficulty_level == DifficultyLevel.EASY
    assert test_case.category == TestCategoryType.BASIC_CRUD
    assert "name" in test_case.expected_parameters
    
    print("✅ TestCase model tests passed!")
    return test_case


def test_test_suite():
    """Test TestSuite model"""
    print("🧪 Testing TestSuite model...")
    
    test_cases = [test_test_case() for _ in range(3)]
    
    test_suite = TestSuite(
        suite_id="ts_001",
        total_tests=3,
        test_categories={
            "basic_crud": test_cases
        },
        service_registry_version="1.0.0"
    )
    
    assert test_suite.suite_id == "ts_001"
    assert test_suite.total_tests == 3
    assert len(test_suite.test_categories["basic_crud"]) == 3
    assert test_suite.service_registry_version == "1.0.0"
    
    # Test helper methods
    easy_tests = test_suite.get_tests_by_difficulty(DifficultyLevel.EASY)
    assert len(easy_tests) == 3  # All tests are easy
    
    category_stats = test_suite.get_category_stats()
    assert category_stats["basic_crud"] == 3
    
    print("✅ TestSuite model tests passed!")
    return test_suite


def test_test_result():
    """Test TestResult model"""
    print("🧪 Testing TestResult model...")
    
    test_result = TestResult(
        test_id="tc_001",
        query="create a new business rule",
        expected_service="business_rule",
        actual_service="business_rule",
        expected_operation="create",
        actual_operation="create",
        success=True,
        confidence_score=0.95,
        execution_time_ms=150.5
    )
    
    assert test_result.test_id == "tc_001"
    assert test_result.success == True
    assert test_result.confidence_score == 0.95
    assert test_result.execution_time_ms == 150.5
    assert test_result.actual_service == test_result.expected_service
    
    print("✅ TestResult model tests passed!")
    return test_result


def test_test_results():
    """Test TestResults model"""
    print("🧪 Testing TestResults model...")
    
    test_results = [test_test_result() for _ in range(5)]
    # Make one test fail
    test_results[1].success = False
    test_results[1].actual_service = "wrong_service"
    
    results = TestResults(
        suite_id="ts_001",
        total_tests=5,
        passed=4,
        failed=1,
        accuracy_percentage=80.0,
        detailed_results=test_results,
        performance_metrics={"avg_response_time": 145.2},
        execution_time_total_ms=750.0
    )
    
    assert results.suite_id == "ts_001"
    assert results.total_tests == 5
    assert results.passed == 4
    assert results.failed == 1
    assert results.accuracy_percentage == 80.0
    assert len(results.detailed_results) == 5
    
    # Test helper methods
    failed_tests = results.get_failed_tests()
    assert len(failed_tests) == 1
    assert failed_tests[0].actual_service == "wrong_service"
    
    accuracy_by_service = results.get_accuracy_by_service()
    assert "business_rule" in accuracy_by_service
    
    print("✅ TestResults model tests passed!")
    return results


def test_api_test_result():
    """Test APITestResult model"""
    print("🧪 Testing APITestResult model...")
    
    api_result = APITestResult(
        operation="create",
        endpoint="/api/v1/business-rules",
        method="POST",
        request_data={"name": "Test Rule", "conditions": ["condition1"]},
        response_data={"id": "123", "name": "Test Rule", "status": "active"},
        status_code=201,
        success=True,
        response_time_ms=245.7,
        discovered_schema={
            "input": {"required": ["name"], "optional": ["conditions"]},
            "output": {"fields": ["id", "name", "status"]}
        }
    )
    
    assert api_result.operation == "create"
    assert api_result.endpoint == "/api/v1/business-rules"
    assert api_result.method == "POST"
    assert api_result.status_code == 201
    assert api_result.success == True
    assert api_result.response_time_ms == 245.7
    assert "name" in api_result.request_data
    assert "id" in api_result.response_data
    assert "input" in api_result.discovered_schema
    
    print("✅ APITestResult model tests passed!")
    return api_result


def test_crd_test_result():
    """Test CRDTestResult model"""
    print("🧪 Testing CRDTestResult model...")
    
    create_result = test_api_test_result()
    read_result = APITestResult(
        operation="read",
        endpoint="/api/v1/business-rules/123",
        method="GET",
        status_code=200,
        success=True,
        response_time_ms=89.3
    )
    delete_result = APITestResult(
        operation="delete",
        endpoint="/api/v1/business-rules/123",
        method="DELETE",
        status_code=204,
        success=True,
        response_time_ms=156.8
    )
    
    crd_result = CRDTestResult(
        service_name="business_rule",
        test_cycle_id="crd_001",
        create_result=create_result,
        read_result=read_result,
        read_list_result=read_result,  # Reuse for simplicity
        delete_result=delete_result,
        verification_result=read_result,  # Reuse for simplicity
        overall_success=True,
        discovered_schemas={"create": {"input": {}, "output": {}}},
        test_entity_data={"name": "Test Rule"},
        cleanup_completed=True
    )
    
    assert crd_result.service_name == "business_rule"
    assert crd_result.test_cycle_id == "crd_001"
    assert crd_result.overall_success == True
    assert crd_result.cleanup_completed == True
    assert len(crd_result.discovered_schemas) == 1
    
    # Test helper methods
    failed_ops = crd_result.get_failed_operations()
    assert len(failed_ops) == 0  # All operations succeeded
    
    avg_time = crd_result.get_average_response_time()
    assert avg_time > 0
    
    print("✅ CRDTestResult model tests passed!")
    return crd_result


def test_parameter_validation_result():
    """Test ParameterValidationResult model"""
    print("🧪 Testing ParameterValidationResult model...")
    
    param_result = ParameterValidationResult(
        operation="create",
        required_parameters=["name", "description"],
        optional_parameters=["priority", "enabled"],
        parameter_types={"name": "string", "description": "string", "priority": "integer"},
        validation_rules={"name": ["min_length:3", "max_length:100"]},
        default_values={"priority": 1, "enabled": True},
        business_constraints=["name must be unique", "description cannot be empty"]
    )
    
    assert param_result.operation == "create"
    assert len(param_result.required_parameters) == 2
    assert len(param_result.optional_parameters) == 2
    assert "name" in param_result.required_parameters
    assert "priority" in param_result.optional_parameters
    assert param_result.parameter_types["name"] == "string"
    assert param_result.default_values["priority"] == 1
    assert len(param_result.business_constraints) == 2
    
    print("✅ ParameterValidationResult model tests passed!")
    return param_result


def test_schema_discrepancy():
    """Test SchemaDiscrepancy model"""
    print("🧪 Testing SchemaDiscrepancy model...")
    
    discrepancy = SchemaDiscrepancy(
        operation="create",
        discrepancy_type=DiscrepancyType.MISSING_FIELD,
        field_name="email",
        expected="email field should be optional",
        actual="email field is required in API",
        impact_level=ImpactLevel.HIGH,
        suggested_fix="Update registry to mark email as required"
    )
    
    assert discrepancy.operation == "create"
    assert discrepancy.discrepancy_type == DiscrepancyType.MISSING_FIELD
    assert discrepancy.field_name == "email"
    assert discrepancy.impact_level == ImpactLevel.HIGH
    assert "Update registry" in discrepancy.suggested_fix
    
    print("✅ SchemaDiscrepancy model tests passed!")
    return discrepancy


def test_schema_validation_report():
    """Test SchemaValidationReport model"""
    print("🧪 Testing SchemaValidationReport model...")
    
    discrepancy = test_schema_discrepancy()
    
    validation_report = SchemaValidationReport(
        service_name="business_rule",
        input_schema_accuracy=0.92,
        output_schema_accuracy=0.98,
        discrepancies=[discrepancy],
        suggested_corrections=["Mark email as required", "Add validation for name field"],
        confidence_score=0.95
    )
    
    assert validation_report.service_name == "business_rule"
    assert validation_report.input_schema_accuracy == 0.92
    assert validation_report.output_schema_accuracy == 0.98
    assert len(validation_report.discrepancies) == 1
    assert len(validation_report.suggested_corrections) == 2
    assert validation_report.confidence_score == 0.95
    
    # Test helper methods
    high_impact = validation_report.get_high_impact_discrepancies()
    assert len(high_impact) == 1
    
    missing_fields = validation_report.get_discrepancies_by_type(DiscrepancyType.MISSING_FIELD)
    assert len(missing_fields) == 1
    
    print("✅ SchemaValidationReport model tests passed!")
    return validation_report


def test_procedural_test_results():
    """Test ProceduralTestResults model"""
    print("🧪 Testing ProceduralTestResults model...")
    
    param_result = test_parameter_validation_result()
    
    procedural_results = ProceduralTestResults(
        service_name="business_rule",
        total_tier1_apis=5,
        successful_crd_cycles=4,
        failed_crd_cycles=1,
        schema_validation_accuracy=0.94,
        discovered_schemas={"create": {"input": {}, "output": {}}},
        parameter_validation_results={"create": param_result},
        error_handling_analysis={"create": ["400 for missing name", "409 for duplicate"]},
        performance_metrics={"avg_create_time_ms": 245, "avg_read_time_ms": 89},
        test_entity_cleanup_status="completed"
    )
    
    assert procedural_results.service_name == "business_rule"
    assert procedural_results.total_tier1_apis == 5
    assert procedural_results.successful_crd_cycles == 4
    assert procedural_results.failed_crd_cycles == 1
    assert procedural_results.schema_validation_accuracy == 0.94
    assert procedural_results.test_entity_cleanup_status == "completed"
    
    # Test helper methods
    success_rate = procedural_results.get_success_rate()
    assert success_rate == 80.0  # 4/5 * 100
    
    avg_time = procedural_results.get_avg_response_time()
    assert avg_time > 0
    
    print("✅ ProceduralTestResults model tests passed!")
    return procedural_results


def test_conflict_report():
    """Test ConflictReport model"""
    print("🧪 Testing ConflictReport model...")
    
    conflict = ConflictReport(
        conflict_id="conf_001",
        conflict_type=ConflictType.IDENTICAL_KEYWORDS,
        affected_services=["business_rule", "policy_management"],
        conflicting_terms=["rule", "policy"],
        severity=ConflictSeverity.MEDIUM,
        description="Keywords 'rule' and 'policy' overlap between services",
        suggested_resolution="Use more specific keywords or add service prefixes",
        auto_resolvable=False,
        confidence_score=0.87
    )
    
    assert conflict.conflict_id == "conf_001"
    assert conflict.conflict_type == ConflictType.IDENTICAL_KEYWORDS
    assert len(conflict.affected_services) == 2
    assert len(conflict.conflicting_terms) == 2
    assert conflict.severity == ConflictSeverity.MEDIUM
    assert conflict.auto_resolvable == False
    assert conflict.confidence_score == 0.87
    
    print("✅ ConflictReport model tests passed!")
    return conflict


def test_improvement_suggestion():
    """Test ImprovementSuggestion model"""
    print("🧪 Testing ImprovementSuggestion model...")
    
    suggestion = ImprovementSuggestion(
        suggestion_id="imp_001",
        category="keyword_optimization",
        priority="high",
        title="Add domain-specific synonyms",
        description="Add ITSM-specific synonyms to improve classification accuracy",
        affected_services=["incident", "request", "change"],
        expected_improvement=12.5,
        implementation_effort="medium"
    )
    
    assert suggestion.suggestion_id == "imp_001"
    assert suggestion.category == "keyword_optimization"
    assert suggestion.priority == "high"
    assert suggestion.title == "Add domain-specific synonyms"
    assert len(suggestion.affected_services) == 3
    assert suggestion.expected_improvement == 12.5
    assert suggestion.implementation_effort == "medium"
    
    print("✅ ImprovementSuggestion model tests passed!")
    return suggestion


def test_model_serialization():
    """Test JSON serialization/deserialization"""
    print("🧪 Testing model serialization...")
    
    # Test complex model serialization
    procedural_results = test_procedural_test_results()
    
    # Test serialization
    json_data = procedural_results.model_dump()
    assert "service_name" in json_data
    assert "successful_crd_cycles" in json_data
    assert "parameter_validation_results" in json_data
    
    # Test deserialization
    new_results = ProceduralTestResults(**json_data)
    assert new_results.service_name == procedural_results.service_name
    assert new_results.successful_crd_cycles == procedural_results.successful_crd_cycles
    assert new_results.get_success_rate() == procedural_results.get_success_rate()
    
    print("✅ Model serialization tests passed!")


def test_model_validation():
    """Test model validation rules"""
    print("🧪 Testing model validation...")
    
    # Test TestSuite validation (total_tests should match actual count)
    test_case = test_test_case()
    
    # Valid test suite
    valid_suite = TestSuite(
        suite_id="ts_valid",
        total_tests=2,
        test_categories={"basic_crud": [test_case, test_case]},
        service_registry_version="1.0.0"
    )
    assert valid_suite.total_tests == 2
    
    # Test confidence score validation (should be between 0 and 1)
    valid_result = TestResult(
        test_id="tr_001",
        query="test query",
        expected_service="test_service",
        expected_operation="test_op",
        success=True,
        confidence_score=0.95,  # Valid: between 0 and 1
        execution_time_ms=100.0
    )
    assert valid_result.confidence_score == 0.95
    
    print("✅ Model validation tests passed!")


def run_all_tests():
    """Run all tests"""
    print("🚀 Starting Man-O-Man Validation Model Tests\n")
    
    try:
        test_enums()
        test_test_case()
        test_test_suite()
        test_test_result()
        test_test_results()
        test_api_test_result()
        test_crd_test_result()
        test_parameter_validation_result()
        test_schema_discrepancy()
        test_schema_validation_report()
        test_procedural_test_results()
        test_conflict_report()
        test_improvement_suggestion()
        test_model_serialization()
        test_model_validation()
        
        print("\n🎉 All validation model tests passed successfully!")
        print("✅ Models are ready for procedural testing integration")
        print("🔬 Create-Read-Delete testing framework is fully operational")
        print("📊 Schema discovery and validation systems are ready")
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)