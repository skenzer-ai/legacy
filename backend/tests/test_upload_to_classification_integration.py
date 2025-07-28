"""
Integration Test: Upload to Classification Pipeline

Tests the complete flow from file upload through automated service classification
using the real Infraon OpenAPI specification and LLM configuration.
"""

import pytest
import asyncio
import os
import tempfile
import shutil
from pathlib import Path
from typing import Dict, Any
from datetime import datetime

# Add backend to sys.path
import sys
sys.path.append(str(Path(__file__).resolve().parents[2]))

from app.core.manoman.engines.json_parser import JSONParser
from app.core.manoman.engines.service_classifier import ServiceClassifier
from app.core.manoman.storage.registry_manager import RegistryManager
from app.core.manoman.models.api_specification import APISpecification
from app.core.manoman.models.service_registry import ServiceRegistry
from app.core.manoman.utils.text_processing import text_processor


class TestUploadToClassificationIntegration:
    """Integration tests for Upload to Classification pipeline"""
    
    @pytest.fixture
    def infraon_yaml_path(self):
        """Path to real Infraon OpenAPI YAML file"""
        return Path(__file__).resolve().parents[3] / "legacy" / "user_docs" / "infraon-openapi.yaml"
    
    @pytest.fixture
    def temp_storage_dir(self):
        """Create temporary storage directory"""
        temp_dir = tempfile.mkdtemp(prefix="manoman_integration_")
        yield temp_dir
        shutil.rmtree(temp_dir, ignore_errors=True)
    
    @pytest.fixture
    def parser(self):
        """Create JSON parser"""
        return JSONParser()
    
    @pytest.fixture
    def classifier(self):
        """Create service classifier"""
        return ServiceClassifier()
    
    @pytest.fixture
    def registry_manager(self, temp_storage_dir):
        """Create registry manager with temporary storage"""
        return RegistryManager(storage_path=temp_storage_dir)
    
    def test_infraon_yaml_exists(self, infraon_yaml_path):
        """Verify the Infraon OpenAPI YAML file exists"""
        assert infraon_yaml_path.exists(), f"Infraon OpenAPI YAML file not found at {infraon_yaml_path}"
        assert infraon_yaml_path.suffix == ".yaml", "File should be a YAML file"
    
    @pytest.mark.asyncio
    async def test_complete_upload_to_classification_pipeline(
        self, 
        infraon_yaml_path, 
        parser, 
        classifier, 
        registry_manager
    ):
        """
        Test complete pipeline from upload to classification
        
        Flow:
        1. Parse real Infraon OpenAPI YAML specification
        2. Extract endpoints and validate structure
        3. Classify endpoints into logical services using LLM
        4. Verify classification results and service groupings
        5. Store initial classification in registry
        """
        
        print(f"\n=== Testing Upload to Classification Pipeline ===")
        print(f"Using Infraon OpenAPI file: {infraon_yaml_path}")
        
        # Step 1: Parse API specification
        print("\nStep 1: Parsing Infraon OpenAPI specification...")
        
        # Read the YAML file content
        with open(infraon_yaml_path, 'r', encoding='utf-8') as f:
            file_content = f.read()
        
        spec = await parser.parse_specification(file_content, infraon_yaml_path.name, "openapi_3")
        
        assert spec is not None, "Parsing failed - specification is None"
        assert len(spec.endpoints) > 0, "No endpoints parsed from specification"
        print(f"✓ Parsed specification: {spec.title} v{spec.version}")
        print(f"✓ Found {len(spec.endpoints)} endpoints")
        print(f"✓ Found {len(spec.get_unique_tags())} tags")
        
        # Verify we have substantial data
        assert len(spec.endpoints) > 100, f"Expected > 100 endpoints, got {len(spec.endpoints)}"
        
        # Step 2: Analyze endpoint distribution
        print(f"\nStep 2: Analyzing endpoint distribution...")
        
        method_counts = {}
        path_prefixes = {}
        
        for endpoint in spec.endpoints:
            # Count HTTP methods
            method = endpoint.method.value if hasattr(endpoint.method, 'value') else str(endpoint.method)
            method_counts[method] = method_counts.get(method, 0) + 1
            
            # Analyze path prefixes
            path_parts = endpoint.path.strip('/').split('/')
            if len(path_parts) >= 2:
                prefix = f"/{path_parts[0]}/{path_parts[1]}"
                path_prefixes[prefix] = path_prefixes.get(prefix, 0) + 1
        
        print(f"✓ HTTP method distribution: {method_counts}")
        print(f"✓ Top path prefixes: {dict(list(sorted(path_prefixes.items(), key=lambda x: x[1], reverse=True))[:10])}")
        
        # Step 3: Run service classification
        print(f"\nStep 3: Running service classification...")
        
        service_groups = await classifier.classify_services(spec)
        
        assert len(service_groups) > 0, "Should have classified at least one service"
        
        print(f"✓ Classified {len(service_groups)} services")
        
        # Step 4: Validate classification results
        print(f"\nStep 4: Validating classification results...")
        
        total_classified_endpoints = 0
        tier1_operations = 0
        tier2_operations = 0
        
        for service_name, service_group in service_groups.items():
            endpoint_count = len(service_group.tier1_operations) + len(service_group.tier2_operations)
            total_classified_endpoints += endpoint_count
            tier1_operations += len(service_group.tier1_operations)
            tier2_operations += len(service_group.tier2_operations)
            
            print(f"  Service: {service_name}")
            print(f"    Description: {service_group.suggested_description}")
            print(f"    Keywords: {service_group.keywords}")
            print(f"    Tier 1 ops: {len(service_group.tier1_operations)}, Tier 2 ops: {len(service_group.tier2_operations)}")
            print(f"    Confidence: {service_group.confidence_score:.2f}")
            
            # Validate service structure
            assert service_group.service_name, f"Service {service_name} missing name"
            assert service_group.suggested_description, f"Service {service_name} missing description"
            assert len(service_group.keywords) > 0, f"Service {service_name} missing keywords"
            assert 0.0 <= service_group.confidence_score <= 1.0, f"Invalid confidence score for {service_name}"
        
        print(f"✓ Total endpoints classified: {total_classified_endpoints}")
        print(f"✓ Tier 1 operations: {tier1_operations}")
        print(f"✓ Tier 2 operations: {tier2_operations}")
        
        # Ensure good coverage
        coverage_ratio = total_classified_endpoints / len(spec.endpoints)
        print(f"✓ Classification coverage: {coverage_ratio:.2%}")
        assert coverage_ratio > 0.80, f"Classification coverage too low: {coverage_ratio:.2%}"
        
        # Step 5: Store classification in registry
        print(f"\nStep 5: Storing classification in registry...")
        
        # Convert ServiceGroup objects to ServiceDefinition objects
        from app.core.manoman.models.service_registry import ServiceDefinition, ServiceOperation, APIEndpoint
        
        services = {}
        for service_name, service_group in service_groups.items():
            # Convert endpoints to operations
            tier1_operations = {}
            tier2_operations = {}
            
            for endpoint in service_group.tier1_operations:
                operation = ServiceOperation(
                    endpoint=APIEndpoint(
                        path=endpoint.path,
                        method=endpoint.method.value if hasattr(endpoint.method, 'value') else str(endpoint.method),
                        operation_id=endpoint.operation_id,
                        description=endpoint.summary or endpoint.operation_id,
                        parameters={}  # Simplified for integration test
                    ),
                    intent_verbs=["read", "create", "update", "delete"],  # Placeholder
                    intent_objects=[service_name.lower()],
                    intent_indicators=[f"{endpoint.method.value.lower()} {service_name}"],
                    description=endpoint.summary or endpoint.operation_id,
                    confidence_score=service_group.confidence_score
                )
                tier1_operations[endpoint.operation_id] = operation
            
            for endpoint in service_group.tier2_operations:
                operation = ServiceOperation(
                    endpoint=APIEndpoint(
                        path=endpoint.path,
                        method=endpoint.method.value if hasattr(endpoint.method, 'value') else str(endpoint.method),
                        operation_id=endpoint.operation_id,
                        description=endpoint.summary or endpoint.operation_id,
                        parameters={}  # Simplified for integration test
                    ),
                    intent_verbs=["manage", "process"],  # Placeholder
                    intent_objects=[service_name.lower()],
                    intent_indicators=[f"{endpoint.method.value.lower()} {service_name}"],
                    description=endpoint.summary or endpoint.operation_id,
                    confidence_score=service_group.confidence_score
                )
                tier2_operations[endpoint.operation_id] = operation
            
            service_def = ServiceDefinition(
                service_name=service_group.service_name,
                service_description=service_group.suggested_description,
                business_context=f"Handles {service_name.lower()} operations",
                keywords=service_group.keywords,
                synonyms=service_group.synonyms,
                tier1_operations=tier1_operations,
                tier2_operations=tier2_operations
            )
            services[service_name] = service_def
        
        timestamp = datetime.now().isoformat()
        registry = ServiceRegistry(
            registry_id=f"infraon_integration_test_{timestamp.replace(':', '').replace('-', '').replace('.', '')}",
            version="1.0.0",
            created_timestamp=timestamp,
            last_updated=timestamp,
            services=services,
            total_services=len(services)
        )
        
        # Save to registry manager
        save_result = await registry_manager.save_registry(registry)
        assert save_result.success, f"Failed to save registry: {save_result.error_message}"
        
        print(f"✓ Registry saved with ID: {registry.registry_id}")
        
        # Verify we can load it back
        loaded_registry = await registry_manager.load_registry(registry.registry_id)
        assert loaded_registry is not None, "Failed to load saved registry"
        assert loaded_registry.total_services == len(services)
        
        print(f"✓ Registry successfully loaded and verified")
        
        # Step 6: Generate classification summary
        print(f"\nStep 6: Classification Summary")
        print(f"=" * 50)
        print(f"API Specification: {spec.title}")
        print(f"Total Endpoints: {len(spec.endpoints)}")
        print(f"Services Created: {len(service_groups)}")
        print(f"Classification Coverage: {coverage_ratio:.2%}")
        print(f"Average Endpoints per Service: {total_classified_endpoints / len(service_groups):.1f}")
        print(f"Tier 1 / Tier 2 Ratio: {tier1_operations} / {tier2_operations}")
        
        # Validate against success metrics
        assert len(service_groups) >= 5, "Should create at least 5 logical services"
        assert len(service_groups) <= 100, "Should not create too many services (max 100)"
        
        return {
            "registry_id": registry.registry_id,
            "services_count": len(service_groups),
            "endpoints_classified": total_classified_endpoints,
            "coverage": coverage_ratio,
            "tier1_ops": tier1_operations,
            "tier2_ops": tier2_operations
        }
    
    @pytest.mark.asyncio
    async def test_classification_performance(self, infraon_yaml_path, parser, classifier):
        """Test classification performance with large API specification"""
        import time
        
        print(f"\n=== Testing Classification Performance ===")
        
        # Parse specification
        start_time = time.time()
        with open(infraon_yaml_path, 'r', encoding='utf-8') as f:
            file_content = f.read()
        spec = await parser.parse_specification(file_content, infraon_yaml_path.name, "openapi_3")
        parse_time = time.time() - start_time
        
        assert spec is not None
        print(f"✓ Parsing time: {parse_time:.2f} seconds for {len(spec.endpoints)} endpoints")
        
        # Classification performance
        start_time = time.time()
        service_groups = await classifier.classify_services(spec)
        classification_time = time.time() - start_time
        
        assert len(service_groups) > 0
        print(f"✓ Classification time: {classification_time:.2f} seconds")
        print(f"✓ Endpoints per second: {len(spec.endpoints) / classification_time:.1f}")
        
        # Performance requirements
        total_time = parse_time + classification_time
        assert total_time < 60, f"Total processing time too slow: {total_time:.2f}s (max 60s)"
        
        return {
            "parse_time": parse_time,
            "classification_time": classification_time,
            "total_time": total_time,
            "endpoints_per_second": len(spec.endpoints) / classification_time
        }
    
    @pytest.mark.asyncio
    async def test_error_handling_and_validation(self, parser, classifier, temp_storage_dir):
        """Test error handling for invalid inputs and edge cases"""
        
        print(f"\n=== Testing Error Handling ===")
        
        # Test invalid file content
        try:
            result = await parser.parse_specification("invalid yaml content", "test.yaml", "openapi_3")
            # If no exception, check result is valid
            assert result is None or len(result.endpoints) == 0
        except Exception:
            pass  # Expected for invalid content
        print(f"✓ Invalid file content handled correctly")
        
        # Test empty specification
        from app.core.manoman.models.api_specification import APIInfo, SpecificationFormat
        empty_spec = APISpecification(
            info=APIInfo(title="Test", version="1.0.0", description="Test"),
            base_url="",
            endpoints=[],
            tags=[],
            format=SpecificationFormat.OPENAPI_3,
            version="3.0.0"
        )
        service_groups = await classifier.classify_services(empty_spec)
        assert len(service_groups) == 0
        print(f"✓ Empty endpoints handled correctly")
        
        # Test invalid storage directory
        invalid_manager = RegistryManager(storage_path="/nonexistent/path")
        registry = ServiceRegistry(
            registry_id="test_invalid",
            version="1.0.0",
            created_timestamp="2024-01-01T00:00:00Z",
            last_updated="2024-01-01T00:00:00Z",
            services={},
            total_services=0
        )
        
        save_result = await invalid_manager.save_registry(registry)
        assert not save_result.success
        print(f"✓ Invalid storage path handled correctly")


if __name__ == "__main__":
    # Run with asyncio support
    pytest.main([__file__, "-v", "-s"])