"""
SMTP Email Provider for marketing campaigns.
Supports both DRY_RUN mode (save to outbox) and real email sending.
"""

import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from typing import Optional

from src.config import get_config
from src.utils.state import MessagesState
from src.utils.common import create_campaign_folder


class SMTPProvider:
    """Basic SMTP email provider with DRY_RUN support."""
    
    def __init__(self):
        self.config = get_config()
    
    def send(self, subject: str, body_text: str, state: MessagesState, html: Optional[str] = None) -> str:
        """
        Send email via SMTP or save to outbox in DRY_RUN mode.
        
        Args:
            subject: Email subject line
            body_text: Plain text email body
            state: Current workflow state
            html: Optional HTML email body
            
        Returns:
            Status message
        """
        try:
            # Check DRY_RUN mode first - no credentials needed for outbox
            dry_run = os.getenv("DRY_RUN", "true").lower() == "true"
            
            if dry_run:
                return self._save_to_outbox(subject, body_text, html, state)
            
            # For real sending, get and validate email configuration
            smtp_host = os.getenv("EMAIL_SMTP_HOST", "smtp.gmail.com")
            smtp_port = int(os.getenv("EMAIL_SMTP_PORT", "587"))
            username = os.getenv("EMAIL_USERNAME", "")
            password = os.getenv("EMAIL_PASSWORD", "")
            from_email = os.getenv("EMAIL_FROM", username)
            to_email = os.getenv("EMAIL_TO", "")
            
            if not all([smtp_host, username, password, from_email, to_email]):
                return "❌ Missing required email configuration"
            
            return self._send_real_email(subject, body_text, html, smtp_host, smtp_port, 
                                       username, password, from_email, to_email)
                
        except Exception as e:
            return f"❌ Email sending failed: {str(e)}"
    
    def _save_to_outbox(self, subject: str, body_text: str, html: Optional[str], 
                       state: MessagesState) -> str:
        """Save email content to outbox folder."""
        try:
            # Create campaign-specific folder
            from src.utils.common import create_campaign_folder
            campaign_folder = create_campaign_folder(state, "data/outbox")
            
            # Save plain text version
            txt_path = os.path.join(campaign_folder, "email_post.txt")
            with open(txt_path, "w", encoding="utf-8") as f:
                f.write(f"Subject: {subject}\n\n")
                f.write(body_text)
            
            # Save HTML version if provided
            if html:
                html_path = os.path.join(campaign_folder, "email_post.html")
                with open(html_path, "w", encoding="utf-8") as f:
                    f.write(f"<!DOCTYPE html>\n<html>\n<head>\n")
                    f.write(f"<title>{subject}</title>\n</head>\n<body>\n")
                    f.write(html)
                    f.write(f"\n</body>\n</html>")
                
                return f"✅ Email saved to outbox: {txt_path} and {html_path}"
            else:
                return f"✅ Email saved to outbox: {txt_path}"
                
        except Exception as e:
            return f"❌ Failed to save email to outbox: {str(e)}"
    
    def _send_real_email(self, subject: str, body_text: str, html: Optional[str],
                        smtp_host: str, smtp_port: int, username: str, password: str,
                        from_email: str, to_email: str) -> str:
        """Send actual email via SMTP."""
        try:
            # Create message
            if html:
                # Create multipart message for both text and HTML
                msg = MIMEMultipart("alternative")
                msg["Subject"] = subject
                msg["From"] = from_email
                msg["To"] = to_email
                
                # Add both text and HTML parts
                text_part = MIMEText(body_text, "plain")
                html_part = MIMEText(html, "html")
                
                msg.attach(text_part)
                msg.attach(html_part)
            else:
                # Plain text only
                msg = MIMEText(body_text)
                msg["Subject"] = subject
                msg["From"] = from_email
                msg["To"] = to_email
            
            # Connect and send
            with smtplib.SMTP(smtp_host, smtp_port) as server:
                server.starttls()
                server.login(username, password)
                server.send_message(msg)
            
            return f"✅ Email sent successfully to {to_email}"
            
        except Exception as e:
            return f"❌ SMTP sending failed: {str(e)}"
