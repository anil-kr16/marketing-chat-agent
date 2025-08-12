from typing import Any, Dict, List
from langsmith import traceable
from src.utils.state import MessagesState


def _get_latest_user_message(state: MessagesState) -> str:
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


def _build_social_posts(parsed_intent: Dict[str, Any], post_content: str, hashtags: List[str], image_url: str) -> List[Dict[str, Any]]:
    from src.config import get_config
    
    # Get explicitly requested channels from parsed intent
    channels = parsed_intent.get("channels") or []
    channels = [str(c).strip().title() for c in channels if str(c).strip()]
    
    # If no channels specified, use ALL enabled channels (same logic as sender_node)
    if not channels:
        cfg = get_config()
        if cfg.enable_email:
            channels.append("Email")
        if cfg.enable_facebook:
            channels.append("Facebook")
        if cfg.enable_instagram:
            channels.append("Instagram")
        if cfg.enable_twitter:
            channels.append("Twitter")
        if cfg.enable_linkedin:
            channels.append("LinkedIn")
        
        # Fallback if no channels enabled
        if not channels:
            channels = ["Generic"]
    hashtag_suffix = ("\n\n" + " ".join(hashtags)) if hashtags else ""
    full_text = (post_content or "").strip() + hashtag_suffix
    posts: List[Dict[str, Any]] = []
    for channel in channels:
        posts.append({
            "channel": channel,
            "text": full_text.strip(),
            "imageUrl": image_url or None,
        })
    return posts


def _build_email(parsed_intent: Dict[str, Any], post_content: str, ctas: List[str], image_url: str) -> Dict[str, Any]:
    goal = parsed_intent.get("goal") or "Your Campaign"
    audience = parsed_intent.get("audience") or "your audience"
    subject_cta = ctas[0] if ctas else "Learn more"
    subject = f"{goal} – {subject_cta}"
    greeting_line = f"Hello {audience}," if audience and audience != "your audience" else "Hello,"
    body_lines: List[str] = [greeting_line, "", (post_content or "").strip()]
    if ctas:
        body_lines.append("")
        body_lines.append("Calls to action:")
        for cta in ctas[:3]:
            body_lines.append(f"- {cta}")
    return {
        "subject": subject,
        "preheader": goal,
        "bodyText": "\n".join(body_lines).strip(),
        "imageUrl": image_url or None,
    }


def _collect_prompt_hints(state: MessagesState) -> Dict[str, Any]:
    hints: Dict[str, Any] = {}
    for key in ["image_prompt_hint", "text_prompt_hint", "cta_prompt_hint", "hashtag_prompt_hint"]:
        if key in state:
            hints[key] = state[key]
    return hints


def _collect_artifacts(state: MessagesState) -> Dict[str, Any]:
    artifacts: Dict[str, Any] = {}
    if "parsed_intent" in state:
        artifacts["parsed_intent"] = state["parsed_intent"]
    if "creative_brief" in state:
        artifacts["creative_brief"] = state["creative_brief"]
    prompt_hints = _collect_prompt_hints(state)
    if prompt_hints:
        artifacts["prompt_hints"] = prompt_hints
    if "image_url" in state or "image_prompt" in state:
        artifacts["image"] = {"url": state.get("image_url"), "prompt": state.get("image_prompt")}
    if "post_content" in state:
        artifacts["text"] = {"post_content": state.get("post_content")}
    if "hashtags" in state:
        artifacts["hashtags"] = state.get("hashtags", [])
    if "ctas" in state:
        artifacts["ctas"] = state.get("ctas", [])
    latest_user_message = _get_latest_user_message(state)
    if latest_user_message:
        artifacts["original_user_input"] = latest_user_message
    if "meta" in state and isinstance(state["meta"], dict):
        artifacts["meta"] = state["meta"]
    return artifacts


@traceable(name="Response Generator Node")
def response_generator_node(state: MessagesState) -> MessagesState:
    parsed_intent = state.get("parsed_intent", {})
    post_content = state.get("post_content", "")
    hashtags = state.get("hashtags", [])
    ctas = state.get("ctas", [])
    image_url = state.get("image_url", "")

    social_media_posts = _build_social_posts(parsed_intent, post_content, hashtags, image_url)
    email = _build_email(parsed_intent, post_content, ctas, image_url)
    artifacts = _collect_artifacts(state)
    prompt_hints = artifacts.get("prompt_hints", {})

    by_node: Dict[str, Any] = {
        "ParseIntentNode": {"parsed_intent": parsed_intent},
        "CreativeGenerationNode": {"creative_brief": state.get("creative_brief", {}), "prompt_hints": prompt_hints},
        "TextGenerationNode": {"post_content": post_content},
        "CTAHashtagNode": {"hashtags": hashtags, "ctas": ctas},
        "ImageGenerationNode": {"imageUrl": image_url, "imagePrompt": state.get("image_prompt", "")},
        "ResponseGeneratorNode": {"social_media_posts": social_media_posts, "email": email},
        "LLMMetadata": state.get("meta", {}),
    }

    final_response: Dict[str, Any] = {
        "socialMediaPosts": social_media_posts,
        "email": email,
        "creativeBrief": state.get("creative_brief", {}),
        "promptHints": prompt_hints,
        "byNode": by_node,
        "artifacts": artifacts,
        "llmMetadata": state.get("meta", {}),
    }

    state["final_response"] = final_response
    return state

