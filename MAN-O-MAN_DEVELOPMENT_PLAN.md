# Man-O-Man Service Registry Management System
## Comprehensive Development Plan

---

## Executive Summary

The **Man-O-Man** module is an intelligent service registry management system that enables users to upload API specifications, automatically classify services, interactively define service metadata, and validate the entire system accuracy. This module serves as the foundation for the service-centric tier classification system in the unified AugmentAgent.

---

## System Architecture Overview

```
JSON Upload → Auto-Classification → Interactive Definition → Validation → Registry Update
     ↓              ↓                    ↓                  ↓            ↓
File Parser → Service Grouper → Agent-Assisted Setup → Testing Suite → Production Ready
```

---

## Core Components and Directory Structure

```
backend/app/core/manoman/
├── __init__.py
├── models/
│   ├── __init__.py
│   ├── service_registry.py      # Pydantic models for registry schema
│   ├── api_specification.py     # Models for raw API specs
│   └── validation_models.py     # Test and validation models
├── engines/
│   ├── __init__.py
│   ├── json_parser.py          # JSON spec parsing and analysis
│   ├── service_classifier.py   # Auto-classification of services
│   ├── conflict_detector.py    # Keyword/synonym conflict detection
│   └── accuracy_tester.py      # System accuracy validation
├── agents/
│   ├── __init__.py
│   ├── definition_agent.py     # Interactive service definition agent
│   └── testing_agent.py       # Automated testing and feedback agent
├── storage/
│   ├── __init__.py
│   ├── registry_manager.py     # Service registry CRUD operations
│   └── version_control.py      # Registry versioning and history
├── api/
│   ├── __init__.py
│   ├── upload.py              # File upload endpoints
│   ├── classification.py     # Classification management endpoints
│   ├── definition.py          # Interactive definition endpoints
│   └── validation.py          # Testing and validation endpoints
└── utils/
    ├── __init__.py
    ├── text_processing.py     # NLP utilities for classification
    └── registry_helpers.py    # Helper functions for registry operations
```

---

## Detailed Component Specifications

### 1. Data Models (`models/`)

#### 1.1 Service Registry Model (`service_registry.py`)

```python
from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Union
from enum import Enum

class OperationType(str, Enum):
    LIST = "list"
    GET_BY_ID = "get_by_id"
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"

class TierLevel(str, Enum):
    TIER1 = "tier1"
    TIER2 = "tier2"

class APIEndpoint(BaseModel):
    path: str
    method: str
    operation_id: str
    description: Optional[str] = None
    parameters: Dict[str, any] = Field(default_factory=dict)
    
class ServiceOperation(BaseModel):
    endpoint: APIEndpoint
    intent_verbs: List[str] = Field(default_factory=list)
    intent_objects: List[str] = Field(default_factory=list)
    intent_indicators: List[str] = Field(default_factory=list)
    description: str
    confidence_score: float = Field(default=0.8)
    
class ServiceDefinition(BaseModel):
    service_name: str
    service_description: str
    business_context: str
    keywords: List[str] = Field(default_factory=list)
    synonyms: List[str] = Field(default_factory=list)
    tier1_operations: Dict[str, ServiceOperation] = Field(default_factory=dict)
    tier2_operations: Dict[str, ServiceOperation] = Field(default_factory=dict)
    created_at: str
    updated_at: str
    version: str = "1.0"
    
class ServiceRegistry(BaseModel):
    version: str
    services: Dict[str, ServiceDefinition] = Field(default_factory=dict)
    global_keywords: Dict[str, List[str]] = Field(default_factory=dict)  # Conflict tracking
    classification_rules: Dict[str, any] = Field(default_factory=dict)
    created_at: str
    updated_at: str
```

#### 1.2 API Specification Model (`api_specification.py`)

```python
class RawAPIEndpoint(BaseModel):
    path: str
    method: str
    operation_id: str
    description: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    parameters: List[Dict] = Field(default_factory=list)
    request_body: Optional[Dict] = None
    responses: Dict[str, Dict] = Field(default_factory=dict)
    
class APISpecification(BaseModel):
    source_file: str
    total_endpoints: int
    endpoints: List[RawAPIEndpoint]
    parsed_at: str
    classification_status: str = "pending"  # pending, processing, completed, failed
```

