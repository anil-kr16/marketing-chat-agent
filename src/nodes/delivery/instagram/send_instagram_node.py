from __future__ import annotations

import os
from typing import Any, Dict

from langsmith import traceable

from src.utils.state import MessagesState
from src.config import get_config
from src.utils.common import ensure_dir, get_project_root, create_campaign_folder


@traceable(name="Send Instagram Node")
def send_instagram_node(state: MessagesState) -> MessagesState:
    """
    Send Instagram content. In DRY_RUN mode, saves content to outbox.
    In production, would integrate with Instagram Business API.
    """
    cfg = get_config()
    if not cfg.enable_instagram:
        return state

    # Get Instagram post from final_response
    final_response = state.get("final_response", {})
    social_posts = final_response.get("socialMediaPosts", [])
    
    instagram_post = None
    for post in social_posts:
        if post.get("channel", "").lower() == "instagram":
            instagram_post = post
            break
    
    if not instagram_post:
        return state

    text_content = instagram_post.get("text", "")
    image_url = instagram_post.get("imageUrl", "")
    
    # In DRY_RUN mode, save to outbox
    if cfg.dry_run or True:  # Always save to outbox for now (until real API implemented)
        base_outbox = os.path.join(get_project_root(), cfg.outbox_dir)
        
        # Create campaign folder
        campaign_dir = create_campaign_folder(state, base_outbox)
        
        # Use standardized filename
        path = os.path.join(campaign_dir, "instagram_post.txt")
        
        with open(path, "w", encoding="utf-8") as f:
            f.write("INSTAGRAM POST\n")
            f.write("=" * 50 + "\n\n")
            f.write(f"Text:\n{text_content}\n\n")
            if image_url:
                f.write(f"Image: {image_url}\n\n")
            f.write("Platform: Instagram\n")
            f.write("Format: Social Media Post\n")
        
        status = f"DRY_RUN: wrote {path}"
    else:
        # TODO: Implement actual Instagram Business API integration
        # This would use Facebook Graph API to post to Instagram Business accounts
        status = "Instagram API not implemented yet"

    # Update delivery results
    delivery = state.setdefault("delivery", {"requested": [], "results": {}})
    delivery.setdefault("results", {})["instagram"] = status
    
    return state
