"""
Generic API response models.

These models define standard response formats used across all endpoints.
"""

from typing import Optional, Any, Dict
from pydantic import BaseModel, Field


class APIResponse(BaseModel):
    """
    Standard API response wrapper.
    
    All API endpoints return responses in this consistent format.
    """
    success: bool = Field(
        description="Whether the request was successful",
        example=True
    )
    
    message: str = Field(
        description="Human-readable message about the result",
        example="Operation completed successfully"
    )
    
    data: Optional[Any] = Field(
        description="The actual response data (varies by endpoint)",
        default=None
    )
    
    error_code: Optional[str] = Field(
        description="Error code if the request failed",
        default=None,
        example="VALIDATION_ERROR"
    )
    
    request_id: Optional[str] = Field(
        description="Unique identifier for this request (for debugging)",
        default=None,
        example="req_abc123def456"
    )


class ErrorResponse(BaseModel):
    """
    Standard error response format.
    
    Used when API requests fail for any reason.
    """
    success: bool = Field(
        description="Always false for error responses",
        default=False
    )
    
    error: str = Field(
        description="Error type or category",
        example="ValidationError"
    )
    
    message: str = Field(
        description="Human-readable error message",
        example="The provided input is invalid"
    )
    
    details: Optional[Dict[str, Any]] = Field(
        description="Additional error details",
        default=None,
        example={"field": "user_input", "issue": "too_short"}
    )
    
    error_code: Optional[str] = Field(
        description="Specific error code for programmatic handling",
        default=None,
        example="INPUT_TOO_SHORT"
    )
    
    request_id: Optional[str] = Field(
        description="Request identifier for debugging",
        default=None,
        example="req_abc123def456"
    )


class HealthResponse(BaseModel):
    """
    Health check response format.
    
    Used by the /health endpoint to report service status.
    """
    status: str = Field(
        description="Overall service health status",
        example="healthy"
    )
    
    version: str = Field(
        description="API version",
        example="1.0.0"
    )
    
    timestamp: str = Field(
        description="Current server timestamp",
        example="2024-01-15T10:30:00Z"
    )
    
    uptime_seconds: float = Field(
        description="How long the server has been running",
        example=3600.5
    )
    
    components: Dict[str, str] = Field(
        description="Status of individual service components",
        example={
            "database": "healthy",
            "redis": "healthy", 
            "task_queue": "healthy",
            "marketing_agent": "healthy"
        }
    )
    
    metrics: Optional[Dict[str, Any]] = Field(
        description="Optional performance metrics",
        default=None,
        example={
            "active_campaigns": 3,
            "completed_today": 42,
            "average_processing_time": 27.5
        }
    )


class StatusResponse(BaseModel):
    """
    Service status response format.
    
    Provides more detailed information than health check.
    """
    service: str = Field(
        description="Service name",
        example="Marketing Agent API"
    )
    
    environment: str = Field(
        description="Environment (development, staging, production)",
        example="production"
    )
    
    version: str = Field(
        description="Service version",
        example="1.0.0"
    )
    
    build: Optional[str] = Field(
        description="Build number or commit hash",
        default=None,
        example="abc123def456"
    )
    
    deployed_at: Optional[str] = Field(
        description="When this version was deployed",
        default=None,
        example="2024-01-15T08:00:00Z"
    )
    
    configuration: Dict[str, Any] = Field(
        description="Current service configuration",
        example={
            "max_concurrent_campaigns": 5,
            "supported_channels": ["email", "instagram", "facebook"],
            "ai_models": ["gpt-4o", "dall-e-3"]
        }
    )
    
    statistics: Dict[str, Any] = Field(
        description="Usage statistics",
        example={
            "total_campaigns_created": 1250,
            "campaigns_today": 42,
            "success_rate_24h": 98.5,
            "average_processing_time": 27.3
        }
    )


class ValidationErrorResponse(BaseModel):
    """
    Specific response format for validation errors.
    
    Provides detailed field-level validation error information.
    """
    success: bool = Field(default=False)
    error: str = Field(default="ValidationError")
    message: str = Field(description="Summary of validation errors")
    
    validation_errors: list[Dict[str, Any]] = Field(
        description="Detailed validation error information",
        example=[
            {
                "field": "user_input",
                "message": "String too short",
                "type": "value_error.any_str.min_length",
                "input": "hi"
            },
            {
                "field": "options.channels",
                "message": "Invalid channel 'tiktok'",
                "type": "value_error",
                "input": ["instagram", "tiktok"]
            }
        ]
    )
