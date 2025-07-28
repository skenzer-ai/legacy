"""
Validation and Testing Data Models

Comprehensive Pydantic models for testing, validation, and procedural API testing
including Create-Read-Delete cycles, schema discovery, and accuracy metrics.
"""

from pydantic import BaseModel, Field, validator
from typing import List, Dict, Optional, Any, Union
from datetime import datetime
from enum import Enum


class TestCategoryType(str, Enum):
    """Types of test categories"""
    BASIC_CRUD = "basic_crud"
    SERVICE_IDENTIFICATION = "service_identification"
    OPERATION_CLASSIFICATION = "operation_classification"
    EDGE_CASES = "edge_cases"
    MULTI_SERVICE = "multi_service"
    PROCEDURAL_API = "procedural_api"


class DifficultyLevel(str, Enum):
    """Test difficulty levels"""
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


class ConflictType(str, Enum):
    """Types of conflicts that can be detected"""
    IDENTICAL_KEYWORDS = "identical_keywords"
    SEMANTIC_SIMILARITY = "semantic_similarity"
    AMBIGUOUS_INTENT = "ambiguous_intent"
    OVERLAPPING_CONTEXT = "overlapping_context"


class ConflictSeverity(str, Enum):
    """Severity levels for conflicts"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class DiscrepancyType(str, Enum):
    """Types of schema discrepancies"""
    MISSING_FIELD = "missing_field"
    WRONG_TYPE = "wrong_type"
    INCORRECT_REQUIREMENT = "incorrect_requirement"
    EXTRA_FIELD = "extra_field"
    FORMAT_MISMATCH = "format_mismatch"


class ImpactLevel(str, Enum):
    """Impact levels for issues"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class TestCase(BaseModel):
    """Individual test case for service/operation classification"""
    test_id: str = Field(..., description="Unique test identifier")
    query: str = Field(..., description="Test query to classify")
    expected_service: str = Field(..., description="Expected service name")
    expected_operation: str = Field(..., description="Expected operation name")
    expected_tier: str = Field(..., description="Expected tier (tier1/tier2)")
    expected_parameters: Dict[str, Any] = Field(default_factory=dict, description="Expected parameters")
    difficulty_level: DifficultyLevel = Field(..., description="Test difficulty")
    category: TestCategoryType = Field(..., description="Test category")
    description: Optional[str] = Field(None, description="Test case description")
    
    class Config:
        extra = "forbid"


class TestSuite(BaseModel):
    """Collection of test cases organized by category"""
    suite_id: str = Field(..., description="Unique test suite identifier")
    total_tests: int = Field(..., description="Total number of tests")
    test_categories: Dict[str, List[TestCase]] = Field(..., description="Tests organized by category")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Suite creation time")
    service_registry_version: str = Field(..., description="Version of registry being tested")
    
    class Config:
        extra = "forbid"
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
    
    @validator('total_tests')
    def validate_total_count(cls, v, values):
        """Ensure total_tests matches actual test count"""
        if 'test_categories' in values:
            actual_count = sum(len(tests) for tests in values['test_categories'].values())
            if v != actual_count:
                raise ValueError(f'total_tests ({v}) does not match actual count ({actual_count})')
        return v
    
    def get_tests_by_difficulty(self, difficulty: DifficultyLevel) -> List[TestCase]:
        """Get all tests of specific difficulty level"""
        tests = []
        for category_tests in self.test_categories.values():
            tests.extend([test for test in category_tests if test.difficulty_level == difficulty])
        return tests
    
    def get_category_stats(self) -> Dict[str, int]:
        """Get test count by category"""
        return {category: len(tests) for category, tests in self.test_categories.items()}


class TestResult(BaseModel):
    """Individual test execution result"""
    test_id: str = Field(..., description="Test case identifier")
    query: str = Field(..., description="Test query")
    expected_service: str = Field(..., description="Expected service")
    actual_service: Optional[str] = Field(None, description="Actual classified service")
    expected_operation: str = Field(..., description="Expected operation")
    actual_operation: Optional[str] = Field(None, description="Actual classified operation")
    success: bool = Field(..., description="Whether test passed")
    confidence_score: float = Field(default=0.0, ge=0.0, le=1.0, description="Classification confidence")
    error_message: Optional[str] = Field(None, description="Error message if test failed")
    execution_time_ms: float = Field(..., description="Test execution time")
    
    class Config:
        extra = "forbid"


