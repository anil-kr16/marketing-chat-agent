"""
Configuration management for the Marketing Agent API.

This module handles environment variables, default settings,
and configuration validation for the API server.
"""

import os
from typing import List, Optional
from pydantic import BaseSettings, Field
from functools import lru_cache


class APIConfig(BaseSettings):
    """
    API Configuration settings loaded from environment variables.
    
    Uses Pydantic BaseSettings for automatic environment variable
    loading with type validation and default values.
    """
    
    # Core API Settings
    api_host: str = Field(default="0.0.0.0", env="API_HOST")
    api_port: int = Field(default=8000, env="API_PORT") 
    api_title: str = Field(default="Marketing Agent API", env="API_TITLE")
    api_version: str = Field(default="1.0.0", env="API_VERSION")
    debug: bool = Field(default=False, env="DEBUG")
    reload: bool = Field(default=False, env="RELOAD")
    
    # Security Settings
    api_key_header: str = Field(default="X-API-Key", env="API_KEY_HEADER")
    default_api_key: str = Field(default="demo-key-12345", env="DEFAULT_API_KEY")
    allowed_origins: List[str] = Field(default=["*"], env="ALLOWED_ORIGINS")
    rate_limit_per_minute: int = Field(default=60, env="RATE_LIMIT_PER_MINUTE")
    
    # Background Processing
    redis_url: str = Field(default="redis://localhost:6379/0", env="REDIS_URL")
    max_concurrent_campaigns: int = Field(default=5, env="MAX_CONCURRENT_CAMPAIGNS")
    campaign_timeout_seconds: int = Field(default=300, env="CAMPAIGN_TIMEOUT_SECONDS")
    task_result_expires: int = Field(default=3600, env="TASK_RESULT_EXPIRES")
    
    # File Storage
    file_storage_path: str = Field(default="./storage", env="FILE_STORAGE_PATH")
    file_url_prefix: str = Field(default="http://localhost:8000/api/v1/campaigns", env="FILE_URL_PREFIX")
    max_file_size_mb: int = Field(default=50, env="MAX_FILE_SIZE_MB")
    
    # Logging and Monitoring
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    enable_metrics: bool = Field(default=True, env="ENABLE_METRICS")
    enable_tracing: bool = Field(default=False, env="ENABLE_TRACING")
    
    # Marketing Agent Settings (inherit from main project)
    openai_api_key: str = Field(env="OPENAI_API_KEY")
    llm_model: str = Field(default="gpt-4o", env="LLM_MODEL")
    dry_run: bool = Field(default=True, env="DRY_RUN")
    
    # Channel Configuration
    enable_email: bool = Field(default=True, env="ENABLE_EMAIL")
    enable_facebook: bool = Field(default=True, env="ENABLE_FACEBOOK")
    enable_instagram: bool = Field(default=True, env="ENABLE_INSTAGRAM")
    enable_twitter: bool = Field(default=False, env="ENABLE_TWITTER")
    enable_linkedin: bool = Field(default=False, env="ENABLE_LINKEDIN")
    
    # Email Settings (if not using DRY_RUN)
    email_smtp_host: str = Field(default="smtp.gmail.com", env="EMAIL_SMTP_HOST")
    email_username: Optional[str] = Field(default=None, env="EMAIL_USERNAME")
    email_password: Optional[str] = Field(default=None, env="EMAIL_PASSWORD")
    email_from: Optional[str] = Field(default=None, env="EMAIL_FROM")
    email_to: Optional[str] = Field(default=None, env="EMAIL_TO")
    
    class Config:
        """Pydantic configuration."""
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        
        # Custom parsing for list fields
        @classmethod
        def parse_env_var(cls, field_name: str, raw_val: str):
            if field_name == 'allowed_origins':
                return [origin.strip() for origin in raw_val.split(',')]
            return cls.json_loads(raw_val)

    def get_enabled_channels(self) -> List[str]:
        """Get list of enabled delivery channels."""
        channels = []
        if self.enable_email:
            channels.append("email")
        if self.enable_facebook:
            channels.append("facebook")
        if self.enable_instagram:
            channels.append("instagram")
        if self.enable_twitter:
            channels.append("twitter")
        if self.enable_linkedin:
            channels.append("linkedin")
        return channels

    def validate_config(self) -> List[str]:
        """
        Validate the configuration and return any errors.
        
        Returns:
            List of error messages (empty if configuration is valid)
        """
        errors = []
        
        # Check required fields
        if not self.openai_api_key:
            errors.append("OPENAI_API_KEY is required")
        
        # Validate API key format
        if self.openai_api_key and not self.openai_api_key.startswith('sk-'):
            errors.append("OPENAI_API_KEY should start with 'sk-'")
        
        # Validate port range
        if not (1 <= self.api_port <= 65535):
            errors.append(f"API_PORT must be between 1 and 65535, got {self.api_port}")
        
        # Validate concurrent campaigns limit
        if self.max_concurrent_campaigns < 1:
            errors.append("MAX_CONCURRENT_CAMPAIGNS must be at least 1")
        
        # Validate timeout
        if self.campaign_timeout_seconds < 60:
            errors.append("CAMPAIGN_TIMEOUT_SECONDS should be at least 60 seconds")
        
        # Validate log level
        valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        if self.log_level.upper() not in valid_levels:
            errors.append(f"LOG_LEVEL must be one of {valid_levels}")
        
        # Check if any channels are enabled
        if not any([self.enable_email, self.enable_facebook, self.enable_instagram, 
                   self.enable_twitter, self.enable_linkedin]):
            errors.append("At least one delivery channel must be enabled")
        
        # Validate email settings if email is enabled and not in dry run
        if self.enable_email and not self.dry_run:
            if not self.email_username:
                errors.append("EMAIL_USERNAME is required when email is enabled and not in dry run")
            if not self.email_from:
                errors.append("EMAIL_FROM is required when email is enabled and not in dry run")
        
        return errors

    def get_file_storage_config(self) -> dict:
        """Get file storage configuration dictionary."""
        return {
            "storage_path": self.file_storage_path,
            "url_prefix": self.file_url_prefix,
            "max_size_mb": self.max_file_size_mb
        }

    def get_security_config(self) -> dict:
        """Get security configuration dictionary."""
        return {
            "api_key_header": self.api_key_header,
            "rate_limit": self.rate_limit_per_minute,
            "allowed_origins": self.allowed_origins
        }

    def is_production(self) -> bool:
        """Check if running in production mode."""
        return not self.debug and not self.reload

    def __str__(self) -> str:
        """String representation of configuration (hiding sensitive data)."""
        return f"APIConfig(host={self.api_host}, port={self.api_port}, debug={self.debug})"


