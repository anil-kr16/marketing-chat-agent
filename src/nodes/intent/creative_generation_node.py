from __future__ import annotations

from typing import Any, Dict

from langsmith import traceable

from src.utils.state import MessagesState
from src.utils.common import get_latest_user_text


@traceable(name="Creative Generation Node")
def creative_generation_node(state: MessagesState) -> MessagesState:
    """Prepare a robust creative brief and prompt hints for downstream nodes."""

    parsed_intent: Dict[str, Any] = state.get("parsed_intent", {}) if isinstance(state, dict) else {}
    user_text = get_latest_user_text(state)

    goal = parsed_intent.get("goal") or (user_text[:80] + "...") if user_text else "Marketing Campaign"
    audience = parsed_intent.get("audience") or "General audience"
    channels = parsed_intent.get("channels") or ["Generic"]
    tone = parsed_intent.get("tone") or "Engaging, brand-friendly"
    budget = parsed_intent.get("budget") or "N/A"

    primary_channel = channels[0] if isinstance(channels, list) and channels else "Generic"

    creative_brief = {
        "goal": goal,
        "audience": audience,
        "channels": channels,
        "primary_channel": primary_channel,
        "tone": tone,
        "budget": budget,
    }

    state["creative_brief"] = creative_brief
    state["image_prompt_hint"] = (
        f"Visual for: {goal}. Audience: {audience}. Channel focus: {primary_channel}. Tone: {tone}."
    )
    state["text_prompt_hint"] = (
        f"Write a short post for {primary_channel}. Goal: {goal}. Audience: {audience}. Tone: {tone}."
    )
    state["cta_prompt_hint"] = (
        f"CTAs for {primary_channel}. Goal: {goal}. Audience: {audience}. Tone: {tone}."
    )
    state["hashtag_prompt_hint"] = (
        f"Hashtags for {primary_channel}. Goal: {goal}. Audience: {audience}. Tone: {tone}."
    )

    return state

