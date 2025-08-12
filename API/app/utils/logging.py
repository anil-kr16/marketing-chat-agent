"""
Logging configuration for the Marketing Agent API.

This module sets up structured logging with appropriate formatting
for both development and production environments.
"""

import logging
import sys
from typing import Optional
from datetime import datetime

from app.utils.config import get_api_config


class ColoredFormatter(logging.Formatter):
    """
    Custom log formatter that adds colors for different log levels.
    
    Makes logs easier to read during development.
    """
    
    # ANSI color codes
    COLORS = {
        'DEBUG': '\033[36m',      # Cyan
        'INFO': '\033[32m',       # Green
        'WARNING': '\033[33m',    # Yellow
        'ERROR': '\033[31m',      # Red
        'CRITICAL': '\033[35m',   # Magenta
    }
    RESET = '\033[0m'
    
    def format(self, record):
        """Format log record with colors if in development."""
        # Add color if in development
        if hasattr(self, 'use_colors') and self.use_colors:
            color = self.COLORS.get(record.levelname, '')
            record.levelname = f"{color}{record.levelname}{self.RESET}"
        
        return super().format(record)


def setup_logging() -> logging.Logger:
    """
    Set up logging configuration for the API.
    
    Returns:
        Configured logger instance
    """
    config = get_api_config()
    
    # Create logger
    logger = logging.getLogger("marketing_api")
    logger.setLevel(getattr(logging, config.log_level.upper()))
    
    # Avoid duplicate handlers
    if logger.handlers:
        return logger
    
    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, config.log_level.upper()))
    
    # Create formatter
    if config.debug:
        # Development format with colors
        formatter = ColoredFormatter(
            fmt='%(asctime)s | %(levelname)-8s | %(name)s:%(lineno)d | %(message)s',
            datefmt='%H:%M:%S'
        )
        formatter.use_colors = True
    else:
        # Production format (JSON-like for log aggregation)
        formatter = logging.Formatter(
            fmt='{"timestamp": "%(asctime)s", "level": "%(levelname)s", "logger": "%(name)s", "line": %(lineno)d, "message": "%(message)s"}',
            datefmt='%Y-%m-%dT%H:%M:%S'
        )
    
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # Suppress noisy third-party loggers in production
    if not config.debug:
        logging.getLogger("uvicorn").setLevel(logging.WARNING)
        logging.getLogger("fastapi").setLevel(logging.WARNING)
        logging.getLogger("httpx").setLevel(logging.WARNING)
    
    logger.info(f"📝 Logging configured (level: {config.log_level})")
    return logger


def log_request(method: str, path: str, status_code: int, duration_ms: float, logger: Optional[logging.Logger] = None):
    """
    Log HTTP request information.
    
    Args:
        method: HTTP method (GET, POST, etc.)
        path: Request path
        status_code: HTTP status code
        duration_ms: Request duration in milliseconds
        logger: Logger instance (will create one if not provided)
    """
    if logger is None:
        logger = setup_logging()
    
    # Choose log level based on status code
    if status_code >= 500:
        level = logging.ERROR
        emoji = "❌"
    elif status_code >= 400:
        level = logging.WARNING
        emoji = "⚠️"
    elif status_code >= 300:
        level = logging.INFO
        emoji = "↗️"
    else:
        level = logging.INFO
        emoji = "✅"
    
    message = f"{emoji} {method} {path} → {status_code} ({duration_ms:.1f}ms)"
    logger.log(level, message)


def log_campaign_event(campaign_id: str, event: str, details: Optional[str] = None, logger: Optional[logging.Logger] = None):
    """
    Log campaign-related events.
    
    Args:
        campaign_id: Campaign identifier
        event: Event name (created, started, completed, failed, etc.)
        details: Optional additional details
        logger: Logger instance
    """
    if logger is None:
        logger = setup_logging()
    
    # Event emojis for better readability
    event_emojis = {
        'created': '📝',
        'started': '🚀', 
        'processing': '⚡',
        'completed': '✅',
        'failed': '❌',
        'cancelled': '🛑',
        'webhook_called': '📞',
        'files_stored': '💾'
    }
    
    emoji = event_emojis.get(event, '📋')
    message = f"{emoji} Campaign {campaign_id}: {event}"
    
    if details:
        message += f" - {details}"
    
    # Choose log level based on event type
    if event in ['failed', 'error']:
        logger.error(message)
    elif event in ['completed', 'created']:
        logger.info(message)
    else:
        logger.debug(message)


def log_performance_metrics(metrics: dict, logger: Optional[logging.Logger] = None):
    """
    Log performance metrics.
    
    Args:
        metrics: Dictionary of performance metrics
        logger: Logger instance
    """
    if logger is None:
        logger = setup_logging()
    
    # Format metrics for logging
    formatted_metrics = []
    for key, value in metrics.items():
        if isinstance(value, float):
            formatted_metrics.append(f"{key}={value:.2f}")
        else:
            formatted_metrics.append(f"{key}={value}")
    
    message = f"📊 Performance: {', '.join(formatted_metrics)}"
    logger.info(message)


def setup_request_logging():
    """
    Set up request logging middleware configuration.
    
    Returns configuration for FastAPI middleware.
    """
    return {
        "format": '%(asctime)s | %(levelname)s | %(client_ip)s | %(method)s %(path)s | %(status_code)s | %(duration)sms',
        "level": "INFO"
    }
