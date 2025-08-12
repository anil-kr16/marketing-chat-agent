"""
Email formatting and template rendering utilities.

This module provides functionality to render HTML email templates
with campaign data while maintaining backwards compatibility.
"""

from __future__ import annotations

import os
from typing import Dict, Any, Optional, List
from dataclasses import dataclass


@dataclass
class EmailContent:
    """Structured email content."""
    
    subject: str
    html_body: str
    plain_text_body: str
    has_image: bool = False
    image_attachment_name: str = "campaign_image"


class EmailTemplateEngine:
    """Renders email templates with campaign data."""
    
    def __init__(self, template_dir: str = "src/templates/email"):
        """
        Initialize template engine.
        
        Args:
            template_dir: Directory containing email templates
        """
        self.template_dir = template_dir
        
    def render_marketing_email(self, 
                             campaign_data: Dict[str, Any],
                             image_attachment_name: str = "campaign_image") -> EmailContent:
        """
        Render a marketing campaign email.
        
        Args:
            campaign_data: Campaign data for template rendering
            image_attachment_name: Name of image attachment for HTML reference
            
        Returns:
            EmailContent with HTML and plain text versions
        """
        try:
            # Try to use Jinja2 for template rendering
            html_body = self._render_html_template(campaign_data, image_attachment_name)
            plain_text_body = self._render_plain_text_fallback(campaign_data)
            
            subject = campaign_data.get("subject", campaign_data.get("campaign_title", "Marketing Campaign"))
            has_image = bool(campaign_data.get("hero_image"))
            
            return EmailContent(
                subject=subject,
                html_body=html_body,
                plain_text_body=plain_text_body,
                has_image=has_image,
                image_attachment_name=image_attachment_name
            )
            
        except Exception as e:
            print(f"⚠️ Template rendering failed: {e}")
            # Fallback to plain text only
            return self._fallback_to_plain_text(campaign_data)
    
    def _render_html_template(self, 
                            campaign_data: Dict[str, Any], 
                            image_attachment_name: str) -> str:
        """
        Render HTML template with Jinja2.
        
        Args:
            campaign_data: Data for template
            image_attachment_name: Image attachment reference
            
        Returns:
            Rendered HTML content
        """
        try:
            from jinja2 import Environment, FileSystemLoader
            
            # Set up Jinja2 environment
            env = Environment(loader=FileSystemLoader(self.template_dir))
            template = env.get_template("marketing_campaign.html")
            
            # Prepare template data
            template_data = self._prepare_template_data(campaign_data, image_attachment_name)
            
            # Render template
            return template.render(**template_data)
            
        except ImportError:
            print("⚠️ Jinja2 not available. Using simple template substitution.")
            return self._simple_html_template(campaign_data, image_attachment_name)
        except Exception as e:
            print(f"⚠️ Jinja2 template rendering failed: {e}")
            return self._simple_html_template(campaign_data, image_attachment_name)
    
    def _simple_html_template(self, 
                            campaign_data: Dict[str, Any], 
                            image_attachment_name: str) -> str:
        """
        Simple HTML template without Jinja2 dependency.
        
        Args:
            campaign_data: Campaign data
            image_attachment_name: Image attachment reference
            
        Returns:
            Simple HTML email content
        """
        campaign_title = campaign_data.get("campaign_title", "Marketing Campaign")
        audience_greeting = campaign_data.get("audience_greeting", "Hello!")
        marketing_copy = campaign_data.get("marketing_copy", "")
        cta_buttons = campaign_data.get("cta_buttons", [])
        hashtags = campaign_data.get("hashtags", [])
        hero_image = campaign_data.get("hero_image")
        
        # Build CTA buttons HTML
        cta_html = ""
        if cta_buttons:
            for i, cta in enumerate(cta_buttons):
                button_class = "cta-button primary" if i == 0 else "cta-button"
                cta_html += f'<a href="#" style="display: inline-block; padding: 15px 30px; margin: 10px 5px; background-color: {"#007bff" if i == 0 else "#28a745"}; color: white; text-decoration: none; border-radius: 5px; font-weight: bold;">{cta}</a>'
        
        # Build hashtags HTML
        hashtag_html = ""
        if hashtags:
            hashtag_html = '<div style="background-color: #f8f9fa; padding: 20px; border-radius: 5px; margin: 20px 0; text-align: center;">'
            for hashtag in hashtags:
                hashtag_html += f'<span style="display: inline-block; background-color: #e9ecef; color: #495057; padding: 5px 10px; margin: 3px; border-radius: 15px; font-size: 14px;">{hashtag}</span>'
            hashtag_html += '</div>'
        
        # Build image HTML
        image_html = ""
        if hero_image:
            image_html = f'<div style="text-align: center; padding: 0;"><img src="cid:{image_attachment_name}" alt="{campaign_title}" style="width: 100%; max-width: 600px; height: auto; display: block; border: none;" /></div>'
        
        # Simple HTML template
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{campaign_title}</title>
</head>
<body style="margin: 0; padding: 0; background-color: #f4f4f4; font-family: Arial, sans-serif;">
    <div style="max-width: 600px; margin: 0 auto; background-color: #ffffff; border-radius: 8px; overflow: hidden;">
        <!-- Header -->
        <div style="background-color: #007bff; color: white; padding: 20px; text-align: center;">
            <h1 style="margin: 0; font-size: 24px;">🚀 {campaign_title}</h1>
        </div>
        
        <!-- Hero Image -->
        {image_html}
        
        <!-- Content -->
        <div style="padding: 30px 25px;">
            <div style="font-size: 18px; color: #333333; margin-bottom: 20px; font-weight: bold;">
                {audience_greeting}
            </div>
            
            <div style="font-size: 16px; line-height: 1.6; color: #555555; margin-bottom: 30px;">
                {marketing_copy}
            </div>
            
            <!-- CTAs -->
            <div style="text-align: center; margin: 30px 0;">
                {cta_html}
            </div>
            
            <!-- Hashtags -->
            {hashtag_html}
        </div>
        
        <!-- Footer -->
        <div style="background-color: #6c757d; color: white; padding: 20px; text-align: center; font-size: 12px;">
            <p>Marketing Campaign | <a href="#" style="color: white;">Unsubscribe</a></p>
        </div>
    </div>
