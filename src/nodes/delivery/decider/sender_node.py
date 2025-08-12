from __future__ import annotations

from typing import Any, Dict, List

from langsmith import traceable

from src.utils.state import MessagesState
from src.config import get_config


def _route_channels(state: MessagesState) -> List[str]:
    cfg = get_config()
    requested = []
    intent = state.get("parsed_intent", {})
    for ch in intent.get("channels", []) or []:
        if isinstance(ch, str) and ch.strip():
            requested.append(ch.strip().title())
    # If no channels specified, use ALL enabled channels
    if not requested:
        if cfg.enable_email:
            requested.append("Email")
        if cfg.enable_facebook:
            requested.append("Facebook")
        if cfg.enable_instagram:
            requested.append("Instagram")
        if cfg.enable_twitter:
            requested.append("Twitter")
        if cfg.enable_linkedin:
            requested.append("LinkedIn")
    allowed = []
    for ch in requested:
        if ch == "Email" and cfg.enable_email:
            allowed.append("Email")
        elif ch in {"Instagram", "Insta"} and cfg.enable_instagram:
            allowed.append("Instagram")
        elif ch == "Facebook" and cfg.enable_facebook:
            allowed.append("Facebook")
        elif ch in {"Twitter", "X"} and cfg.enable_twitter:
            allowed.append("Twitter")
        elif ch == "Linkedin" and cfg.enable_linkedin:
            allowed.append("LinkedIn")
    seen = set()
    result = []
    for ch in allowed:
        key = ch.lower()
        if key not in seen:
            seen.add(key)
            result.append(ch)
    return result


@traceable(name="Sender Node")
def sender_node(state: MessagesState) -> MessagesState:
    channels = _route_channels(state)
    state["deliveryPlan"] = {"channels": channels, "decider": "SenderNode"}
    state["delivery"] = {"requested": channels, "results": {}}
    return state

