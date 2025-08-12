"""
Campaign management API endpoints.

This module defines all the REST API endpoints for creating,
tracking, and managing marketing campaigns.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Path, status
from fastapi.responses import FileResponse

from app.models.campaign import (
    CampaignRequest, CampaignResponse, CampaignCreateResponse,
    CampaignListResponse, CampaignStatus
)
from app.models.responses import APIResponse, ErrorResponse
from app.services.campaign_service import campaign_service
from app.services.file_service import file_service
from app.utils.auth import get_current_api_key
from app.utils.logging import setup_logging, log_campaign_event

# Create router for campaign endpoints
router = APIRouter(dependencies=[Depends(get_current_api_key)])
logger = setup_logging()


@router.post(
    "/campaigns",
    response_model=CampaignCreateResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create Marketing Campaign",
    description="""
    Create a new marketing campaign from natural language input.
    
    The campaign will be processed asynchronously in the background.
    Use the returned campaign_id to track progress and retrieve results.
    
    **Example Input:**
    ```json
    {
        "user_input": "promote eco-friendly water bottle for outdoor enthusiasts with $300 budget",
        "options": {
            "channels": ["instagram", "email"],
            "tone": "inspirational",
            "include_images": true,
            "dry_run": true
        }
    }
    ```
    
    **Processing Time:** Typically 25-30 seconds for full campaign generation.
    """
)
async def create_campaign(
    request: CampaignRequest,
    api_key: str = Depends(get_current_api_key)
):
    """
    Create a new marketing campaign.
    
    This endpoint immediately returns a campaign ID and starts
    background processing. The actual campaign generation happens
    asynchronously.
    """
    try:
        # Create campaign and start processing
        campaign_id = await campaign_service.create_campaign(request)
        
        log_campaign_event(campaign_id, "created", f"User input: {request.user_input[:50]}...")
        
        return CampaignCreateResponse(
            campaign_id=campaign_id,
            status=CampaignStatus.PENDING,
            message="Campaign created successfully. Use the campaign_id to track progress.",
            estimated_completion_time="25-30 seconds",
            status_url=f"/api/v1/campaigns/{campaign_id}/status",
            websocket_url=f"/api/v1/campaigns/{campaign_id}/stream"
        )
        
    except Exception as e:
        logger.error(f"Failed to create campaign: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create campaign: {str(e)}"
        )


@router.get(
    "/campaigns/{campaign_id}",
    response_model=CampaignResponse,
    summary="Get Campaign Details",
    description="""
    Retrieve complete details for a specific campaign.
    
    Returns all available information including:
    - Campaign status and progress
    - Generated content (if completed)
    - Delivery results
    - Performance metrics
    - File download URLs
    
    **Status Values:**
    - `pending`: Campaign created, waiting to start
    - `processing`: Currently being generated  
    - `completed`: Successfully finished
    - `failed`: Generation failed
    - `cancelled`: User cancelled
    """
)
async def get_campaign(
    campaign_id: str = Path(..., description="Unique campaign identifier"),
    api_key: str = Depends(get_current_api_key)
):
    """Get complete campaign information by ID."""
    campaign = await campaign_service.get_campaign(campaign_id)
    
    if not campaign:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Campaign {campaign_id} not found"
        )
    
    return campaign


@router.get(
    "/campaigns/{campaign_id}/status", 
    response_model=APIResponse,
    summary="Get Campaign Status",
    description="""
    Get just the status and progress information for a campaign.
    
    This is a lightweight endpoint for polling campaign progress
    without retrieving the full campaign data.
    
    **Polling Recommendation:** Check every 2-3 seconds while status is 'processing'.
    """
)
async def get_campaign_status(
    campaign_id: str = Path(..., description="Unique campaign identifier"),
    api_key: str = Depends(get_current_api_key)
):
    """Get campaign status and progress."""
    status_info = await campaign_service.get_campaign_status(campaign_id)
    
    if not status_info:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Campaign {campaign_id} not found"
        )
    
    return APIResponse(
        success=True,
        message="Campaign status retrieved successfully",
        data=status_info
    )


@router.delete(
    "/campaigns/{campaign_id}",
    response_model=APIResponse,
    summary="Cancel Campaign",
    description="""
    Cancel a campaign that is currently processing.
    
    **Note:** Only campaigns with status 'pending' or 'processing' can be cancelled.
    Completed, failed, or already cancelled campaigns cannot be cancelled.
    """
)
async def cancel_campaign(
    campaign_id: str = Path(..., description="Unique campaign identifier"),
    api_key: str = Depends(get_current_api_key)
):
    """Cancel a campaign if it's still processing."""
    success = await campaign_service.cancel_campaign(campaign_id)
    
    if not success:
        # Check if campaign exists
        campaign = await campaign_service.get_campaign(campaign_id)
        if not campaign:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Campaign {campaign_id} not found"
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Campaign {campaign_id} cannot be cancelled (status: {campaign.status})"
            )
    
    log_campaign_event(campaign_id, "cancelled", "User requested cancellation")
    
    return APIResponse(
        success=True,
        message=f"Campaign {campaign_id} has been cancelled",
        data={"campaign_id": campaign_id, "status": "cancelled"}
    )