### 2. Core Engines (`engines/`)

#### 2.1 JSON Parser (`json_parser.py`)

**Purpose**: Parse uploaded API specification files and extract structured data

```python
class JSONParser:
    """
    Parses various API specification formats (OpenAPI 3.0, Swagger 2.0, custom formats)
    and converts them into standardized RawAPIEndpoint objects.
    """
    
    def __init__(self):
        self.supported_formats = ["openapi_3", "swagger_2", "infraon_custom"]
        
    async def parse_specification(self, file_content: str, format_hint: str = None) -> APISpecification:
        """
        Input: Raw JSON string from uploaded file
        Output: APISpecification object with parsed endpoints
        
        Process:
        1. Detect format (OpenAPI 3.0, Swagger 2.0, etc.)
        2. Extract all endpoint definitions
        3. Normalize to standard format
        4. Create APISpecification object
        """
        
    def _detect_format(self, content: Dict) -> str:
        """Auto-detect API specification format"""
        
    def _extract_endpoints_openapi(self, spec: Dict) -> List[RawAPIEndpoint]:
        """Extract endpoints from OpenAPI 3.0 format"""
        
    def _extract_endpoints_infraon(self, spec: Dict) -> List[RawAPIEndpoint]:
        """Extract endpoints from Infraon custom format"""
        
    def _normalize_endpoint(self, endpoint_data: Dict, format_type: str) -> RawAPIEndpoint:
        """Convert endpoint to standard format"""
```

#### 2.2 Service Classifier (`service_classifier.py`)

**Purpose**: Automatically group APIs into logical services and suggest classifications

```python
class ServiceClassifier:
    """
    Analyzes parsed API endpoints and automatically groups them into logical services
    based on URL patterns, operation patterns, and semantic similarity.
    """
    
    def __init__(self, nlp_model: str = "en_core_web_sm"):
        self.nlp = spacy.load(nlp_model)
        self.crud_patterns = self._load_crud_patterns()
        
    async def classify_services(self, api_spec: APISpecification) -> Dict[str, List[RawAPIEndpoint]]:
        """
        Input: APISpecification with raw endpoints
        Output: Dictionary mapping service names to endpoint lists
        
        Process:
        1. Group endpoints by URL path patterns
        2. Identify CRUD operation patterns
        3. Use semantic similarity for edge cases
        4. Suggest service names and descriptions
        """
        
    def _group_by_path_patterns(self, endpoints: List[RawAPIEndpoint]) -> Dict[str, List[RawAPIEndpoint]]:
        """Group endpoints by common URL path segments"""
        
    def _identify_crud_operations(self, endpoints: List[RawAPIEndpoint]) -> Dict[str, str]:
        """Map endpoints to CRUD operation types"""
        
    def _suggest_service_metadata(self, service_name: str, endpoints: List[RawAPIEndpoint]) -> Dict[str, any]:
        """Generate initial service description and keywords"""
        
    def _extract_business_context(self, endpoints: List[RawAPIEndpoint]) -> str:
        """Analyze endpoints to suggest business context"""
```

#### 2.3 Conflict Detector (`conflict_detector.py`)

**Purpose**: Detect and resolve keyword/synonym conflicts between services

```python
class ConflictDetector:
    """
    Identifies potential conflicts in keywords and synonyms between services
    and suggests resolutions to maintain classification accuracy.
    """
    
    def __init__(self, similarity_threshold: float = 0.8):
        self.similarity_threshold = similarity_threshold
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        
    async def detect_conflicts(self, registry: ServiceRegistry) -> List[ConflictReport]:
        """
        Input: Complete service registry
        Output: List of detected conflicts with suggested resolutions
        
        Conflict Types:
        1. Identical keywords across services
        2. High semantic similarity between synonyms
        3. Ambiguous intent verb mappings
        4. Overlapping business contexts
        """
        
    def _check_keyword_overlap(self, services: Dict[str, ServiceDefinition]) -> List[Dict]:
        """Detect exact keyword matches between services"""
        
    def _check_semantic_similarity(self, services: Dict[str, ServiceDefinition]) -> List[Dict]:
        """Find semantically similar keywords/synonyms"""
        
    def _suggest_resolution(self, conflict: Dict) -> Dict[str, str]:
        """Suggest ways to resolve detected conflicts"""
        
class ConflictReport(BaseModel):
    conflict_type: str
    affected_services: List[str]
    conflicting_terms: List[str]
    severity: str  # low, medium, high
    suggested_resolution: str
    auto_resolvable: bool
```

