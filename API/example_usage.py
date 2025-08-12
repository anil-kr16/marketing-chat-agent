#!/usr/bin/env python3
"""
Example usage of the Marketing Agent API.

This script demonstrates how to interact with the API using Python.
It shows both synchronous and asynchronous usage patterns.
"""

import asyncio
import time
import requests
import websocket
import json
from typing import Dict, Any

# API Configuration
API_BASE_URL = "http://localhost:8000"
API_KEY = "demo-key-12345"
HEADERS = {
    "X-API-Key": API_KEY,
    "Content-Type": "application/json"
}


def synchronous_example():
    """
    Example using synchronous requests (requests library).
    
    This is the simplest way to interact with the API.
    """
    print("🚀 Synchronous API Example")
    print("=" * 50)
    
    # 1. Check API health
    print("1. Checking API health...")
    health_response = requests.get(f"{API_BASE_URL}/api/v1/health")
    print(f"   Health status: {health_response.json()['status']}")
    
    # 2. Create a marketing campaign
    print("\n2. Creating marketing campaign...")
    campaign_request = {
        "user_input": "promote eco-friendly water bottle for outdoor enthusiasts with $300 budget",
        "options": {
            "channels": ["instagram", "email"],
            "tone": "inspirational",
            "include_images": True,
            "dry_run": True
        }
    }
    
    create_response = requests.post(
        f"{API_BASE_URL}/api/v1/campaigns",
        headers=HEADERS,
        json=campaign_request
    )
    
    if create_response.status_code == 201:
        campaign_data = create_response.json()
        campaign_id = campaign_data["campaign_id"]
        print(f"   ✅ Campaign created: {campaign_id}")
        
        # 3. Poll for completion
        print("\n3. Polling for campaign completion...")
        max_attempts = 60  # Wait up to 60 seconds
        attempt = 0
        
        while attempt < max_attempts:
            status_response = requests.get(
                f"{API_BASE_URL}/api/v1/campaigns/{campaign_id}/status",
                headers=HEADERS
            )
            
            if status_response.status_code == 200:
                status_data = status_response.json()["data"]
                campaign_status = status_data["status"]
                
                print(f"   Status: {campaign_status}", end="")
                
                if "progress" in status_data and status_data["progress"]:
                    progress = status_data["progress"]
                    print(f" - {progress['current_step']} ({progress['percentage']}%)")
                else:
                    print()
                
                if campaign_status in ["completed", "failed", "cancelled"]:
                    break
                    
            time.sleep(2)  # Wait 2 seconds between polls
            attempt += 1
        
        # 4. Get final results
        if campaign_status == "completed":
            print("\n4. Retrieving final results...")
            results_response = requests.get(
                f"{API_BASE_URL}/api/v1/campaigns/{campaign_id}",
                headers=HEADERS
            )
            
            if results_response.status_code == 200:
                campaign_results = results_response.json()
                
                print("   ✅ Campaign completed successfully!")
                print(f"   📝 Marketing copy: {campaign_results['generated_content']['marketing_copy'][:100]}...")
                print(f"   🏷️ Hashtags: {', '.join(campaign_results['generated_content']['hashtags'][:3])}")
                print(f"   📊 Tokens used: {campaign_results['performance_metrics']['total_tokens']}")
                
                # 5. List and download files
                print("\n5. Checking generated files...")
                files_response = requests.get(
                    f"{API_BASE_URL}/api/v1/campaigns/{campaign_id}/files",
                    headers=HEADERS
                )
                
                if files_response.status_code == 200:
                    files_data = files_response.json()["data"]["files"]
                    print(f"   📁 Generated {len(files_data)} files:")
                    
                    for file_info in files_data:
                        print(f"      - {file_info['filename']} ({file_info['size_human']})")
        else:
            print(f"   ❌ Campaign {campaign_status}")
    else:
        print(f"   ❌ Failed to create campaign: {create_response.text}")


