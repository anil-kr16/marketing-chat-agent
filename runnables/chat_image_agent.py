#!/usr/bin/env python3
"""
Interactive chat interface for the Image Only Agent.
Perfect for unit testing image generation in isolation.

Usage:
    python -m runnables.chat_image_agent
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from langchain.schema import HumanMessage

from src.agents.micro.image_only_agent import ImageOnlyAgent
from src.agents.text_agent.utils.ui import (
    print_colored, print_banner, format_message, 
    print_summary_header, print_kv
)
from src.utils.state import MessagesState


def print_image_summary(result: MessagesState):
    """Print a summary of image generation results."""
    print_summary_header()
    
    # Image generation results
    image_url = result.get("image_url", "")
    image_prompt = result.get("image_prompt", "")
    parsed_intent = result.get("parsed_intent", {})
    
    print_colored("🖼️ IMAGE GENERATION RESULTS", "36")
    print("─" * 60)
    
    if image_url:
        print_kv("✅ Status", "Image generated successfully")
        print_kv("🖼️ Image URL", image_url)
        print_kv("🎨 Generated Prompt", image_prompt)
        
        if parsed_intent:
            goal = parsed_intent.get("goal", "")
            audience = parsed_intent.get("audience", "")
            if goal:
                print_kv("🎯 Campaign Goal", goal)
            if audience:
                print_kv("👥 Target Audience", audience)
        
        # Check if file exists locally
        if image_url.startswith("/static/images/"):
            file_path = f"static/images/{os.path.basename(image_url)}"
            if os.path.exists(file_path):
                file_size = os.path.getsize(file_path)
                print_kv("📁 Local File", f"{file_path} ({file_size:,} bytes)")
    else:
        print_kv("❌ Status", "Image generation failed")
    
    # Show metadata if available
    meta = result.get("meta", {})
    if meta and "image_generation" in meta:
        img_meta = meta["image_generation"]
        print_colored("\n📊 GENERATION METADATA", "33")
        print("─" * 60)
        print_kv("🤖 Model", img_meta.get("model", "Unknown"))
        print_kv("⚡ Prompt Used", img_meta.get("prompt", "")[:100] + "...")


def main():
    """Run the interactive Image Only Agent chat."""
    print_banner("🖼️ Image Generation Agent")
    
    agent = ImageOnlyAgent()
    
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
                print_image_summary(result)
                
            except KeyboardInterrupt:
                print("\n\n👋 Goodbye!")
                break
            except Exception as e:
                print_colored(f"❌ Error: {str(e)}", "31")
                
    except KeyboardInterrupt:
        print("\n\n👋 Goodbye!")


if __name__ == "__main__":
    main()
