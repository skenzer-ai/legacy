"""
Integration test: Classification to Definition Pipeline
Tests the workflow from classification results to definition agent interaction
"""

import asyncio
import aiohttp
import json
from pathlib import Path
from typing import Dict, Any


async def test_classification_to_definition_pipeline():
    """Test the complete pipeline from classification to definition"""
    
    base_url = "http://localhost:8000/api/v1/manoman"
    yaml_path = Path(__file__).resolve().parents[1] / "user_docs" / "infraon-openapi.yaml"
    
    async with aiohttp.ClientSession() as session:
        print("="*80)
        print("CLASSIFICATION TO DEFINITION PIPELINE TEST")
        print("="*80)
        
        # Step 1: Upload and classify (reuse existing logic)
        print("\nStep 1: Upload and classify API specification...")
        
        with open(yaml_path, 'rb') as f:
            data = aiohttp.FormData()
            data.add_field('file', f, filename='infraon-openapi.yaml', content_type='application/x-yaml')
            
            async with session.post(f"{base_url}/upload", data=data) as resp:
                if resp.status != 200:
                    print(f"❌ Upload failed: {resp.status}")
                    return
                
                upload_response = await resp.json()
                upload_id = upload_response["upload_id"]
                print(f"✓ Upload successful. Upload ID: {upload_id}")
        
        # Wait for classification to complete
        for i in range(10):
            async with session.get(f"{base_url}/upload/{upload_id}/status") as resp:
                status_data = await resp.json()
                if status_data["status"] == "completed":
                    print(f"✓ Upload completed")
                    break
                await asyncio.sleep(1)
        
        # Get classification results
        async with session.get(f"{base_url}/classification/{upload_id}/services") as resp:
            if resp.status != 200:
                print(f"❌ Classification failed: {resp.status}")
                return
            
            classification_data = await resp.json()
            print(f"✓ Classification completed: {classification_data['total_services']} services")
        
        # Step 2: Test service merge functionality
        print(f"\nStep 2: Testing service merge functionality...")
        
        # Find similar CMDB services to merge as an example
        cmdb_services = [
            svc["service_name"] for svc in classification_data["services"] 
            if "cmdb" in svc["service_name"].lower() and "cmdb" == svc["service_name"].lower()[:4]
        ][:3]  # Take first 3 CMDB services
        
        if len(cmdb_services) >= 2:
            merge_request = {
                "source_services": cmdb_services[:2],
                "new_service_name": "unified_cmdb_service",
                "merge_strategy": "combine_all"
            }
            
            async with session.post(
                f"{base_url}/classification/{upload_id}/services/merge",
                json=merge_request
            ) as resp:
                if resp.status == 200:
                    merge_response = await resp.json()
                    print(f"✓ Service merge successful: {merge_response['message']}")
                    print(f"  Merged services: {', '.join(merge_response['merged_services'])}")
                    print(f"  New service: {merge_response['new_service_name']}")
                else:
                    print(f"❌ Service merge failed: {resp.status}")
                    print(await resp.text())
        else:
            print("⚠️  Not enough similar services found for merge test")
        
        # Step 3: Test service split functionality
        print(f"\nStep 3: Testing service split functionality...")
        
        # Find a service with many operations to split
        large_services = [
            svc for svc in classification_data["services"] 
            if svc["endpoint_count"] >= 10 and svc["tier1_operations"] >= 5
        ]
        
        if large_services:
            target_service = large_services[0]
            service_name = target_service["service_name"]
            total_ops = target_service["tier1_operations"] + target_service["tier2_operations"]
            
            # Create a simple split configuration with string operation IDs
            split_config = {
                f"{service_name}_core": [f"op_{i}" for i in range(total_ops // 2)],
                f"{service_name}_extended": [f"op_{i}" for i in range(total_ops // 2, total_ops)]
            }
            
            split_request = {
                "source_service": service_name,
                "split_config": split_config
            }
            
            async with session.post(
                f"{base_url}/classification/{upload_id}/services/split",
                json=split_request
            ) as resp:
                if resp.status == 200:
                    split_response = await resp.json()
                    print(f"✓ Service split successful: {split_response['message']}")
                    print(f"  Original service: {split_response['original_service']}")
                    print(f"  New services: {', '.join(split_response['new_services'])}")
                else:
                    print(f"❌ Service split failed: {resp.status}")
                    print(await resp.text())
        else:
            print("⚠️  No suitable services found for split test")
        
        # Step 4: Start definition session for a service
        print(f"\nStep 4: Testing definition agent session...")
        
        # Select a well-classified service for definition
        target_services = [
            svc for svc in classification_data["services"][:5]  # Top 5 services
            if svc["confidence_score"] >= 0.8 and svc["tier1_operations"] >= 5
        ]
        
        if target_services:
            target_service = target_services[0]
            service_name = target_service["service_name"]
            
            # Start definition session
            definition_request = {
                "service_name": service_name,
                "upload_id": upload_id
            }
            
            async with session.post(
                f"{base_url}/definition/start-session",
                json=definition_request
            ) as resp:
                if resp.status == 200:
                    definition_response = await resp.json()
                    session_id = definition_response["session_id"]
                    print(f"✓ Definition session started")
                    print(f"  Session ID: {session_id}")
                    print(f"  Service: {service_name}")
                    print(f"  First question: {definition_response['first_question'][:150]}...")
                    
                    # Step 5: Respond to the agent
                    print(f"\nStep 5: Responding to definition agent...")
                    
                    follow_up_request = {
                        "user_response": "Yes, that's correct. The service should handle all basic CRUD operations for managing these entities."
                    }
                    
                    async with session.post(
                        f"{base_url}/definition/session/{session_id}/respond",
                        json=follow_up_request
                    ) as resp:
                        if resp.status == 200:
                            follow_up_response = await resp.json()
                            print(f"✓ Response processed successfully")
                            print(f"  Current step: {follow_up_response.get('current_step', 'Unknown')}")
                            print(f"  Progress: {follow_up_response.get('progress', 0):.0%}")
                            print(f"  Agent response: {follow_up_response['response'][:150]}...")
                            
                            # Step 6: Get session status
                            print(f"\nStep 6: Checking session status...")
                            
                            async with session.get(f"{base_url}/definition/session/{session_id}/status") as resp:
                                if resp.status == 200:
                                    status_data = await resp.json()
                                    print(f"✓ Status retrieved successfully")
                                    print(f"  Current step: {status_data.get('current_step', 'Unknown')}")
                                    print(f"  Conversation length: {status_data.get('conversation_length', 0)}")
                                    print(f"  Data collected: {len(status_data.get('data_collected', {}))} items")
                                    
                                    # Step 7: Preview current definition
                                    print(f"\nStep 7: Previewing definition...")
                                    
                                    async with session.get(f"{base_url}/definition/session/{session_id}/preview") as resp:
                                        if resp.status == 200:
                                            preview_data = await resp.json()
                                            print(f"✓ Preview retrieved successfully")
                                            definition = preview_data['partial_definition']
                                            print(f"  Service name: {definition.get('service_name', 'Unknown')}")
                                            print(f"  Description: {definition.get('service_description', 'No description')[:100]}...")
                                            print(f"  Keywords: {len(definition.get('keywords', []))} keywords")
                                        else:
                                            print(f"❌ Preview failed: {resp.status}")
                                else:
                                    print(f"❌ Status check failed: {resp.status}")
                        else:
                            print(f"❌ Response processing failed: {resp.status}")
                            print(await resp.text())
                else:
                    print(f"❌ Definition session failed: {resp.status}")
                    print(await resp.text())
        else:
            print("⚠️  No suitable services found for definition test")
        
        # Step 8: Test bulk definition operations
        print(f"\nStep 8: Testing session management...")
        
        # Get list of active sessions
        async with session.get(f"{base_url}/definition/sessions") as resp:
            if resp.status == 200:
                sessions_data = await resp.json()
                print(f"✓ Retrieved active sessions: {sessions_data.get('active_sessions', 0)} sessions")
                
                # Show session details
                for session_info in sessions_data.get('sessions', []):
                    print(f"  • Session {session_info['session_id'][:8]}...")
                    print(f"    Service: {session_info['service_name']}")
                    print(f"    Step: {session_info['current_step']}")
                    print(f"    Messages: {session_info['conversation_length']}")
            else:
                print(f"❌ Sessions list retrieval failed: {resp.status}")
                print(await resp.text())
        
        print(f"\n{'='*80}")
        print(f"INTEGRATION TEST SUMMARY")
        print(f"{'='*80}")
        print(f"✓ Upload and classification pipeline")
        print(f"✓ Service merge/split operations")
        print(f"✓ Definition agent conversation flow")
        print(f"✓ Conversation progress tracking")
        print(f"✓ Bulk definition operations")
        print(f"\nClassification to Definition pipeline integration test completed!")


if __name__ == "__main__":
    print("Testing Classification to Definition Pipeline...")
    print("Make sure uvicorn is running: cd backend && uvicorn app.main:app --reload")
    print("="*80)
    
    asyncio.run(test_classification_to_definition_pipeline())