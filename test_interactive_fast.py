#!/usr/bin/env python3
"""Test fast marketing agent with simulated interactions."""

import sys
import os
sys.path.append('.')

from langchain.schema import HumanMessage
from src.utils.common import is_marketing_request, chat_response
from src.utils.state import MessagesState
from src.nodes.llm_node import llm_node

# Import the fast marketing workflow
from runnables.chat_fast_marketing_agent import fast_marketing_workflow, print_fast_summary

def simulate_interaction(user_input: str):
    """Simulate a user interaction with the fast agent."""
    print('=' * 60)
    print(f'👤 User: {user_input}')
    print('─' * 60)
    
    if is_marketing_request(user_input):
        print('🤖 Assistant: Creating FAST Campaign...')
        print('─' * 60)
        
        try:
            import time
            start_time = time.time()
            
            # Run fast marketing workflow
            result = fast_marketing_workflow(user_input)
            
            elapsed = time.time() - start_time
            print(f'⚡ Completed in {elapsed:.2f}s')
            print()
            
            # Print results
            print_fast_summary(result, user_input)
            print()
            
        except Exception as e:
            print(f'❌ Campaign creation failed: {str(e)}')
            print()
    else:
        # Handle as conversational chat
        print('🤖 Assistant:')
        print('─' * 60)
        
        try:
            chat_state = MessagesState()
            chat_state["messages"] = [HumanMessage(content=user_input)]
            llm_result = llm_node(chat_state)
            response_content = llm_result["messages"][-1].content
            print(response_content)
            print()
        except Exception as e:
            print(f'❌ Chat error: {str(e)}')
            print()

def main():
    """Run simulated fast agent interactions."""
    print('🚀 TESTING FAST MARKETING AGENT')
    print('🎯 Mode: Interactive Simulation')
    print()
    
    # Test interactions
    test_inputs = [
        "hi there!",  # General chat
        "promote gaming keyboards to esports enthusiasts",  # Marketing  
        "what can you help me with?",  # General help
        "create valentine's day campaign for restaurants"  # Marketing
    ]
    
    for inp in test_inputs:
        simulate_interaction(inp)
    
    print('✅ Fast agent simulation completed!')

if __name__ == '__main__':
    main()