</body>
</html>
"""
        return html.strip()
    
    def _prepare_template_data(self, 
                             campaign_data: Dict[str, Any], 
                             image_attachment_name: str) -> Dict[str, Any]:
        """
        Prepare data for template rendering.
        
        Args:
            campaign_data: Raw campaign data
            image_attachment_name: Image attachment reference
            
        Returns:
            Template-ready data dictionary
        """
        # Use cid: reference for email image attachment
        hero_image = None
        if campaign_data.get("hero_image"):
            hero_image = f"cid:{image_attachment_name}"
        
        return {
            "campaign_title": campaign_data.get("campaign_title", "Marketing Campaign"),
            "audience_greeting": campaign_data.get("audience_greeting", "Hello!"),
            "marketing_copy": campaign_data.get("marketing_copy", ""),
            "cta_buttons": campaign_data.get("cta_buttons", []),
            "hashtags": campaign_data.get("hashtags", []),
            "hero_image": hero_image,
        }
    
    def _render_plain_text_fallback(self, campaign_data: Dict[str, Any]) -> str:
        """
        Render plain text version for email clients that don't support HTML.
        
        Args:
            campaign_data: Campaign data
            
        Returns:
            Plain text email content
        """
        campaign_title = campaign_data.get("campaign_title", "Marketing Campaign")
        audience_greeting = campaign_data.get("audience_greeting", "Hello!")
        marketing_copy = campaign_data.get("marketing_copy", "")
        cta_buttons = campaign_data.get("cta_buttons", [])
        hashtags = campaign_data.get("hashtags", [])
        
        lines = [
            f"🚀 {campaign_title}",
            "=" * 50,
            "",
            audience_greeting,
            "",
            marketing_copy,
            "",
        ]
        
        if cta_buttons:
            lines.append("Call to Action:")
            for cta in cta_buttons:
                lines.append(f"• {cta}")
            lines.append("")
        
        if hashtags:
            lines.append("Hashtags:")
            lines.append(" ".join(hashtags))
            lines.append("")
        
        lines.extend([
            "---",
            "Marketing Campaign | Unsubscribe | Contact Us"
        ])
        
        return "\n".join(lines)
    
    def _fallback_to_plain_text(self, campaign_data: Dict[str, Any]) -> EmailContent:
        """
        Fallback to plain text email if template rendering fails.
        
        Args:
            campaign_data: Campaign data
            
        Returns:
            EmailContent with plain text only
        """
        plain_text = self._render_plain_text_fallback(campaign_data)
        subject = campaign_data.get("subject", campaign_data.get("campaign_title", "Marketing Campaign"))
        
        return EmailContent(
            subject=subject,
            html_body="",  # No HTML on fallback
            plain_text_body=plain_text,
            has_image=False
        )


def render_marketing_email(campaign_data: Dict[str, Any], 
                         image_attachment_name: str = "campaign_image") -> EmailContent:
    """
    Convenience function to render a marketing email.
    
    Args:
        campaign_data: Campaign data for rendering
        image_attachment_name: Name for image attachment reference
        
    Returns:
        EmailContent with rendered email
    """
    engine = EmailTemplateEngine()
    return engine.render_marketing_email(campaign_data, image_attachment_name)
