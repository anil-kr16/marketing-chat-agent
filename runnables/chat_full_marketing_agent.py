#!/usr/bin/env python3
"""
Interactive chat interface for the Full Marketing Agent.
Complete end-to-end marketing campaign generation.

Usage:
    python -m runnables.chat_full_marketing_agent
"""

import sys
import os
from typing import Dict
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

# === NEW STATEFUL CONSULTATION IMPORTS ===
from src.services.consultation_manager import get_consultation_manager
from src.utils.state_converter import consultant_to_campaign_state, preserve_consultation_context
from src.graphs.consultant.stateful_marketing_graph import create_stateful_marketing_graph
from src.utils.marketing_state import MarketingConsultantState, ConsultationStage


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
    """Run the interactive Full Marketing Agent with stateful consultation."""
    print_banner("🚀 Full Marketing Campaign Agent")
    print_colored("Type Ctrl+C to exit", "33")
    print_colored("🧠 Now with intelligent consultation flow!", "36")
    print_colored("💡 Try: 'promote [product]' to start a consultation", "33")
    print()
    
    # Initialize consultation manager and agents
    consultation_manager = get_consultation_manager()
    stateful_graph = create_stateful_marketing_graph().compile()
    agent = FullMarketingAgent()
    
    # Track active consultation sessions per user (simplified for demo)
    active_consultations: Dict[str, str] = {}  # user_id -> session_id
    
    try:
        while True:
            # Get user input
            user_input = input("👤 User: ").strip()
            if not user_input:
                continue
                
            if user_input.lower() in ["exit", "quit", "bye"]:
                print_colored("👋 Goodbye!", "35")
                break
            
            # Check if user is in an active consultation session
            user_id = "demo_user"  # In real app, get from auth
            session_id = active_consultations.get(user_id)
            
            if session_id:
                # User is in active consultation - treat input as answer to current question
                print("─" * 64)
                print_colored("🧠 Continuing consultation...", "32")
                print("─" * 64)
                print_colored("💡 Great! Let me process your answer and ask the next question.", "33")
                print()
                
                try:
                    # Get current consultation state
                    consultation_state = consultation_manager.get_session_state(session_id)
                    if consultation_state:
                        # Update with user's answer
                        if consultation_state.qa_history and not consultation_state.qa_history[-1].get("answer"):
                            consultation_state.update_last_answer(user_input)
                            print_colored(f"✅ Answer received: {user_input}", "32")
                            print()
                            
                            # Continue consultation with the answer
                            consultation_result_dict = stateful_graph.invoke(consultation_state)
                            consultation_result = MarketingConsultantState(**consultation_result_dict)
                            
                            # Update session state
                            consultation_manager.update_session_state(session_id, consultation_result)
                            
                            # Handle consultation result
                            if consultation_result.stage == ConsultationStage.COMPLETED and consultation_result.has_enough_info:
                                # Consultation complete - convert to campaign and execute
                                print_colored("✅ Consultation complete! Creating your campaign...", "32")
                                print()
                                
                                # Show gathered information
                                print("📋 Consultation Summary:")
                                print("─" * 40)
                                for key, value in consultation_result.parsed_intent.items():
                                    if value:
                                        formatted_key = key.replace("_", " ").title()
                                        print_kv(f"📌 {formatted_key}", str(value))
                                print()
                                
                                # Convert consultation state to campaign state
                                campaign_state = consultant_to_campaign_state(consultation_result)
                                
                                # Execute campaign creation
                                campaign_result = agent.run(campaign_state)
                                print_campaign_summary(campaign_result)
                                print()
                                
                                # Mark consultation as complete and cleanup
                                consultation_manager.complete_session(session_id)
                                if user_id in active_consultations:
                                    del active_consultations[user_id]
                                    
                            elif consultation_result.stage == ConsultationStage.GATHERING:
                                # Show next question
                                if consultation_result.qa_history:
                                    last_qa = consultation_result.qa_history[-1]
                                    if last_qa.get("question") and not last_qa.get("answer"):
                                        print_colored("🤖 Assistant:", "32")
                                        print(last_qa["question"])
                                        print()
                                        
                                        # Show progress based on information completeness, not just question count
                                        core_fields = ["goal", "audience", "channels", "budget", "tone", "timeline"]
                                        filled_fields = sum(1 for field in core_fields if consultation_result.parsed_intent.get(field))
                                        total_fields = len(core_fields)
                                        progress = min((filled_fields / total_fields) * 100, 100)
                                        
                                        # Show progress based on information gathered
                                        print_colored(f"💡 Progress: {filled_fields}/{total_fields} fields completed ({progress:.0f}%)", "33")
                                        print()
                            else:
                                # Handle other stages
                                print_colored(f"🤖 Consultation stage: {consultation_result.stage}", "33")
                                print()
                                
                        else:
                            print_colored("❌ No active question to answer", "31")
                            print()
                            
                    else:
                        print_colored("❌ Consultation session expired", "31")
                        if user_id in active_consultations:
                            del active_consultations[user_id]
                        print()
                        
                except Exception as e:
                    print_colored(f"❌ Consultation error: {str(e)}", "31")
                    print("Let me try to help you anyway.")
                    print()
                    if user_id in active_consultations:
                        del active_consultations[user_id]
                        
            elif is_marketing_request(user_input):
                # === NEW STATEFUL CONSULTATION FLOW ===
                print("─" * 64)
                print_colored("🧠 Starting intelligent consultation...", "36")
                print("─" * 64)
                print_colored("💡 I'll ask you a few questions to understand your needs better.", "33")
                print_colored("💡 Just answer naturally - I'll guide you through the process!", "33")
                print()
                
                try:
                    # Create or continue consultation session
                    user_id = "demo_user"  # In real app, get from auth
                    session_id = active_consultations.get(user_id)
                    
                    if session_id:
                        # Continue existing consultation
                        consultation_state = consultation_manager.get_session_state(session_id)
                        if consultation_state:
                            # Update with user's latest response
                            if consultation_state.qa_history and not consultation_state.qa_history[-1].get("answer"):
                                consultation_state.update_last_answer(user_input)
                                # After updating answer, we need to process it and continue consultation
                                user_provided_answer = True
                            else:
                                user_provided_answer = False
                        else:
                            # Session expired, start new one
                            consultation_state = MarketingConsultantState(
                                user_input=user_input,
                                session_id=""
                            )
                            session_id = consultation_manager.create_session(user_input)
                            active_consultations[user_id] = session_id
                            consultation_state.session_id = session_id
                            user_provided_answer = False
                    else:
                        # Start new consultation
                        session_id = consultation_manager.create_session(user_input)
                        active_consultations[user_id] = session_id
                        consultation_state = consultation_manager.get_session_state(session_id)
                        user_provided_answer = False
                        
                    # Ensure we have a valid consultation state
                    if not consultation_state:
                        consultation_state = MarketingConsultantState(
                            user_input=user_input,
                            session_id=session_id
                        )
                        user_provided_answer = False
                    
                    # Run stateful consultation
                    try:
                        consultation_result_dict = stateful_graph.invoke(consultation_state)
                        # Convert dict back to MarketingConsultantState object
                        consultation_result = MarketingConsultantState(**consultation_result_dict)
                    except Exception as consultation_error:
                        print_colored(f"❌ Consultation flow error: {str(consultation_error)}", "31")
                        print("Let me help you create a campaign directly instead.")
                        print()
                        
                        # Fallback to direct campaign creation
                        state: MessagesState = {"messages": [HumanMessage(content=user_input)]}
                        
                        from src.nodes.intent.parse_intent_node import parse_intent_node
                        parsed_state = parse_intent_node(state)
                        
                        campaign_result = agent.run(parsed_state)
                        print_campaign_summary(campaign_result)
                        print()
                        continue
                    
                    # Update session state
                    consultation_manager.update_session_state(session_id, consultation_result)
                    
                    # Check consultation result
                    if consultation_result.stage == ConsultationStage.COMPLETED and consultation_result.has_enough_info:
                        # Consultation complete - convert to campaign and execute
                        print_colored("✅ Consultation complete! Creating your campaign...", "32")
                        print()
                        
                        # Show gathered information
                        print("📋 Consultation Summary:")
                        print("─" * 40)
                        for key, value in consultation_result.parsed_intent.items():
                            if value:
                                formatted_key = key.replace("_", " ").title()
                                print_kv(f"📌 {formatted_key}", str(value))
                        print()
                        
                        # Convert consultation state to campaign state
                        campaign_state = consultant_to_campaign_state(consultation_result)
                        
                        # Show progress indicators
                        print("─" * 64)
                        print_colored("🤖 Assistant: Creating Marketing Campaign...", "32")
                        print("─" * 64)
                        print("📋 Step 1/7: Using consultation data...")
                        print("🎨 Step 2/7: Creating creative brief...")
                        print("📝 Step 3/7: Generating marketing copy...")
                        print("🖼️  Step 4/7: Creating visual content (this may take 15-20s)...")
                        print("🏷️  Step 5/7: Generating hashtags & CTAs...")
                        print("🔍 Step 6/7: Reviewing content quality...")
                        print("📦 Step 7/7: Packaging final campaign...")
                        print()
                        print_colored("⏳ Please wait... (Full process takes ~25-30 seconds)", "33")
                        print()
                        
                        # Execute campaign creation
                        campaign_result = agent.run(campaign_state)
                        
                        # Preserve consultation context in results
                        campaign_result = preserve_consultation_context(consultation_result, campaign_result)
                        
                        # Show results
                        print_colored("✅ CAMPAIGN CREATION COMPLETED!", "32")
                        print()
                        
                        # Print results
                        print_campaign_summary(campaign_result)
                        print()
                        
                        # Mark consultation as complete and cleanup
                        consultation_manager.complete_session(session_id)
                        if user_id in active_consultations:
                            del active_consultations[user_id]
                            
                    elif consultation_result.stage == ConsultationStage.GATHERING:
                        # Consultation needs more info - ask next question
                        if consultation_result.qa_history:
                            last_qa = consultation_result.qa_history[-1]
                            if last_qa.get("question") and not last_qa.get("answer"):
                                # Waiting for user to answer this question
                                print_colored("🤖 Assistant:", "32")
                                print(last_qa["question"])
                                print()
                                
                                # Show progress
                                progress = min((consultation_result.question_count / consultation_result.max_questions) * 100, 100)
                                print_colored(f"💡 Progress: {consultation_result.question_count}/{consultation_result.max_questions} questions ({progress:.0f}%)", "33")
                                print()
                            elif last_qa.get("answer") and user_provided_answer:
                                # User just provided an answer, show next question if available
                                if len(consultation_result.qa_history) > 1:
                                    next_qa = consultation_result.qa_history[-1]
                                    if next_qa.get("question") and not next_qa.get("answer"):
                                        print_colored("🤖 Assistant:", "32")
                                        print(next_qa["question"])
                                        print()
                                        
                                        # Show updated progress
                                        progress = min((consultation_result.question_count / consultation_result.max_questions) * 100, 100)
                                        print_colored(f"💡 Progress: {consultation_result.question_count}/{consultation_result.max_questions} questions ({progress:.0f}%)", "33")
                                        print()
                                    else:
                                        # Processing answer, might be moving to validation
                                        print_colored("🤖 Assistant:", "32")
                                        print("Thank you for that information! Let me process what you've shared and determine what else we need.")
                                        print()
                                else:
                                    # First answer provided, show next question
                                    print_colored("🤖 Assistant:", "32")
                                    print("Great! Now let me ask you the next question to gather more details.")
                                    print()
                        
                    elif consultation_result.stage == ConsultationStage.FAILED:
                        # Consultation failed - provide helpful message
                        print_colored("❌ I had trouble understanding your request.", "31")
                        print("Let me help you with a marketing campaign. What specifically would you like to promote?")
                        print()
                        
                        # Cleanup failed session
                        if user_id in active_consultations:
                            del active_consultations[user_id]
                    
                    else:
                        # Unexpected state - fallback
                        print_colored("🤔 Let me ask a clarifying question to better help you.", "33")
                        print("What specifically would you like to promote or market?")
                        print()
                    
                    # Update session state
                    consultation_manager.update_session_state(session_id, consultation_result)
                    
                    # Check consultation result
                    if consultation_result.stage == ConsultationStage.COMPLETED and consultation_result.has_enough_info:
                        # Consultation complete - convert to campaign and execute
                        print_colored("✅ Consultation complete! Creating your campaign...", "32")
                        print()
                        
                        # Show gathered information
                        print("📋 Consultation Summary:")
                        print("─" * 40)
                        for key, value in consultation_result.parsed_intent.items():
                            if value:
                                formatted_key = key.replace("_", " ").title()
                                print_kv(f"📌 {formatted_key}", str(value))
                        print()
                        
                        # Convert consultation state to campaign state
                        campaign_state = consultant_to_campaign_state(consultation_result)
                        
                        # Show progress indicators
                        print("─" * 64)
                        print_colored("🤖 Assistant: Creating Marketing Campaign...", "32")
                        print("─" * 64)
                        print("📋 Step 1/7: Using consultation data...")
                        print("🎨 Step 2/7: Creating creative brief...")
                        print("📝 Step 3/7: Generating marketing copy...")
                        print("🖼️  Step 4/7: Creating visual content (this may take 15-20s)...")
                        print("🏷️  Step 5/7: Generating hashtags & CTAs...")
                        print("🔍 Step 6/7: Reviewing content quality...")
                        print("📦 Step 7/7: Packaging final campaign...")
                        print()
                        print_colored("⏳ Please wait... (Full process takes ~25-30 seconds)", "33")
                        print()
                        
                        # Execute campaign creation
                        campaign_result = agent.run(campaign_state)
                        
                        # Preserve consultation context in results
                        campaign_result = preserve_consultation_context(consultation_result, campaign_result)
                        
                        # Show results
                        print_colored("✅ CAMPAIGN CREATION COMPLETED!", "32")
                        print()
                        
                        # Print results
                        print_campaign_summary(campaign_result)
                        print()
                        
                        # Mark consultation as complete and cleanup
                        consultation_manager.complete_session(session_id)
                        if user_id in active_consultations:
                            del active_consultations[user_id]
                        
                    elif consultation_result.stage == ConsultationStage.GATHERING:
                        # Consultation needs more info - ask next question
                        if consultation_result.qa_history:
                            last_qa = consultation_result.qa_history[-1]
                            if last_qa.get("question") and not last_qa.get("answer"):
                                # Waiting for user to answer this question
                                print_colored("🤖 Assistant:", "32")
                                print(last_qa["question"])
                                print()
                                
                                # Show progress
                                progress = min((consultation_result.question_count / consultation_result.max_questions) * 100, 100)
                                print_colored(f"💡 Progress: {consultation_result.question_count}/{consultation_result.max_questions} questions ({progress:.0f}%)", "33")
                                print()
                            elif last_qa.get("answer") and user_provided_answer:
                                # User just provided an answer, show next question if available
                                if len(consultation_result.qa_history) > 1:
                                    next_qa = consultation_result.qa_history[-1]
                                    if next_qa.get("question") and not next_qa.get("answer"):
                                        print_colored("🤖 Assistant:", "32")
                                        print(next_qa["question"])
                                        print()
                                        
                                        # Show updated progress
                                        progress = min((consultation_result.question_count / consultation_result.max_questions) * 100, 100)
                                        print_colored(f"💡 Progress: {consultation_result.question_count}/{consultation_result.max_questions} questions ({progress:.0f}%)", "33")
                                        print()
                                    else:
                                        # Processing answer, might be moving to validation
                                        print_colored("🤖 Assistant:", "32")
                                        print("Thank you for that information! Let me process what you've shared and determine what else we need.")
                                        print()
                                else:
                                    # First answer provided, show next question
                                    print_colored("🤖 Assistant:", "32")
                                    print("Great! Now let me ask you the next question to gather more details.")
                                    print()
                        
                    elif consultation_result.stage == ConsultationStage.FAILED:
                        # Consultation failed - provide helpful message
                        print_colored("❌ I had trouble understanding your request.", "31")
                        print("Let me help you with a marketing campaign. What specifically would you like to promote?")
                        print()
                        
                        # Cleanup failed session
                        if user_id in active_consultations:
                            del active_consultations[user_id]
                    
                    else:
                        # Unexpected state - fallback
                        print_colored("🤔 Let me ask a clarifying question to better help you.", "33")
                        print("What specifically would you like to promote or market?")
                        print()
                        
                except Exception as e:
                    print_colored(f"❌ Consultation error: {str(e)}", "31")
                    print("Let me try to help you anyway. What would you like to promote?")
                    print()
                    
                    # Cleanup on error
                    if user_id in active_consultations:
                        del active_consultations[user_id]
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
