"""
Test utilities and helper functions for marketing agent testing.
"""

import os
import sys
import tempfile
from typing import Dict, Any, List
from langchain.schema import HumanMessage

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from src.utils.state import MessagesState


def create_test_state(user_input: str, **kwargs) -> MessagesState:
    """Create a test state with user input and optional additional data."""
    state: MessagesState = {
        "messages": [HumanMessage(content=user_input)],
        **kwargs
    }
    return state


def setup_test_environment():
    """Set up environment variables for testing."""
    os.environ["DRY_RUN"] = "true"
    os.environ["ENABLE_EMAIL"] = "true"
    os.environ["ENABLE_INSTAGRAM"] = "true"
    os.environ["ENABLE_FACEBOOK"] = "true"
    os.environ["ENABLE_TWITTER"] = "true"
    os.environ["ENABLE_LINKEDIN"] = "true"


def cleanup_test_files(base_dir: str = "data/outbox"):
    """Clean up test-generated files."""
    import shutil
    if os.path.exists(base_dir):
        for item in os.listdir(base_dir):
            item_path = os.path.join(base_dir, item)
            if os.path.isdir(item_path):
                shutil.rmtree(item_path)
            else:
                os.remove(item_path)


def assert_agent_success(result: MessagesState, component: str) -> None:
    """Assert that an agent run was successful."""
    assert result is not None, f"{component} returned None"
    assert "messages" in result, f"{component} missing messages in result"
    assert len(result["messages"]) > 0, f"{component} returned empty messages"


def assert_content_generated(result: MessagesState, content_key: str) -> None:
    """Assert that specific content was generated."""
    assert content_key in result, f"Missing {content_key} in result"
    content = result[content_key]
    assert content, f"{content_key} is empty"
    
    if isinstance(content, str):
        assert len(content.strip()) > 0, f"{content_key} is empty string"
    elif isinstance(content, list):
        assert len(content) > 0, f"{content_key} is empty list"


def assert_intent_parsed(result: MessagesState) -> None:
    """Assert that intent was parsed successfully."""
    assert "parsed_intent" in result, "Missing parsed_intent in result"
    intent = result["parsed_intent"]
    assert isinstance(intent, dict), "parsed_intent is not a dict"
    assert "goal" in intent, "Missing goal in parsed_intent"


def assert_files_created(expected_files: List[str], base_dir: str = "data/outbox") -> None:
    """Assert that expected files were created."""
    if not os.path.exists(base_dir):
        raise AssertionError(f"Output directory {base_dir} does not exist")
    
    # Find the latest campaign folder
    items = os.listdir(base_dir)
    campaign_folders = [item for item in items if os.path.isdir(os.path.join(base_dir, item))]
    
    if not campaign_folders:
        raise AssertionError("No campaign folders found")
    
    latest_campaign = max(campaign_folders, 
                         key=lambda f: os.path.getctime(os.path.join(base_dir, f)))
    campaign_path = os.path.join(base_dir, latest_campaign)
    
    actual_files = os.listdir(campaign_path)
    
    for expected_file in expected_files:
        assert expected_file in actual_files, f"Expected file {expected_file} not found. Found: {actual_files}"


class TestResultValidator:
    """Helper class for validating test results."""
    
    def __init__(self, result: MessagesState):
        self.result = result
    
    def has_content(self, key: str) -> bool:
        """Check if result has non-empty content for key."""
        return key in self.result and bool(self.result[key])
    
    def get_content(self, key: str, default=None):
        """Get content safely."""
        return self.result.get(key, default)
    
    def validate_text_generation(self) -> bool:
        """Validate text generation results."""
        return (
            self.has_content("post_content") and
            self.has_content("parsed_intent") and
            len(self.result["post_content"].strip()) > 20
        )
    
    def validate_image_generation(self) -> bool:
        """Validate image generation results."""
        return (
            self.has_content("image_url") and
            self.has_content("image_prompt") and
            self.result["image_url"].startswith("/static/images/")
        )
    
    def validate_hashtag_generation(self) -> bool:
        """Validate hashtag generation results."""
        hashtags = self.result.get("hashtags", [])
        ctas = self.result.get("ctas", [])
        return len(hashtags) > 0 or len(ctas) > 0
    
    def validate_full_campaign(self) -> bool:
        """Validate full campaign generation."""
        return (
            self.has_content("final_response") and
            self.has_content("delivery") and
            "results" in self.result["delivery"]
        )


# Test data samples
SAMPLE_INPUTS = {
    "simple": "promote smartphones",
    "seasonal": "promote fitness app on new year",
    "multichannel": "sell smart watches on instagram facebook email",
    "detailed": "promote organic skincare to young women on instagram with engaging tone $500 budget",
    "b2b": "market business software to startups on linkedin email",
    "cultural": "promote traditional jewelry on diwali to indian families"
}

EXPECTED_OUTPUTS = {
    "text_components": ["post_content", "parsed_intent"],
    "image_components": ["image_url", "image_prompt"],
    "hashtag_components": ["hashtags", "ctas"],
    "full_campaign": ["final_response", "delivery", "parsed_intent", "post_content"],
    "multichannel_files": ["email_post.txt", "instagram_post.txt", "facebook_post.txt"]
}
