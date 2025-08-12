from __future__ import annotations
import os
from typing import Any, Dict

from langsmith import traceable

from src.utils.state import MessagesState
from src.config import get_config
from src.providers.email.smtp_provider import SMTPProvider


@traceable(name="Send Email Node")
def send_email_node(state: MessagesState) -> MessagesState:
    cfg = get_config()
    if not cfg.enable_email:
        return state

    email_payload: Dict[str, Any] = state.get("final_response", {}).get("email", {})
    if not email_payload:
        return state

    subject = email_payload.get("subject") or "Campaign"
    body_text = email_payload.get("bodyText") or ""

    # Check if OAuth Gmail is preferred
    use_oauth = os.getenv("USE_OAUTH_GMAIL", "false").lower() == "true"
    
    if use_oauth:
        # Use OAuth Gmail provider (most secure)
        try:
            from src.providers.email.oauth_gmail_provider import OAuthGmailProvider
            print("🔐 Using OAuth Gmail provider (secure)")
            status = OAuthGmailProvider().send(subject=subject, body_text=body_text, state=state)
        except ImportError as e:
            print(f"⚠️ OAuth Gmail provider not available: {e}")
            print("💡 Run: pip install google-auth google-auth-oauthlib google-auth-httplib2 google-api-python-client")
            print("🔄 Falling back to SMTP provider...")
            use_oauth = False
        except Exception as e:
            print(f"⚠️ OAuth Gmail failed: {e}. Falling back to SMTP provider.")
            use_oauth = False
    
    if not use_oauth:
        # Use SMTP providers (app password or enhanced HTML)
        if cfg.enable_html_email or cfg.enable_email_templates:
            # Use enhanced SMTP provider for HTML emails
            try:
                from src.providers.email.enhanced_smtp_provider import EnhancedSMTPProvider
                print("🎨 Using Enhanced SMTP provider (HTML emails)")
                status = EnhancedSMTPProvider().send(subject=subject, body_text=body_text, state=state)
            except ImportError as e:
                print(f"⚠️ Enhanced SMTP provider not available: {e}. Using standard provider.")
                status = SMTPProvider().send(subject=subject, body_text=body_text, state=state)
            except Exception as e:
                print(f"⚠️ Enhanced email sending failed: {e}. Falling back to standard provider.")
                status = SMTPProvider().send(subject=subject, body_text=body_text, state=state)
        else:
            # Use original SMTP provider (plain text)
            print("📧 Using Standard SMTP provider (plain text)")
            status = SMTPProvider().send(subject=subject, body_text=body_text, state=state)

    delivery = state.setdefault("delivery", {"requested": [], "results": {}})
    delivery.setdefault("results", {})["email"] = status
    return state

