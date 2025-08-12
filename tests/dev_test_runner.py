#!/usr/bin/env python3
"""
Development Test Runner - Quick tests for developers.

This script provides fast, focused testing for development workflows.
"""

import os
import sys
import time
from typing import Dict, Any

# Add project root to path
project_root = os.path.dirname(os.path.dirname(__file__))
sys.path.append(project_root)

from tests.utils.test_helpers import (
    create_test_state, setup_test_environment, cleanup_test_files,
    TestResultValidator, SAMPLE_INPUTS
)
from src.agents.micro.text_only_agent import TextOnlyAgent
from src.agents.micro.image_only_agent import ImageOnlyAgent
from src.agents.micro.hashtag_only_agent import HashtagOnlyAgent
from src.agents.campaign.full_marketing_agent import FullMarketingAgent
from src.agents.text_agent.utils.ui import print_colored
from langchain.schema import HumanMessage





def print_test_header(title: str):
    """Print test header."""
    print("\n" + "=" * 60)
    print_colored(f"🧪 {title}", "36")
    print("=" * 60)


def print_test_result(test_name: str, passed: bool, duration: float, details: str = ""):
    """Print individual test result."""
    status = "✅ PASS" if passed else "❌ FAIL"
    color = "32" if passed else "31"
    print_colored(f"{status} {test_name} ({duration:.2f}s)", color)
    if details:
        print(f"   {details}")


def quick_agent_test(agent_class, agent_name: str, test_input: str) -> Dict[str, Any]:
    """Run a quick test on an agent."""
    start_time = time.time()
    
    try:
        agent = agent_class()
        state = create_test_state(test_input)
        result = agent.run(state)
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Basic validation
        validator = TestResultValidator(result)
        
        success = False
        details = ""
        
        if agent_name == "TextOnlyAgent":
            success = validator.validate_text_generation()
            if success:
                content_length = len(result.get("post_content", ""))
                details = f"Generated {content_length} chars"
            else:
                details = "No valid text generated"
                
        elif agent_name == "ImageOnlyAgent":
            success = validator.validate_image_generation()
            if success:
                image_url = result.get("image_url", "")
                details = f"Image: {os.path.basename(image_url)}"
            else:
                details = "No valid image generated"
                
        elif agent_name == "HashtagOnlyAgent":
            success = validator.validate_hashtag_generation()
            if success:
                hashtag_count = len(result.get("hashtags", []))
                cta_count = len(result.get("ctas", []))
                details = f"{hashtag_count} hashtags, {cta_count} CTAs"
            else:
                details = "No hashtags/CTAs generated"
        
        return {
            "success": success,
            "duration": duration,
            "details": details,
            "result": result
        }
        
    except Exception as e:
        end_time = time.time()
        return {
            "success": False,
            "duration": end_time - start_time,
            "details": f"Error: {str(e)[:50]}...",
            "result": None
        }


def quick_integration_test() -> Dict[str, Any]:
    """Run a quick integration test."""
    start_time = time.time()
    
    try:
        agent = FullMarketingAgent()
        state = create_test_state("promote tech product on instagram email")
        
        # Initial run
        result = agent.run(state)
        
        # FullMarketingAgent doesn't need confirmation - runs directly
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Validate full campaign
        validator = TestResultValidator(result)
        success = validator.validate_full_campaign()
        
        details = ""
        if success:
            delivery = result.get("delivery", {})
            channels = len(delivery.get("results", {}))
            details = f"Delivered to {channels} channels"
        else:
            details = "Campaign generation failed"
        
        return {
            "success": success,
            "duration": duration,
            "details": details,
            "result": result
        }
        
    except Exception as e:
        end_time = time.time()
        return {
            "success": False,
            "duration": end_time - start_time,
            "details": f"Error: {str(e)[:50]}...",
            "result": None
        }


def run_dev_tests():
    """Run development test suite."""
    print_test_header("DEVELOPMENT TEST SUITE - QUICK VALIDATION")
    
    # Setup
    setup_test_environment()
    cleanup_test_files()
    
    total_tests = 0
    passed_tests = 0
    total_time = 0.0
    
    # Test micro agents
    print_colored("\n🔬 MICRO AGENT TESTS", "33")
    print("-" * 40)
    
    micro_agents = [
        (TextOnlyAgent, "TextOnlyAgent"),
        (ImageOnlyAgent, "ImageOnlyAgent"), 
        (HashtagOnlyAgent, "HashtagOnlyAgent")
    ]
    
    for agent_class, agent_name in micro_agents:
        test_result = quick_agent_test(agent_class, agent_name, SAMPLE_INPUTS["simple"])
        
        total_tests += 1
        total_time += test_result["duration"]
        
        if test_result["success"]:
            passed_tests += 1
        
        print_test_result(
            agent_name,
            test_result["success"],
            test_result["duration"],
            test_result["details"]
        )
    
    # Test integration
    print_colored("\n🔗 INTEGRATION TEST", "33")
    print("-" * 40)
    
    integration_result = quick_integration_test()
    total_tests += 1
    total_time += integration_result["duration"]
    
    if integration_result["success"]:
        passed_tests += 1
    
    print_test_result(
        "Full Marketing Flow",
        integration_result["success"],
        integration_result["duration"],
        integration_result["details"]
    )
    
    # Summary
    print_test_header("DEV TEST SUMMARY")
    
    success_rate = (passed_tests / total_tests) * 100 if total_tests > 0 else 0
    
    print(f"✅ Tests Passed: {passed_tests}/{total_tests}")
    print(f"📈 Success Rate: {success_rate:.1f}%")
    print(f"⏱️  Total Time: {total_time:.2f}s")
    print(f"⚡ Avg Time: {total_time/total_tests:.2f}s per test")
    
    if passed_tests == total_tests:
        print_colored("\n🎉 ALL DEV TESTS PASSED! Ready to commit! ✅", "32")
        return True
    else:
        print_colored(f"\n❌ {total_tests - passed_tests} TESTS FAILED! Fix before committing!", "31")
        return False


def main():
    """Main entry point."""
    success = run_dev_tests()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
