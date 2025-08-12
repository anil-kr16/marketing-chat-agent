#!/usr/bin/env python3
"""
Main test runner for Marketing Chat Agent.

This script provides different test execution modes for development and QA workflows.
"""

import os
import sys
import unittest
import time
import argparse
from typing import List, Optional

# Add project root to path
project_root = os.path.dirname(os.path.dirname(__file__))
sys.path.append(project_root)

from tests.utils.test_helpers import setup_test_environment, cleanup_test_files


class TestResult:
    """Container for test execution results."""
    
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.errors = 0
        self.skipped = 0
        self.total_time = 0.0
        self.failures = []
        self.errors_list = []


def print_header(title: str):
    """Print a formatted header."""
    print("\n" + "=" * 80)
    print(f"🧪 {title}")
    print("=" * 80)


def print_subheader(title: str):
    """Print a formatted subheader."""
    print(f"\n📋 {title}")
    print("-" * 60)


def run_test_suite(test_pattern: str, description: str) -> TestResult:
    """Run a specific test suite and return results."""
    print_subheader(f"Running {description}")
    
    # Discover and run tests
    loader = unittest.TestLoader()
    suite = loader.discover('tests', pattern=test_pattern)
    
    # Custom test runner to capture results
    class CustomTestResult(unittest.TextTestResult):
        def __init__(self, stream, descriptions, verbosity):
            super().__init__(stream, descriptions, verbosity)
            self.test_results = TestResult()
        
        def addSuccess(self, test):
            super().addSuccess(test)
            self.test_results.passed += 1
        
        def addError(self, test, err):
            super().addError(test, err)
            self.test_results.errors += 1
            self.test_results.errors_list.append((test, err))
        
        def addFailure(self, test, err):
            super().addFailure(test, err)
            self.test_results.failed += 1
            self.test_results.failures.append((test, err))
        
        def addSkip(self, test, reason):
            super().addSkip(test, reason)
            self.test_results.skipped += 1
    
    # Run tests
    start_time = time.time()
    runner = unittest.TextTestRunner(
        verbosity=2, 
        resultclass=CustomTestResult,
        stream=sys.stdout
    )
    result = runner.run(suite)
    end_time = time.time()
    
    # Update timing
    result.test_results.total_time = end_time - start_time
    
    return result.test_results


def run_unit_tests() -> TestResult:
    """Run all unit tests."""
    return run_test_suite('test_*_agent.py', 'Unit Tests (Micro Agents)')


def run_integration_tests() -> TestResult:
    """Run all integration tests."""
    return run_test_suite('test_*_flow.py', 'Integration Tests (Full Workflows)')


def run_all_tests() -> List[TestResult]:
    """Run all test suites."""
    results = []
    
    # Unit tests
    results.append(run_unit_tests())
    
    # Integration tests  
    results.append(run_integration_tests())
    
    return results


def print_summary(results: List[TestResult]):
    """Print test execution summary."""
    print_header("TEST EXECUTION SUMMARY")
    
    total_passed = sum(r.passed for r in results)
    total_failed = sum(r.failed for r in results)
    total_errors = sum(r.errors for r in results)
    total_skipped = sum(r.skipped for r in results)
    total_time = sum(r.total_time for r in results)
    
    print(f"✅ Tests Passed:  {total_passed}")
    print(f"❌ Tests Failed:  {total_failed}")
    print(f"💥 Test Errors:   {total_errors}")
    print(f"⏭️  Tests Skipped: {total_skipped}")
    print(f"⏱️  Total Time:    {total_time:.2f}s")
    
    # Success rate
    total_tests = total_passed + total_failed + total_errors
    if total_tests > 0:
        success_rate = (total_passed / total_tests) * 100
        print(f"📈 Success Rate:  {success_rate:.1f}%")
    
    # Overall status
    if total_failed == 0 and total_errors == 0:
        print("\n🎉 ALL TESTS PASSED! ✅")
        return True
    else:
        print(f"\n❌ TESTS FAILED! ({total_failed} failures, {total_errors} errors)")
        return False


def run_quick_smoke_test():
    """Run a quick smoke test to verify basic functionality."""
    print_header("QUICK SMOKE TEST")
    
    try:
        # Test basic imports
        print("📦 Testing imports...")
        from src.agents.micro.text_only_agent import TextOnlyAgent
        from src.agents.micro.image_only_agent import ImageOnlyAgent
        from src.agents.micro.hashtag_only_agent import HashtagOnlyAgent
        from src.agents.campaign.full_marketing_agent import FullMarketingAgent
        print("   ✅ All agents imported successfully")
        
        # Test basic agent creation
        print("🏗️  Testing agent creation...")
        text_agent = TextOnlyAgent()
        image_agent = ImageOnlyAgent()
        hashtag_agent = HashtagOnlyAgent()
        full_agent = FullMarketingAgent()
        print("   ✅ All agents created successfully")
        
        print("\n🎉 SMOKE TEST PASSED! System is ready for testing.")
        return True
        
    except Exception as e:
        print(f"\n❌ SMOKE TEST FAILED! Error: {e}")
        return False


def main():
    """Main test runner entry point."""
    parser = argparse.ArgumentParser(description='Marketing Chat Agent Test Runner')
    parser.add_argument('--mode', choices=['unit', 'integration', 'all', 'smoke'], 
                       default='all', help='Test execution mode')
    parser.add_argument('--cleanup', action='store_true', 
                       help='Clean up test files before running')
    parser.add_argument('--verbose', action='store_true',
                       help='Verbose output')
    
    args = parser.parse_args()
    
    # Setup
    print_header("MARKETING CHAT AGENT - TEST RUNNER")
    print(f"🎯 Mode: {args.mode.upper()}")
    print(f"📁 Working Directory: {os.getcwd()}")
    
    # Setup test environment
    setup_test_environment()
    
    # Cleanup if requested
    if args.cleanup:
        print("🧹 Cleaning up test files...")
        cleanup_test_files()
        cleanup_test_files("static/images")
    
    success = True
    
    if args.mode == 'smoke':
        success = run_quick_smoke_test()
    
    elif args.mode == 'unit':
        results = [run_unit_tests()]
        success = print_summary(results)
    
    elif args.mode == 'integration':
        results = [run_integration_tests()]
        success = print_summary(results)
    
    elif args.mode == 'all':
        results = run_all_tests()
        success = print_summary(results)
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