async def asynchronous_example():
    """
    Example using asynchronous requests (httpx library).
    
    More efficient for handling multiple campaigns simultaneously.
    """
    print("\n🔄 Asynchronous API Example")
    print("=" * 50)
    
    import httpx
    
    async with httpx.AsyncClient() as client:
        # Create multiple campaigns simultaneously
        campaign_requests = [
            {
                "user_input": f"promote product {i} for target audience {i}",
                "options": {"channels": ["instagram"], "dry_run": True}
            }
            for i in range(3)
        ]
        
        print("1. Creating multiple campaigns...")
        
        # Create campaigns in parallel
        create_tasks = [
            client.post(
                f"{API_BASE_URL}/api/v1/campaigns",
                headers=HEADERS,
                json=request
            )
            for request in campaign_requests
        ]
        
        create_responses = await asyncio.gather(*create_tasks)
        campaign_ids = []
        
        for response in create_responses:
            if response.status_code == 201:
                campaign_id = response.json()["campaign_id"]
                campaign_ids.append(campaign_id)
                print(f"   ✅ Created campaign: {campaign_id}")
        
        # Monitor all campaigns
        print(f"\n2. Monitoring {len(campaign_ids)} campaigns...")
        
        while campaign_ids:
            # Check status of all campaigns
            status_tasks = [
                client.get(
                    f"{API_BASE_URL}/api/v1/campaigns/{campaign_id}/status",
                    headers=HEADERS
                )
                for campaign_id in campaign_ids
            ]
            
            status_responses = await asyncio.gather(*status_tasks)
            completed_campaigns = []
            
            for i, response in enumerate(status_responses):
                if response.status_code == 200:
                    campaign_id = campaign_ids[i]
                    status_data = response.json()["data"]
                    campaign_status = status_data["status"]
                    
                    if campaign_status in ["completed", "failed", "cancelled"]:
                        completed_campaigns.append(campaign_id)
                        print(f"   ✅ Campaign {campaign_id}: {campaign_status}")
            
            # Remove completed campaigns from monitoring
            for campaign_id in completed_campaigns:
                campaign_ids.remove(campaign_id)
            
            if campaign_ids:
                await asyncio.sleep(2)  # Wait before next check
        
        print("   🎉 All campaigns completed!")


def websocket_example():
    """
    Example using WebSocket for real-time updates.
    
    Demonstrates how to receive live progress updates.
    """
    print("\n📡 WebSocket Real-time Example")
    print("=" * 50)
    
    # First create a campaign
    campaign_request = {
        "user_input": "create social media campaign for tech startup",
        "options": {"channels": ["instagram"], "dry_run": True}
    }
    
    create_response = requests.post(
        f"{API_BASE_URL}/api/v1/campaigns",
        headers=HEADERS,
        json=campaign_request
    )
    
    if create_response.status_code != 201:
        print("   ❌ Failed to create campaign for WebSocket example")
        return
    
    campaign_id = create_response.json()["campaign_id"]
    print(f"   📝 Created campaign: {campaign_id}")
    
    # Connect to WebSocket
    ws_url = f"ws://localhost:8000/api/v1/campaigns/{campaign_id}/stream?api_key={API_KEY}"
    print(f"   🔌 Connecting to WebSocket...")
    
    def on_message(ws, message):
        """Handle incoming WebSocket messages."""
        try:
            data = json.loads(message)
            msg_type = data.get("type")
            
            if msg_type == "connected":
                print(f"   ✅ Connected to campaign stream")
            elif msg_type == "progress_update":
                progress_data = data["data"]
                print(f"   ⚡ Progress: {progress_data['current_step']} ({progress_data['percentage']}%)")
            elif msg_type == "complete":
                print(f"   🎉 Campaign completed: {data['data']['message']}")
                ws.close()
            elif msg_type == "error":
                print(f"   ❌ Error: {data['data']['error']}")
                ws.close()
                
        except json.JSONDecodeError:
            print(f"   📝 Raw message: {message}")
    
    def on_error(ws, error):
        """Handle WebSocket errors."""
        print(f"   ❌ WebSocket error: {error}")
    
    def on_close(ws, close_status_code, close_msg):
        """Handle WebSocket close."""
        print(f"   🔌 WebSocket closed")
    
    # Create and run WebSocket connection
    ws = websocket.WebSocketApp(
        ws_url,
        on_message=on_message,
        on_error=on_error,
        on_close=on_close
    )
    
    print("   📡 Streaming real-time updates...")
    ws.run_forever()


def main():
    """Run all examples."""
    print("🎯 Marketing Agent API Examples")
    print("=" * 60)
    print("This script demonstrates various ways to interact with the API.")
    print("Make sure the API server is running on localhost:8000")
    print()
    
    try:
        # Test API connectivity first
        health_response = requests.get(f"{API_BASE_URL}/api/v1/health", timeout=5)
        if health_response.status_code != 200:
            print("❌ API server is not responding correctly")
            return
            
    except requests.exceptions.RequestException:
        print("❌ Cannot connect to API server. Make sure it's running on localhost:8000")
        return
    
    # Run examples
    synchronous_example()
    
    # Uncomment to run async example
    # asyncio.run(asynchronous_example())
    
    # Uncomment to run WebSocket example
    # websocket_example()
    
    print("\n✅ Examples completed!")
    print("\n💡 Next steps:")
    print("   - Visit http://localhost:8000/docs for interactive API documentation")
    print("   - Check the generated files in the API storage directory")
    print("   - Integrate the API into your own applications")


if __name__ == "__main__":
    main()