class TestResults(BaseModel):
    """Complete test execution results"""
    suite_id: str = Field(..., description="Test suite identifier")
    total_tests: int = Field(..., description="Total tests executed")
    passed: int = Field(..., description="Number of passed tests")
    failed: int = Field(..., description="Number of failed tests")
    accuracy_percentage: float = Field(..., ge=0.0, le=100.0, description="Overall accuracy")
    detailed_results: List[TestResult] = Field(..., description="Individual test results")
    performance_metrics: Dict[str, float] = Field(default_factory=dict, description="Performance metrics")
    execution_time_total_ms: float = Field(..., description="Total execution time")
    executed_at: datetime = Field(default_factory=datetime.utcnow, description="Execution timestamp")
    
    class Config:
        extra = "forbid"
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
    
    def get_results_by_category(self, category: TestCategoryType) -> List[TestResult]:
        """Get results filtered by test category"""
        # This would need category info from original test cases
        return [result for result in self.detailed_results 
                if result.test_id.startswith(category.value)]
    
    def get_failed_tests(self) -> List[TestResult]:
        """Get all failed test results"""
        return [result for result in self.detailed_results if not result.success]
    
    def get_accuracy_by_service(self) -> Dict[str, float]:
        """Calculate accuracy per service"""
        service_stats = {}
        for result in self.detailed_results:
            service = result.expected_service
            if service not in service_stats:
                service_stats[service] = {'total': 0, 'passed': 0}
            service_stats[service]['total'] += 1
            if result.success:
                service_stats[service]['passed'] += 1
        
        return {service: (stats['passed'] / stats['total'] * 100) 
                for service, stats in service_stats.items()}


class APITestResult(BaseModel):
    """Individual API endpoint test result"""
    operation: str = Field(..., description="Operation being tested")
    endpoint: str = Field(..., description="API endpoint path")
    method: str = Field(..., description="HTTP method")
    request_data: Dict[str, Any] = Field(default_factory=dict, description="Request data sent")
    response_data: Dict[str, Any] = Field(default_factory=dict, description="Response data received")
    status_code: int = Field(..., description="HTTP status code")
    success: bool = Field(..., description="Whether API call succeeded")
    response_time_ms: float = Field(..., description="API response time")
    discovered_schema: Dict[str, Any] = Field(default_factory=dict, description="Discovered request/response schema")
    validation_errors: List[str] = Field(default_factory=list, description="Schema validation errors")
    error_message: Optional[str] = Field(None, description="Error message if test failed")
    
    class Config:
        extra = "forbid"


class CRDTestResult(BaseModel):
    """Create-Read-Delete test cycle result"""
    service_name: str = Field(..., description="Service being tested")
    test_cycle_id: str = Field(..., description="Unique test cycle identifier")
    create_result: APITestResult = Field(..., description="Create operation result")
    read_result: APITestResult = Field(..., description="Read operation result")
    read_list_result: APITestResult = Field(..., description="List operation result")
    update_result: Optional[APITestResult] = Field(None, description="Update operation result (if available)")
    delete_result: APITestResult = Field(..., description="Delete operation result")
    verification_result: APITestResult = Field(..., description="Verification that entity was deleted")
    overall_success: bool = Field(..., description="Whether entire cycle succeeded")
    discovered_schemas: Dict[str, Dict] = Field(default_factory=dict, description="Schemas discovered for each operation")
    test_entity_data: Dict[str, Any] = Field(default_factory=dict, description="Test data used")
    cleanup_completed: bool = Field(..., description="Whether test cleanup completed successfully")
    
    class Config:
        extra = "forbid"
    
    def get_failed_operations(self) -> List[str]:
        """Get list of operations that failed"""
        failed = []
        if not self.create_result.success:
            failed.append("create")
        if not self.read_result.success:
            failed.append("read")
        if not self.read_list_result.success:
            failed.append("read_list")
        if self.update_result and not self.update_result.success:
            failed.append("update")
        if not self.delete_result.success:
            failed.append("delete")
        if not self.verification_result.success:
            failed.append("verification")
        return failed
    
    def get_average_response_time(self) -> float:
        """Calculate average response time across all operations"""
        times = [
            self.create_result.response_time_ms,
            self.read_result.response_time_ms,
            self.read_list_result.response_time_ms,
            self.delete_result.response_time_ms,
            self.verification_result.response_time_ms
        ]
        if self.update_result:
            times.append(self.update_result.response_time_ms)
        return sum(times) / len(times)


class ParameterValidationResult(BaseModel):
    """Parameter validation result for an operation"""
    operation: str = Field(..., description="Operation name")
    required_parameters: List[str] = Field(default_factory=list, description="Required parameters")
    optional_parameters: List[str] = Field(default_factory=list, description="Optional parameters")
    parameter_types: Dict[str, str] = Field(default_factory=dict, description="Parameter data types")
    validation_rules: Dict[str, List[str]] = Field(default_factory=dict, description="Validation rules per parameter")
    default_values: Dict[str, Any] = Field(default_factory=dict, description="Default values")
    business_constraints: List[str] = Field(default_factory=list, description="Business logic constraints")
    
    class Config:
        extra = "forbid"


