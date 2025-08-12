#!/usr/bin/env python3
"""
Interactive chat interface for the Full Marketing Agent.
Complete end-to-end marketing campaign generation.

Usage:
    python -m runnables.chat_full_marketing_agent
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from langchain.schema import HumanMessage

from src.agents.campaign.full_marketing_agent import FullMarketingAgent
from src.agents.text_agent.utils.ui import (
    print_colored, print_banner, format_message, 
    print_summary_header, print_kv
)
from src.utils.state import MessagesState
from src.utils.common import is_marketing_request, chat_response
from src.nodes.llm_node import llm_node
from src.config import get_config


def print_monitoring_summary(result: MessagesState):
    """Print beautiful monitoring and performance data."""
    meta = result.get("meta", {})
    final_response = result.get("final_response", {})
    llm_metadata = final_response.get("llmMetadata", {})
    
    # Combine all metadata sources
    all_metadata = {**meta, **llm_metadata}
    
    if not all_metadata:
        return
        
    print_colored("\n📊 PERFORMANCE & MONITORING", "36")
    print("═" * 64)
    
    # 1. LLM Usage Summary
    llm_calls = {}
    total_tokens = 0
    total_input_tokens = 0  
    total_output_tokens = 0
    
    for key, data in all_metadata.items():
        if isinstance(data, dict) and "model" in data:
            usage = data.get("usage", {})
            if usage:
                input_tokens = usage.get("input_tokens", 0)
                output_tokens = usage.get("output_tokens", 0)
                total_call_tokens = usage.get("total_tokens", input_tokens + output_tokens)
                
                llm_calls[key] = {
                    "model": data.get("model", "Unknown"),
                    "input_tokens": input_tokens,
                    "output_tokens": output_tokens,
                    "total_tokens": total_call_tokens
                }
                
                total_tokens += total_call_tokens
                total_input_tokens += input_tokens
                total_output_tokens += output_tokens
    
    if llm_calls:
        print_colored("🤖 LLM Usage Summary:", "33")
        print("─" * 40)
        
        for call_name, data in llm_calls.items():
            # Clean up call name for display
            display_name = call_name.replace("_llm", "").replace("_", " ").title()
            model = data["model"]
            tokens_str = f"{data['total_tokens']} tokens ({data['input_tokens']} in + {data['output_tokens']} out)"
            print(f"  • {display_name}: {model}")
            print(f"    └─ {tokens_str}")
        
        print()
        print_colored(f"📈 Total Usage: {total_tokens} tokens ({total_input_tokens} in + {total_output_tokens} out)", "32")
        print_colored(f"🔢 LLM Calls Made: {len(llm_calls)}", "32")
    
    # 2. Image Generation Details  
    image_meta = all_metadata.get("image_generation", {})
    if image_meta:
        print()
        print_colored("🖼️ Image Generation:", "35")
        print("─" * 40)
        model = image_meta.get("model", "Unknown")
        print(f"  • Model: {model}")
        
        if "output_path" in image_meta:
            filename = image_meta["output_path"].split("/")[-1]
            print(f"  • Generated File: {filename}")
        
        if "response_metadata" in image_meta:
            resp_meta = image_meta["response_metadata"]
            if "revised_prompt" in resp_meta:
                revised = resp_meta["revised_prompt"][:100] + "..." if len(resp_meta["revised_prompt"]) > 100 else resp_meta["revised_prompt"]
                print(f"  • Revised Prompt: {revised}")
    
    # 3. Performance Timing (if available)
    delivery = result.get("delivery", {})
    if delivery.get("results"):
        print()
        print_colored("📬 Delivery Performance:", "34")
        print("─" * 40)
        delivered_count = len([r for r in delivery["results"].values() if "Successfully" in r])
        total_channels = len(delivery["results"])
        print(f"  • Channels Delivered: {delivered_count}/{total_channels}")
        print(f"  • Success Rate: {(delivered_count/total_channels*100):.1f}%")
    
    # 4. Model Details  
    if llm_calls:
        print()
        print_colored("⚙️ Model Details:", "90")
        print("─" * 40)
        unique_models = set(data["model"] for data in llm_calls.values())
        for model in unique_models:
            calls_count = sum(1 for data in llm_calls.values() if data["model"] == model)
            print(f"  • {model}: {calls_count} call{'s' if calls_count > 1 else ''}")
    
    print("═" * 64)


def print_campaign_summary(result: MessagesState):
    """Print a comprehensive summary of the marketing campaign results."""
    print_summary_header()
    
    # Campaign intent
    parsed_intent = result.get("parsed_intent", {})
    if parsed_intent:
        print_colored("🎯 CAMPAIGN OVERVIEW", "36")
        print("─" * 60)
        print_kv("Goal", parsed_intent.get("goal", "Not specified"))
        print_kv("Audience", parsed_intent.get("audience", "Not specified"))
        print_kv("Channels", ", ".join(parsed_intent.get("channels", [])))
        print_kv("Tone", parsed_intent.get("tone", "Not specified"))
        if parsed_intent.get("budget"):
            print_kv("Budget", parsed_intent.get("budget"))
    
    # Generated content
    print_colored("\n📝 GENERATED CONTENT", "33")
    print("─" * 60)
    
    post_content = result.get("post_content", "")
    if post_content:
        print_kv("✅ Marketing Copy", post_content)
    
    hashtags = result.get("hashtags", [])
    if hashtags:
        print_kv("🏷️ Hashtags", " ".join(hashtags))
    
    ctas = result.get("ctas", [])
    if ctas:
        print_kv("📢 CTAs", ", ".join(ctas))
    
    image_url = result.get("image_url", "")
    if image_url:
        print_kv("🖼️ Generated Image", image_url)
    
    # Review results
    if "review_approved" in result:
        print_colored("\n🔍 CONTENT REVIEW", "35")
        print("─" * 60)
        approved = result.get("review_approved", False)
        status = "✅ APPROVED" if approved else "❌ REJECTED"
        print_kv("Review Status", status)
        
        comments = result.get("review_comments", "")
        if comments:
            print_kv("Review Comments", comments)
    
    # Delivery results
    delivery = result.get("delivery", {})
    if delivery:
        print_colored("\n📱 DELIVERY RESULTS", "32")
        print("─" * 60)
        
        requested = delivery.get("requested", [])
        if requested:
            print_kv("Requested Channels", ", ".join(requested))
        
        delivery_results = delivery.get("results", {})
        for channel, status in delivery_results.items():
            status_icon = "✅" if "Successfully" in status else "❌"
            print_kv(f"{status_icon} {channel.title()}", status)
    
    # Final response structure
    final_response = result.get("final_response", {})
    if final_response:
        print_colored("\n📋 CAMPAIGN PACKAGE", "34")
        print("─" * 60)
        
        email = final_response.get("email", {})
        if email:
            print_kv("Email Subject", email.get("subject", ""))
        
        social_posts = final_response.get("socialMediaPosts", [])
        if social_posts:
            print_kv("Social Media Posts", f"{len(social_posts)} posts created")
    
    # Metadata and tracking
    meta = result.get("meta", {})
    if meta:
        print_colored("\n📊 PERFORMANCE METRICS", "33")
        print("─" * 60)
        
        # Collect all LLM calls
        llm_calls = []
        for key, value in meta.items():
            if key.endswith("_llm") and isinstance(value, dict):
                llm_calls.append((key, value))
        
        if llm_calls:
            total_tokens = 0
            for call_name, call_data in llm_calls:
                model = call_data.get("model", "Unknown")
                usage = call_data.get("usage") or call_data.get("token_usage", {})
                
                if hasattr(usage, 'total_tokens'):
                    tokens = usage.total_tokens
                    total_tokens += tokens
                elif isinstance(usage, dict):
                    tokens = usage.get("total_tokens", 0)
                    total_tokens += tokens
                else:
                    tokens = 0
                
                print_kv(f"🤖 {call_name.replace('_', ' ').title()}", f"{model} ({tokens} tokens)")
            
            print_kv("🔢 Total Tokens Used", str(total_tokens))
        
        # Image generation info
        image_meta = meta.get("image_generation", {})
        if image_meta:
            print_kv("🖼️ Image Model", image_meta.get("model", "DALL-E 3"))
    
    # Beautiful monitoring section - show AFTER all campaign results
    print_monitoring_summary(result)


def is_marketing_request(user_input: str) -> bool:
    """Detect if user input is a marketing campaign request."""
    # COMMENTED OUT FOR LLM-ONLY TESTING
    # marketing_keywords = [
    #     "promote", "promoto", "promte", "promo", "marketing", "market", "maarket", 
    #     "campaign", "advertise", "sell", "launch", "announce", "create a campaign", 
    #     "social media post", "email campaign", "instagram", "facebook", 
    #     "twitter", "linkedin", "brand", "product", "service", "customer", 
    #     "audience", "target", "sales", "revenue", "conversion", "engagement", 
    #     "awareness", "ad", "ads", "commercial", "publicity"
    # ]
    
    user_lower = user_input.lower()
    
    # Check for exact keyword matches - COMMENTED OUT FOR LLM-ONLY TESTING
    # if any(keyword in user_lower for keyword in marketing_keywords):
    #     return True
    
    # Check for common marketing patterns (more flexible) - COMMENTED OUT FOR LLM-ONLY TESTING
    # marketing_patterns = [
    #     "create campaign", "make ad", "build campaign", "design ad",
    #     "want to promote", "need to market", "help me sell",
    #     "on instagram", "on facebook", "on twitter", "on linkedin",
    #     "for diwali", "for new year", "on new year", "new year", 
    #     "for sale", "for launch", "to kids", "to audience"
    # ]
    
    # if any(pattern in user_lower for pattern in marketing_patterns):
    #     return True
    
    # Check for action + product combinations - COMMENTED OUT FOR LLM-ONLY TESTING
    # action_words = ["lets", "let's", "help", "create", "make", "build", "design"]
    # product_indicators = ["tags", "post", "content", "ad", "campaign", "copy"]
    
    # has_action = any(action in user_lower for action in action_words)
    # has_product = any(product in user_lower for product in product_indicators)
    
    # return has_action and has_product
    
    # TEMPORARY: Use LLM classification instead of hardcoded keywords
    from src.nodes.router_node import _llm_classify
    
    try:
        result = _llm_classify(user_input)
        return result == "campaign"
    except Exception:
        # Fallback to False if LLM fails
        return False


def chat_response(user_input: str) -> str:
    """Generate conversational response for non-marketing requests."""
    user_lower = user_input.lower()
    
    if any(greeting in user_lower for greeting in ["hi", "hello", "hey", "good morning", "good afternoon"]):
        return """Hello! I'm your AI Marketing Agent. I help create complete marketing campaigns!

