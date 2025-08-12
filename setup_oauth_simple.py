#!/usr/bin/env python3
"""Simple OAuth credentials setup for CourseHero Gmail."""

import json
import os

def create_oauth_credentials():
    """Create OAuth credentials file from user input."""
    print('🔐 OAUTH CREDENTIALS SETUP FOR COURSEHERO')
    print('=' * 42)
    print()
    
    print('📝 Please provide your Google OAuth credentials:')
    print()
    
    client_id = input('Google Client ID: ').strip()
    if not client_id:
        print('❌ Client ID is required')
        return False
    
    client_secret = input('Google Client Secret: ').strip()
    if not client_secret:
        print('❌ Client Secret is required')
        return False
    
    # Create OAuth credentials in Google's expected format
    oauth_data = {
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
    
    # Save to file
    credentials_file = 'gmail_credentials.json'
    try:
        with open(credentials_file, 'w') as f:
            json.dump(oauth_data, f, indent=2)
        
        print()
        print(f'✅ OAuth credentials saved to: {credentials_file}')
        print()
        
        # Display what to add to .env
        print('📝 ADD THESE LINES TO YOUR .ENV FILE:')
        print('=' * 35)
        print('USE_OAUTH_GMAIL=true')
        print(f'GOOGLE_CLIENT_ID={client_id}')
        print(f'GOOGLE_CLIENT_SECRET={client_secret}')
        print()
        
        return True
        
    except Exception as e:
        print(f'❌ Failed to save OAuth credentials: {e}')
        return False

def main():
    """Run OAuth setup."""
    success = create_oauth_credentials()
    
    if success:
        print('🎉 OAuth credentials setup complete!')
        print()
        print('📋 NEXT STEPS:')
        print('1. Update your .env file with the lines above')
        print('2. Run: python test_oauth_gmail.py')
        print('3. Authorize in browser when prompted')
        print('4. Test email sending!')
    else:
        print('❌ OAuth setup failed')

if __name__ == '__main__':
    main()
