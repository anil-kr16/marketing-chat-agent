"""
Integration tests for multichannel delivery functionality.
"""

import unittest
import os
import sys

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from tests.utils.test_helpers import (
    create_test_state, setup_test_environment, cleanup_test_files,
    assert_agent_success, assert_files_created, SAMPLE_INPUTS
)
from src.agents.campaign.full_marketing_agent import FullMarketingAgent
from langchain.schema import HumanMessage


class TestMultichannelDelivery(unittest.TestCase):
    """Test cases for multichannel content delivery."""
    
    @classmethod
    def setUpClass(cls):
        """Set up test environment."""
        setup_test_environment()
        cls.agent = FullMarketingAgent()
    
    def setUp(self):
        """Set up each test."""
        cleanup_test_files()
    
    def test_instagram_facebook_email_delivery(self):
        """Test delivery to Instagram, Facebook, and Email."""
        state = create_test_state("promote fitness app on instagram facebook email")
        
        # Run complete flow
        result = self.agent.run(state)
        result["messages"].append(HumanMessage(content="yes"))
        final_result = self.agent.run(result)
        
        # Check delivery results
        delivery = final_result.get("delivery", {})
        results = delivery.get("results", {})
        
        expected_channels = ["instagram", "facebook", "email"]
        for channel in expected_channels:
            self.assertIn(channel, results, f"Missing delivery result for {channel}")
            self.assertIn("DRY_RUN: wrote", results[channel], f"No file written for {channel}")
        
        # Verify files were created
        assert_files_created(["instagram_post.txt", "facebook_post.txt", "email_post.txt"])
    
    def test_single_channel_delivery(self):
        """Test delivery to a single channel."""
        state = create_test_state("promote smartphones on email")
        
        # Run complete flow
        result = self.agent.run(state)
        result["messages"].append(HumanMessage(content="yes"))
        final_result = self.agent.run(result)
        
        # Check delivery results
        delivery = final_result.get("delivery", {})
        results = delivery.get("results", {})
        
        self.assertIn("email", results)
        self.assertEqual(len(results), 1, "Should only deliver to one channel")
        
        # Verify only email file was created
        assert_files_created(["email_post.txt"])
    
    def test_channel_specific_content_formatting(self):
        """Test that content is formatted appropriately for each channel."""
        state = create_test_state("promote tech startup on instagram facebook email")
        
        # Run complete flow
        result = self.agent.run(state)
        result["messages"].append(HumanMessage(content="yes"))
        final_result = self.agent.run(result)
        
        # Get final response
        final_response = final_result.get("final_response", {})
        social_posts = final_response.get("socialMediaPosts", [])
        email_content = final_response.get("email", {})
        
        # Check social media posts
        if social_posts:
            channels_found = [post.get("channel") for post in social_posts]
            self.assertIn("Instagram", channels_found)
            self.assertIn("Facebook", channels_found)
            
            # Each post should have proper structure
            for post in social_posts:
                self.assertIn("channel", post)
                self.assertIn("text", post)
                self.assertTrue(len(post["text"]) > 0)
        
        # Check email content
        if email_content:
            self.assertIn("subject", email_content)
            self.assertIn("bodyText", email_content)
            self.assertTrue(len(email_content["bodyText"]) > 0)
    
    def test_delivery_error_handling(self):
        """Test handling of delivery errors."""
        # This would test scenarios where delivery might fail
        # For now, test that the system doesn't crash with edge cases
        state = create_test_state("promote product on nonexistentchannel")
        
        # Run complete flow
        result = self.agent.run(state)
        result["messages"].append(HumanMessage(content="yes"))
        final_result = self.agent.run(result)
        
        # Should still complete without crashing
        self.assertIsNotNone(final_result)
        self.assertIn("delivery", final_result)
    
    def test_campaign_folder_organization(self):
        """Test that all channel files are organized in the same campaign folder."""
        state = create_test_state("sell products on instagram facebook email")
        
        # Run complete flow
        result = self.agent.run(state)
        result["messages"].append(HumanMessage(content="yes"))
        final_result = self.agent.run(result)
        
        # Check that all files are in the same campaign folder
        outbox_dir = "data/outbox"
        if os.path.exists(outbox_dir):
            items = os.listdir(outbox_dir)
            campaign_folders = [item for item in items if os.path.isdir(os.path.join(outbox_dir, item))]
            
            if campaign_folders:
                # Should be only one campaign folder
                self.assertEqual(len(campaign_folders), 1, "Multiple campaign folders created")
                
                # All files should be in this folder
                campaign_path = os.path.join(outbox_dir, campaign_folders[0])
                files = os.listdir(campaign_path)
                
                expected_files = ["instagram_post.txt", "facebook_post.txt", "email_post.txt"]
                for expected_file in expected_files:
                    self.assertIn(expected_file, files, f"{expected_file} not in campaign folder")
    
    def test_content_consistency_across_channels(self):
        """Test that core message is consistent across all channels."""
        state = create_test_state("promote eco-friendly products on instagram facebook email")
        
        # Run complete flow
        result = self.agent.run(state)
        result["messages"].append(HumanMessage(content="yes"))
        final_result = self.agent.run(result)
        
        # Get content from different channels
        final_response = final_result.get("final_response", {})
        social_posts = final_response.get("socialMediaPosts", [])
        email_content = final_response.get("email", {})
        
        # Extract key terms from the campaign
        goal = final_result.get("parsed_intent", {}).get("goal", "").lower()
        key_terms = ["eco", "friendly", "product"]
        
        # Check that key terms appear across channels
        if social_posts:
            for post in social_posts:
                text = post.get("text", "").lower()
                # At least one key term should appear
                has_key_term = any(term in text for term in key_terms)
                self.assertTrue(has_key_term, f"Key terms missing in {post.get('channel')} post")
        
        if email_content:
            email_text = email_content.get("bodyText", "").lower()
            has_key_term = any(term in email_text for term in key_terms)
            self.assertTrue(has_key_term, "Key terms missing in email content")


if __name__ == "__main__":
    unittest.main()