💡 Just tell me what you want to promote, and I'll create:
   📝 Marketing copy
   🖼️ Visual content  
   🏷️ Hashtags & CTAs
   📧 Multi-channel delivery

📌 Try saying something like:
   • "promote new smartphones to tech enthusiasts on instagram"
   • "create a campaign for diwali jewelry sale"
   • "market fitness app to young professionals"

What would you like to promote today?"""
    
    elif any(word in user_lower for word in ["help", "what can you do", "capabilities"]):
        return """I'm a Full Marketing Campaign Agent! Here's what I can do:

✅ **Complete Campaign Creation:**
   📝 Generate compelling marketing copy
   🖼️ Create stunning visuals with DALL-E
   🏷️ Design hashtags and call-to-actions
   📊 Multi-channel delivery (Email, Instagram, Facebook, LinkedIn)

✅ **Smart Features:**
   🎯 Audience targeting
   🔍 Intent parsing
   📈 Performance optimization
   🌍 Cultural sensitivity

📌 **How to use me:**
Just describe what you want to promote! Examples:
   • "promote eco-friendly products to millennials"
   • "launch B2B software for startups on linkedin"
   • "announce holiday sale for fashion brand"

Ready to create something amazing?"""
    
    elif any(word in user_lower for word in ["thanks", "thank you", "awesome", "great"]):
        return "You're welcome! Ready to create your next marketing campaign? Just tell me what you'd like to promote!"
    
    else:
        return f"""I'm not sure how to help with that specific request.