@lru_cache()
def get_api_config() -> APIConfig:
    """
    Get the API configuration instance.
    
    Uses LRU cache to ensure we only create one configuration
    instance throughout the application lifecycle.
    """
    return APIConfig()


def setup_environment():
    """
    Set up environment variables for the marketing agent.
    
    This ensures the main marketing agent project can access
    the same configuration through its normal environment loading.
    """
    config = get_api_config()
    
    # Set marketing agent environment variables
    os.environ["OPENAI_API_KEY"] = config.openai_api_key
    os.environ["LLM_MODEL"] = config.llm_model
    os.environ["DRY_RUN"] = str(config.dry_run).lower()
    
    # Channel settings
    os.environ["ENABLE_EMAIL"] = str(config.enable_email).lower()
    os.environ["ENABLE_FACEBOOK"] = str(config.enable_facebook).lower()
    os.environ["ENABLE_INSTAGRAM"] = str(config.enable_instagram).lower()
    os.environ["ENABLE_TWITTER"] = str(config.enable_twitter).lower()
    os.environ["ENABLE_LINKEDIN"] = str(config.enable_linkedin).lower()
    
    # Email settings
    if config.email_username:
        os.environ["EMAIL_USERNAME"] = config.email_username
    if config.email_password:
        os.environ["EMAIL_PASSWORD"] = config.email_password
    if config.email_from:
        os.environ["EMAIL_FROM"] = config.email_from
    if config.email_to:
        os.environ["EMAIL_TO"] = config.email_to
    
    os.environ["EMAIL_SMTP_HOST"] = config.email_smtp_host


def validate_startup_config():
    """
    Validate configuration at startup and raise errors if invalid.
    
    This should be called during application startup to catch
    configuration errors early.
    """
    config = get_api_config()
    errors = config.validate_config()
    
    if errors:
        error_msg = "Configuration validation failed:\n" + "\n".join(f"  - {error}" for error in errors)
        raise ValueError(error_msg)
    
    # Set up environment for marketing agent
    setup_environment()
    
    return config