### 3. Interactive Agents (`agents/`)

#### 3.1 Definition Agent (`definition_agent.py`)

**Purpose**: Interactive agent that chats with users to define service metadata

```python
class ServiceDefinitionAgent:
    """
    Conversational agent that guides users through defining comprehensive
    service metadata including descriptions, keywords, and operation classifications.
    """
    
    def __init__(self, llm_service: LLMService):
        self.llm_service = llm_service
        self.conversation_memory = {}
        
    async def start_definition_session(self, service_name: str, initial_endpoints: List[RawAPIEndpoint]) -> str:
        """
        Start interactive session for defining a service
        
        Input: Service name and raw endpoints
        Output: Session ID for tracking conversation
        
        Conversation Flow:
        1. Present initial classification results
        2. Ask for service description refinement
        3. Collect keywords and synonyms
        4. Classify operations into Tier 1/2
        5. Validate intent mappings
        6. Review and confirm final definition
        """
        
    async def process_user_response(self, session_id: str, user_input: str) -> Dict[str, any]:
        """
        Process user response and continue conversation
        
        Output Format:
        {
            "response": "Agent's next question/comment",
            "current_step": "description/keywords/operations/review",
            "progress": 0.6,
            "data_collected": {...},
            "needs_user_input": true/false,
            "completion_status": "in_progress/completed"
        }
        """
        
    def _generate_service_questions(self, service_name: str, endpoints: List[RawAPIEndpoint]) -> List[str]:
        """Generate targeted questions about the service"""
        
    def _extract_keywords_from_response(self, user_response: str) -> List[str]:
        """Parse user response to extract keywords and synonyms"""
        
    def _classify_operations_interactively(self, endpoints: List[RawAPIEndpoint], user_preferences: Dict) -> Dict[str, any]:
        """Help user classify operations into tiers with explanations"""
```

#### 3.2 Testing Agent (`testing_agent.py`)

**Purpose**: Automated testing and accuracy validation agent with procedural API testing

