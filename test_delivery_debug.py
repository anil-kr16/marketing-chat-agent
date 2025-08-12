#!/usr/bin/env python3
"""Debug delivery and file creation issues."""

import sys
import os
sys.path.append('.')

from langchain.schema import HumanMessage
from src.utils.state import MessagesState
from src.nodes.intent.parse_intent_node import parse_intent_node
from src.nodes.delivery.decider.sender_node import sender_node

def test_delivery_flow():
    """Test the delivery flow specifically."""
    print('🔍 DEBUGGING DELIVERY FLOW')
    print('=' * 50)
    
    # Create test state with content
    state = MessagesState()
    state["messages"] = [HumanMessage(content="promote winter coats to college students via email")]
    state["post_content"] = "Stay warm this winter with our cozy coats!"
    state["hashtags"] = ["#WinterCoats", "#CollegeStyle", "#StayWarm"]
    state["ctas"] = ["Shop Now!", "Stay Cozy!", "Get Yours Today!"]
    
    print('📋 Step 1: Testing Intent Parsing')
    print('─' * 30)
    try:
        parsed_state = parse_intent_node(state)
        parsed_intent = parsed_state.get("parsed_intent", {})
        print(f'✅ Parsed Intent: {parsed_intent}')
        print(f'   Goal: {parsed_intent.get("goal", "NOT SET")}')
        print(f'   Channels: {parsed_intent.get("channels", "NOT SET")}')
        print()
    except Exception as e:
        print(f'❌ Intent parsing failed: {e}')
        return

    print('🚀 Step 2: Testing Delivery')
    print('─' * 30)
    try:
        # Update state with parsed intent
        state.update(parsed_state)
        
        # Call sender node
        delivery_state = sender_node(state)
        delivery_result = delivery_state.get("delivery", {})
        print(f'✅ Delivery Result: {delivery_result}')
        
        # Check what files should have been created
        print()
        print('📁 Expected Files:')
        if delivery_result.get("results"):
            for channel, result in delivery_result["results"].items():
                print(f'   {channel}: {result}')
        else:
            print('   ❌ No delivery results found')
            
    except Exception as e:
        print(f'❌ Delivery failed: {e}')
        import traceback
        traceback.print_exc()
    
    print()
    print('📂 Current outbox contents:')
    try:
        import subprocess
        result = subprocess.run(['ls', '-la', 'data/outbox/'], capture_output=True, text=True)
        print(result.stdout)
    except:
        print('   ❌ Could not list outbox contents')

if __name__ == '__main__':
    test_delivery_flow()
