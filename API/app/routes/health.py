"""
Health check and status API endpoints.

These endpoints provide information about service health,
configuration, and operational metrics.
"""

from datetime import datetime, timezone
from fastapi import APIRouter, status

from app.models.responses import HealthResponse, StatusResponse, APIResponse
from app.services.task_manager import task_manager
from app.services.file_service import file_service
from app.utils.config import get_api_config
from app.utils.logging import setup_logging

# Create router for health endpoints (no authentication required)
router = APIRouter()
logger = setup_logging()

# Track service start time
service_start_time = datetime.now(timezone.utc)


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Health Check",
    description="""
    Basic health check endpoint for load balancers and monitoring.
    
    Returns service health status and component availability.
    This endpoint does not require authentication.
    
    **Health Status Values:**
    - `healthy`: All components operational
    - `degraded`: Some components have issues but service is functional
    - `unhealthy`: Critical components are down
    """
)
async def health_check():
    """
    Perform health check and return service status.
    
    This endpoint is typically used by:
    - Load balancers for routing decisions
    - Monitoring systems for alerting
    - Container orchestrators for restart decisions
    """
    config = get_api_config()
    current_time = datetime.now(timezone.utc)
    uptime = (current_time - service_start_time).total_seconds()
    
    # Check component health
    components = {}
    overall_healthy = True
    
    # Check task manager
    try:
        if task_manager.is_healthy():
            components["task_manager"] = "healthy"
        else:
            components["task_manager"] = "degraded"
            overall_healthy = False
    except Exception:
        components["task_manager"] = "unhealthy"
        overall_healthy = False
    
    # Check file storage
    try:
        file_service.storage_path.exists()
        components["file_storage"] = "healthy"
    except Exception:
        components["file_storage"] = "unhealthy"
        overall_healthy = False
    
    # Check marketing agent (simplified)
    try:
        # Simple check - can we import the main components?
        from src.agents.campaign.full_marketing_agent import FullMarketingAgent
        components["marketing_agent"] = "healthy"
    except Exception:
        components["marketing_agent"] = "unhealthy"
        overall_healthy = False
    
    # Check configuration
    try:
        config_errors = config.validate_config()
        if not config_errors:
            components["configuration"] = "healthy"
        else:
            components["configuration"] = "degraded"
            overall_healthy = False
    except Exception:
        components["configuration"] = "unhealthy"
        overall_healthy = False
    
    # Overall status
    if overall_healthy:
        overall_status = "healthy"
    elif any(status == "unhealthy" for status in components.values()):
        overall_status = "unhealthy"
    else:
        overall_status = "degraded"
    
    # Gather metrics
    metrics = {}
    try:
        task_stats = task_manager.get_stats()
        metrics.update({
            "active_campaigns": task_stats["running_tasks"],
            "total_campaigns": task_stats["total_tasks"],
            "success_rate": task_stats["success_rate"]
        })
    except Exception:
        pass
    
    try:
        storage_stats = file_service.get_storage_stats()
        metrics.update({
            "stored_files": storage_stats["file_count"],
            "storage_size": storage_stats["total_size_human"]
        })
    except Exception:
        pass
    
    return HealthResponse(
        status=overall_status,
        version=config.api_version,
        timestamp=current_time.isoformat(),
        uptime_seconds=uptime,
        components=components,
        metrics=metrics if metrics else None
    )