```python
class TestingAgent:
    """
    Automated agent that generates test queries, validates classification accuracy,
    performs procedural API testing, and provides feedback on system performance.
    """
    
    def __init__(self, llm_service: LLMService, query_classifier: QueryClassifier, api_client: InfraonAPIClient):
        self.llm_service = llm_service
        self.query_classifier = query_classifier
        self.api_client = api_client
        self.procedural_test_results = {}
        
    async def generate_test_suite(self, registry: ServiceRegistry) -> TestSuite:
        """
        Generate comprehensive test queries for all services
        
        Test Categories:
        1. Basic CRUD operations
        2. Service identification accuracy
        3. Operation classification precision
        4. Edge cases and ambiguous queries
        5. Multi-service queries
        6. Procedural API validation
        """
        
    async def run_accuracy_tests(self, registry: ServiceRegistry, test_suite: TestSuite) -> TestResults:
        """
        Execute test suite and measure accuracy
        
        Metrics:
        - Service identification accuracy
        - Operation classification precision
        - Parameter extraction accuracy
        - Overall system confidence scores
        - API procedural test success rates
        """
        
    async def run_procedural_api_tests(self, service_name: str, service_def: ServiceDefinition) -> ProceduralTestResults:
        """
        Execute comprehensive procedural testing for Tier 1 APIs
        
        Test Flow for each service:
        1. CREATE: Test entity creation with various parameter combinations
        2. READ: Verify created entity can be retrieved (list + get_by_id)
        3. UPDATE: Modify entity with different field combinations
        4. DELETE: Remove entity and verify deletion
        5. VALIDATE: Confirm input/output schemas match documentation
        
        This validates:
        - Required vs optional parameters
        - Parameter data types and formats
        - Response schema structure
        - Error handling for invalid inputs
        - API consistency and reliability
        """
        
    async def _execute_create_read_delete_cycle(self, service_def: ServiceDefinition) -> CRDTestResult:
        """
        Execute Create-Read-Delete cycle for a service
        
        Process:
        1. Generate realistic test data based on service context
        2. CREATE: Call create API with test data
        3. READ: Retrieve created entity by ID and verify data integrity
        4. READ LIST: Confirm entity appears in list operations
        5. DELETE: Remove test entity
        6. VERIFY: Confirm entity no longer exists
        
        Returns detailed results including:
        - Actual input/output schemas observed
        - Parameter validation results
        - Error responses and handling
        - Performance metrics
        """
        
    async def _generate_test_entity_data(self, service_name: str, operation: ServiceOperation) -> Dict[str, any]:
        """
        Generate realistic test data for entity creation
        
        Uses service context and business logic to create meaningful test data:
        - business_rule: Creates a simple approval workflow rule
        - announcement: Creates a maintenance notification
        - user: Creates a test user account
        - incident: Creates a test service disruption
        """
        
    async def _validate_api_schemas(self, service_def: ServiceDefinition, test_results: Dict) -> SchemaValidationReport:
        """
        Compare actual API behavior with documented schemas
        
        Validates:
        1. Request schema accuracy (required/optional fields, data types)
        2. Response schema structure and field types
        3. Error response formats and HTTP status codes
        4. Parameter validation behavior
        5. Business logic constraints
        
        Updates service registry with validated schema information
        """
        
    async def analyze_failures(self, test_results: TestResults) -> List[ImprovementSuggestion]:
        """Analyze failed tests and suggest improvements"""
        
class TestSuite(BaseModel):
    total_tests: int
    test_categories: Dict[str, List[TestCase]]
    created_at: str
    
class TestCase(BaseModel):
    query: str
    expected_service: str
    expected_operation: str
    expected_tier: str
    expected_parameters: Dict[str, any]
    difficulty_level: str  # easy, medium, hard
    
class TestResults(BaseModel):
    total_tests: int
    passed: int
    failed: int
    accuracy_percentage: float
    detailed_results: List[TestResult]
    performance_metrics: Dict[str, float]
    procedural_test_summary: Dict[str, ProceduralTestResults]

class ProceduralTestResults(BaseModel):
    service_name: str
    total_tier1_apis: int
    successful_crd_cycles: int
    failed_crd_cycles: int
    schema_validation_accuracy: float
    discovered_schemas: Dict[str, Dict[str, any]]  # operation -> {input_schema, output_schema}
    parameter_validation_results: Dict[str, ParameterValidationResult]
    error_handling_analysis: Dict[str, List[str]]
    performance_metrics: Dict[str, float]
    test_entity_cleanup_status: str  # "completed", "partial", "failed"

class CRDTestResult(BaseModel):
    service_name: str
    test_cycle_id: str
    create_result: APITestResult
    read_result: APITestResult
    read_list_result: APITestResult
    update_result: Optional[APITestResult] = None  # If update API exists
    delete_result: APITestResult
    verification_result: APITestResult
    overall_success: bool
    discovered_schemas: Dict[str, Dict]
    test_entity_data: Dict[str, any]
    cleanup_completed: bool

class APITestResult(BaseModel):
    operation: str
    endpoint: str
    method: str
    request_data: Dict[str, any]
    response_data: Dict[str, any]
    status_code: int
    success: bool
    response_time_ms: float
    discovered_schema: Dict[str, any]
    validation_errors: List[str]
    error_message: Optional[str] = None

class ParameterValidationResult(BaseModel):
    operation: str
    required_parameters: List[str]
    optional_parameters: List[str]
    parameter_types: Dict[str, str]
    validation_rules: Dict[str, List[str]]
    default_values: Dict[str, any]
    business_constraints: List[str]

class SchemaValidationReport(BaseModel):
    service_name: str
    validation_timestamp: str
    input_schema_accuracy: float
    output_schema_accuracy: float
    discrepancies: List[SchemaDiscrepancy]
    suggested_corrections: List[str]
    confidence_score: float

class SchemaDiscrepancy(BaseModel):
    operation: str
    discrepancy_type: str  # "missing_field", "wrong_type", "incorrect_requirement"
    expected: str
    actual: str
    impact_level: str  # "low", "medium", "high"
```

### 4. Storage Management (`storage/`)

#### 4.1 Registry Manager (`registry_manager.py`)

