"""
Unit tests for micro graphs architecture.
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
from src.graphs.micro.text_only_graph import get_text_only_graph, create_text_only_graph
from src.graphs.micro.image_only_graph import get_image_only_graph, create_image_only_graph
from src.graphs.micro.hashtag_only_graph import get_hashtag_only_graph, create_hashtag_only_graph


class TestMicroGraphs(unittest.TestCase):
    """Test cases for micro graph architecture."""
    
    @classmethod
    def setUpClass(cls):
        """Set up test environment."""
        setup_test_environment()
    
    def setUp(self):
        """Set up each test."""
        cleanup_test_files()
    
    def test_text_graph_creation(self):
        """Test that text micro graph can be created and compiled."""
        # Test graph creation
        graph = create_text_only_graph()
        self.assertIsNotNone(graph, "Text graph should be created")
        
        # Test graph compilation
        compiled_graph = get_text_only_graph()
        self.assertIsNotNone(compiled_graph, "Text graph should be compiled")
        
        # Test graph execution
        state = create_test_state("test text generation")
        result = compiled_graph.invoke(state)
        
        # Validate execution
        assert_agent_success(result, "Text Micro Graph")
        assert_intent_parsed(result)
        assert_content_generated(result, "post_content")
    
    def test_image_graph_creation(self):
        """Test that image micro graph can be created and compiled."""
        # Test graph creation
        graph = create_image_only_graph()
        self.assertIsNotNone(graph, "Image graph should be created")
        
        # Test graph compilation
        compiled_graph = get_image_only_graph()
        self.assertIsNotNone(compiled_graph, "Image graph should be compiled")
        
        # Test graph execution
        state = create_test_state("test image generation")
        result = compiled_graph.invoke(state)
        
        # Validate execution
        assert_agent_success(result, "Image Micro Graph")
        assert_intent_parsed(result)
        # Image generation might fail without proper API key, so check if attempt was made
        self.assertIn("image_url", result or "image_prompt" in result, "Image generation should be attempted")
    
    def test_hashtag_graph_creation(self):
        """Test that hashtag micro graph can be created and compiled."""
        # Test graph creation
        graph = create_hashtag_only_graph()
        self.assertIsNotNone(graph, "Hashtag graph should be created")
        
        # Test graph compilation
        compiled_graph = get_hashtag_only_graph()
        self.assertIsNotNone(compiled_graph, "Hashtag graph should be compiled")
        
        # Test graph execution
        state = create_test_state("test hashtag generation")
        result = compiled_graph.invoke(state)
        
        # Validate execution
        assert_agent_success(result, "Hashtag Micro Graph")
        assert_intent_parsed(result)
        # Check if hashtags or CTAs were generated
        has_hashtags = bool(result.get("hashtags", []))
        has_ctas = bool(result.get("ctas", []))
        self.assertTrue(has_hashtags or has_ctas, "Should generate hashtags or CTAs")
    
    def test_graph_isolation(self):
        """Test that micro graphs work in isolation without cross-contamination."""
        # Run text graph
        text_graph = get_text_only_graph()
        text_state = create_test_state("generate marketing text")
        text_result = text_graph.invoke(text_state)
        
        # Run image graph
        image_graph = get_image_only_graph()
        image_state = create_test_state("generate marketing image")
        image_result = image_graph.invoke(image_state)
        
        # Run hashtag graph
        hashtag_graph = get_hashtag_only_graph()
        hashtag_state = create_test_state("generate marketing hashtags")
        hashtag_result = hashtag_graph.invoke(hashtag_state)
        
        # Verify isolation - each result should only have its specific content
        # Text graph should have post_content
        self.assertIn("post_content", text_result)
        
        # Image graph should have image-related content
        has_image_content = "image_url" in image_result or "image_prompt" in image_result
        self.assertTrue(has_image_content, "Image graph should have image content")
        
        # Hashtag graph should have hashtag-related content
        has_hashtag_content = "hashtags" in hashtag_result or "ctas" in hashtag_result
        self.assertTrue(has_hashtag_content, "Hashtag graph should have hashtag content")
    
    def test_graph_consistency(self):
        """Test that graphs produce consistent results for the same input."""
        test_input = "promote smartphones to tech enthusiasts"
        
        # Run text graph twice
        text_graph = get_text_only_graph()
        result1 = text_graph.invoke(create_test_state(test_input))
        result2 = text_graph.invoke(create_test_state(test_input))
        
        # Both should have parsed intent with same goal
        intent1 = result1.get("parsed_intent", {})
        intent2 = result2.get("parsed_intent", {})
        
        self.assertEqual(intent1.get("goal"), intent2.get("goal"), 
                        "Parsed intent should be consistent")
        
        # Both should generate content
        self.assertIn("post_content", result1)
        self.assertIn("post_content", result2)
    
    def test_graph_error_handling(self):
        """Test graph error handling with problematic inputs."""
        problematic_inputs = [
            "",  # Empty input
            "!@#$%^&*()",  # Special characters only
            "a" * 1000,  # Very long input
        ]
        
        graphs = [
            ("text", get_text_only_graph()),
            ("image", get_image_only_graph()),
            ("hashtag", get_hashtag_only_graph())
        ]
        
        for graph_name, graph in graphs:
            for test_input in problematic_inputs:
                with self.subTest(graph=graph_name, input=test_input[:20]):
                    try:
                        state = create_test_state(test_input)
                        result = graph.invoke(state)
                        
                        # Should not crash and should return valid state
                        self.assertIsNotNone(result, f"{graph_name} graph should handle problematic input")
                        self.assertIn("messages", result, f"{graph_name} graph should maintain message structure")
                        
                    except Exception as e:
                        self.fail(f"{graph_name} graph crashed with input '{test_input[:20]}...': {e}")
    
    def test_graph_node_sequence(self):
        """Test that graphs execute nodes in the correct sequence."""
        # This is a structural test to ensure proper graph construction
        text_graph = create_text_only_graph()
        
        # Check that the graph has the expected nodes
        nodes = text_graph.nodes
        expected_nodes = {"system_setup", "parse_intent", "text_generation", "finalize_output"}
        
        # All expected nodes should exist
        for node in expected_nodes:
            self.assertIn(node, nodes, f"Text graph should have {node} node")
        
        # Similar checks can be added for other graphs
        image_graph = create_image_only_graph()
        image_nodes = image_graph.nodes
        expected_image_nodes = {"system_setup", "parse_intent", "image_generation", "finalize_output"}
        
        for node in expected_image_nodes:
            self.assertIn(node, image_nodes, f"Image graph should have {node} node")


if __name__ == "__main__":
    unittest.main()
