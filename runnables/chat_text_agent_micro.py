#!/usr/bin/env python3
"""
Interactive chat interface for the Text Only Agent.
Perfect for unit testing text generation in isolation.

Usage:
    python -m runnables.chat_text_agent_micro
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from langchain.schema import HumanMessage

from src.agents.micro.text_only_agent import TextOnlyAgent
from src.agents.text_agent.utils.ui import (
    print_colored, print_banner, format_message, 
    print_summary_header, print_kv
)
from src.utils.state import MessagesState


def print_text_summary(result: MessagesState):
    """Print a summary of text generation results."""
    print_summary_header()
    
    # Text generation results
    post_content = result.get("post_content", "")
    parsed_intent = result.get("parsed_intent", {})
    
    print_colored("📝 TEXT GENERATION RESULTS", "36")
    print("─" * 60)
    
    if post_content:
        print_kv("✅ Status", "Text generated successfully")
        print_kv("📝 Marketing Copy", post_content)
        
        if parsed_intent:
            goal = parsed_intent.get("goal", "")
            audience = parsed_intent.get("audience", "")
            channels = parsed_intent.get("channels", [])
            tone = parsed_intent.get("tone", "")
            budget = parsed_intent.get("budget", "")
            
            if goal:
                print_kv("🎯 Campaign Goal", goal)
            if audience:
                print_kv("👥 Target Audience", audience)
            if channels:
                print_kv("📱 Channels", ", ".join(channels))
            if tone:
                print_kv("🎭 Tone", tone)
            if budget:
                print_kv("💰 Budget", budget)
    else:
        print_kv("❌ Status", "Text generation failed")
    
    # Show metadata if available
    meta = result.get("meta", {})
    if meta and "text_generation_llm" in meta:
        text_meta = meta["text_generation_llm"]
        print_colored("\n📊 GENERATION METADATA", "33")
        print("─" * 60)
        print_kv("🤖 Model", text_meta.get("model", "Unknown"))
        
        usage = text_meta.get("usage")
        if usage:
            input_tokens = getattr(usage, "input_tokens", 0)
            output_tokens = getattr(usage, "output_tokens", 0)
            total_tokens = input_tokens + output_tokens
            print_kv("🔢 Tokens", f"{total_tokens} ({input_tokens} in + {output_tokens} out)")
        
        prompt = text_meta.get("prompt", "")
        if prompt:
            preview = prompt[:100] + "..." if len(prompt) > 100 else prompt
            print_kv("💭 Prompt Preview", preview)


def main():
    """Run the interactive Text Only Agent chat."""
    print_banner("📝 Text Generation Agent")
    
    agent = TextOnlyAgent()
    
    try:
        while True:
            user_input = input("\n👤 You: ").strip()
            
            if not user_input:
                continue
                
            if user_input.lower() in ['exit', 'quit', 'bye']:
                print("\n👋 Goodbye!")
                break
            
            # Create state with user message
            state: MessagesState = {
                "messages": [HumanMessage(content=user_input)]
            }
            
            print("─" * 64)
            print_colored("🤖 Agent", "32")
            print("─" * 64)
            
            # Run the agent
            try:
                result = agent.run(state)
                
                # Display agent response
                messages = result.get("messages", [])
                if messages:
                    last_message = messages[-1]
                    if hasattr(last_message, 'content'):
                        print(last_message.content)
                
                # Show detailed summary
                print_text_summary(result)
                
            except KeyboardInterrupt:
                print("\n\n👋 Goodbye!")
                break
            except Exception as e:
                print_colored(f"❌ Error: {str(e)}", "31")
                
    except KeyboardInterrupt:
        print("\n\n👋 Goodbye!")


if __name__ == "__main__":
    main()
