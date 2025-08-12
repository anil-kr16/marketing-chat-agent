"""
OAuth Gmail Provider for secure email sending.
Uses Google OAuth 2.0 for authentication instead of app passwords.
"""

import os
import base64
from typing import Optional

from src.config import get_config
from src.utils.state import MessagesState
from src.utils.common import create_campaign_folder


class OAuthGmailProvider:
    """Gmail provider using OAuth 2.0 authentication."""
    
    SCOPES = ['https://www.googleapis.com/auth/gmail.send']
    
    def __init__(self):
        self.config = get_config()
        self.service = None
    
    def send(self, subject: str, body_text: str, state: MessagesState) -> str:
        """
        Send email via Gmail API using OAuth 2.0.
        
        Args:
            subject: Email subject line
            body_text: Plain text email body
            state: Current workflow state
            
        Returns:
            Status message
        """
        try:
            # Check DRY_RUN mode first - no credentials needed for outbox
            dry_run = os.getenv("DRY_RUN", "true").lower() == "true"
            
            if dry_run:
                return self._save_to_outbox(subject, body_text, state)
            
            # For real sending, check for required OAuth configuration
            client_id = os.getenv("GOOGLE_CLIENT_ID", "")
            client_secret = os.getenv("GOOGLE_CLIENT_SECRET", "")
            
            if not all([client_id, client_secret]):
                return "❌ Missing OAuth configuration (GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET)"
            
            return self._send_via_gmail_api(subject, body_text, state)
                
        except Exception as e:
            return f"❌ OAuth Gmail sending failed: {str(e)}"
    
    def _save_to_outbox(self, subject: str, body_text: str, state: MessagesState) -> str:
        """Save OAuth email content to outbox folder."""
        try:
            # Create campaign-specific folder
            from src.utils.common import create_campaign_folder
            campaign_folder = create_campaign_folder(state, "data/outbox")
            
            # Generate HTML content using template engine
            html_content = self._generate_html_content(state)
            
            # Save plain text version
            txt_path = os.path.join(campaign_folder, "email_post.txt")
            with open(txt_path, "w", encoding="utf-8") as f:
                f.write(f"Subject: {subject}\n")
                f.write(f"Provider: OAuth Gmail\n\n")
                f.write(body_text)
            
            # Save HTML version
            html_path = os.path.join(campaign_folder, "email_post.html")
            with open(html_path, "w", encoding="utf-8") as f:
                f.write(html_content)
            
            # Handle image optimization
            image_url = state.get("image_url", "")
            if image_url and os.path.exists(image_url):
                optimized_path = self._optimize_and_save_image(image_url, campaign_folder)
                if optimized_path:
                    return f"✅ OAuth email saved to outbox: {html_path} (with optimized image: {optimized_path})"
            
            return f"✅ OAuth email saved to outbox: {html_path}"
                
        except Exception as e:
            return f"❌ Failed to save OAuth email to outbox: {str(e)}"
    
    def _generate_html_content(self, state: MessagesState) -> str:
        """Generate HTML content using email template engine."""
        try:
            from src.utils.email_formatter import EmailTemplateEngine
            
            template_engine = EmailTemplateEngine()
            
            # Extract campaign data
            parsed_intent = state.get("parsed_intent", {})
            final_response = state.get("final_response", {})
            email_content = final_response.get("email", {})
            
            campaign_data = {
                "subject": email_content.get("subject", "Marketing Campaign"),
                "content": state.get("post_content", ""),
                "ctas": state.get("ctas", []),
                "hashtags": state.get("hashtags", []),
                "goal": parsed_intent.get("goal", ""),
                "audience": parsed_intent.get("audience", "")
            }
            
            # Generate HTML using template
            image_url = state.get("image_url", "")
            if image_url and os.path.exists(image_url):
                return template_engine.render_marketing_email(campaign_data, image_url)
            else:
                return template_engine.render_marketing_email(campaign_data)
                
        except ImportError:
            # Fallback to simple HTML if template engine not available
            return self._generate_simple_html(state)
        except Exception as e:
            print(f"OAuth template generation failed: {e}, using simple HTML")
            return self._generate_simple_html(state)
    
    def _generate_simple_html(self, state: MessagesState) -> str:
        """Generate simple HTML email as fallback."""
        final_response = state.get("final_response", {})
        email_content = final_response.get("email", {})
        subject = email_content.get("subject", "Marketing Campaign")
        content = state.get("post_content", "")
        
        html = f"""<!DOCTYPE html>
<html>
<head>
    <title>{subject}</title>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background: #f4f4f4; padding: 20px; text-align: center; }}
        .content {{ padding: 20px; }}
        .footer {{ text-align: center; color: #666; font-size: 12px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>{subject}</h1>
        </div>
        <div class="content">
            <p>{content}</p>
        </div>
        <div class="footer">
            <p>Sent via OAuth Gmail Provider</p>
        </div>
    </div>
</body>
</html>"""
        return html
    
    def _optimize_and_save_image(self, image_path: str, campaign_folder: str) -> Optional[str]:
        """Optimize and save image for email."""
        try:
            from src.utils.image_optimizer import EmailImageOptimizer
            
            optimizer = EmailImageOptimizer()
            optimized_path = os.path.join(campaign_folder, "campaign_image_optimized.jpg")
            
            if optimizer.optimize_for_email(image_path, optimized_path):
                return optimized_path
            return None
            
        except ImportError:
            # If optimizer not available, just copy the original
            import shutil
            dest_path = os.path.join(campaign_folder, "campaign_image_original.png")
            shutil.copy2(image_path, dest_path)
            return dest_path
        except Exception as e:
            print(f"OAuth image optimization failed: {e}")
            return None
    
    def _get_credentials(self):
        """Get OAuth 2.0 credentials for Gmail API."""
        try:
            from google.auth.transport.requests import Request
            from google_auth_oauthlib.flow import InstalledAppFlow
            from google.oauth2.credentials import Credentials
            import pickle
            
            creds = None
            token_file = "token.pickle"
            
            # Load existing credentials
            if os.path.exists(token_file):
                with open(token_file, "rb") as token:
                    creds = pickle.load(token)
            
            # If no valid credentials, get new ones
            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    creds.refresh(Request())
                else:
                    client_id = os.getenv("GOOGLE_CLIENT_ID")
                    client_secret = os.getenv("GOOGLE_CLIENT_SECRET")
                    
                    # Create OAuth flow
                    flow = InstalledAppFlow.from_client_config(
                        {
                            "installed": {
                                "client_id": client_id,
                                "client_secret": client_secret,
                                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                                "token_uri": "https://oauth2.googleapis.com/token",
                                "redirect_uris": ["http://localhost"]
                            }
                        },
                        self.SCOPES
                    )
                    creds = flow.run_local_server(port=0)
                
                # Save credentials for next run
                with open(token_file, "wb") as token:
                    pickle.dump(creds, token)
            
            return creds
            
        except ImportError:
            raise ImportError("Google OAuth libraries not installed. Run: pip install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client")
        except Exception as e:
            raise Exception(f"OAuth credential setup failed: {str(e)}")
    
    def _build_gmail_service(self):
        """Build Gmail API service."""
        try:
            from googleapiclient.discovery import build
            
            creds = self._get_credentials()
            service = build("gmail", "v1", credentials=creds)
            return service
            
        except ImportError:
            raise ImportError("Google API client not installed")
        except Exception as e:
            raise Exception(f"Gmail service setup failed: {str(e)}")
    
    def _create_message(self, subject: str, body_text: str, html_content: str) -> dict:
        """Create email message for Gmail API."""
        try:
            from email.mime.multipart import MIMEMultipart
            from email.mime.text import MIMEText
            
            from_email = os.getenv("EMAIL_FROM", "")
            to_email = os.getenv("EMAIL_TO", "")
            
            # Create message
            message = MIMEMultipart("alternative")
            message["to"] = to_email
            message["from"] = from_email
            message["subject"] = subject
            
            # Add text and HTML parts
            text_part = MIMEText(body_text, "plain")
            html_part = MIMEText(html_content, "html")
            
            message.attach(text_part)
            message.attach(html_part)
            
            # Encode for Gmail API
            raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
            
            return {"raw": raw_message}
            
        except Exception as e:
            raise Exception(f"Message creation failed: {str(e)}")
    
    def _send_via_gmail_api(self, subject: str, body_text: str, state: MessagesState) -> str:
        """Send actual email via Gmail API."""
        try:
            # Build Gmail service
            service = self._build_gmail_service()
            
            # Generate HTML content
            html_content = self._generate_html_content(state)
            
            # Create message
            message = self._create_message(subject, body_text, html_content)
            
            # Send message
            result = service.users().messages().send(userId="me", body=message).execute()
            
            to_email = os.getenv("EMAIL_TO", "recipient")
            return f"✅ OAuth email sent successfully to {to_email} (Message ID: {result['id']})"
            
        except Exception as e:
            return f"❌ Gmail API sending failed: {str(e)}"
