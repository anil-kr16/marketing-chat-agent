#!/usr/bin/env python3
"""
QA Test Runner - Comprehensive tests for quality assurance.

This script provides thorough testing for QA workflows and CI/CD.
"""

import os
import sys
import time
import json
from typing import Dict, Any, List

# Add project root to path
project_root = os.path.dirname(os.path.dirname(__file__))
sys.path.append(project_root)

from tests.utils.test_helpers import (
    create_test_state, setup_test_environment, cleanup_test_files,
    TestResultValidator, SAMPLE_INPUTS, assert_files_created
)
from src.agents.micro.text_only_agent import TextOnlyAgent
from src.agents.micro.image_only_agent import ImageOnlyAgent
from src.agents.micro.hashtag_only_agent import HashtagOnlyAgent
from src.agents.campaign.full_marketing_agent import FullMarketingAgent
from langchain.schema import HumanMessage


def print_colored(text: str, color_code: str):
    """Print colored text."""
    print(f"\033[{color_code}m{text}\033[0m")


def print_qa_header(title: str):
    """Print QA test header."""
    print("\n" + "=" * 70)
    print_colored(f"🔍 {title}", "36")
    print("=" * 70)


def comprehensive_agent_test(agent_class, agent_name: str) -> Dict[str, Any]:
    """Run comprehensive tests on an agent."""
    print_colored(f"\n📋 Testing {agent_name}", "33")
    print("-" * 50)
    
    results = {
        "agent": agent_name,
        "tests": {},
        "overall_success": True,
        "total_time": 0.0
    }
    
    test_cases = [
        ("Basic functionality", SAMPLE_INPUTS["simple"]),
        ("Seasonal context", SAMPLE_INPUTS["seasonal"]),
        ("Detailed campaign", SAMPLE_INPUTS["detailed"]),
        ("B2B campaign", SAMPLE_INPUTS["b2b"]),
        ("Cultural context", SAMPLE_INPUTS["cultural"])
    ]
    
    for test_name, test_input in test_cases:
        start_time = time.time()
        
        try:
            agent = agent_class()
            state = create_test_state(test_input)
            result = agent.run(state)
            
            end_time = time.time()
            duration = end_time - start_time
            results["total_time"] += duration
            
            # Validate based on agent type
            validator = TestResultValidator(result)
            success = False
            details = {}
            
            if agent_name == "TextOnlyAgent":
                success = validator.validate_text_generation()
                if success:
                    details = {
                        "content_length": len(result.get("post_content", "")),
                        "has_intent": "parsed_intent" in result,
                        "has_goal": bool(result.get("parsed_intent", {}).get("goal"))
                    }
                    
            elif agent_name == "ImageOnlyAgent":
                success = validator.validate_image_generation()
                if success:
                    details = {
                        "image_url": result.get("image_url", ""),
                        "has_prompt": bool(result.get("image_prompt")),
                        "prompt_length": len(result.get("image_prompt", ""))
                    }
                    
            elif agent_name == "HashtagOnlyAgent":
                success = validator.validate_hashtag_generation()
                if success:
                    details = {
                        "hashtag_count": len(result.get("hashtags", [])),
                        "cta_count": len(result.get("ctas", [])),
                        "hashtags_valid": all(tag.startswith("#") for tag in result.get("hashtags", []))
                    }
            
            results["tests"][test_name] = {
                "success": success,
                "duration": duration,
                "details": details
            }
            
            if not success:
                results["overall_success"] = False
            
            status = "✅ PASS" if success else "❌ FAIL"
            print(f"  {status} {test_name} ({duration:.2f}s)")
            
        except Exception as e:
            end_time = time.time()
            duration = end_time - start_time
            results["total_time"] += duration
            
            results["tests"][test_name] = {
                "success": False,
                "duration": duration,
                "error": str(e)
            }
            results["overall_success"] = False
            
            print(f"  ❌ FAIL {test_name} ({duration:.2f}s) - Error: {str(e)[:50]}...")
    
    return results


