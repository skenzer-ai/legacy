"""
Test script to verify the improved classification via uvicorn API
"""

import asyncio
import aiohttp
import json
from pathlib import Path


async def test_classification_api():
    """Test the classification API with real Infraon OpenAPI YAML"""
    
    base_url = "http://localhost:8000/api/v1/manoman"
    yaml_path = Path(__file__).resolve().parents[1] / "user_docs" / "infraon-openapi.yaml"
    
    async with aiohttp.ClientSession() as session:
        # Step 1: Upload the YAML file
        print("Step 1: Uploading Infraon OpenAPI YAML file...")
        
        with open(yaml_path, 'rb') as f:
            data = aiohttp.FormData()
            data.add_field('file', f, filename='infraon-openapi.yaml', content_type='application/x-yaml')
            
            async with session.post(f"{base_url}/upload", data=data) as resp:
                if resp.status != 200:
                    print(f"Upload failed: {resp.status}")
                    print(await resp.text())
                    return
                
                upload_response = await resp.json()
                upload_id = upload_response["upload_id"]
                print(f"✓ Upload successful. Upload ID: {upload_id}")
        
        # Step 2: Wait for upload to complete
        print("\nStep 2: Checking upload status...")
        for i in range(10):  # Wait up to 10 seconds
            async with session.get(f"{base_url}/upload/{upload_id}/status") as resp:
                status_data = await resp.json()
                if status_data["status"] == "completed":
                    print(f"✓ Upload completed. Total endpoints: {status_data.get('total_endpoints', 'Unknown')}")
                    break
                elif status_data["status"] == "failed":
                    print(f"✗ Upload failed: {status_data.get('error_message', 'Unknown error')}")
                    return
                else:
                    print(f"  Status: {status_data['status']}...")
                    await asyncio.sleep(1)
        
        # Step 3: Get classification results
        print("\nStep 3: Getting classification results...")
        async with session.get(f"{base_url}/classification/{upload_id}/services") as resp:
            if resp.status != 200:
                print(f"Classification failed: {resp.status}")
                print(await resp.text())
                return
            
            classification_data = await resp.json()
            
            print(f"\n{'='*80}")
            print(f"CLASSIFICATION RESULTS")
            print(f"{'='*80}")
            print(f"Total Services: {classification_data['total_services']}")
            print(f"High Confidence: {classification_data['classification_summary']['high_confidence']}")
            print(f"Medium Confidence: {classification_data['classification_summary']['medium_confidence']}")
            print(f"Needs Review: {classification_data['classification_summary']['needs_review']}")
            
            # Show top 10 services
            print(f"\n{'='*80}")
            print(f"TOP 10 SERVICES (by confidence)")
            print(f"{'='*80}")
            
            for i, service in enumerate(classification_data['services'][:10], 1):
                print(f"\n{i}. {service['service_name'].upper()}")
                print(f"   Endpoints: {service['endpoint_count']}")
                print(f"   ├── Tier 1 (CRUD): {service['tier1_operations']}")
                print(f"   └── Tier 2 (Specialized): {service['tier2_operations']}")
                print(f"   Confidence: {service['confidence_score']:.2f}")
                print(f"   Description: {service['suggested_description'][:100]}...")
                if service['keywords']:
                    print(f"   Keywords: {', '.join(service['keywords'][:5])}")
            
            # Show services with complete CRUD
            complete_crud = [s for s in classification_data['services'] if s['tier1_operations'] >= 5]
            print(f"\n{'='*80}")
            print(f"SERVICES WITH COMPLETE CRUD ({len(complete_crud)} total)")
            print(f"{'='*80}")
            
            for service in complete_crud[:20]:
                print(f"• {service['service_name']} ({service['tier1_operations']} CRUD + {service['tier2_operations']} specialized)")
            
            if len(complete_crud) > 20:
                print(f"... and {len(complete_crud) - 20} more")
        
        # Step 4: Check for conflicts
        print(f"\n\n{'='*80}")
        print(f"CHECKING FOR CONFLICTS")
        print(f"{'='*80}")
        
        async with session.get(f"{base_url}/classification/{upload_id}/conflicts") as resp:
            if resp.status == 200:
                conflicts_data = await resp.json()
                print(f"Total Conflicts: {conflicts_data['total_conflicts']}")
                if conflicts_data['total_conflicts'] > 0:
                    print(f"├── High Severity: {conflicts_data['high_severity_count']}")
                    print(f"├── Medium Severity: {conflicts_data['medium_severity_count']}")
                    print(f"└── Low Severity: {conflicts_data['low_severity_count']}")
                    
                    # Show first few conflicts
                    for conflict in conflicts_data['conflicts'][:5]:
                        print(f"\n• {conflict['conflict_type']} ({conflict['severity']})")
                        print(f"  Affected: {', '.join(conflict['affected_services'])}")
                        print(f"  {conflict['description']}")
                else:
                    print("✓ No conflicts detected!")


if __name__ == "__main__":
    print("Testing Man-O-Man Classification API via uvicorn...")
    print("Make sure uvicorn is running: cd backend && uvicorn app.main:app --reload")
    print("="*80)
    
    asyncio.run(test_classification_api())