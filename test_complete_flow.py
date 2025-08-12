#!/usr/bin/env python3
"""Test the complete delivery flow: response generator → email node."""

import sys
import os
sys.path.append('.')

from src.utils.state import MessagesState
from src.nodes.compose.response_generator_node import response_generator_node
from src.nodes.delivery.email.send_email_node import send_email_node

def test_complete_delivery_flow():
    """Test complete flow from response generation to email delivery."""
    print('🔄 TESTING COMPLETE DELIVERY FLOW')
    print('=' * 50)
    
    # Create test state with content
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
    
    print('📋 Initial State:')
    print(f'   Post Content: {state["post_content"][:50]}...')
    print(f'   Hashtags: {state["hashtags"]}')
    print(f'   CTAs: {state["ctas"]}')
    print(f'   Channels: {state["parsed_intent"]["channels"]}')
    print()
    
    # Step 1: Response Generator
    print('📦 Step 1: Running Response Generator')
    try:
        state = response_generator_node(state)
        email_payload = state.get("final_response", {}).get("email", {})
        
        if email_payload:
            print(f'   ✅ Email payload created')
            print(f'   📧 Subject: {email_payload.get("subject", "NO SUBJECT")}')
            print(f'   📄 Body length: {len(email_payload.get("bodyText", ""))} chars')
        else:
            print('   ❌ No email payload in final_response')
            return
    except Exception as e:
        print(f'   ❌ Response generator failed: {e}')
        return
    
    print()
    
    # Step 2: Email Delivery
    print('📧 Step 2: Running Email Delivery')
    try:
        state = send_email_node(state)
        
        delivery = state.get("delivery", {})
        if delivery:
            print(f'   ✅ Email delivery completed')
            print(f'   📬 Delivery results: {delivery.get("results", {})}')
        else:
            print('   ❌ No delivery info added to state')
            
    except Exception as e:
        print(f'   ❌ Email delivery failed: {e}')
        import traceback
        traceback.print_exc()
    
    print()
    
    # Step 3: Check Files
    print('📁 Step 3: Checking Created Files')
    try:
        import subprocess
        result = subprocess.run(['find', 'data/outbox', '-type', 'f', '-name', '*.txt'], capture_output=True, text=True)
        if result.stdout.strip():
            print('   ✅ Files found:')
            for file in result.stdout.strip().split('\n'):
                print(f'      📄 {file}')
                # Show file content preview
                try:
                    with open(file, 'r') as f:
                        content = f.read()
                        print(f'         Content: {content[:100]}...')
                except:
                    pass
        else:
            print('   ❌ No .txt files found in outbox')
            
            # Check if any folders were created
            result = subprocess.run(['find', 'data/outbox', '-type', 'd'], capture_output=True, text=True)
            if result.stdout.strip():
                print('   📁 Directories found:')
                for dir in result.stdout.strip().split('\n'):
                    if dir != 'data/outbox':
                        print(f'      📁 {dir}')
    except Exception as e:
        print(f'   ❌ Could not check files: {e}')

if __name__ == '__main__':
    test_complete_delivery_flow()
