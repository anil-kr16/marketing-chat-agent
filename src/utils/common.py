"""
Common utilities shared across nodes.
"""

from __future__ import annotations

import os
import time
import re
from typing import Optional, Any

from src.utils.state import MessagesState


def get_project_root() -> str:
    """Return the absolute path to the repository root.

    Assumes this file lives at `src/utils/common.py`.
    """
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


def get_latest_user_text(state: MessagesState) -> str:
    """Return the most recent user (Human) message content if available.

    Falls back to the last message content if message types are not available.
    """
    try:
        from langchain.schema import HumanMessage
        for message in reversed(state.get("messages", [])):
            if isinstance(message, HumanMessage):
                return message.content
        if state.get("messages"):
            return getattr(state["messages"][-1], "content", "")
    except Exception:
        pass
    return ""


def ensure_dir(path: str) -> str:
    """Create directory if it does not exist and return the path."""
    os.makedirs(path, exist_ok=True)
    return path


def to_camel_case(s: str) -> str:
    """Convert snake_case or kebab-case to camelCase.

    Leaves strings without separators unchanged.
    """
    if not s:
        return s
    # Normalize kebab-case to snake_case
    s = s.replace("-", "_")
    parts = s.split("_")
    return parts[0] + "".join(p.capitalize() or "" for p in parts[1:])


def camelize(obj: Any) -> Any:
    """Recursively convert dict keys to camelCase.

    - Dict: keys camelCased, values processed recursively
    - List/Tuple: elements processed recursively
    - Other: returned as-is
    """
    if isinstance(obj, dict):
        return {to_camel_case(str(k)): camelize(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [camelize(v) for v in obj]
    return obj


def create_campaign_folder(state: MessagesState, outbox_dir: str) -> str:
    """
    Create a unique campaign folder for organizing output files.
    
    Returns the full path to the campaign folder.
    Example: /path/to/outbox/promote_watches_1754894123/
    """
    # Generate campaign folder name
    parsed_intent = state.get("parsed_intent", {})
    goal = parsed_intent.get("goal", "campaign")
    
    # Clean goal for folder name (remove special chars, spaces)
    clean_goal = re.sub(r'[^\w\s-]', '', goal.lower())
    clean_goal = re.sub(r'[-\s]+', '_', clean_goal)[:20]  # Max 20 chars
    
    # Add timestamp for uniqueness
    timestamp = int(time.time())
    folder_name = f"{clean_goal}_{timestamp}"
    
    # Create full path
    campaign_dir = os.path.join(outbox_dir, folder_name)
    ensure_dir(campaign_dir)
    
    return campaign_dir


def is_marketing_request(user_input: str) -> bool:
    """
    Detect if user input is a marketing request vs general chat.
    
    Returns True if the input appears to be asking for marketing/campaign creation.
    """
    input_lower = user_input.lower().strip()
    
    # Marketing keywords (including common typos) - COMMENTED OUT FOR LLM-ONLY TESTING
    # marketing_keywords = [
    #     # Core marketing terms
    #     'promote', 'promoto', 'promoot', 'marketing', 'maarket', 'market',
    #     'campaign', 'advertise', 'advertisement', 'ad', 'ads',
    #     'sell', 'selling', 'launch', 'announce', 'boost',
    #     
    #     # Social media
    #     'instagram', 'facebook', 'twitter', 'social media', 'post',
    #     'hashtag', 'hashtags', 'share', 'viral',
    #     
    #     # Business terms  
    #     'product', 'service', 'brand', 'business', 'company',
    #     'customers', 'audience', 'target', 'sales',
    #     
    #     # Action words
    #     'create', 'generate', 'make', 'build', 'design',
    #     'write', 'craft', 'develop',
    #     
    #     # Specific requests
    #     'email campaign', 'social post', 'content', 'copy',
    #     'slogan', 'tagline', 'cta', 'call to action'
    # ]
    
    # Seasonal/event terms (common in marketing) - COMMENTED OUT FOR LLM-ONLY TESTING
    # seasonal_terms = [
    #     'christmas', 'new year', 'yewar', 'holiday', 'black friday',
    #     'valentine', 'easter', 'halloween', 'thanksgiving', 
    #     'diwali', 'summer', 'winter', 'spring', 'fall'
    # ]
    
    # Check for marketing keywords - COMMENTED OUT FOR LLM-ONLY TESTING
    # for keyword in marketing_keywords:
    #     if keyword in input_lower:
    #         return True
    
    # Check for seasonal terms combined with business context - COMMENTED OUT FOR LLM-ONLY TESTING
    # for term in seasonal_terms:
    #     if term in input_lower and any(biz in input_lower for biz in ['for', 'to', 'promote', 'sell', 'market']):
    #         return True
    
    # Pattern-based detection - COMMENTED OUT FOR LLM-ONLY TESTING
    # marketing_patterns = [
    #     r'promote .+ (to|for|on)',  # "promote X to Y"
    #     r'(create|make|generate) .+ (campaign|ad|post|content)',  # "create X campaign"
    #     r'(sell|market) .+ (to|for)',  # "sell X to Y" 
    #     r'(launch|announce) .+ (product|service)',  # "launch X product"
    #     r'(target|reach) .+ (audience|customers)',  # "target X audience"
    #     r'(boost|increase) .+ (sales|engagement)',  # "boost X sales"
    # ]
    
    # for pattern in marketing_patterns:
    #     if re.search(pattern, input_lower):
    #         return True
    
    # TEMPORARY: Use LLM classification instead of hardcoded keywords
    from src.nodes.router_node import _llm_classify
    
    try:
        result = _llm_classify(user_input)
        return result == "campaign"
    except Exception:
        # Fallback to False if LLM fails
        return False


def chat_response(user_input: str) -> str:
    """
    Generate hardcoded conversational responses for non-marketing queries.
    
    Used when general chat is disabled to keep responses marketing-focused.
    """
    input_lower = user_input.lower().strip()
    
    # Greetings
    greetings = ['hi', 'hello', 'hey', 'good morning', 'good afternoon', 'good evening']
    if any(greeting in input_lower for greeting in greetings):
        return ("👋 Hello! I'm your AI Marketing Assistant. I specialize in creating "
                "compelling marketing campaigns, social media posts, and promotional content.\n\n"
                "Try asking me to promote a product, create a campaign, or generate social media content!")
    
    # Help requests
    help_terms = ['help', 'what can you do', 'what do you do', 'commands', 'options']
    if any(term in input_lower for term in help_terms):
        return ("🚀 I can help you create powerful marketing campaigns! Here's what I can do:\n\n"
                "📝 Generate compelling marketing copy\n"
                "📱 Create social media posts with hashtags\n"
                "🎨 Generate promotional images\n"
                "📧 Draft email campaigns\n"
                "🎯 Target specific audiences and channels\n\n"
                "Example: 'Promote our new smartwatch to fitness enthusiasts on Instagram and Facebook'")
    
    # Status/how are you
    if any(phrase in input_lower for phrase in ['how are you', 'how do you feel', 'what\'s up']):
        return ("🤖 I'm doing great and ready to help with your marketing needs! "
                "I'm optimized for creating engaging campaigns that convert. "
                "What would you like to promote today?")
    
    # Generic fallback
    return ("🎯 I'm focused on helping you create amazing marketing campaigns! "
            "I'm not sure how to help with that request, but I'd love to assist with:\n\n"
            "• Promoting products or services\n"
            "• Creating social media content\n" 
            "• Generating marketing copy\n"
            "• Building email campaigns\n\n"
            "What would you like to market or promote?")