class SchemaDiscrepancy(BaseModel):
    """Schema validation discrepancy"""
    operation: str = Field(..., description="Operation with discrepancy")
    discrepancy_type: DiscrepancyType = Field(..., description="Type of discrepancy")
    field_name: Optional[str] = Field(None, description="Field name if applicable")
    expected: str = Field(..., description="Expected value/behavior")
    actual: str = Field(..., description="Actual value/behavior")
    impact_level: ImpactLevel = Field(..., description="Impact level")
    suggested_fix: Optional[str] = Field(None, description="Suggested resolution")
    
    class Config:
        extra = "forbid"


class SchemaValidationReport(BaseModel):
    """Comprehensive schema validation report"""
    service_name: str = Field(..., description="Service name")
    validation_timestamp: datetime = Field(default_factory=datetime.utcnow, description="Validation time")
    input_schema_accuracy: float = Field(..., ge=0.0, le=1.0, description="Input schema accuracy")
    output_schema_accuracy: float = Field(..., ge=0.0, le=1.0, description="Output schema accuracy")
    discrepancies: List[SchemaDiscrepancy] = Field(default_factory=list, description="Found discrepancies")
    suggested_corrections: List[str] = Field(default_factory=list, description="Suggested registry corrections")
    confidence_score: float = Field(..., ge=0.0, le=1.0, description="Overall confidence in validation")
    
    class Config:
        extra = "forbid"
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
    
    def get_high_impact_discrepancies(self) -> List[SchemaDiscrepancy]:
        """Get discrepancies with high impact"""
        return [disc for disc in self.discrepancies if disc.impact_level == ImpactLevel.HIGH]
    
    def get_discrepancies_by_type(self, disc_type: DiscrepancyType) -> List[SchemaDiscrepancy]:
        """Get discrepancies of specific type"""
        return [disc for disc in self.discrepancies if disc.discrepancy_type == disc_type]


class ProceduralTestResults(BaseModel):
    """Results from procedural API testing"""
    service_name: str = Field(..., description="Service tested")
    total_tier1_apis: int = Field(..., description="Total Tier 1 APIs in service")
    successful_crd_cycles: int = Field(..., description="Successful Create-Read-Delete cycles")
    failed_crd_cycles: int = Field(..., description="Failed Create-Read-Delete cycles")
    schema_validation_accuracy: float = Field(..., ge=0.0, le=1.0, description="Schema validation accuracy")
    discovered_schemas: Dict[str, Dict[str, Any]] = Field(
        default_factory=dict, 
        description="Discovered schemas by operation"
    )
    parameter_validation_results: Dict[str, ParameterValidationResult] = Field(
        default_factory=dict,
        description="Parameter validation results by operation"
    )
    error_handling_analysis: Dict[str, List[str]] = Field(
        default_factory=dict,
        description="Error handling analysis by operation"
    )
    performance_metrics: Dict[str, float] = Field(
        default_factory=dict,
        description="Performance metrics"
    )
    test_entity_cleanup_status: str = Field(..., description="Test entity cleanup status")
    
    class Config:
        extra = "forbid"
    
    def get_success_rate(self) -> float:
        """Calculate overall success rate"""
        total = self.successful_crd_cycles + self.failed_crd_cycles
        return (self.successful_crd_cycles / total * 100) if total > 0 else 0.0
    
    def get_avg_response_time(self) -> float:
        """Get average response time across all operations"""
        times = [v for k, v in self.performance_metrics.items() if k.endswith('_time_ms')]
        return sum(times) / len(times) if times else 0.0


class ConflictReport(BaseModel):
    """Service registry conflict detection report"""
    conflict_id: str = Field(..., description="Unique conflict identifier")
    conflict_type: ConflictType = Field(..., description="Type of conflict")
    affected_services: List[str] = Field(..., description="Services involved in conflict")
    conflicting_terms: List[str] = Field(..., description="Terms causing conflict")
    severity: ConflictSeverity = Field(..., description="Conflict severity")
    description: str = Field(..., description="Human-readable conflict description")
    suggested_resolution: str = Field(..., description="Suggested resolution")
    auto_resolvable: bool = Field(..., description="Whether conflict can be resolved automatically")
    confidence_score: float = Field(..., ge=0.0, le=1.0, description="Confidence in conflict detection")
    detected_at: datetime = Field(default_factory=datetime.utcnow, description="Detection timestamp")
    
    class Config:
        extra = "forbid"
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


class ImprovementSuggestion(BaseModel):
    """Improvement suggestion based on test analysis"""
    suggestion_id: str = Field(..., description="Unique suggestion identifier")
    category: str = Field(..., description="Suggestion category")
    priority: str = Field(..., description="Priority level")
    title: str = Field(..., description="Brief suggestion title")
    description: str = Field(..., description="Detailed suggestion description")
    affected_services: List[str] = Field(default_factory=list, description="Services that would benefit")
    expected_improvement: float = Field(..., description="Expected accuracy improvement percentage")
    implementation_effort: str = Field(..., description="Implementation effort estimate")
    
    class Config:
        extra = "forbid"