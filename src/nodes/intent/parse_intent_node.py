from typing import Dict, Any
import re
import os
import json
from dotenv import load_dotenv
from langsmith import traceable
from langchain_openai import ChatOpenAI
from langchain.schema import SystemMessage, HumanMessage
from src.utils.state import MessagesState
from src.utils.common import get_latest_user_text
from src.config import get_config

load_dotenv()

@traceable(name="Parse Intent Node")
def parse_intent_node(state: MessagesState) -> MessagesState:
    """
    Beginner-friendly explanation:

    This node reads the user's latest message and converts it into a structured
    dictionary called "parsed_intent" with keys: goal, audience, channels, tone, budget.
    """
    messages = state["messages"]

    user_input = get_latest_user_text(state)
    last_ai = ""
    try:
        for msg in reversed(state.get("messages", [])):
            if msg.__class__.__name__ == "AIMessage":
                last_ai = getattr(msg, "content", "") or ""
                break
    except Exception:
        last_ai = ""
    
    # Start with prior parsed intent if present so we don't lose context when the
    # user sends short follow-ups like "no - tone should be fun".
    prior: Dict[str, Any] = state.get("parsed_intent", {}) if isinstance(state.get("parsed_intent"), dict) else {}
    parsed_intent: Dict[str, Any] = {
        "goal": "",
        "audience": "",
        "channels": [],
        "tone": "",
        "budget": ""
    }
    
    try:
        # Detect if the last AI turn was a specific clarifying question
        asked_field = None
        if "What is the campaign goal?" in last_ai:
            asked_field = "goal"
        elif "Who is the target audience?" in last_ai:
            asked_field = "audience"
        elif "Which channels should we use?" in last_ai:
            asked_field = "channels"
        elif "Any preferred tone?" in last_ai:
            asked_field = "tone"
        elif "What's the budget" in last_ai or "What’s the budget" in last_ai:
            asked_field = "budget"

        in_confirmation = "Shall I create the post now?" in last_ai

        # If we know which field we asked for, map short answers directly
        cleaned_answer = user_input.strip().strip(' .,!')
        if asked_field and cleaned_answer:
            if asked_field == "channels":
                parts = re.split(r',|\band\b', cleaned_answer, flags=re.IGNORECASE)
                parsed_intent["channels"] = [p.strip().title() for p in parts if p.strip()]
            else:
                parsed_intent[asked_field] = cleaned_answer

        # Goal: from explicit updates first, otherwise from free brief (skip free brief when replying to confirmation)
        explicit_goal = re.search(r'\bgoal\s*(?:should\s*be|is|:|-)\s*(.+)$', user_input, re.IGNORECASE)
        if explicit_goal:
            parsed_intent["goal"] = explicit_goal.group(1).strip().strip(' .,')
        elif not in_confirmation and not asked_field:
            # Extract goal more intelligently - include timing/seasonal context
            # Match patterns like "promote X on new year" -> goal: "promote X on new year"
            # But exclude when "on" is followed by social media channels
            known_channels_pattern = r'\b(?:instagram|facebook|twitter|linkedin|email|youtube|tiktok|snapchat|insta)\b'
            
            # If "on" is followed by a channel, split there. Otherwise, include the full context
            goal_match = re.search(r'^(.*?)(?:\s+(?:to|for)\s+)', user_input, re.IGNORECASE)
            if goal_match:
                parsed_intent["goal"] = goal_match.group(1).strip()
            else:
                # Check if "on" is followed by a channel
                on_channel_match = re.search(rf'^(.*?)\s+on\s+({known_channels_pattern})', user_input, re.IGNORECASE)
                if on_channel_match:
                    parsed_intent["goal"] = on_channel_match.group(1).strip()
                else:
                    # Include everything as goal if no clear channel separation
                    # This handles cases like "promote X on new year" 
                    parsed_intent["goal"] = user_input.strip()
        
        # Audience: explicit updates first, otherwise from free brief (skip generic parse during confirmation replies)
        explicit_audience = re.search(r'\b(audience|audiance)\s*(?:should\s*be|is|:|-)\s*([^\n\r]+)', user_input, re.IGNORECASE)
        if explicit_audience:
            parsed_intent["audience"] = explicit_audience.group(2).strip().strip(' .,')
        elif not in_confirmation and not asked_field:
            audience_match = re.search(r'\bto\s+(.*?)(?:\s+on\s+|\s+via\s+|\s+through\s+|\s+using\s+|\s+with\s+a\s+)', user_input, re.IGNORECASE)
            if audience_match:
                parsed_intent["audience"] = audience_match.group(1).strip()
        
        # Channels: from explicit update or free brief (skip generic parse during confirmation replies)
        explicit_channels = re.search(r'\bchannels?\s*(?:are|is|:|-)\s*([^\n\r]+)', user_input, re.IGNORECASE)
        if explicit_channels:
            raw_channels = explicit_channels.group(1)
            parts = re.split(r',|\band\b', raw_channels, flags=re.IGNORECASE)
            parsed_intent["channels"] = [part.strip().strip(', ').title() for part in parts if part.strip()]
        elif not in_confirmation and not asked_field:
            # Look for specific social media platforms, not just anything after "on"
            known_channels = ['instagram', 'facebook', 'twitter', 'linkedin', 'email', 'youtube', 'tiktok', 'snapchat']
            found_channels = []
            
            for channel in known_channels:
                # Check for channel mentions in various forms
                if re.search(rf'\b{channel}\b', user_input, re.IGNORECASE):
                    found_channels.append(channel.title())
                elif channel == 'instagram' and re.search(r'\binsta\b', user_input, re.IGNORECASE):
                    found_channels.append('Instagram')
            
            if found_channels:
                parsed_intent["channels"] = found_channels
        
        tone_match = re.search(r'\bwith\s+a\s+(.*?)(?:\s*tone\b|\s*voice\b|\s*approach\b|\s*style\b|\.|\s+budget\b)', user_input, re.IGNORECASE)
        if tone_match:
            parsed_intent["tone"] = tone_match.group(1).strip()
        else:
            # Also handle follow-ups like: "tone should be fun" or "tone: playful"
            alt_tone = re.search(r'\btone\s*(?:should\s*be|is|:)\s*([a-zA-Z ,\-]+)', user_input, re.IGNORECASE)
            if alt_tone:
                parsed_intent["tone"] = alt_tone.group(1).strip().strip(' .,')
        
        budget_match = re.search(r'\bbudget\s+(?:is\s+)?(\$?\s*\d{1,3}(?:,\d{3})*(?:\.\d+)?|\$?\s*\d+\s*k)', user_input, re.IGNORECASE)
        if budget_match:
            parsed_intent["budget"] = budget_match.group(1).replace(' ', '')

        # Decide whether to invoke LLM fallback. Avoid fallback for short corrective turns,
        # confirmation replies, or when we already have a prior intent and this turn is short,
        # to prevent the LLM from fabricating unrelated defaults.
        explicit_update = any([
            bool(parsed_intent["goal"]),
            bool(parsed_intent["audience"]),
            bool(parsed_intent["channels"]),
            bool(parsed_intent["tone"]),
            bool(parsed_intent["budget"]),
        ])
        short_turn = len(user_input.strip()) < 40

        if (not all([
            parsed_intent["goal"],
            parsed_intent["audience"],
            parsed_intent["channels"],
            parsed_intent["tone"],
            parsed_intent["budget"],
        ])) and not (explicit_update and short_turn) and not in_confirmation and not (prior and short_turn):
            cfg = get_config()
            api_key = cfg.openai_api_key
            if api_key:
                try:
                    llm = ChatOpenAI(model=cfg.llm_model, temperature=0.1, api_key=api_key)
                    system_message = SystemMessage(content=(
                        "You extract structured marketing campaign intent from user text. "
                        "Return ONLY a valid JSON object with this exact schema: "
                        "{\"goal\": string, \"audience\": string, \"channels\": string[], \"tone\": string, \"budget\": string}. "
                        "Do not include markdown, code fences, or any extra text."
                    ))
                    human_message = HumanMessage(content=f"User input: {user_input}\nExtract the JSON now.")
                    response = llm.invoke([system_message, human_message])
                    content = getattr(response, "content", "")

                    meta_entry = {
                        "node": "parse_intent",
                        "model": getattr(llm, "model", "gpt-4o"),
                        "usage": getattr(response, "usage_metadata", None),
                        "response_metadata": getattr(response, "response_metadata", None),
                    }
                    try:
                        state_meta = state.setdefault("meta", {})
                        state_meta["parse_intent_llm"] = meta_entry
                    except Exception:
                        pass

                    llm_data = None
                    try:
                        llm_data = json.loads(content)
                    except Exception:
                        match = re.search(r"\{[\s\S]*\}", content)
                        if match:
                            try:
                                llm_data = json.loads(match.group(0))
                            except Exception:
                                llm_data = None

                    if isinstance(llm_data, dict):
                        if isinstance(llm_data.get("goal"), str) and llm_data.get("goal").strip():
                            parsed_intent["goal"] = llm_data["goal"].strip()
                        if isinstance(llm_data.get("audience"), str) and llm_data.get("audience").strip():
                            parsed_intent["audience"] = llm_data["audience"].strip()

                        channels_value = llm_data.get("channels")
                        if isinstance(channels_value, list):
                            parsed_intent["channels"] = [str(c).strip().title() for c in channels_value if str(c).strip()]
                        elif isinstance(channels_value, str) and channels_value.strip():
                            parts = re.split(r',|\band\b', channels_value, flags=re.IGNORECASE)
                            parsed_intent["channels"] = [p.strip().title() for p in parts if p.strip()]

                        if isinstance(llm_data.get("tone"), str) and llm_data.get("tone").strip():
                            parsed_intent["tone"] = llm_data["tone"].strip()
                        if isinstance(llm_data.get("budget"), str) and llm_data.get("budget").strip():
                            parsed_intent["budget"] = llm_data["budget"].strip()
                except Exception as llm_error:
                    print(f"LLM fallback failed: {llm_error}")
        
        # Merge with prior to avoid wiping previously captured values
        merged = {
            "goal": parsed_intent["goal"] or prior.get("goal", ""),
            "audience": parsed_intent["audience"] or prior.get("audience", ""),
            "channels": parsed_intent["channels"] or prior.get("channels", []),
            "tone": parsed_intent["tone"] or prior.get("tone", ""),
            "budget": parsed_intent["budget"] or prior.get("budget", ""),
        }
        state["parsed_intent"] = merged
        return state
        
    except Exception as e:
        print(f"Error parsing intent: {str(e)}")
        print(f"Input text: {user_input}")
        raise