@router.get(
    "/campaigns",
    response_model=CampaignListResponse,
    summary="List Campaigns",
    description="""
    List campaigns with pagination support.
    
    Returns a paginated list of campaigns, most recent first.
    Use this to browse campaign history or find specific campaigns.
    """
)
async def list_campaigns(
    page: int = Query(1, ge=1, description="Page number (1-based)"),
    per_page: int = Query(10, ge=1, le=100, description="Items per page (max 100)"),
    status_filter: Optional[CampaignStatus] = Query(None, description="Filter by campaign status"),
    api_key: str = Depends(get_current_api_key)
):
    """
    List campaigns with pagination.
    
    Note: This is a simplified implementation using in-memory storage.
    In production, implement proper database queries with filtering and pagination.
    """
    # Get all campaigns (in production, this would be a database query)
    all_campaigns = []
    
    for campaign_id in campaign_service.campaigns.keys():
        campaign = await campaign_service.get_campaign(campaign_id)
        if campaign:
            # Apply status filter if provided
            if status_filter is None or campaign.status == status_filter:
                all_campaigns.append(campaign)
    
    # Sort by creation time (newest first)
    all_campaigns.sort(key=lambda x: x.created_at, reverse=True)
    
    # Apply pagination
    total = len(all_campaigns)
    start_idx = (page - 1) * per_page
    end_idx = start_idx + per_page
    campaigns_page = all_campaigns[start_idx:end_idx]
    
    return CampaignListResponse(
        campaigns=campaigns_page,
        total=total,
        page=page,
        per_page=per_page,
        has_more=end_idx < total
    )


@router.get(
    "/campaigns/{campaign_id}/files/{filename}",
    response_class=FileResponse,
    summary="Download Campaign File",
    description="""
    Download a specific file generated for a campaign.
    
    **Available Files:**
    - `image.png` - Generated campaign image
    - `email_post.html` - HTML email content
    - `email_post.txt` - Plain text email content
    - `instagram_post.txt` - Instagram post content
    - `facebook_post.txt` - Facebook post content
    
    **Security:** Only files belonging to the specified campaign can be accessed.
    """
)
async def download_campaign_file(
    campaign_id: str = Path(..., description="Unique campaign identifier"),
    filename: str = Path(..., description="Name of the file to download"),
    api_key: str = Depends(get_current_api_key)
):
    """Download a campaign file."""
    # Verify campaign exists
    campaign = await campaign_service.get_campaign(campaign_id)
    if not campaign:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Campaign {campaign_id} not found"
        )
    
    # Check if file exists
    if not file_service.file_exists(campaign_id, filename):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"File {filename} not found for campaign {campaign_id}"
        )
    
    try:
        return file_service.get_file_response(campaign_id, filename)
    except Exception as e:
        logger.error(f"Failed to serve file {filename} for campaign {campaign_id}: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve file"
        )


@router.get(
    "/campaigns/{campaign_id}/files",
    response_model=APIResponse,
    summary="List Campaign Files",
    description="""
    List all files available for a campaign.
    
    Returns metadata about each file including:
    - File name and size
    - MIME type
    - Last modified time
    - Download URL
    """
)
async def list_campaign_files(
    campaign_id: str = Path(..., description="Unique campaign identifier"),
    api_key: str = Depends(get_current_api_key)
):
    """List all files for a campaign."""
    # Verify campaign exists
    campaign = await campaign_service.get_campaign(campaign_id)
    if not campaign:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Campaign {campaign_id} not found"
        )
    
    # Get file list
    files = file_service.list_campaign_files(campaign_id)
    
    # Add download URLs
    for file_info in files:
        file_info["download_url"] = f"/api/v1/campaigns/{campaign_id}/files/{file_info['filename']}"
    
    return APIResponse(
        success=True,
        message=f"Found {len(files)} files for campaign {campaign_id}",
        data={
            "campaign_id": campaign_id,
            "files": files,
            "total_files": len(files)
        }
    )
