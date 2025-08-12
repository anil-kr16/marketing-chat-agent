"""
Consultation Configuration Settings

This module provides configuration settings specifically for the stateful
marketing consultation flow, extending the base configuration with
consultation-specific parameters.

Key Settings:
- Session management timeouts and cleanup intervals
- Question limits and flow control parameters
- LLM evaluation settings and fallback thresholds
- Analytics and monitoring configuration

Architecture Benefits:
- Centralized configuration for consultation behavior
- Easy tuning of consultation parameters without code changes
- Environment-specific overrides for development vs production
- Clear separation of consultation settings from campaign settings

Integration:
- Used by consultation manager for session settings
- Referenced by consultant nodes for flow control
- Applied by question prioritizer for limits and thresholds
- Utilized by completeness evaluator for LLM settings
"""

from typing import Dict, Any, Optional
from dataclasses import dataclass
import os
from enum import Enum

from src.config.settings import get_config as get_base_config


class ConsultationMode(str, Enum):
    """
    Different modes for consultation behavior.
    
    These modes control how aggressive or conservative the
    consultation flow is in gathering information.
    """
    THOROUGH = "thorough"    # Ask many questions, high quality threshold
    BALANCED = "balanced"    # Standard question count, reasonable threshold
    QUICK = "quick"          # Minimal questions, lower quality threshold
    ADAPTIVE = "adaptive"    # Adjust based on user response patterns


@dataclass
class ConsultationConfig:
    """
    Complete configuration for stateful marketing consultation.
    
    This centralizes all configuration parameters that control
    the behavior of the consultation flow.
    """
    
    # === SESSION MANAGEMENT ===
    session_timeout_minutes: int = 30
    """How long consultation sessions remain active without interaction."""
    
    cleanup_interval_minutes: int = 5
    """How often to clean up expired sessions."""
    
    max_concurrent_sessions: int = 100
    """Maximum number of concurrent consultation sessions."""
    
    # === QUESTIONING FLOW ===
    consultation_mode: ConsultationMode = ConsultationMode.BALANCED
    """Overall consultation strategy and aggressiveness."""
    
    max_questions_per_session: int = 8
    """Maximum questions to ask before forcing completion."""
    
    min_questions_before_evaluation: int = 2
    """Minimum questions before allowing completeness evaluation."""
    
    question_timeout_seconds: int = 300
    """How long to wait for user response to a question."""
    
    # === COMPLETENESS EVALUATION ===
    enable_llm_evaluation: bool = True
    """Whether to use LLM for intelligent completeness evaluation."""
    
    llm_evaluation_model: str = "gpt-4o"
    """Model to use for completeness evaluation."""
    
    llm_evaluation_temperature: float = 0.1
    """Temperature for LLM evaluation (lower = more consistent)."""
    
    completeness_threshold: float = 0.7
    """Minimum completeness score to consider consultation ready."""
    
    quality_threshold: float = 0.6
    """Minimum quality score for individual responses."""
    
    # === FALLBACK BEHAVIOR ===
    enable_fallback_on_llm_failure: bool = True
    """Whether to use heuristic fallback when LLM evaluation fails."""
    
    max_llm_retries: int = 2
    """Number of times to retry LLM evaluation on failure."""
    
    fallback_to_campaign_after_questions: int = 6
    """Force campaign creation after this many questions regardless."""
    
    # === USER EXPERIENCE ===
    show_progress_indicators: bool = True
    """Whether to show consultation progress to users."""
    
    show_completion_percentage: bool = True
    """Whether to show percentage completion during consultation."""
    
    enable_conversation_summaries: bool = True
    """Whether to generate and show conversation summaries."""
    
    # === ANALYTICS AND MONITORING ===
    enable_consultation_analytics: bool = True
    """Whether to collect analytics on consultation performance."""
    
    track_response_quality: bool = True
    """Whether to track and analyze response quality metrics."""
    
    track_completion_rates: bool = True
    """Whether to track consultation completion vs abandonment rates."""
    
    # === DEVELOPMENT AND DEBUGGING ===
    enable_debug_logging: bool = False
    """Whether to enable detailed debug logging."""
    
    save_consultation_transcripts: bool = False
    """Whether to save full consultation transcripts for analysis."""
    
    enable_consultation_replay: bool = False
    """Whether to enable consultation replay for debugging."""