**Purpose**: CRUD operations for service registry with persistence

```python
class RegistryManager:
    """
    Manages service registry storage, versioning, and CRUD operations
    with support for atomic updates and rollback capabilities.
    """
    
    def __init__(self, storage_path: str = "processed_data/service_registry/"):
        self.storage_path = storage_path
        self.current_registry: Optional[ServiceRegistry] = None
        
    async def load_registry(self, version: str = "latest") -> ServiceRegistry:
        """Load service registry from storage"""
        
    async def save_registry(self, registry: ServiceRegistry, version: str = None) -> str:
        """Save registry with automatic versioning"""
        
    async def add_service(self, service_name: str, service_def: ServiceDefinition) -> bool:
        """Add new service to registry with conflict checking"""
        
    async def update_service(self, service_name: str, updates: Dict[str, any]) -> bool:
        """Update existing service definition"""
        
    async def delete_service(self, service_name: str) -> bool:
        """Remove service from registry"""
        
    async def merge_services(self, service_names: List[str], new_service_name: str, merge_strategy: str) -> bool:
        """Combine multiple services into one"""
        
    async def split_service(self, service_name: str, split_config: Dict[str, List[str]]) -> bool:
        """Split one service into multiple services"""
        
    def _validate_registry_integrity(self, registry: ServiceRegistry) -> List[str]:
        """Validate registry for consistency and conflicts"""
        
    def _create_backup(self, registry: ServiceRegistry) -> str:
        """Create registry backup before major changes"""
```

### 5. FastAPI Endpoints (`api/`)

#### 5.1 Upload API (`upload.py`)

```python
# Endpoint specifications with input/output schemas

POST /api/v1/manoman/upload
"""
Upload API specification file for processing

Input:
- Multipart form with JSON file
- Optional format hint

Output:
{
    "upload_id": "uuid",
    "filename": "infraon-api.json",
    "total_endpoints": 1288,
    "parsing_status": "completed",
    "classification_status": "pending",
    "estimated_services": 85,
    "next_step": "classification"
}
"""

GET /api/v1/manoman/upload/{upload_id}/status
"""
Check upload processing status

Output:
{
    "upload_id": "uuid",
    "status": "processing",
    "progress": 0.75,
    "current_step": "service_classification",
    "services_identified": 67,
    "services_remaining": 18,
    "estimated_completion": "2024-01-15T10:30:00Z"
}
"""
```

#### 5.2 Classification API (`classification.py`)

```python
GET /api/v1/manoman/classification/{upload_id}/services
"""
Get auto-classified services

Output:
{
    "upload_id": "uuid",
    "total_services": 83,
    "services": [
        {
            "service_name": "business_rule",
            "endpoint_count": 12,
            "suggested_description": "Business rule management and automation",
            "tier1_operations": 5,
            "tier2_operations": 7,
            "confidence_score": 0.85,
            "needs_review": false
        }
    ],
    "classification_summary": {
        "high_confidence": 65,
        "medium_confidence": 15,
        "needs_review": 3
    }
}
"""

POST /api/v1/manoman/classification/{upload_id}/services/merge
"""
Merge multiple services into one

Input:
{
    "source_services": ["service1", "service2"],
    "new_service_name": "combined_service",
    "merge_strategy": "combine_all"  # combine_all, prefer_first, custom
}
"""

POST /api/v1/manoman/classification/{upload_id}/services/split
"""
Split service into multiple services

Input:
{
    "source_service": "large_service",
    "split_config": {
        "service1": ["endpoint1", "endpoint2"],
        "service2": ["endpoint3", "endpoint4"]
    }
}
"""
```

#### 5.3 Definition API (`definition.py`)