@router.get(
    "/status",
    response_model=StatusResponse,
    summary="Detailed Status",
    description="""
    Detailed service status with configuration and statistics.
    
    Provides more comprehensive information than the health check:
    - Service configuration
    - Usage statistics  
    - Performance metrics
    - Build information
    
    **Note:** This endpoint does not require authentication but may expose
    sensitive configuration in development environments.
    """
)
async def service_status():
    """Get detailed service status and configuration."""
    config = get_api_config()
    current_time = datetime.now(timezone.utc)
    
    # Service configuration (sanitized for security)
    configuration = {
        "environment": "development" if config.debug else "production",
        "api_version": config.api_version,
        "max_concurrent_campaigns": config.max_concurrent_campaigns,
        "supported_channels": config.get_enabled_channels(),
        "ai_models": ["gpt-4o", "dall-e-3"],  # Static for now
        "rate_limit_per_minute": config.rate_limit_per_minute,
        "file_storage_enabled": True,
        "dry_run_mode": config.dry_run
    }
    
    # Usage statistics
    statistics = {}
    try:
        task_stats = task_manager.get_stats()
        storage_stats = file_service.get_storage_stats()
        
        statistics = {
            "uptime_seconds": task_stats["uptime_seconds"],
            "total_campaigns_created": task_stats["total_tasks"],
            "active_campaigns": task_stats["running_tasks"],
            "completed_campaigns": task_stats["completed_tasks"],
            "success_rate_percent": task_stats["success_rate"],
            "total_files_stored": storage_stats["file_count"],
            "storage_usage": storage_stats["total_size_human"],
            "campaigns_with_files": storage_stats["campaign_count"]
        }
    except Exception as e:
        logger.error(f"Failed to gather statistics: {str(e)}")
        statistics = {"error": "Statistics temporarily unavailable"}
    
    return StatusResponse(
        service="Marketing Agent API",
        environment="development" if config.debug else "production",
        version=config.api_version,
        build=None,  # Could add git commit hash here
        deployed_at=None,  # Could add deployment timestamp
        configuration=configuration,
        statistics=statistics
    )


@router.get(
    "/ping",
    response_model=APIResponse,
    summary="Simple Ping",
    description="""
    Minimal ping endpoint for basic connectivity testing.
    
    Returns immediately with a simple response.
    Useful for:
    - Network connectivity tests
    - Basic service availability checks
    - Response time measurement
    """
)
async def ping():
    """Simple ping endpoint for connectivity testing."""
    return APIResponse(
        success=True,
        message="pong",
        data={
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "service": "Marketing Agent API"
        }
    )


@router.get(
    "/metrics",
    response_model=APIResponse,
    summary="Service Metrics",
    description="""
    Prometheus-style metrics for monitoring systems.
    
    Returns operational metrics in a structured format suitable
    for monitoring and alerting systems.
    """
)
async def get_metrics():
    """Get service metrics for monitoring."""
    try:
        task_stats = task_manager.get_stats()
        storage_stats = file_service.get_storage_stats()
        config = get_api_config()
        
        uptime_seconds = (datetime.now(timezone.utc) - service_start_time).total_seconds()
        
        metrics = {
            # Service metrics
            "marketing_api_uptime_seconds": uptime_seconds,
            "marketing_api_info": {
                "version": config.api_version,
                "environment": "development" if config.debug else "production"
            },
            
            # Campaign metrics
            "marketing_campaigns_total": task_stats["total_tasks"],
            "marketing_campaigns_active": task_stats["running_tasks"],
            "marketing_campaigns_completed": task_stats["completed_tasks"],
            "marketing_campaigns_success_rate": task_stats["success_rate"] / 100,
            
            # Resource metrics
            "marketing_api_max_concurrent_campaigns": config.max_concurrent_campaigns,
            "marketing_api_rate_limit_per_minute": config.rate_limit_per_minute,
            
            # Storage metrics
            "marketing_files_total": storage_stats["file_count"],
            "marketing_storage_bytes": storage_stats["total_size_bytes"],
            "marketing_campaigns_with_files": storage_stats["campaign_count"]
        }
        
        return APIResponse(
            success=True,
            message="Metrics retrieved successfully",
            data=metrics
        )
        
    except Exception as e:
        logger.error(f"Failed to gather metrics: {str(e)}")
        return APIResponse(
            success=False,
            message="Failed to retrieve metrics",
            data={"error": str(e)}
        )
