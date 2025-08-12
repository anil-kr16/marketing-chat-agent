#!/usr/bin/env python3
"""
FAST Interactive Marketing Agent - No Image Generation
Perfect for quick iterations and testing.

Usage:
    python -m runnables.chat_fast_marketing_agent
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from langchain.schema import HumanMessage, SystemMessage

from src.agents.text_agent.utils.ui import (
    print_colored, print_banner, print_kv
)
from src.utils.state import MessagesState
from src.utils.common import is_marketing_request, chat_response
from src.nodes.intent.parse_intent_node import parse_intent_node
from src.nodes.generation.text.text_generation_node import text_generation_node
from src.nodes.generation.cta_hashtag.cta_hashtag_node import cta_hashtag_node
from src.nodes.compose.response_generator_node import response_generator_node
from src.nodes.delivery.decider.sender_node import sender_node
from src.nodes.llm_node import llm_node
from src.config import get_config


def fast_marketing_workflow(user_input: str) -> dict:
    """Run fast marketing workflow without images but WITH delivery."""
    
    # Initialize state
    state: MessagesState = {
        "messages": [
            SystemMessage(content="You are a world-class marketing agent focused on creating compelling campaigns."),
            HumanMessage(content=user_input)
        ]
    }
    
    print("📋 Parsing your request...")
    state = parse_intent_node(state)
    
    print("📝 Generating marketing copy...")
    state = text_generation_node(state)
    
    print("🏷️ Creating hashtags & CTAs...")
    state = cta_hashtag_node(state)
    
    print("📦 Composing final campaign...")
    state = response_generator_node(state)
    
    print("🚀 Delivering to channels...")
    state = sender_node(state)
    
    # Execute delivery to all requested channels
    from src.registries.channels import CHANNELS
    requested_channels = state.get("delivery", {}).get("requested", [])
    
    for channel in requested_channels:
        channel_key = channel.lower()
        if channel_key in CHANNELS:
            try:
                delivery_node = CHANNELS[channel_key]
                state = delivery_node(state)
                print(f"  ✅ {channel}: Content saved to outbox")
            except Exception as e:
                print(f"  ❌ {channel}: Delivery failed - {str(e)}")
                # Update delivery results with error
                delivery = state.setdefault("delivery", {"requested": [], "results": {}})
                delivery.setdefault("results", {})[channel_key] = f"Failed: {str(e)}"
    
    return state


def print_fast_summary(result: dict, user_input: str):
    """Print summary for fast marketing results."""
    
    print_colored("✅ FAST CAMPAIGN COMPLETED!", "32")
    print("─" * 64)
    
    # Original request
    print_kv("📝 Original Request", user_input)
    
    # Campaign overview
    parsed_intent = result.get("parsed_intent", {})
    if parsed_intent:
        print()
        print_colored("🎯 CAMPAIGN OVERVIEW", "36")
        print("─" * 40)
        print_kv("Goal", parsed_intent.get("goal", "Not specified"))
        print_kv("Audience", parsed_intent.get("audience", "Not specified"))
        print_kv("Channels", ", ".join(parsed_intent.get("channels", [])))
        print_kv("Tone", parsed_intent.get("tone", "Not specified"))
    
    # Generated content
    post_content = result.get("post_content", "")
    if post_content:
        print()
        print_colored("📝 MARKETING COPY", "33")
        print("─" * 40)
        print(post_content)
    
    # Hashtags and CTAs
    hashtags = result.get("hashtags", [])
    ctas = result.get("ctas", [])
    
    if hashtags:
        print()
        print_colored("🏷️ HASHTAGS", "34")
        print("─" * 40)
        for i, hashtag in enumerate(hashtags[:8], 1):  # Show first 8
            print(f"{i:2d}. {hashtag}")
        if len(hashtags) > 8:
            print(f"    ... and {len(hashtags) - 8} more")
    
    if ctas:
        print()
        print_colored("📢 CALL-TO-ACTIONS", "35")
        print("─" * 40)
        for i, cta in enumerate(ctas, 1):
            print(f"{i}. {cta}")
    
    print()
    # Show delivery results
    delivery = result.get("delivery", {})
    if delivery.get("results"):
        print()
        print_colored("📬 DELIVERY STATUS", "36")
        print("─" * 40)
        for channel, status in delivery["results"].items():
            if "wrote" in status:
                file_path = status.split("wrote ")[-1]
                print_kv(f"✅ {channel.title()}", f"Saved to {file_path}")
            else:
                print_kv(f"📤 {channel.title()}", status)
    
    print()
    print_colored("⚡ Campaign created in seconds! No images = faster iteration.", "32")


def main():
    """Run the fast interactive marketing agent."""
    print_banner("⚡ FAST Marketing Agent")
    print_colored("Type Ctrl+C to exit", "33")
    print_colored("⚡ NO IMAGE GENERATION = LIGHTNING FAST RESULTS!", "36")
    print()
    
    try:
        while True:
            # Get user input
            user_input = input("👤 User: ").strip()
            if not user_input:
                continue
                
            if user_input.lower() in ["exit", "quit", "bye"]:
                print_colored("👋 Goodbye!", "35")
                break
            
            # Check if this is a marketing request
            if is_marketing_request(user_input):
                print("─" * 64)
                print_colored("🤖 Assistant: Creating FAST Campaign...", "32")
                print("─" * 64)
                
                try:
                    import time
                    start_time = time.time()
                    
                    # Run fast marketing workflow
                    result = fast_marketing_workflow(user_input)
                    
                    elapsed = time.time() - start_time
                    print(f"⚡ Completed in {elapsed:.2f}s")
                    print()
                    
                    # Print results
                    print_fast_summary(result, user_input)
                    print()  # Add spacing after campaign summary
                    
                except Exception as e:
                    print_colored(f"❌ Campaign creation failed: {str(e)}", "31")
                    print("Please try again with a different request.")
                    print()  # Add spacing after error
            else:
                # Handle as conversational chat
                cfg = get_config()
                
                if cfg.enable_general_chat:
                    # Use real LLM for general conversation
                    print("─" * 64)
                    print_colored("🤖 Assistant:", "32")
                    print("─" * 64)
                    
                    chat_state = MessagesState()
                    chat_state["messages"] = [HumanMessage(content=user_input)]
                    
                    try:
                        llm_result = llm_node(chat_state)
                        response_content = llm_result["messages"][-1].content
                        print(response_content)
                        print()  # Add spacing after AI response
                    except Exception as e:
                        print_colored(f"❌ Chat error: {str(e)}", "31")
                        print("Please try again or ask me to create a marketing campaign.")
                        print()  # Add spacing after error
                else:
                    # Use hardcoded marketing-focused responses
                    response = chat_response(user_input)
                    print("─" * 64)
                    print_colored("🤖 Assistant:", "32")
                    print("─" * 64)
                    print(response)
                    print()  # Add spacing after hardcoded response
                
    except KeyboardInterrupt:
        print_colored("\n👋 Goodbye!", "35")


if __name__ == "__main__":
    main()