def get_consultation_config() -> ConsultationConfig:
    """
    Get consultation configuration with environment overrides.
    
    This reads the base configuration and applies any environment-specific
    overrides for consultation behavior.
    
    Returns:
        Configured ConsultationConfig instance
        
    Environment Variables:
        CONSULTATION_MODE: thorough|balanced|quick|adaptive
        CONSULTATION_TIMEOUT_MINUTES: Session timeout in minutes
        MAX_QUESTIONS_PER_SESSION: Maximum questions per consultation
        ENABLE_LLM_EVALUATION: true|false for LLM evaluation
        COMPLETENESS_THRESHOLD: Float 0-1 for completion threshold
        DEBUG_CONSULTATION: true|false for debug mode
    """
    # Start with default configuration
    config = ConsultationConfig()
    
    # Apply environment overrides
    consultation_mode = os.getenv("CONSULTATION_MODE", "balanced").lower()
    if consultation_mode in [mode.value for mode in ConsultationMode]:
        config.consultation_mode = ConsultationMode(consultation_mode)
    
    # Session management overrides
    if timeout := os.getenv("CONSULTATION_TIMEOUT_MINUTES"):
        try:
            config.session_timeout_minutes = int(timeout)
        except ValueError:
            pass
    
    if cleanup := os.getenv("CONSULTATION_CLEANUP_MINUTES"):
        try:
            config.cleanup_interval_minutes = int(cleanup)
        except ValueError:
            pass
    
    # Question flow overrides
    if max_questions := os.getenv("MAX_QUESTIONS_PER_SESSION"):
        try:
            config.max_questions_per_session = int(max_questions)
        except ValueError:
            pass
    
    if min_questions := os.getenv("MIN_QUESTIONS_BEFORE_EVALUATION"):
        try:
            config.min_questions_before_evaluation = int(min_questions)
        except ValueError:
            pass
    
    # LLM evaluation overrides
    if llm_eval := os.getenv("ENABLE_LLM_EVALUATION"):
        config.enable_llm_evaluation = llm_eval.lower() in ["true", "1", "yes", "on"]
    
    if model := os.getenv("CONSULTATION_LLM_MODEL"):
        config.llm_evaluation_model = model
    
    if temp := os.getenv("CONSULTATION_LLM_TEMPERATURE"):
        try:
            config.llm_evaluation_temperature = float(temp)
        except ValueError:
            pass
    
    # Threshold overrides
    if completeness_threshold := os.getenv("COMPLETENESS_THRESHOLD"):
        try:
            threshold = float(completeness_threshold)
            if 0.0 <= threshold <= 1.0:
                config.completeness_threshold = threshold
        except ValueError:
            pass
    
    if quality_threshold := os.getenv("QUALITY_THRESHOLD"):
        try:
            threshold = float(quality_threshold)
            if 0.0 <= threshold <= 1.0:
                config.quality_threshold = threshold
        except ValueError:
            pass
    
    # Development and debugging overrides
    if debug := os.getenv("DEBUG_CONSULTATION"):
        config.enable_debug_logging = debug.lower() in ["true", "1", "yes", "on"]
    
    if analytics := os.getenv("ENABLE_CONSULTATION_ANALYTICS"):
        config.enable_consultation_analytics = analytics.lower() in ["true", "1", "yes", "on"]
    
    # Apply mode-specific presets
    config = _apply_mode_presets(config)
    
    return config


def _apply_mode_presets(config: ConsultationConfig) -> ConsultationConfig:
    """
    Apply mode-specific preset configurations.
    
    This adjusts various parameters based on the selected consultation mode
    to provide coherent behavior profiles.
    
    Args:
        config: Base configuration to modify
        
    Returns:
        Configuration with mode-specific adjustments applied
    """
    if config.consultation_mode == ConsultationMode.THOROUGH:
        # Thorough mode: Ask more questions, higher quality thresholds
        config.max_questions_per_session = 10
        config.min_questions_before_evaluation = 3
        config.completeness_threshold = 0.8
        config.quality_threshold = 0.7
        config.fallback_to_campaign_after_questions = 8
        
    elif config.consultation_mode == ConsultationMode.QUICK:
        # Quick mode: Fewer questions, lower quality thresholds
        config.max_questions_per_session = 5
        config.min_questions_before_evaluation = 1
        config.completeness_threshold = 0.6
        config.quality_threshold = 0.5
        config.fallback_to_campaign_after_questions = 4
        
    elif config.consultation_mode == ConsultationMode.ADAPTIVE:
        # Adaptive mode: Adjust based on user response patterns
        config.max_questions_per_session = 8  # Standard max
        config.min_questions_before_evaluation = 2
        config.completeness_threshold = 0.7
        config.quality_threshold = 0.6
        # Additional adaptive logic would be implemented in the nodes
        
    # Balanced mode uses default values
    
    return config