def comprehensive_integration_test() -> Dict[str, Any]:
    """Run comprehensive integration tests."""
    print_colored(f"\n📋 Testing Full Marketing Integration", "33")
    print("-" * 50)
    
    results = {
        "tests": {},
        "overall_success": True,
        "total_time": 0.0
    }
    
    integration_tests = [
        ("Single channel campaign", "promote product on email"),
        ("Multi-channel campaign", "sell watches on instagram facebook email"),
        ("Seasonal campaign", "promote gifts on christmas to families"),
        ("B2B campaign", "market software to enterprises on linkedin email"),
        ("Cultural campaign", "promote jewelry on diwali to indian families")
    ]
    
    for test_name, test_input in integration_tests:
        start_time = time.time()
        
        try:
            # Clean up before each test
            cleanup_test_files()
            
            agent = FullMarketingAgent()
            state = create_test_state(test_input)
            
            # Run with confirmation
            result = agent.run(state)
            if result.get("agent_flags", {}).get("awaiting_confirmation"):
                result["messages"].append(HumanMessage(content="yes"))
                result = agent.run(result)
            
            end_time = time.time()
            duration = end_time - start_time
            results["total_time"] += duration
            
            # Comprehensive validation
            validator = TestResultValidator(result)
            success = validator.validate_full_campaign()
            
            details = {}
            if success:
                # Check delivery
                delivery = result.get("delivery", {})
                delivery_results = delivery.get("results", {})
                
                # Check files created
                files_created = []
                try:
                    outbox_dir = "data/outbox"
                    if os.path.exists(outbox_dir):
                        items = os.listdir(outbox_dir)
                        campaign_folders = [item for item in items if os.path.isdir(os.path.join(outbox_dir, item))]
                        if campaign_folders:
                            latest_folder = max(campaign_folders, key=lambda f: os.path.getctime(os.path.join(outbox_dir, f)))
                            folder_path = os.path.join(outbox_dir, latest_folder)
                            files_created = os.listdir(folder_path)
                except Exception:
                    pass
                
                details = {
                    "channels_delivered": len(delivery_results),
                    "files_created": len(files_created),
                    "has_final_response": "final_response" in result,
                    "content_components": {
                        "post_content": bool(result.get("post_content")),
                        "hashtags": bool(result.get("hashtags")),
                        "ctas": bool(result.get("ctas")),
                        "image_url": bool(result.get("image_url"))
                    }
                }
            
            results["tests"][test_name] = {
                "success": success,
                "duration": duration,
                "details": details
            }
            
            if not success:
                results["overall_success"] = False
            
            status = "✅ PASS" if success else "❌ FAIL"
            print(f"  {status} {test_name} ({duration:.2f}s)")
            
        except Exception as e:
            end_time = time.time()
            duration = end_time - start_time
            results["total_time"] += duration
            
            results["tests"][test_name] = {
                "success": False,
                "duration": duration,
                "error": str(e)
            }
            results["overall_success"] = False
            
            print(f"  ❌ FAIL {test_name} ({duration:.2f}s) - Error: {str(e)[:50]}...")
    
    return results


def generate_qa_report(all_results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Generate comprehensive QA report."""
    total_tests = 0
    passed_tests = 0
    total_time = 0.0
    
    component_results = {}
    
    for result in all_results:
        if "agent" in result:
            # Micro agent result
            agent_name = result["agent"]
            component_results[agent_name] = result
            
            for test_name, test_result in result["tests"].items():
                total_tests += 1
                total_time += test_result["duration"]
                if test_result["success"]:
                    passed_tests += 1
        else:
            # Integration result
            component_results["Integration"] = result
            
            for test_name, test_result in result["tests"].items():
                total_tests += 1
                total_time += test_result["duration"]
                if test_result["success"]:
                    passed_tests += 1
    
    success_rate = (passed_tests / total_tests) * 100 if total_tests > 0 else 0
    
    report = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "summary": {
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "failed_tests": total_tests - passed_tests,
            "success_rate": success_rate,
            "total_time": total_time,
            "avg_test_time": total_time / total_tests if total_tests > 0 else 0
        },
        "components": component_results,
        "overall_success": all(r["overall_success"] for r in all_results)
    }
    
    return report


def save_qa_report(report: Dict[str, Any]):
    """Save QA report to file."""
    os.makedirs("tests/reports", exist_ok=True)
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    filename = f"tests/reports/qa_report_{timestamp}.json"
    
    with open(filename, 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"\n📄 QA Report saved: {filename}")


def run_qa_tests():
    """Run comprehensive QA test suite."""
    print_qa_header("QA TEST SUITE - COMPREHENSIVE VALIDATION")
    
    # Setup
    setup_test_environment()
    cleanup_test_files()
    
    all_results = []
    
    # Test micro agents
    print_colored("\n🔬 MICRO AGENT COMPREHENSIVE TESTS", "35")
    
    micro_agents = [
        (TextOnlyAgent, "TextOnlyAgent"),
        (ImageOnlyAgent, "ImageOnlyAgent"),
        (HashtagOnlyAgent, "HashtagOnlyAgent")
    ]
    
    for agent_class, agent_name in micro_agents:
        result = comprehensive_agent_test(agent_class, agent_name)
        all_results.append(result)
    
    # Test integration
    print_colored("\n🔗 INTEGRATION COMPREHENSIVE TESTS", "35")
    
    integration_result = comprehensive_integration_test()
    all_results.append(integration_result)
    
    # Generate report
    report = generate_qa_report(all_results)
    
    # Print summary
    print_qa_header("QA TEST SUMMARY")
    
    summary = report["summary"]
    print(f"✅ Tests Passed: {summary['passed_tests']}/{summary['total_tests']}")
    print(f"📈 Success Rate: {summary['success_rate']:.1f}%")
    print(f"⏱️  Total Time: {summary['total_time']:.2f}s")
    print(f"⚡ Avg Time: {summary['avg_test_time']:.2f}s per test")
    
    # Component breakdown
    print_colored("\n📊 COMPONENT BREAKDOWN", "33")
    for component, result in report["components"].items():
        status = "✅" if result["overall_success"] else "❌"
        test_count = len(result["tests"])
        passed_count = sum(1 for t in result["tests"].values() if t["success"])
        print(f"  {status} {component}: {passed_count}/{test_count} tests passed")
    
    # Save report
    save_qa_report(report)
    
    if report["overall_success"]:
        print_colored("\n🎉 ALL QA TESTS PASSED! Production ready! ✅", "32")
        return True
    else:
        failed_tests = summary['total_tests'] - summary['passed_tests']
        print_colored(f"\n❌ {failed_tests} TESTS FAILED! Fix before production!", "31")
        return False


def main():
    """Main entry point."""
    success = run_qa_tests()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
