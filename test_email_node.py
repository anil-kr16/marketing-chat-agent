#!/usr/bin/env python3
"""Test the email delivery node directly."""

import sys
import os
sys.path.append('.')

from src.utils.state import MessagesState
from src.nodes.delivery.email.send_email_node import send_email_node
from src.utils.common import create_campaign_folder

def test_email_node_direct():
    """Test email node directly."""
    print('📧 TESTING EMAIL NODE DIRECTLY')
    print('=' * 40)
    
    # Create test state with all required content
    state = MessagesState()
    state["post_content"] = "🎉 Winter Sale! Get 50% off cozy coats perfect for college students. Stay warm in style! ❄️"
    state["hashtags"] = ["#WinterSale", "#CollegeStyle", "#CozyCoats"]
    state["ctas"] = ["Shop Now!", "Get 50% Off!", "Stay Warm!"]
    state["parsed_intent"] = {
        "goal": "promote winter coats",
        "audience": "college students", 
        "channels": ["Email"],
        "tone": "energetic",
        "budget": ""
    }
    
    print('📋 Input State:')
    print(f'   Post Content: {state["post_content"][:50]}...')
    print(f'   Hashtags: {len(state["hashtags"])} items')
    print(f'   CTAs: {len(state["ctas"])} items')
    print(f'   Parsed Intent: {state["parsed_intent"]}')
    print()
    
    print('🔧 Testing Campaign Folder Creation:')
    try:
        outbox_dir = "data/outbox"
        campaign_folder = create_campaign_folder(state, outbox_dir)
        print(f'   ✅ Campaign folder: {campaign_folder}')
    except Exception as e:
        print(f'   ❌ Campaign folder failed: {e}')
        return
    
    print()
    print('📧 Testing Email Node:')
    try:
        # Call the email node directly
        result_state = send_email_node(state)
        
        print(f'   ✅ Email node executed successfully')
        print(f'   State keys after email: {list(result_state.keys())}')
        
        # Check if delivery was added to state
        if "delivery" in result_state:
            delivery = result_state["delivery"]
            print(f'   📬 Delivery info: {delivery}')
        else:
            print(f'   ❌ No delivery info added to state')
            
    except Exception as e:
        print(f'   ❌ Email node failed: {e}')
        import traceback
        traceback.print_exc()
    
    print()
    print('📁 Checking outbox after email node:')
    try:
        import subprocess
        result = subprocess.run(['find', 'data/outbox', '-type', 'f'], capture_output=True, text=True)
        if result.stdout.strip():
            print('   ✅ Files found:')
            for file in result.stdout.strip().split('\n'):
                print(f'      {file}')
        else:
            print('   ❌ No files found in outbox')
    except Exception as e:
        print(f'   ❌ Could not check outbox: {e}')

if __name__ == '__main__':
    test_email_node_direct()
