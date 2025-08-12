from typing import Dict
import os

from dotenv import load_dotenv
from langsmith import traceable
from langchain_openai import ChatOpenAI
from langchain.schema import SystemMessage, HumanMessage
from src.config import get_config
from src.utils.common import get_latest_user_text
from src.utils.openai import build_llm
from src.utils.state import MessagesState


def _build_text_prompt(intent: Dict, fallback_user_text: str) -> str:
    if intent:
        goal = intent.get("goal") or "a product marketing campaign"
        audience = intent.get("audience") or "the target audience"
        channels = intent.get("channels") or []
        tone = intent.get("tone") or "engaging and brand-friendly"
        channels_str = ", ".join(channels) if channels else "social channels"
        
        # Include original user context to preserve cultural references and specific details
        context_note = f"\n\nOriginal user context for additional details: '{fallback_user_text}'" if fallback_user_text else ""
        
        return (
            f"Write a concise, high-conversion social post for {channels_str}. "
            f"Campaign goal: {goal}. Audience: {audience}. Tone: {tone}. "
            f"Keep it 40-80 words, include a clear benefit and a clean call-to-action."
            f"{context_note}"
        )
    else:
        return (
            "Write a concise, high-conversion marketing post (40-80 words) based on this brief: "
            f"{fallback_user_text}. Include a clear benefit and a clean call-to-action."
        )


@traceable(name="Text Generation Node")
def text_generation_node(state: MessagesState) -> MessagesState:
    """Generate short marketing copy; fallback to user text if intent missing."""
    load_dotenv()

    parsed_intent: Dict = state.get("parsed_intent", {}) if isinstance(state, dict) else {}
    
    # Get original user input (not just latest) to preserve cultural context
    fallback_user_text = get_latest_user_text(state)
    
    # Look for the first substantial user input to preserve cultural context
    original_user_text = ""
    try:
        from langchain.schema import HumanMessage
        for message in state.get("messages", []):
            if isinstance(message, HumanMessage):
                content = message.content.strip()
                # Skip short confirmation responses
                if len(content) > 10 and content.lower() not in {"yes", "no", "email", "instagram", "facebook", "twitter", "linkedin"}:
                    original_user_text = content
                    break
    except Exception:
        pass
    
    # Use original user text if it's more substantial than fallback
    context_text = original_user_text if len(original_user_text) > len(fallback_user_text) else fallback_user_text
    prompt = _build_text_prompt(parsed_intent, context_text)

    cfg = get_config()
    api_key = cfg.openai_api_key
    if not api_key:
        return state

    llm = build_llm()

    system = SystemMessage(content=(
        "You are a skilled marketing copywriter. Return only the post text without extra explanations."
    ))
    human = HumanMessage(content=prompt)

    try:
        response = llm.invoke([system, human])
        content = getattr(response, "content", "").strip()
        if content:
            state["post_content"] = content

        try:
            state_meta = state.setdefault("meta", {})
            state_meta["text_generation_llm"] = {
                "model": getattr(llm, "model", "gpt-4o"),
                "usage": getattr(response, "usage_metadata", None),
                "response_metadata": getattr(response, "response_metadata", None),
                "prompt": prompt,
            }
        except Exception:
            pass
    except Exception as e:
        print(f"Text generation failed: {e}")

    return state

