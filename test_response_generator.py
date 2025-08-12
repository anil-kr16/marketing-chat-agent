#!/usr/bin/env python3
"""Test the response generator node."""

import sys
import os
sys.path.append('.')

from src.utils.state import MessagesState
from src.nodes.compose.response_generator_node import response_generator_node

def test_response_generator():
    """Test response generator node."""
    print('📦 TESTING RESPONSE GENERATOR NODE')
    print('=' * 45)
    
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
    
    print('📋 Input State:')
    print(f'   Post Content: {state["post_content"][:50]}...')
    print(f'   Hashtags: {state["hashtags"]}')
    print(f'   CTAs: {state["ctas"]}')
    print()
    
    print('📦 Running Response Generator:')
    try:
        result_state = response_generator_node(state)
        
        print('✅ Response generator completed')
        print('📄 Generated final_response:')
        
        final_response = result_state.get("final_response", {})
        if final_response:
            for key, value in final_response.items():
                if key == "email" and isinstance(value, dict):
                    print(f'   📧 {key}:')
                    for sub_key, sub_value in value.items():
                        if isinstance(sub_value, str) and len(sub_value) > 100:
                            print(f'      {sub_key}: {sub_value[:100]}...')
                        else:
                            print(f'      {sub_key}: {sub_value}')
                else:
                    print(f'   {key}: {str(value)[:100]}...' if len(str(value)) > 100 else f'   {key}: {value}')
        else:
            print('   ❌ No final_response generated')
            
    except Exception as e:
        print(f'❌ Response generator failed: {e}')
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    test_response_generator()
