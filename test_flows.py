#!/usr/bin/env python3
"""Quick test script for chat and marketing flows."""

import sys
import os
sys.path.append('.')

from langchain.schema import HumanMessage
from src.utils.common import is_marketing_request, chat_response
from src.utils.state import MessagesState
from src.nodes.llm_node import llm_node

def test_chat_detection():
    """Test chat detection functionality."""
    print('🧪 Testing Chat Detection:')
    print('─' * 40)
    
    # Test general chat
    general_inputs = ['hi there!', 'what is python?', 'how are you?']
    for inp in general_inputs:
        is_marketing = is_marketing_request(inp)
        print(f'"{inp}" → Marketing: {is_marketing}')
    
    print()
    
    # Test marketing inputs
    marketing_inputs = ['promote smartwatches', 'create campaign for diwali', 'market shoes to teens']
    for inp in marketing_inputs:
        is_marketing = is_marketing_request(inp)
        print(f'"{inp}" → Marketing: {is_marketing}')
    
    print()

def test_chat_responses():
    """Test hardcoded chat responses."""
    print('🧪 Testing Chat Responses:')
    print('─' * 40)
    
    response = chat_response('hi there!')
    print('General greeting response:')
    print(response[:150] + '...' if len(response) > 150 else response)
    print()

def test_llm_node():
    """Test LLM node for general chat."""
    print('🧪 Testing LLM Node:')
    print('─' * 40)
    
    try:
        state = MessagesState()
        state['messages'] = [HumanMessage(content='What is 2+2? Answer briefly.')]
        result = llm_node(state)
        print('LLM Response:', result['messages'][-1].content)
        print('✅ LLM Node working')
    except Exception as e:
        print('❌ LLM Node error:', str(e))
    print()

if __name__ == '__main__':
    print('🚀 Testing Core Chat & Marketing Flows')
    print('=' * 50)
    test_chat_detection()
    test_chat_responses() 
    test_llm_node()
    print('✅ Core tests completed!')