```python
POST /api/v1/manoman/definition/start-session
"""
Start interactive service definition session

Input:
{
    "service_name": "business_rule",
    "upload_id": "uuid"
}

Output:
{
    "session_id": "session_uuid",
    "service_name": "business_rule",
    "initial_analysis": {
        "suggested_description": "...",
        "suggested_keywords": [...],
        "endpoint_summary": {...}
    },
    "first_question": "I've analyzed the business_rule service with 12 endpoints. The service appears to handle automated business logic and rule management. Would you like to refine this description or add more context about what this service does in your organization?"
}
"""

POST /api/v1/manoman/definition/session/{session_id}/respond
"""
Continue definition conversation

Input:
{
    "user_response": "Yes, this service also handles workflow automation and conditional logic for our approval processes."
}

Output:
{
    "response": "Great! I'll add workflow automation and approval processes to the context. Now, let's work on keywords. I suggest: 'rule', 'policy', 'automation', 'workflow', 'condition'. What other terms might users use when referring to this service?",
    "current_step": "keywords",
    "progress": 0.4,
    "data_collected": {
        "description": "Business rule management, automation, workflow automation and conditional logic for approval processes",
        "keywords": ["rule", "policy", "automation", "workflow", "condition"]
    },
    "needs_user_input": true
}
"""

GET /api/v1/manoman/definition/session/{session_id}/preview
"""
Preview the current service definition

Output: Complete ServiceDefinition object as it currently stands
"""

POST /api/v1/manoman/definition/session/{session_id}/complete
"""
Finalize service definition and add to registry
"""
```

#### 5.4 Validation API (`validation.py`)

```python
POST /api/v1/manoman/validation/generate-tests
"""
Generate test suite for current registry

Output:
{
    "test_suite_id": "uuid",
    "total_tests": 450,
    "test_categories": {
        "basic_crud": 200,
        "service_identification": 150,
        "operation_classification": 75,
        "edge_cases": 25
    },
    "estimated_duration": "5 minutes"
}
"""

POST /api/v1/manoman/validation/run-tests/{test_suite_id}
"""
Execute test suite

Output:
{
    "test_run_id": "uuid",
    "status": "running",
    "progress": 0.0,
    "tests_completed": 0,
    "tests_total": 450
}
"""

GET /api/v1/manoman/validation/results/{test_run_id}
"""
Get test results

Output:
{
    "test_run_id": "uuid",
    "status": "completed",
    "overall_accuracy": 0.89,
    "results_by_category": {
        "basic_crud": {"accuracy": 0.95, "passed": 190, "failed": 10},
        "service_identification": {"accuracy": 0.87, "passed": 130, "failed": 20}
    },
    "failed_tests": [...],
    "improvement_suggestions": [...],
    "procedural_test_summary": {
        "total_services_tested": 83,
        "successful_crd_cycles": 78,
        "schema_discovery_accuracy": 0.92,
        "cleanup_success_rate": 0.98
    }
}
"""

POST /api/v1/manoman/validation/run-procedural-tests
"""
Execute procedural API testing for all Tier 1 operations

Input:
{
    "services": ["business_rule", "announcement"],  # Optional: specific services
    "test_config": {
        "include_update_tests": true,
        "cleanup_test_entities": true,
        "validate_schemas": true,
        "generate_test_data_variations": 3
    }
}

Output:
{
    "procedural_test_id": "uuid",
    "status": "running",
    "services_to_test": 83,
    "estimated_duration": "15 minutes",
    "current_service": null,
    "progress": 0.0
}
"""

GET /api/v1/manoman/validation/procedural-results/{procedural_test_id}
"""
Get procedural testing results

Output:
{
    "procedural_test_id": "uuid",
    "status": "completed",
    "overall_success_rate": 0.94,
    "services_tested": 83,
    "successful_services": 78,
    "failed_services": 5,
    "results_by_service": {
        "business_rule": {
            "crd_cycle_success": true,
            "schema_validation_accuracy": 0.96,
            "discovered_schemas": {
                "create": {
                    "input_schema": {
                        "required": ["name", "description", "conditions"],
                        "optional": ["priority", "enabled"],
                        "types": {"name": "string", "description": "string", "conditions": "array"}
                    },
                    "output_schema": {
                        "fields": ["id", "name", "description", "created_at", "status"],
                        "types": {"id": "integer", "created_at": "datetime", "status": "string"}
                    }
                },
                "read": {...},
                "delete": {...}
            },
            "parameter_validation": {
                "required_fields_verified": ["name", "description"],
                "optional_fields_verified": ["priority"],
                "type_validation_accuracy": 1.0,
                "business_constraints": ["name must be unique", "conditions cannot be empty"]
            },
            "test_entity_cleanup": "completed",
            "performance_metrics": {
                "avg_create_time_ms": 245,
                "avg_read_time_ms": 89,
                "avg_delete_time_ms": 156
            }
        }
    },
    "schema_discrepancies": [
        {
            "service": "user_management",
            "operation": "create",
            "issue": "Documentation shows 'email' as optional, but API requires it",
            "impact": "high",
            "suggested_fix": "Update registry to mark email as required"
        }
    ],
    "registry_updates_suggested": 12,
    "cleanup_summary": {
        "total_test_entities_created": 249,
        "successfully_cleaned": 244,
        "manual_cleanup_required": 5
    }
}
"""

POST /api/v1/manoman/validation/update-registry-from-tests
"""
Apply discovered schemas and validations to service registry

Input:
{
    "procedural_test_id": "uuid",
    "apply_schema_updates": true,
    "apply_parameter_validations": true,
    "auto_resolve_discrepancies": false,
    "services_to_update": ["business_rule", "announcement"]  # Optional
}

Output:
{
    "update_job_id": "uuid",
    "services_to_update": 15,
    "schema_updates": 47,
    "parameter_updates": 23,
    "conflicts_requiring_review": 3,
    "status": "processing"
}
"""

GET /api/v1/manoman/validation/cleanup-test-entities/{procedural_test_id}
"""
Manual cleanup of test entities that weren't automatically removed

Output:
{
    "cleanup_status": "completed",
    "entities_cleaned": 5,
    "cleanup_failures": 0,
    "services_affected": ["user_management", "asset_tracking"]
}
"""
```

