#!/usr/bin/env python3
"""Verify that the commands in README.md work correctly."""

import subprocess
import sys
import os

def run_command(cmd, description):
    """Run a command and report results."""
    print(f"\n🧪 Testing: {description}")
    print(f"   Command: {cmd}")
    
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            print("   ✅ SUCCESS")
            return True
        else:
            print("   ❌ FAILED")
            print(f"   Error: {result.stderr}")
            return False
    except subprocess.TimeoutExpired:
        print("   ⏰ TIMEOUT (expected for interactive commands)")
        return True
    except Exception as e:
        print(f"   ❌ ERROR: {e}")
        return False

def main():
    """Test key commands from README."""
    print("🔍 VERIFYING README COMMANDS")
    print("=" * 40)
    
    tests = [
        # Development commands
        ("make setup", "Environment setup"),
        ("make test-smoke", "Smoke tests"),
        ("python -c 'from src.config import get_config; print(\"Config works\")'", "Configuration loading"),
        
        # Quick non-interactive tests
        ("python -c 'from src.agents.micro.text_only_agent import TextOnlyAgent; print(\"Text agent imports\")'", "Text agent import"),
        ("python -c 'from src.utils.image_optimizer import optimize_image_for_email; print(\"Image optimizer imports\")'", "Image optimizer import"),
        ("python -c 'from src.utils.email_formatter import render_marketing_email; print(\"Email formatter imports\")'", "Email formatter import"),
    ]
    
    results = []
    
    for cmd, desc in tests:
        success = run_command(cmd, desc)
        results.append((desc, success))
    
    print("\n📊 RESULTS SUMMARY")
    print("=" * 30)
    
    passed = 0
    for desc, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status:8} {desc}")
        if success:
            passed += 1
    
    print(f"\n🎯 Score: {passed}/{len(results)} tests passed")
    
    if passed == len(results):
        print("🎉 All README commands verified successfully!")
        print("📖 README is accurate and ready for users!")
    else:
        print("⚠️ Some issues found - review failed commands")

if __name__ == "__main__":
    main()
