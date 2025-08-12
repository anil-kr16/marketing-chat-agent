from __future__ import annotations

import os
from typing import Literal

from langsmith import traceable
from langchain_openai import ChatOpenAI
from langchain.schema import SystemMessage, HumanMessage

from src.utils.state import MessagesState


def _latest_user_text(state: MessagesState) -> str:
    try:
        from langchain.schema import HumanMessage
        for msg in reversed(state.get("messages", [])):
            if isinstance(msg, HumanMessage):
                return msg.content
        if state.get("messages"):
            return getattr(state["messages"][-1], "content", "")
    except Exception:
        pass
    return ""


def _heuristic_mode(user_text: str) -> Literal["campaign", "chat"] | None:
    text = user_text.strip().lower()
    if not text:
        return None
    # COMMENTED OUT FOR LLM-ONLY TESTING
    # creation_keywords = [
    #     "create", "generate", "write", "draft", "make",
    #     "campaign", "post", "caption", "ad", "email", "subject line",
    #     "hashtags", "cta",
    # ]
    # if any(kw in text for kw in creation_keywords):
    #     return "campaign"
    # chat_clues = ["what", "how", "why", "explain", "news", "trend", "tips", "best practices"]
    # if any(text.startswith(c) for c in chat_clues):
    #     return "chat"
    # TEMPORARY: Return None to always fall back to LLM classification
    return None


def _llm_classify(user_text: str) -> Literal["campaign", "chat"]:
    try:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            return "chat"
        llm = ChatOpenAI(model=os.getenv("LLM_MODEL", "gpt-4o"), temperature=0.0, api_key=api_key)
        system = SystemMessage(content=(
            "Classify the user's message as either 'campaign' or 'chat'.\n"
            "Return ONLY one of these exact strings: campaign or chat."
        ))
        human = HumanMessage(content=f"User message: {user_text}")
        resp = llm.invoke([system, human])
        out = (resp.content or "").strip().lower()
        if "campaign" in out:
            return "campaign"
        return "chat"
    except Exception:
        return "chat"


@traceable(name="Router Node")
def router_node(state: MessagesState) -> MessagesState:
    """Decide agent_mode: 'chat' or 'campaign'."""
    # If we are awaiting a yes/no confirmation from the user, we must stay in
    # campaign mode so the TextCreatorAgent can proceed (or ask for changes).
    # This takes precedence over heuristics and LLM classification.
    try:
        flags = state.get("agent_flags", {}) if isinstance(state.get("agent_flags"), dict) else {}
        if flags.get("awaiting_confirmation") or flags.get("in_campaign"):
            state["agent_mode"] = "campaign"
            return state
    except Exception:
        pass

    # Forced mode via flags
    force_mode = state.get("agent_flags", {}).get("force_mode") if isinstance(state.get("agent_flags"), dict) else None
    if force_mode in {"chat", "campaign"}:
        state["agent_mode"] = force_mode
        return state

    # If essentials are already parsed and the user's last message looks like a
    # confirmation/command to proceed, bias to campaign mode.
    try:
        parsed = state.get("parsed_intent", {}) if isinstance(state.get("parsed_intent"), dict) else {}
        essentials_ok = bool(parsed.get("goal")) and bool(parsed.get("audience")) and bool(parsed.get("channels"))
        if essentials_ok:
            user_text = _latest_user_text(state).strip().lower()
            confirm_tokens = {"yes", "y", "ok", "okay", "go", "proceed", "create", "looks good", "sure", "yes please", "do it"}
            if any(tok in user_text for tok in confirm_tokens):
                state["agent_mode"] = "campaign"
                return state
    except Exception:
        pass

    user_text = _latest_user_text(state)
    mode = _heuristic_mode(user_text)
    if not mode:
        mode = _llm_classify(user_text)

    state["agent_mode"] = mode
    return state