---

## Implementation Phases

### Phase 1: Foundation (Week 1)
1. Create directory structure and data models
2. Implement JSON parser for API specifications
3. Build basic service classifier
4. Set up registry storage system

### Phase 2: Auto-Classification (Week 2)
1. Implement advanced service grouping algorithms
2. Build conflict detection system
3. Create initial FastAPI endpoints for upload and classification
4. Add service merge/split functionality

### Phase 3: Interactive Definition (Week 3)
1. Implement definition agent with conversation management
2. Build interactive API endpoints
3. Add session management and progress tracking
4. Create service definition preview and finalization

### Phase 4: Validation and Testing (Week 4)
1. Implement testing agent and test generation
2. Build accuracy validation system
3. **Implement procedural API testing (Create-Read-Delete cycles)**
4. **Add schema discovery and validation framework**
5. Add performance benchmarking
6. Create improvement suggestion engine

### Phase 5: Schema Validation and Registry Enhancement (Week 5)
1. **Build comprehensive procedural testing for all Tier 1 APIs**
2. **Implement automatic schema discovery and registry updates**
3. **Add test entity cleanup and management system**
4. **Create schema discrepancy detection and resolution**
5. Integrate with existing AugmentAgent architecture

### Phase 6: Production Integration (Week 6)
1. Add registry hot-reloading for production systems
2. **Implement Tier 2 API procedural testing framework**
3. Implement monitoring and logging
4. Create comprehensive documentation
5. **Add automated registry validation pipelines**

---

## Success Metrics

1. **Upload Processing**: Handle 1000+ endpoint API specs in <30 seconds
2. **Auto-Classification**: Achieve >85% accuracy in initial service grouping  
3. **Conflict Detection**: Identify 100% of exact keyword conflicts
4. **Interactive Definition**: Complete service definition in <10 minutes per service
5. **Test Validation**: Generate and execute comprehensive test suites in <5 minutes
6. **Procedural API Testing**: Successfully execute Create-Read-Delete cycles for >90% of Tier 1 APIs
7. **Schema Discovery**: Achieve >95% accuracy in discovered vs actual API schemas
8. **Test Entity Cleanup**: Automatically clean up >98% of test entities created during validation
9. **Registry Enhancement**: Update service registry with validated schemas and parameters automatically
10. **System Integration**: Zero downtime registry updates in production

---

## Risk Mitigation

1. **Data Loss Prevention**: Automatic backups before major registry changes
2. **Rollback Capability**: Full version control with instant rollback
3. **Validation Gates**: Multi-stage validation before registry updates
4. **Conflict Resolution**: Automated and manual conflict resolution paths
5. **Performance Monitoring**: Real-time monitoring of classification accuracy

This comprehensive system provides a robust foundation for managing service registries at scale while maintaining high accuracy and user control over the classification process.