I specialize in creating marketing campaigns! Try asking me to:
   • "promote [your product/service]"
   • "create a campaign for [your business]" 
   • "market [your offering] to [target audience]"

What would you like to promote today?"""


def main():
    """Run the interactive Full Marketing Agent chat."""
    print_banner("🚀 Full Marketing Campaign Agent")
    print_colored("Type Ctrl+C to exit", "33")
    print()
    
    # Initialize agent
    agent = FullMarketingAgent()
    
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
                # Initialize fresh state for marketing workflow
                state: MessagesState = {"messages": [HumanMessage(content=user_input)]}
                
                # Parse intent first to show user what we understood
                from src.nodes.intent.parse_intent_node import parse_intent_node
                parsed_state = parse_intent_node(state)
                parsed_intent = parsed_state.get("parsed_intent", {})
                
                # Show what we understood before execution
                print("─" * 64)
                print_colored("🤖 Assistant: I understand you want to:", "32")
                print("─" * 64)
                print_kv("📝 Goal", parsed_intent.get("goal", "Not specified"))
                print_kv("🎯 Audience", parsed_intent.get("audience", "Not specified"))
                print_kv("📱 Channels", ", ".join(parsed_intent.get("channels", [])) or "Default channels")
                print_kv("🎨 Tone", parsed_intent.get("tone", "Not specified"))
                print_kv("💰 Budget", parsed_intent.get("budget", "Not specified"))
                print()
                
                # Create visual separator for execution
                print("─" * 64)
                print_colored("🤖 Assistant: Creating Marketing Campaign...", "32")
                print("─" * 64)
                
                # Show progress indicators
                print("📋 Step 1/7: Parsing your request...")
                print("🎨 Step 2/7: Creating creative brief...")
                print("📝 Step 3/7: Generating marketing copy...")
                print("🖼️  Step 4/7: Creating visual content (this may take 15-20s)...")
                print("🏷️  Step 5/7: Generating hashtags & CTAs...")
                print("🔍 Step 6/7: Reviewing content quality...")
                print("📦 Step 7/7: Packaging final campaign...")
                print()
                print_colored("⏳ Please wait... (Full process takes ~25-30 seconds)", "33")
                print()
                
                try:
                    # Run the full marketing agent with already-parsed state
                    result = agent.run(parsed_state)
                    
                    # Clear progress and show results
                    print_colored("✅ CAMPAIGN CREATION COMPLETED!", "32")
                    print()
                    
                    # Print comprehensive summary
                    print_campaign_summary(result)
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
