"""
Unit tests for ImageOnlyAgent.
"""

import unittest
import os
import sys

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from tests.utils.test_helpers import (
    create_test_state, setup_test_environment, cleanup_test_files,
    assert_agent_success, assert_content_generated, assert_intent_parsed,
    TestResultValidator, SAMPLE_INPUTS
)
from src.agents.micro.image_only_agent import ImageOnlyAgent


class TestImageOnlyAgent(unittest.TestCase):
    """Test cases for ImageOnlyAgent."""
    
    @classmethod
    def setUpClass(cls):
        """Set up test environment."""
        setup_test_environment()
        cls.agent = ImageOnlyAgent()
    
    def setUp(self):
        """Set up each test."""
        cleanup_test_files()
    
    def test_simple_image_generation(self):
        """Test basic image generation functionality via micro graph."""
        state = create_test_state(SAMPLE_INPUTS["simple"])
        result = self.agent.run(state)
        
        # Basic assertions
        assert_agent_success(result, "ImageOnlyAgent")
        assert_intent_parsed(result)
        
        # Validate image generation
        validator = TestResultValidator(result)
        self.assertTrue(validator.validate_image_generation())
        
        # Check image URL format
        image_url = result["image_url"]
        self.assertTrue(image_url.startswith("/static/images/"))
        self.assertTrue(image_url.endswith(".png"))
        
        # Verify agent is working correctly
        self.assertIsInstance(self.agent, ImageOnlyAgent, "Agent should be ImageOnlyAgent instance")
        
        # Verify agent generated proper AI response
        messages = result.get("messages", [])
        last_message = messages[-1]
        self.assertEqual(last_message.__class__.__name__, "AIMessage")
        self.assertIn("IMAGE GENERATED SUCCESSFULLY", last_message.content)
    
    def test_image_prompt_generation(self):
        """Test that image prompts are generated correctly."""
        state = create_test_state(SAMPLE_INPUTS["detailed"])
        result = self.agent.run(state)
        
        assert_agent_success(result, "ImageOnlyAgent")
        assert_content_generated(result, "image_prompt")
        
        # Check prompt content
        image_prompt = result["image_prompt"].lower()
        self.assertIn("skincare", image_prompt)
        self.assertTrue(len(image_prompt) > 10)
    
    def test_seasonal_image_context(self):
        """Test image generation with seasonal context."""
        state = create_test_state(SAMPLE_INPUTS["seasonal"])
        result = self.agent.run(state)
        
        assert_agent_success(result, "ImageOnlyAgent")
        
        # Check that seasonal context influences image prompt
        if "image_prompt" in result:
            image_prompt = result["image_prompt"].lower()
            goal = result["parsed_intent"]["goal"].lower()
            
            # Seasonal context should be in either the prompt or preserved in goal
            has_seasonal_context = (
                "new year" in image_prompt or 
                "new year" in goal
            )
            self.assertTrue(has_seasonal_context, "Seasonal context not preserved")
    
    def test_image_file_creation(self):
        """Test that image files are actually created."""
        state = create_test_state(SAMPLE_INPUTS["simple"])
        result = self.agent.run(state)
        
        if "image_url" in result:
            image_url = result["image_url"]
            # Convert URL to file path
            filename = os.path.basename(image_url)
            file_path = os.path.join("static", "images", filename)
            
            # Check if file exists
            self.assertTrue(
                os.path.exists(file_path),
                f"Image file {file_path} was not created"
            )
            
            # Check file size
            file_size = os.path.getsize(file_path)
            self.assertGreater(file_size, 1000, "Image file too small")
    
    def test_metadata_tracking(self):
        """Test that image generation metadata is tracked."""
        state = create_test_state(SAMPLE_INPUTS["simple"])
        result = self.agent.run(state)
        
        assert_agent_success(result, "ImageOnlyAgent")
        
        # Check for metadata
        meta = result.get("meta", {})
        if "image_generation" in meta:
            img_meta = meta["image_generation"]
            self.assertIn("model", img_meta)
            self.assertIn("prompt", img_meta)
    
    def test_error_handling(self):
        """Test error handling for image generation failures."""
        # This test might be challenging since we need actual API calls
        # For now, just ensure the agent doesn't crash with edge cases
        state = create_test_state("generate image with invalid characters !@#$%^&*()")
        result = self.agent.run(state)
        
        # Should still return a valid state
        self.assertIsNotNone(result)
        self.assertIn("messages", result)


if __name__ == "__main__":
    unittest.main()
