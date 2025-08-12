"""
Centralized configuration loader for environment variables.

Usage:
  from src.config import get_config
  cfg = get_config()
  print(cfg.openai_api_key)

This module loads .env once and exposes a simple, typed object.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Optional

from dotenv import load_dotenv


@dataclass(frozen=True)
class Config:
    """Immutable configuration values sourced from environment variables."""

    # API keys
    openai_api_key: Optional[str]
    langsmith_api_key: Optional[str]

    # Models and generation defaults
    llm_model: str
    image_model: str
    temperature: float

    # Paths
    image_output_dir: str  # e.g., static/images
    outbox_dir: str  # where to store dry-run sends

    # Channel toggles
    enable_email: bool
    enable_instagram: bool
    enable_facebook: bool
    enable_twitter: bool
    enable_linkedin: bool

    # Delivery behavior
    dry_run: bool  # if true, do not hit external services; write files locally
    
    # Chat behavior
    enable_general_chat: bool  # if true, enable ChatGPT-like general conversation
    
    # Email enhancement flags (default false = no change to existing behavior)
    enable_html_email: bool    # if true, send HTML emails instead of plain text
    enable_image_optimization: bool  # if true, optimize images for email attachments
    enable_email_templates: bool     # if true, use rich email templates

    # Email settings
    email_smtp_host: str | None
    email_smtp_port: int | None
    email_use_tls: bool
    email_username: str | None
    email_password: str | None
    email_from: str | None
    email_to: str | None  # comma-separated list


_CONFIG: Optional[Config] = None


def _load_config() -> Config:
    load_dotenv()

    openai_api_key = os.getenv("OPENAI_API_KEY")
    langsmith_api_key = os.getenv("LANGSMITH_API_KEY")

    llm_model = os.getenv("LLM_MODEL", "gpt-4o")
    image_model = os.getenv("IMAGE_MODEL", "gpt-image-1")
    temperature_str = os.getenv("LLM_TEMPERATURE", "0.7")
    try:
        temperature = float(temperature_str)
    except ValueError:
        temperature = 0.7

    # Default to static/images in project root
    image_output_dir = os.getenv("IMAGE_OUTPUT_DIR", "static/images")
    outbox_dir = os.getenv("OUTBOX_DIR", "data/outbox")

    def as_bool(val: str | None, default: bool = False) -> bool:
        if val is None:
            return default
        return val.strip().lower() in {"1", "true", "yes", "on"}

    # Channel toggles
    enable_email = as_bool(os.getenv("ENABLE_EMAIL"), True)
    enable_instagram = as_bool(os.getenv("ENABLE_INSTAGRAM"), False)
    enable_facebook = as_bool(os.getenv("ENABLE_FACEBOOK"), False)
    enable_twitter = as_bool(os.getenv("ENABLE_TWITTER"), False)
    enable_linkedin = as_bool(os.getenv("ENABLE_LINKEDIN"), False)

    # Delivery behavior
    dry_run = as_bool(os.getenv("DRY_RUN"), True)
    
    # Chat behavior  
    enable_general_chat = as_bool(os.getenv("ENABLE_GENERAL_CHAT"), True)
    
    # Email enhancement flags (default false for backwards compatibility)
    enable_html_email = as_bool(os.getenv("ENABLE_HTML_EMAIL"), False)
    enable_image_optimization = as_bool(os.getenv("ENABLE_IMAGE_OPTIMIZATION"), False)  
    enable_email_templates = as_bool(os.getenv("ENABLE_EMAIL_TEMPLATES"), False)

    # Email settings
    email_smtp_host = os.getenv("EMAIL_SMTP_HOST")
    email_smtp_port_str = os.getenv("EMAIL_SMTP_PORT")
    try:
        email_smtp_port = int(email_smtp_port_str) if email_smtp_port_str else None
    except ValueError:
        email_smtp_port = None
    email_use_tls = as_bool(os.getenv("EMAIL_USE_TLS"), True)
    email_username = os.getenv("EMAIL_USERNAME")
    email_password = os.getenv("EMAIL_PASSWORD")
    email_from = os.getenv("EMAIL_FROM")
    email_to = os.getenv("EMAIL_TO")  # comma-separated

    return Config(
        openai_api_key=openai_api_key,
        langsmith_api_key=langsmith_api_key,
        llm_model=llm_model,
        image_model=image_model,
        temperature=temperature,
        image_output_dir=image_output_dir,
        outbox_dir=outbox_dir,
        enable_email=enable_email,
        enable_instagram=enable_instagram,
        enable_facebook=enable_facebook,
        enable_twitter=enable_twitter,
        enable_linkedin=enable_linkedin,
        dry_run=dry_run,
        enable_general_chat=enable_general_chat,
        enable_html_email=enable_html_email,
        enable_image_optimization=enable_image_optimization,
        enable_email_templates=enable_email_templates,
        email_smtp_host=email_smtp_host,
        email_smtp_port=email_smtp_port,
        email_use_tls=email_use_tls,
        email_username=email_username,
        email_password=email_password,
        email_from=email_from,
        email_to=email_to,
    )


def get_config() -> Config:
    """Return a singleton Config instance loaded from environment variables."""
    global _CONFIG
    if _CONFIG is None:
        _CONFIG = _load_config()
    return _CONFIG

