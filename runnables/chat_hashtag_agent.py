#!/usr/bin/env python3
"""
Interactive chat interface for the Hashtag Only Agent.
Perfect for unit testing hashtag and CTA generation in isolation.

Usage:
    python -m runnables.chat_hashtag_agent
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from langchain.schema import HumanMessage

from src.agents.micro.hashtag_only_agent import HashtagOnlyAgent
from src.agents.text_agent.utils.ui import (
    print_colored, print_banner, format_message, 
    print_summary_header, print_kv
)
from src.utils.state import MessagesState


def print_hashtag_summary(result: MessagesState):
    """Print a summary of hashtag and CTA generation results."""
    print_summary_header()
    
    # Hashtag and CTA results
    hashtags = result.get("hashtags", [])
    ctas = result.get("ctas", [])
    parsed_intent = result.get("parsed_intent", {})
    
    print_colored("🏷️ HASHTAG & CTA GENERATION RESULTS", "36")
    print("─" * 60)
    
    if hashtags or ctas:
        print_kv("✅ Status", "Generation successful")
        
        if hashtags:
            print_kv("🏷️ Hashtags Generated", f"{len(hashtags)} hashtags")
            hashtag_text = " ".join(hashtags)
            print_kv("📋 Hashtag List", hashtag_text)
        
        if ctas:
            print_kv("📢 CTAs Generated", f"{len(ctas)} call-to-actions")
            for i, cta in enumerate(ctas, 1):
                print_kv(f"  CTA {i}", cta)
        
        if parsed_intent:
            goal = parsed_intent.get("goal", "")
            audience = parsed_intent.get("audience", "")
            channels = parsed_intent.get("channels", [])
            tone = parsed_intent.get("tone", "")
            
            if goal:
                print_kv("🎯 Campaign Goal", goal)
            if audience:
                print_kv("👥 Target Audience", audience)
            if channels:
                print_kv("📱 Channels", ", ".join(channels))
            if tone:
                print_kv("🎭 Tone", tone)
    else:
        print_kv("❌ Status", "Generation failed")
    
    # Show metadata if available
    meta = result.get("meta", {})
    hashtag_meta = meta.get("hashtags_llm") or meta.get("ctas_llm")
    if hashtag_meta:
        print_colored("\n📊 GENERATION METADATA", "33")
        print("─" * 60)
        print_kv("🤖 Model", hashtag_meta.get("model", "Unknown"))
        
        usage = hashtag_meta.get("usage")
        if usage:
            input_tokens = getattr(usage, "input_tokens", 0)
            output_tokens = getattr(usage, "output_tokens", 0)
            total_tokens = input_tokens + output_tokens
            print_kv("🔢 Tokens", f"{total_tokens} ({input_tokens} in + {output_tokens} out)")
        
        prompt = hashtag_meta.get("prompt", "")
        if prompt:
            preview = prompt[:100] + "..." if len(prompt) > 100 else prompt
            print_kv("💭 Prompt Preview", preview)


def main():
    """Run the interactive Hashtag Only Agent chat."""
    print_banner("🏷️ Hashtag & CTA Generation Agent")
    
    agent = HashtagOnlyAgent()
    
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
                print_hashtag_summary(result)
                
            except KeyboardInterrupt:
                print("\n\n👋 Goodbye!")
                break
            except Exception as e:
                print_colored(f"❌ Error: {str(e)}", "31")
                
    except KeyboardInterrupt:
        print("\n\n👋 Goodbye!")


if __name__ == "__main__":
    main()
