#!/usr/bin/env python3
"""Test full marketing agent with simulated interactions."""

import sys
import os
sys.path.append('.')

from langchain.schema import HumanMessage
from src.utils.common import is_marketing_request, chat_response
from src.utils.state import MessagesState
from src.nodes.llm_node import llm_node
from src.agents.campaign.full_marketing_agent import FullMarketingAgent

def simulate_full_agent_interaction(user_input: str):
    """Simulate a user interaction with the full marketing agent."""
    print('=' * 60)
    print(f'👤 User: {user_input}')
    print('─' * 60)
    
    if is_marketing_request(user_input):
        print('🤖 Assistant: Creating Full Marketing Campaign...')
        print('─' * 60)
        
        try:
            import time
            start_time = time.time()
            
            # Create agent and run campaign
            agent = FullMarketingAgent()
            state = MessagesState()
            state["messages"] = [HumanMessage(content=user_input)]
            
            print("🎬 Step 1/7: Parsing your request...")
            print("🎨 Step 2/7: Generating creative brief...")
            print("🔀 Step 3/7: Creating content in parallel...")
            print("     📝 Writing compelling copy...")
            print("     🎨 Creating visual content (this may take 15-20s)...")
            print("     🏷️ Generating hashtags & CTAs...")
            print("🎭 Step 4/7: Composing campaign...")
            print("🚀 Step 5/7: Executing delivery...")
            
            result = agent.run(state)
            
            elapsed = time.time() - start_time
            print(f'✅ Campaign completed in {elapsed:.2f}s')
            print()
            
            # Show what was generated
            print('📊 CAMPAIGN RESULTS:')
            print('─' * 40)
            if result.get('post_content'):
                print(f'📝 Marketing Copy: {result["post_content"][:100]}...')
            if result.get('hashtags'):
                print(f'🏷️ Hashtags: {len(result["hashtags"])} generated')
            if result.get('ctas'):
                print(f'📢 CTAs: {len(result["ctas"])} generated')
            if result.get('image_url'):
                print(f'🖼️ Image: {result["image_url"]}')
            if result.get('delivery'):
                print(f'📬 Delivery: {result["delivery"]}')
            print()
            
        except Exception as e:
            print(f'❌ Campaign creation failed: {str(e)}')
            import traceback
            traceback.print_exc()
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
    """Run simulated full agent interactions."""
    print('🚀 TESTING FULL MARKETING AGENT')
    print('🎯 Mode: Complete Campaign Generation')
    print()
    
    # Test one marketing campaign
    test_input = "promote winter coats to college students"
    simulate_full_agent_interaction(test_input)
    
    print('✅ Full agent simulation completed!')

if __name__ == '__main__':
    main()
