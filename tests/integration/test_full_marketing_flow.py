"""
Integration tests for the complete marketing agent flow.
"""

import unittest
import os
import sys

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from tests.utils.test_helpers import (
    create_test_state, setup_test_environment, cleanup_test_files,
    assert_agent_success, assert_content_generated, assert_intent_parsed,
    assert_files_created, TestResultValidator, SAMPLE_INPUTS, EXPECTED_OUTPUTS
)
from src.agents.campaign.full_marketing_agent import FullMarketingAgent
from langchain.schema import HumanMessage


class TestFullMarketingFlow(unittest.TestCase):
    """Test cases for complete marketing campaign generation."""
    
    @classmethod
    def setUpClass(cls):
        """Set up test environment."""
        setup_test_environment()
        cls.agent = FullMarketingAgent()
    
    def setUp(self):
        """Set up each test."""
        cleanup_test_files()
    
    def test_complete_campaign_generation(self):
        """Test end-to-end campaign generation with user confirmation."""
        # Initial request
        state = create_test_state(SAMPLE_INPUTS["multichannel"])
        result = self.agent.run(state)
        
        # Should ask for confirmation
        self.assertTrue(
            result.get("agent_flags", {}).get("awaiting_confirmation", False),
            "Agent should be awaiting confirmation"
        )
        
        # Provide confirmation
        result["messages"].append(HumanMessage(content="yes"))
        final_result = self.agent.run(result)
        
        # Validate complete campaign
        validator = TestResultValidator(final_result)
        self.assertTrue(validator.validate_full_campaign())
        
        # Check all components were generated
        for component in EXPECTED_OUTPUTS["full_campaign"]:
            assert_content_generated(final_result, component)
    
    def test_multichannel_file_generation(self):
        """Test that files are generated for all requested channels."""
        state = create_test_state(SAMPLE_INPUTS["multichannel"])
        
        # Run with confirmation
        result = self.agent.run(state)
        result["messages"].append(HumanMessage(content="yes"))
        final_result = self.agent.run(result)
        
        # Check delivery results
        delivery = final_result.get("delivery", {})
        results = delivery.get("results", {})
        
        # Should have delivery results for multiple channels
        self.assertGreater(len(results), 1, "Should deliver to multiple channels")
        
        # Check that files were created
        if final_result.get("final_response"):
            # Files should be created in campaign folder
            assert_files_created(EXPECTED_OUTPUTS["multichannel_files"])
    
    def test_seasonal_campaign_context(self):
        """Test that seasonal context is preserved throughout the flow."""
        state = create_test_state(SAMPLE_INPUTS["seasonal"])
        
        # Run complete flow
        result = self.agent.run(state)
        result["messages"].append(HumanMessage(content="yes"))
        final_result = self.agent.run(result)
        
        # Check that seasonal context is preserved
        parsed_intent = final_result.get("parsed_intent", {})
        goal = parsed_intent.get("goal", "").lower()
        
        self.assertIn("new year", goal, "Seasonal context not preserved in goal")
        
        # Check in generated content
        post_content = final_result.get("post_content", "").lower()
        final_response = final_result.get("final_response", {})
        
        # Seasonal context should appear somewhere in the campaign
        has_seasonal = (
            "new year" in post_content or
            "new year" in goal or
            any("new year" in str(v).lower() for v in final_response.values() if isinstance(v, str))
        )
        self.assertTrue(has_seasonal, "Seasonal context lost in campaign")
    
    def test_ai_review_approval_flow(self):
        """Test the AI review and approval process."""
        state = create_test_state(SAMPLE_INPUTS["detailed"])
        
        # Run complete flow
        result = self.agent.run(state)
        result["messages"].append(HumanMessage(content="yes"))
        final_result = self.agent.run(result)
        
        # Check review metadata
        meta = final_result.get("meta", {})
        if "text_review" in meta:
            review = meta["text_review"]
            self.assertIn("approved", review)
            self.assertIn("comments", review)
            
            # If approved, should have final_response
            if review["approved"]:
                self.assertIn("final_response", final_result)
    
    def test_campaign_folder_structure(self):
        """Test that campaign folders are created with proper structure."""
        state = create_test_state(SAMPLE_INPUTS["simple"])
        
        # Run complete flow
        result = self.agent.run(state)
        result["messages"].append(HumanMessage(content="yes"))
        final_result = self.agent.run(result)
        
        # Check that campaign folder was created
        outbox_dir = "data/outbox"
        if os.path.exists(outbox_dir):
            items = os.listdir(outbox_dir)
            campaign_folders = [item for item in items if os.path.isdir(os.path.join(outbox_dir, item))]
            
            self.assertGreater(len(campaign_folders), 0, "No campaign folder created")
            
            # Check folder naming pattern
            latest_folder = campaign_folders[0]
            self.assertTrue("_" in latest_folder, "Campaign folder should have timestamp")
    
    def test_error_recovery(self):
        """Test error handling in the complete flow."""
        # Test with potentially problematic input
        state = create_test_state("!@#$%^&*()")
        result = self.agent.run(state)
        
        # Should still return valid state without crashing
        self.assertIsNotNone(result)
        self.assertIn("messages", result)
    
    def test_metadata_tracking_full_flow(self):
        """Test that metadata is tracked throughout the full flow."""
        state = create_test_state(SAMPLE_INPUTS["detailed"])
        
        # Run complete flow
        result = self.agent.run(state)
        result["messages"].append(HumanMessage(content="yes"))
        final_result = self.agent.run(result)
        
        # Check for comprehensive metadata
        meta = final_result.get("meta", {})
        
        # Should have metadata from multiple components
        expected_meta_keys = [
            "text_generation_llm",
            "image_generation", 
            "hashtags_llm",
            "ctas_llm"
        ]
        
        found_meta = sum(1 for key in expected_meta_keys if key in meta)
        self.assertGreater(found_meta, 0, "No metadata found in full flow")
    
    def test_performance_reasonable_time(self):
        """Test that full flow completes in reasonable time."""
        import time
        
        state = create_test_state(SAMPLE_INPUTS["simple"])
        
        start_time = time.time()
        
        # Run complete flow
        result = self.agent.run(state)
        result["messages"].append(HumanMessage(content="yes"))
        final_result = self.agent.run(result)
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Should complete within reasonable time (adjust based on your needs)
        self.assertLess(duration, 120, f"Full flow took too long: {duration:.2f} seconds")


if __name__ == "__main__":
    unittest.main()