def get_mode_description(mode: ConsultationMode) -> str:
    """
    Get a human-readable description of a consultation mode.
    
    Args:
        mode: The consultation mode to describe
        
    Returns:
        Description of the mode's behavior
    """
    descriptions = {
        ConsultationMode.THOROUGH: (
            "Thorough consultation with comprehensive information gathering. "
            "Asks more questions and has higher quality thresholds for better campaign results."
        ),
        ConsultationMode.BALANCED: (
            "Balanced consultation that gathers sufficient information efficiently. "
            "Good balance between thoroughness and user experience."
        ),
        ConsultationMode.QUICK: (
            "Quick consultation focused on essential information only. "
            "Faster completion with lower quality thresholds."
        ),
        ConsultationMode.ADAPTIVE: (
            "Adaptive consultation that adjusts to user response patterns. "
            "Varies questioning strategy based on user engagement and detail level."
        )
    }
    return descriptions.get(mode, "Unknown consultation mode")


def validate_consultation_config(config: ConsultationConfig) -> Dict[str, Any]:
    """
    Validate consultation configuration for consistency and reasonableness.
    
    Args:
        config: Configuration to validate
        
    Returns:
        Dict with validation results and any issues found
    """
    validation_result = {
        "is_valid": True,
        "warnings": [],
        "errors": [],
        "recommendations": []
    }
    
    # Validate session timeouts
    if config.session_timeout_minutes < 5:
        validation_result["warnings"].append(
            "Session timeout < 5 minutes may interrupt consultations"
        )
    elif config.session_timeout_minutes > 120:
        validation_result["warnings"].append(
            "Session timeout > 2 hours may consume excessive memory"
        )
    
    # Validate question limits
    if config.max_questions_per_session < 3:
        validation_result["errors"].append(
            "Max questions < 3 insufficient for quality consultation"
        )
        validation_result["is_valid"] = False
    elif config.max_questions_per_session > 15:
        validation_result["warnings"].append(
            "Max questions > 15 may frustrate users"
        )
    
    if config.min_questions_before_evaluation >= config.max_questions_per_session:
        validation_result["errors"].append(
            "Min questions before evaluation must be < max questions"
        )
        validation_result["is_valid"] = False
    
    # Validate thresholds
    if not (0.0 <= config.completeness_threshold <= 1.0):
        validation_result["errors"].append(
            "Completeness threshold must be between 0.0 and 1.0"
        )
        validation_result["is_valid"] = False
    
    if not (0.0 <= config.quality_threshold <= 1.0):
        validation_result["errors"].append(
            "Quality threshold must be between 0.0 and 1.0"
        )
        validation_result["is_valid"] = False
    
    # Validate LLM settings
    if config.enable_llm_evaluation and not config.llm_evaluation_model:
        validation_result["errors"].append(
            "LLM model must be specified when LLM evaluation is enabled"
        )
        validation_result["is_valid"] = False
    
    # Provide recommendations
    if config.completeness_threshold > 0.9:
        validation_result["recommendations"].append(
            "Consider lowering completeness threshold for better user experience"
        )
    
    if config.enable_llm_evaluation and config.max_llm_retries == 0:
        validation_result["recommendations"].append(
            "Consider allowing at least 1 LLM retry for robustness"
        )
    
    return validation_result


# === GLOBAL CONFIGURATION INSTANCE ===

# Cache the configuration to avoid repeated environment variable reads
_cached_config: Optional[ConsultationConfig] = None


def get_global_consultation_config() -> ConsultationConfig:
    """
    Get the global consultation configuration instance.
    
    This provides a cached configuration that's shared across
    the application for consistency.
    
    Returns:
        Global ConsultationConfig instance
    """
    global _cached_config
    
    if _cached_config is None:
        _cached_config = get_consultation_config()
        
        # Validate configuration on first load
        validation = validate_consultation_config(_cached_config)
        if not validation["is_valid"]:
            raise ValueError(f"Invalid consultation configuration: {validation['errors']}")
    
    return _cached_config


def reset_consultation_config() -> None:
    """
    Reset the cached consultation configuration.
    
    This forces a fresh configuration load on the next access,
    useful for testing and configuration updates.
    """
    global _cached_config
    _cached_config = None
