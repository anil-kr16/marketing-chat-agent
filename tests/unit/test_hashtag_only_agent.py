"""
Unit tests for HashtagOnlyAgent.
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
from src.agents.micro.hashtag_only_agent import HashtagOnlyAgent


class TestHashtagOnlyAgent(unittest.TestCase):
    """Test cases for HashtagOnlyAgent."""
    
    @classmethod
    def setUpClass(cls):
        """Set up test environment."""
        setup_test_environment()
        cls.agent = HashtagOnlyAgent()
    
    def setUp(self):
        """Set up each test."""
        cleanup_test_files()
    
    def test_hashtag_generation(self):
        """Test basic hashtag generation functionality via micro graph."""
        state = create_test_state(SAMPLE_INPUTS["simple"])
        result = self.agent.run(state)
        
        # Basic assertions
        assert_agent_success(result, "HashtagOnlyAgent")
        assert_intent_parsed(result)
        
        # Validate hashtag generation
        validator = TestResultValidator(result)
        self.assertTrue(validator.validate_hashtag_generation())
        
        # Check hashtag format
        hashtags = result.get("hashtags", [])
        if hashtags:
            for hashtag in hashtags:
                self.assertTrue(hashtag.startswith("#"), f"Hashtag {hashtag} doesn't start with #")
                self.assertGreater(len(hashtag), 2, f"Hashtag {hashtag} too short")
        
        # Verify agent is working correctly
        self.assertIsInstance(self.agent, HashtagOnlyAgent, "Agent should be HashtagOnlyAgent instance")
        
        # Verify agent generated proper AI response
        messages = result.get("messages", [])
        last_message = messages[-1]
        self.assertEqual(last_message.__class__.__name__, "AIMessage")
        self.assertIn("HASHTAGS & CTAS GENERATED SUCCESSFULLY", last_message.content)
    
    def test_cta_generation(self):
        """Test CTA generation functionality."""
        state = create_test_state(SAMPLE_INPUTS["detailed"])
        result = self.agent.run(state)
        
        assert_agent_success(result, "HashtagOnlyAgent")
        
        # Check CTAs
        ctas = result.get("ctas", [])
        self.assertGreater(len(ctas), 0, "No CTAs generated")
        
        for cta in ctas:
            self.assertIsInstance(cta, str)
            self.assertGreater(len(cta.strip()), 5, f"CTA '{cta}' too short")
    
    def test_hashtag_count(self):
        """Test that appropriate number of hashtags are generated."""
        state = create_test_state(SAMPLE_INPUTS["multichannel"])
        result = self.agent.run(state)
        
        assert_agent_success(result, "HashtagOnlyAgent")
        
        hashtags = result.get("hashtags", [])
        if hashtags:
            # Should generate reasonable number of hashtags (typically 5-15)
            self.assertGreaterEqual(len(hashtags), 3, "Too few hashtags generated")
            self.assertLessEqual(len(hashtags), 20, "Too many hashtags generated")
    
    def test_seasonal_hashtags(self):
        """Test hashtags with seasonal context."""
        state = create_test_state(SAMPLE_INPUTS["seasonal"])
        result = self.agent.run(state)
        
        assert_agent_success(result, "HashtagOnlyAgent")
        
        hashtags = result.get("hashtags", [])
        if hashtags:
            # Check if any hashtag contains seasonal reference
            hashtag_text = " ".join(hashtags).lower()
            goal = result["parsed_intent"]["goal"].lower()
            
            has_seasonal_context = (
                "newyear" in hashtag_text or 
                "2024" in hashtag_text or
                "new year" in goal
            )
            self.assertTrue(has_seasonal_context, "Seasonal context not in hashtags")
    
    def test_cultural_hashtags(self):
        """Test hashtags with cultural context."""
        state = create_test_state(SAMPLE_INPUTS["cultural"])
        result = self.agent.run(state)
        
        assert_agent_success(result, "HashtagOnlyAgent")
        
        hashtags = result.get("hashtags", [])
        if hashtags:
            hashtag_text = " ".join(hashtags).lower()
            
            # Should contain cultural references
            has_cultural_context = (
                "diwali" in hashtag_text or
                "traditional" in hashtag_text or
                "festival" in hashtag_text
            )
            self.assertTrue(has_cultural_context, "Cultural context not in hashtags")
    
    def test_b2b_hashtags(self):
        """Test B2B appropriate hashtags."""
        state = create_test_state(SAMPLE_INPUTS["b2b"])
        result = self.agent.run(state)
        
        assert_agent_success(result, "HashtagOnlyAgent")
        
        hashtags = result.get("hashtags", [])
        if hashtags:
            hashtag_text = " ".join(hashtags).lower()
            
            # Should contain business-appropriate terms
            b2b_terms = ["business", "startup", "software", "enterprise", "saas", "tech"]
            has_b2b_context = any(term in hashtag_text for term in b2b_terms)
            self.assertTrue(has_b2b_context, "B2B context not in hashtags")
    
    def test_hashtag_uniqueness(self):
        """Test that generated hashtags are unique."""
        state = create_test_state(SAMPLE_INPUTS["simple"])
        result = self.agent.run(state)
        
        hashtags = result.get("hashtags", [])
        if hashtags:
            unique_hashtags = list(set(hashtags))
            self.assertEqual(
                len(hashtags), 
                len(unique_hashtags), 
                "Duplicate hashtags generated"
            )
    
    def test_metadata_tracking(self):
        """Test that hashtag generation metadata is tracked."""
        state = create_test_state(SAMPLE_INPUTS["simple"])
        result = self.agent.run(state)
        
        assert_agent_success(result, "HashtagOnlyAgent")
        
        # Check for metadata
        meta = result.get("meta", {})
        hashtag_meta = meta.get("hashtags_llm") or meta.get("ctas_llm")
        
        if hashtag_meta:
            self.assertIn("model", hashtag_meta)
            self.assertIn("prompt", hashtag_meta)


if __name__ == "__main__":
    unittest.main()
