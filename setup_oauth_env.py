#!/usr/bin/env python3
"""Setup OAuth credentials in environment variables."""

import os
import json

def setup_oauth_credentials():
    """Setup OAuth credentials for Gmail API."""
    print('🔐 OAUTH CREDENTIALS SETUP')
    print('=' * 27)
    print()
    
    # Get OAuth credentials from user
    client_id = input('Enter your Google Client ID: ').strip()
    if not client_id:
        print('❌ Client ID is required')
        return False
    
    client_secret = input('Enter your Google Client Secret: ').strip()
    if not client_secret:
        print('❌ Client Secret is required')
        return False
    
    # Create OAuth credentials file format
    oauth_credentials = {
        "installed": {
            "client_id": client_id,
            "project_id": "coursehero-marketing-agent",
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
            "client_secret": client_secret,
            "redirect_uris": ["http://localhost"]
        }
    }
    
    # Save credentials file
    try:
        credentials_file = 'gmail_credentials.json'
        with open(credentials_file, 'w') as f:
            json.dump(oauth_credentials, f, indent=2)
        
        print(f'✅ OAuth credentials saved to: {credentials_file}')
        
        # Also show .env additions
        print()
        print('📝 ADD THESE LINES TO YOUR .ENV FILE:')
        print('-' * 35)
        print('USE_OAUTH_GMAIL=true')
        print('GOOGLE_CLIENT_ID=' + client_id)
        print('GOOGLE_CLIENT_SECRET=' + client_secret)
        print()
        
        return True
        
    except Exception as e:
        print(f'❌ Failed to save credentials: {e}')
        return False

def check_oauth_env():
    """Check if OAuth is configured in environment."""
    print('🔍 CHECKING OAUTH ENVIRONMENT')
    print('=' * 28)
    
    # Check .env file
    if os.path.exists('.env'):
        with open('.env', 'r') as f:
            env_content = f.read()
        
        checks = {
            'USE_OAUTH_GMAIL': 'USE_OAUTH_GMAIL=true' in env_content,
            'GOOGLE_CLIENT_ID': 'GOOGLE_CLIENT_ID=' in env_content,
            'GOOGLE_CLIENT_SECRET': 'GOOGLE_CLIENT_SECRET=' in env_content,
            'gmail_credentials.json': os.path.exists('gmail_credentials.json')
        }
        
        for check, status in checks.items():
            print(f'{"✅" if status else "❌"} {check}')
        
        return all(checks.values())
    else:
        print('❌ .env file not found')
        return False

def install_google_libraries():
    """Install required Google libraries."""
    print('\n📦 INSTALLING GOOGLE OAUTH LIBRARIES')
    print('=' * 35)
    
    import subprocess
    import sys
    
    libraries = [
        'google-auth',
        'google-auth-oauthlib', 
        'google-auth-httplib2',
        'google-api-python-client'
    ]
    
    try:
        for lib in libraries:
            print(f'Installing {lib}...')
            subprocess.check_call([sys.executable, '-m', 'pip', 'install', lib], 
                                capture_output=True, text=True)
        
        print('✅ All Google libraries installed!')
        return True
        
    except subprocess.CalledProcessError as e:
        print(f'❌ Installation failed: {e}')
        return False

def main():
    """Run OAuth setup."""
    print('🚀 COURSEHERO OAUTH SETUP')
    print('🎯 Email: anil.kumar@coursehero.com')
    print()
    
    # Install libraries first
    print('📦 Checking Google libraries...')
    try:
        import google.auth
        print('✅ Google libraries already installed')
    except ImportError:
        install_google_libraries()
    
    # Check current OAuth setup
    oauth_configured = check_oauth_env()
    
    if not oauth_configured:
        print('\n🔧 OAuth not configured. Setting up...')
        setup_oauth_credentials()
        
        print('\n📋 NEXT STEPS:')
        print('1. Update your .env file with the lines shown above')
        print('2. Run: python test_oauth_gmail.py')
        print('3. Complete OAuth authorization in browser')
        print('4. Test with: python -m runnables.chat_full_marketing_agent')
    else:
        print('\n✅ OAuth is already configured!')
        print('🧪 Run: python test_oauth_gmail.py')

if __name__ == '__main__':
    main()
