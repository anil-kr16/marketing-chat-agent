#!/usr/bin/env python3
"""Debug HTML email enhancement activation."""

import sys
import os
sys.path.append('.')

from src.config import get_config
from src.utils.state import MessagesState
from langchain.schema import HumanMessage

def debug_config():
    """Debug configuration values."""
    print('🔧 CONFIGURATION DEBUG')
    print('=' * 30)
    
    # Set environment variables
    os.environ['ENABLE_HTML_EMAIL'] = 'true'
    os.environ['ENABLE_EMAIL_TEMPLATES'] = 'true'
    os.environ['ENABLE_IMAGE_OPTIMIZATION'] = 'true'
    os.environ['DRY_RUN'] = 'true'
    
    cfg = get_config()
    print(f'DRY_RUN: {cfg.dry_run}')
    print(f'ENABLE_EMAIL: {cfg.enable_email}')
    print(f'ENABLE_HTML_EMAIL: {cfg.enable_html_email}')
    print(f'ENABLE_EMAIL_TEMPLATES: {cfg.enable_email_templates}')
    print(f'ENABLE_IMAGE_OPTIMIZATION: {cfg.enable_image_optimization}')
    print()

def test_enhanced_provider_direct():
    """Test enhanced provider directly."""
    print('🎨 TESTING ENHANCED PROVIDER DIRECTLY')
    print('=' * 40)
    
    try:
        from src.providers.email.enhanced_smtp_provider import EnhancedSMTPProvider
        
        # Create test state
        state = MessagesState()
        state["post_content"] = "Test marketing content"
        state["hashtags"] = ["#Test", "#Marketing"]
        state["ctas"] = ["Click Here!", "Buy Now!"]
        state["image_url"] = "/static/images/generated_1754964586.png"
        state["parsed_intent"] = {
            "goal": "test campaign",
            "audience": "developers",
            "channels": ["Email"]
        }
        
        # Test enhanced provider
        provider = EnhancedSMTPProvider()
        result = provider.send(
            subject="Test HTML Email",
            body_text="This is a test email with HTML templates.",
            state=state
        )
        
        print(f'✅ Enhanced provider result: {result}')
        
        # Check for HTML files
        import subprocess
        html_files = subprocess.run(['find', 'data/outbox', '-name', '*.html'], capture_output=True, text=True)
        if html_files.stdout.strip():
            print('✅ HTML files found:')
            for file in html_files.stdout.strip().split('\n'):
                print(f'   📄 {file}')
                # Show first few lines
                try:
                    with open(file, 'r') as f:
                        content = f.read()
                        print(f'   Preview: {content[:150]}...')
                except:
                    pass
        else:
            print('❌ No HTML files found')
        
        return True
        
    except Exception as e:
        print(f'❌ Enhanced provider test failed: {e}')
        import traceback
        traceback.print_exc()
        return False

def test_template_engine():
    """Test template engine directly."""
    print()
    print('🎭 TESTING TEMPLATE ENGINE DIRECTLY')
    print('=' * 40)
    
    try:
        from src.utils.email_formatter import render_marketing_email
        
        campaign_data = {
            "subject": "Test Campaign",
            "campaign_title": "Promote Test Products",
            "audience_greeting": "Hello Developers!",
            "marketing_copy": "This is test marketing copy with <strong>HTML</strong> content.",
            "cta_buttons": ["Click Here!", "Buy Now!", "Learn More!"],
            "hashtags": ["#Test", "#Marketing", "#HTML"],
            "hero_image": "test_image_url"
        }
        
        email_content = render_marketing_email(campaign_data)
        
        print(f'✅ Template rendering successful')
        print(f'📧 Subject: {email_content.subject}')
        print(f'🎨 Has HTML: {bool(email_content.html_body)}')
        print(f'📝 Has Text: {bool(email_content.plain_text_body)}')
        print(f'🖼️ Has Image: {email_content.has_image}')
        
        if email_content.html_body:
            print(f'🎨 HTML Preview: {email_content.html_body[:200]}...')
        
        return True
        
    except Exception as e:
        print(f'❌ Template engine test failed: {e}')
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run debugging tests."""
    print('🐛 DEBUGGING HTML EMAIL ENHANCEMENTS')
    print()
    
    debug_config()
    template_ok = test_template_engine()
    provider_ok = test_enhanced_provider_direct()
    
    print()
    print('📊 DEBUG RESULTS')
    print('=' * 20)
    print(f'🎭 Template Engine: {"✅ WORKING" if template_ok else "❌ FAILED"}')
    print(f'🎨 Enhanced Provider: {"✅ WORKING" if provider_ok else "❌ FAILED"}')
    
    if template_ok and provider_ok:
        print()
        print('✅ HTML email system is working!')
        print('💡 HTML files should be created in outbox when enabled')
    else:
        print()
        print('❌ Issues found in HTML email system')
        print('🔧 Check dependencies and configuration')

if __name__ == '__main__':
    main()
