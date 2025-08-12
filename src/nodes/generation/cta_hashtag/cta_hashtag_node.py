from typing import Dict, List
import os

from dotenv import load_dotenv
from langsmith import traceable
from langchain_openai import ChatOpenAI
from langchain.schema import SystemMessage, HumanMessage

from src.config import get_config
from src.utils.common import get_latest_user_text
from src.utils.openai import build_llm
from src.utils.state import MessagesState


def _build_hashtag_prompt(intent: Dict, fallback_user_text: str) -> str:
    if intent:
        goal = intent.get("goal") or "marketing campaign"
        audience = intent.get("audience") or "target audience"
        tone = intent.get("tone") or "brand-appropriate"
        return (
            f"Generate 10 short, platform-friendly hashtags for a campaign. "
            f"Goal: {goal}. Audience: {audience}. Tone: {tone}. "
            f"Return a comma-separated list, no explanations, no # inside words that don't need it."
        )
    else:
        return (
            "Generate 10 short, platform-friendly hashtags for this brief: "
            f"{fallback_user_text}. Return a comma-separated list, no explanations."
        )


def _build_cta_prompt(intent: Dict, fallback_user_text: str) -> str:
    if intent:
        goal = intent.get("goal") or "marketing campaign"
        audience = intent.get("audience") or "target audience"
        tone = intent.get("tone") or "brand-appropriate"
        return (
            f"Generate 3 crisp call-to-action (CTA) lines for the campaign. "
            f"Goal: {goal}. Audience: {audience}. Tone: {tone}. "
            f"Each CTA must be under 8 words. Return as a bullet list with no extra text."
        )
    else:
        return (
            "Generate 3 crisp call-to-action (CTA) lines under 8 words based on this brief: "
            f"{fallback_user_text}. Return as a bullet list only."
        )


@traceable(name="CTA & Hashtag Node")
def cta_hashtag_node(state: MessagesState) -> MessagesState:
    load_dotenv()

    parsed_intent: Dict = state.get("parsed_intent", {}) if isinstance(state, dict) else {}
    fallback_user_text = get_latest_user_text(state)

    cfg = get_config()
    if not cfg.openai_api_key:
        return state

    llm = build_llm()

    # Hashtags
    hashtags_prompt = _build_hashtag_prompt(parsed_intent, fallback_user_text)
    try:
        hashtags_resp = llm.invoke([
            SystemMessage(content="You are a marketing assistant. Return only the requested list."),
            HumanMessage(content=hashtags_prompt),
        ])
        hashtags_raw = getattr(hashtags_resp, "content", "")
        parts = [h.strip() for h in hashtags_raw.replace("\n", ",").split(",")]
        hashtags: List[str] = [p if p.startswith("#") else f"#{p}" for p in parts if p]
        seen = set()
        cleaned = []
        for h in hashtags:
            if h.lower() not in seen and len(h) <= 30:
                seen.add(h.lower())
                cleaned.append(h)
        if cleaned:
            state["hashtags"] = cleaned[:10]
        try:
            state_meta = state.setdefault("meta", {})
            state_meta["hashtags_llm"] = {
                "model": getattr(llm, "model", "gpt-4o"),
                "usage": getattr(hashtags_resp, "usage_metadata", None),
                "response_metadata": getattr(hashtags_resp, "response_metadata", None),
                "prompt": hashtags_prompt,
            }
        except Exception:
            pass
    except Exception as e:
        print(f"Hashtag generation failed: {e}")

    # CTAs
    ctas_prompt = _build_cta_prompt(parsed_intent, fallback_user_text)
    try:
        ctas_resp = llm.invoke([
            SystemMessage(content="You are a marketing assistant. Return only the requested list."),
            HumanMessage(content=ctas_prompt),
        ])
        ctas_raw = getattr(ctas_resp, "content", "")
        lines = [l.strip("- ") for l in ctas_raw.splitlines() if l.strip()]
        ctas = [l for l in lines if 0 < len(l) <= 60]
        if ctas:
            state["ctas"] = ctas[:3]
        try:
            state_meta = state.setdefault("meta", {})
            state_meta["ctas_llm"] = {
                "model": getattr(llm, "model", "gpt-4o"),
                "usage": getattr(ctas_resp, "usage_metadata", None),
                "response_metadata": getattr(ctas_resp, "response_metadata", None),
                "prompt": ctas_prompt,
            }
        except Exception:
            pass
    except Exception as e:
        print(f"CTA generation failed: {e}")

    return state

