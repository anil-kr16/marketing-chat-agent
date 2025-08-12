import os
import base64
import time
from typing import Dict

from dotenv import load_dotenv
from langsmith import traceable
from src.utils.state import MessagesState
from langchain.schema import HumanMessage, BaseMessage
from src.config import get_config
from src.utils.common import get_latest_user_text, get_project_root, ensure_dir


def _ensure_image_dir() -> str:
    project_root = get_project_root()
    images_dir = os.path.join(project_root, "static", "images")
    ensure_dir(images_dir)
    return images_dir


def _build_prompt_from_intent(intent: Dict) -> str:
    goal = intent.get("goal") or "Marketing campaign visual"
    audience = intent.get("audience") or "general audience"
    channels = intent.get("channels") or []
    tone = intent.get("tone") or "modern, engaging"
    channels_str = ", ".join(channels) if channels else "social platforms"
    return (
        f"Create a high-quality marketing visual for: {goal}. "
        f"Target audience: {audience}. Primary channels: {channels_str}. "
        f"Art direction: {tone}. Use clear brand-friendly composition, strong focal subject, "
        f"balanced negative space, legible text area, and vibrant, eye-catching color palette."
    )


@traceable(name="Image Generation Node")
def image_generation_node(state: MessagesState) -> MessagesState:
    load_dotenv()

    parsed_intent = state.get("parsed_intent", {}) if isinstance(state, dict) else {}
    has_intent_data = bool(
        (parsed_intent.get("goal") or "")
        or (parsed_intent.get("audience") or "")
        or (parsed_intent.get("tone") or "")
        or (parsed_intent.get("channels") or [])
    )

    if has_intent_data:
        prompt = _build_prompt_from_intent(parsed_intent)
    else:
        user_text = get_latest_user_text(state)
        prompt = (
            f"Create a high-quality marketing visual based on this brief: {user_text}. "
            f"Use clear brand-friendly composition, strong focal subject, balanced negative space, "
            f"legible text area, and a vibrant, eye-catching palette."
        )

    try:
        from openai import OpenAI  # type: ignore
    except Exception as e:
        print(f"OpenAI SDK not available: {e}")
        return state

    cfg = get_config()
    client = OpenAI()

    saved_url = None
    try:
        response = client.images.generate(
            model="dall-e-3",
            prompt=prompt,
            size="1024x1024",
            n=1,
        )
        if response and getattr(response, "data", None):
            # Get the URL from the response and download the image
            remote_url = response.data[0].url
            if remote_url:
                import requests
                r = requests.get(remote_url, timeout=60)
                r.raise_for_status()
                images_dir = _ensure_image_dir()
                filename = f"generated_{int(time.time())}.png"
                file_path = os.path.join(images_dir, filename)
                with open(file_path, "wb") as f:
                    f.write(r.content)
                saved_url = f"/static/images/{filename}"
            try:
                state_meta = state.setdefault("meta", {})
                state_meta["image_generation"] = {
                    "model": cfg.image_model,
                    "response_metadata": getattr(response, "data", [{}])[0].__dict__ if getattr(response, "data", None) else None,
                    "prompt": prompt,
                    "output_path": file_path,
                }
            except Exception:
                pass
    except Exception as e:
        print(f"Image generation failed: {e}")

    # If first attempt failed, the error is already printed above

    if saved_url:
        state["image_url"] = saved_url
        state["image_prompt"] = prompt

    return state

