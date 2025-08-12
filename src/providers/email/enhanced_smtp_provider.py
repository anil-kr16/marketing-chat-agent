"""
Enhanced SMTP Email Provider with HTML templates and image support.
Supports rich HTML emails with embedded images.
"""

import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.image import MIMEImage
from typing import Optional

from src.config import get_config
from src.utils.state import MessagesState
from src.utils.common import create_campaign_folder


class EnhancedSMTPProvider:
    """Enhanced SMTP provider with HTML email and image support."""
    
    def __init__(self):
        self.config = get_config()
    
    def send(self, subject: str, body_text: str, state: MessagesState) -> str:
        """
        Send enhanced HTML email with embedded images.
        
        Args:
            subject: Email subject line
            body_text: Plain text fallback
            state: Current workflow state with campaign data
            
        Returns:
            Status message
        """
        try:
            # Check DRY_RUN mode first - no credentials needed for outbox
            dry_run = os.getenv("DRY_RUN", "true").lower() == "true"
            
            if dry_run:
                return self._save_to_outbox(subject, body_text, state)
            
            # For real sending, get and validate email configuration
            smtp_host = os.getenv("EMAIL_SMTP_HOST", "smtp.gmail.com")
            smtp_port = int(os.getenv("EMAIL_SMTP_PORT", "587"))
            username = os.getenv("EMAIL_USERNAME", "")
            password = os.getenv("EMAIL_PASSWORD", "")
            from_email = os.getenv("EMAIL_FROM", username)
            to_email = os.getenv("EMAIL_TO", "")
            
            if not all([smtp_host, username, password, from_email, to_email]):
                return "❌ Missing required email configuration"
            
            return self._send_real_email(subject, body_text, state, smtp_host, smtp_port,
                                       username, password, from_email, to_email)
                
        except Exception as e:
            return f"❌ Enhanced email sending failed: {str(e)}"
    
    def _save_to_outbox(self, subject: str, body_text: str, state: MessagesState) -> str:
        """Save enhanced email content to outbox folder."""
        try:
            # Create campaign-specific folder
            from src.utils.common import create_campaign_folder
            campaign_folder = create_campaign_folder(state, "data/outbox")
            
            # Generate HTML content using template engine
            html_content = self._generate_html_content(state)
            
            # Save plain text version
            txt_path = os.path.join(campaign_folder, "email_post.txt")
            with open(txt_path, "w", encoding="utf-8") as f:
                f.write(f"Subject: {subject}\n\n")
                f.write(body_text)
            
            # Save HTML version
            html_path = os.path.join(campaign_folder, "email_post.html")
            with open(html_path, "w", encoding="utf-8") as f:
                f.write(html_content)
            
            # Handle image optimization and saving
            image_url = state.get("image_url", "")
            if image_url and os.path.exists(image_url):
                optimized_path = self._optimize_and_save_image(image_url, campaign_folder)
                if optimized_path:
                    return f"✅ Enhanced email saved to outbox: {html_path} (with optimized image: {optimized_path})"
            
            return f"✅ Enhanced email saved to outbox: {html_path}"
                
        except Exception as e:
            return f"❌ Failed to save enhanced email to outbox: {str(e)}"
    
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
            print(f"Template generation failed: {e}, using simple HTML")
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
        .cta {{ background: #007cba; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>{subject}</h1>
        </div>
        <div class="content">
            <p>{content}</p>
            <p><a href="#" class="cta">Learn More</a></p>
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
            print(f"Image optimization failed: {e}")
            return None
    
    def _send_real_email(self, subject: str, body_text: str, state: MessagesState,
                        smtp_host: str, smtp_port: int, username: str, password: str,
                        from_email: str, to_email: str) -> str:
        """Send actual enhanced email via SMTP."""
        try:
            # Create multipart message for HTML + images
            msg = MIMEMultipart("related")
            msg["Subject"] = subject
            msg["From"] = from_email
            msg["To"] = to_email
            
            # Create alternative container for text/HTML
            msg_alternative = MIMEMultipart("alternative")
            msg.attach(msg_alternative)
            
            # Add text part
            text_part = MIMEText(body_text, "plain")
            msg_alternative.attach(text_part)
            
            # Generate and add HTML part
            html_content = self._generate_html_content(state)
            html_part = MIMEText(html_content, "html")
            msg_alternative.attach(html_part)
            
            # Add image if available
            image_url = state.get("image_url", "")
            if image_url and os.path.exists(image_url):
                with open(image_url, "rb") as f:
                    img_data = f.read()
                
                image = MIMEImage(img_data)
                image.add_header("Content-ID", "<campaign_image>")
                image.add_header("Content-Disposition", "inline", filename="campaign_image.png")
                msg.attach(image)
            
            # Connect and send
            with smtplib.SMTP(smtp_host, smtp_port) as server:
                server.starttls()
                server.login(username, password)
                server.send_message(msg)
            
            return f"✅ Enhanced email sent successfully to {to_email}"
            
        except Exception as e:
            return f"❌ Enhanced SMTP sending failed: {str(e)}"
