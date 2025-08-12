"""
Unit tests for TextOnlyAgent.
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
from src.agents.micro.text_only_agent import TextOnlyAgent


class TestTextOnlyAgent(unittest.TestCase):
    """Test cases for TextOnlyAgent."""
    
    @classmethod
    def setUpClass(cls):
        """Set up test environment."""
        setup_test_environment()
        cls.agent = TextOnlyAgent()
    
    def setUp(self):
        """Set up each test."""
        cleanup_test_files()
    
    def test_simple_text_generation(self):
        """Test basic text generation functionality via micro graph."""
        state = create_test_state(SAMPLE_INPUTS["simple"])
        result = self.agent.run(state)
        
        # Basic assertions
        assert_agent_success(result, "TextOnlyAgent")
        assert_intent_parsed(result)
        assert_content_generated(result, "post_content")
        
        # Validate content quality
        validator = TestResultValidator(result)
        self.assertTrue(validator.validate_text_generation())
        
        # Check content length
        post_content = result["post_content"]
        self.assertGreater(len(post_content), 20, "Generated text too short")
        self.assertLess(len(post_content), 500, "Generated text too long")
        
        # Verify agent is working correctly
        self.assertIsInstance(self.agent, TextOnlyAgent, "Agent should be TextOnlyAgent instance")
    
    def test_seasonal_text_generation(self):
        """Test text generation with seasonal context."""
        state = create_test_state(SAMPLE_INPUTS["seasonal"])
        result = self.agent.run(state)
        
        assert_agent_success(result, "TextOnlyAgent")
        assert_content_generated(result, "post_content")
        
        # Check that seasonal context is preserved
        post_content = result["post_content"].lower()
        goal = result["parsed_intent"]["goal"].lower()
        
        self.assertTrue(
            "new year" in post_content or "new year" in goal,
            "Seasonal context not preserved"
        )
    
    def test_detailed_campaign_text(self):
        """Test text generation with detailed campaign parameters."""
        state = create_test_state(SAMPLE_INPUTS["detailed"])
        result = self.agent.run(state)
        
        assert_agent_success(result, "TextOnlyAgent")
        assert_content_generated(result, "post_content")
        
        # Check intent parsing
        parsed_intent = result["parsed_intent"]
        self.assertIn("skincare", parsed_intent["goal"].lower())
        self.assertEqual(parsed_intent["audience"], "young women")
        self.assertEqual(parsed_intent["tone"], "engaging")
        self.assertEqual(parsed_intent["budget"], "$500")
    
    def test_metadata_tracking(self):
        """Test that metadata is properly tracked through micro graph."""
        state = create_test_state(SAMPLE_INPUTS["simple"])
        result = self.agent.run(state)
        
        assert_agent_success(result, "TextOnlyAgent")
        
        # Check for metadata from micro graph execution
        meta = result.get("meta", {})
        if "text_generation_llm" in meta:
            text_meta = meta["text_generation_llm"]
            self.assertIn("model", text_meta)
            self.assertIn("prompt", text_meta)
        
        # Verify agent generated proper AI response
        messages = result.get("messages", [])
        self.assertGreater(len(messages), 1, "Should have system + user + AI messages")
        
        # Last message should be from AI with detailed response
        last_message = messages[-1]
        self.assertEqual(last_message.__class__.__name__, "AIMessage")
        self.assertIn("TEXT GENERATED SUCCESSFULLY", last_message.content)
    
    def test_empty_input_handling(self):
        """Test handling of empty or invalid input."""
        state = create_test_state("")
        result = self.agent.run(state)
        
        # Should still return a valid state
        self.assertIsNotNone(result)
        self.assertIn("messages", result)
    
    def test_b2b_text_generation(self):
        """Test B2B focused text generation."""
        state = create_test_state(SAMPLE_INPUTS["b2b"])
        result = self.agent.run(state)
        
        assert_agent_success(result, "TextOnlyAgent")
        assert_content_generated(result, "post_content")
        
        # Check B2B context
        parsed_intent = result["parsed_intent"]
        self.assertIn("business", parsed_intent["goal"].lower())
        self.assertIn("startup", parsed_intent["audience"].lower())


if __name__ == "__main__":
    unittest.main()
