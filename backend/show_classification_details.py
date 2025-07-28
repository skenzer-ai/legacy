"""
Script to show detailed classification results for Infraon API
"""

import asyncio
import json
from pathlib import Path
from typing import Dict, List
from collections import defaultdict

# Add backend to sys.path
import sys
sys.path.append(str(Path(__file__).resolve().parent))

from app.core.manoman.engines.json_parser import JSONParser
from app.core.manoman.engines.service_classifier import ServiceClassifier
from app.core.manoman.models.api_specification import RawAPIEndpoint


async def show_classification_details():
    """Parse Infraon API and show detailed classification results"""
    
    # Initialize components
    parser = JSONParser()
    classifier = ServiceClassifier()
    
    # Load Infraon OpenAPI spec
    yaml_path = Path(__file__).resolve().parents[1] / "user_docs" / "infraon-openapi.yaml"
    print(f"Loading API specification from: {yaml_path}\n")
    
    with open(yaml_path, 'r', encoding='utf-8') as f:
        file_content = f.read()
    
    # Parse specification
    spec = await parser.parse_specification(file_content, yaml_path.name, "openapi_3")
    print(f"Total endpoints parsed: {len(spec.endpoints)}")
    print(f"Total tags found: {len(spec.get_unique_tags())}\n")
    
    # Classify services
    print("Running classification...\n")
    service_groups = await classifier.classify_services(spec)
    
    print(f"==========================================")
    print(f"CLASSIFICATION RESULTS")
    print(f"==========================================")
    print(f"Total services created: {len(service_groups)}")
    print(f"==========================================\n")
    
    # Sort services by number of endpoints (descending)
    sorted_services = sorted(
        service_groups.items(), 
        key=lambda x: len(x[1].endpoints), 
        reverse=True
    )
    
    # Show each service in detail
    for idx, (service_name, service_group) in enumerate(sorted_services, 1):
        print(f"\n{'='*80}")
        print(f"SERVICE #{idx}: {service_name.upper()}")
        print(f"{'='*80}")
        print(f"Description: {service_group.suggested_description}")
        print(f"Base Path: {service_group.base_path}")
        print(f"Confidence Score: {service_group.confidence_score:.2f}")
        print(f"Keywords: {', '.join(service_group.keywords[:10])}")
        if service_group.synonyms:
            print(f"Synonyms: {', '.join(service_group.synonyms)}")
        if hasattr(service_group, 'tags') and service_group.tags:
            print(f"API Tags: {', '.join(service_group.tags)}")
        
        print(f"\nTotal Endpoints: {len(service_group.endpoints)}")
        print(f"├── Tier 1 (CRUD): {len(service_group.tier1_operations)}")
        print(f"└── Tier 2 (Specialized): {len(service_group.tier2_operations)}")
        
        # Show Tier 1 operations
        if service_group.tier1_operations:
            print(f"\n📌 TIER 1 OPERATIONS (Basic CRUD):")
            print(f"{'─'*76}")
            
            # Group by CRUD type
            crud_ops = defaultdict(list)
            for op in service_group.tier1_operations:
                method = op.method.value if hasattr(op.method, 'value') else str(op.method)
                
                # Determine CRUD type
                if method == "GET" and "{" not in op.path:
                    crud_type = "LIST"
                elif method == "GET" and "{" in op.path:
                    crud_type = "GET BY ID"
                elif method == "POST":
                    crud_type = "CREATE"
                elif method in ["PUT", "PATCH"]:
                    crud_type = "UPDATE"
                elif method == "DELETE":
                    crud_type = "DELETE"
                else:
                    crud_type = method
                
                crud_ops[crud_type].append(op)
            
            # Display in CRUD order
            crud_order = ["LIST", "GET BY ID", "CREATE", "UPDATE", "DELETE"]
            for crud_type in crud_order:
                if crud_type in crud_ops:
                    for op in crud_ops[crud_type]:
                        method = op.method.value if hasattr(op.method, 'value') else str(op.method)
                        print(f"  {crud_type:<12} {method:<7} {op.path}")
                        if op.summary:
                            print(f"  {'':12} {'':7} └─ {op.summary}")
        
        # Show Tier 2 operations
        if service_group.tier2_operations:
            print(f"\n📌 TIER 2 OPERATIONS (Specialized):")
            print(f"{'─'*76}")
            
            # Sort by path for better readability
            sorted_tier2 = sorted(service_group.tier2_operations, key=lambda x: x.path)
            
            for op in sorted_tier2:
                method = op.method.value if hasattr(op.method, 'value') else str(op.method)
                # Extract operation type from path
                path_parts = op.path.strip('/').split('/')
                operation_hint = path_parts[-1] if path_parts else ""
                
                print(f"  {method:<7} {op.path}")
                if op.summary:
                    print(f"  {'':7} └─ {op.summary}")
                elif operation_hint and not operation_hint.startswith('{'):
                    print(f"  {'':7} └─ Operation: {operation_hint.replace('-', ' ').replace('_', ' ')}")
    
    # Summary statistics
    print(f"\n\n{'='*80}")
    print(f"SUMMARY STATISTICS")
    print(f"{'='*80}")
    
    total_endpoints = sum(len(sg.endpoints) for sg in service_groups.values())
    total_tier1 = sum(len(sg.tier1_operations) for sg in service_groups.values())
    total_tier2 = sum(len(sg.tier2_operations) for sg in service_groups.values())
    
    print(f"Total Services: {len(service_groups)}")
    print(f"Total Endpoints Classified: {total_endpoints}")
    print(f"├── Tier 1 Operations: {total_tier1} ({total_tier1/total_endpoints*100:.1f}%)")
    print(f"└── Tier 2 Operations: {total_tier2} ({total_tier2/total_endpoints*100:.1f}%)")
    
    # Services by size
    print(f"\nService Size Distribution:")
    size_buckets = defaultdict(int)
    for sg in service_groups.values():
        size = len(sg.endpoints)
        if size == 1:
            size_buckets["1 endpoint"] += 1
        elif 2 <= size <= 5:
            size_buckets["2-5 endpoints"] += 1
        elif 6 <= size <= 10:
            size_buckets["6-10 endpoints"] += 1
        elif 11 <= size <= 20:
            size_buckets["11-20 endpoints"] += 1
        else:
            size_buckets["20+ endpoints"] += 1
    
    for bucket, count in sorted(size_buckets.items()):
        print(f"  {bucket}: {count} services")
    
    # Top 10 largest services
    print(f"\nTop 10 Largest Services:")
    for i, (name, sg) in enumerate(sorted_services[:10], 1):
        print(f"  {i:2d}. {name:<30} {len(sg.endpoints):3d} endpoints")
    
    # Services with complete CRUD
    complete_crud = []
    for name, sg in service_groups.items():
        if len(sg.tier1_operations) >= 5:  # All 5 CRUD operations
            complete_crud.append(name)
    
    print(f"\nServices with Complete CRUD Set ({len(complete_crud)} total):")
    for i, name in enumerate(sorted(complete_crud)[:20], 1):  # Show first 20
        print(f"  {i:2d}. {name}")
    if len(complete_crud) > 20:
        print(f"  ... and {len(complete_crud) - 20} more")


if __name__ == "__main__":
    asyncio.run(show_classification_details())