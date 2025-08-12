"""
Campaign Service - Wraps the Marketing Agent for API use.

This service acts as a bridge between the FastAPI web layer and the
core marketing agent functionality, handling async processing and
state management.
"""

import asyncio
import uuid
import time
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from pathlib import Path

# Import from the main marketing agent project
from src.agents.campaign.full_marketing_agent import FullMarketingAgent
from src.utils.state import MessagesState
from src.nodes.intent.parse_intent_node import parse_intent_node
from langchain.schema import HumanMessage

from app.models.campaign import (
    CampaignRequest, CampaignResponse, CampaignStatus, 
    CampaignProgress, GeneratedContent, DeliveryResult,
    PerformanceMetrics, CampaignFiles
)
from app.utils.config import get_api_config
from app.utils.logging import setup_logging


class CampaignService:
    """
    Service class that handles marketing campaign generation.
    
    This service:
    1. Wraps the FullMarketingAgent for API use
    2. Handles async processing with progress tracking
    3. Manages campaign state and results storage
    4. Provides file serving capabilities
    """
    
    def __init__(self):
        """Initialize the campaign service."""
        self.config = get_api_config()
        self.logger = setup_logging()
        self.marketing_agent = FullMarketingAgent()
        
        # In-memory storage for active campaigns
        # In production, this should be a database like PostgreSQL
        self.campaigns: Dict[str, Dict[str, Any]] = {}
        
        # Ensure storage directory exists
        self.storage_path = Path(self.config.file_storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        self.logger.info("✅ Campaign service initialized")

    def generate_campaign_id(self) -> str:
        """Generate a unique campaign identifier."""
        # Use a shorter, more user-friendly ID format
        short_uuid = str(uuid.uuid4()).replace('-', '')[:16]
        return f"camp_{short_uuid}"

    async def create_campaign(self, request: CampaignRequest) -> str:
        """
        Create a new marketing campaign and start processing.
        
        Args:
            request: The campaign creation request
            
        Returns:
            campaign_id: Unique identifier for the created campaign
        """
        campaign_id = self.generate_campaign_id()
        
        # Create campaign record
        campaign_data = {
            "campaign_id": campaign_id,
            "status": CampaignStatus.PENDING,
            "created_at": datetime.now(timezone.utc),
            "user_input": request.user_input,
            "options": request.options.dict(),
            "progress": None,
            "results": None,
            "error_message": None
        }
        
        self.campaigns[campaign_id] = campaign_data
        
        # Start background processing
        asyncio.create_task(self._process_campaign(campaign_id, request))
        
        self.logger.info(f"📝 Created campaign {campaign_id}")
        return campaign_id

    async def _process_campaign(self, campaign_id: str, request: CampaignRequest):
        """
        Background task to process a marketing campaign.
        
        This runs the actual marketing agent workflow and updates
        progress as each step completes.
        """
        try:
            self.logger.info(f"🚀 Starting processing for campaign {campaign_id}")
            
            # Update status to processing
            self.campaigns[campaign_id]["status"] = CampaignStatus.PROCESSING
            self.campaigns[campaign_id]["started_at"] = datetime.now(timezone.utc)
            
            # Define the processing steps for progress tracking
            steps = [
                "parse_intent",
                "creative_brief", 
                "text_generation",
                "image_generation",
                "hashtag_generation",
                "compose_response",
                "delivery"
            ]
            
            start_time = time.time()
            
            # Step 1: Parse intent first to show user what we understood
            self._update_progress(campaign_id, "parse_intent", steps, 0)
            
            # Create initial state with user input
            state: MessagesState = {
                "messages": [HumanMessage(content=request.user_input)]
            }
            
            # Parse intent to get structured data
            parsed_state = parse_intent_node(state)
            parsed_intent = parsed_state.get("parsed_intent", {})
            
            # Apply user options if provided
            if request.options.channels:
                parsed_intent["channels"] = request.options.channels
            if request.options.tone:
                parsed_intent["tone"] = request.options.tone
            if request.options.budget:
                parsed_intent["budget"] = request.options.budget
            
            parsed_state["parsed_intent"] = parsed_intent
            
            # Step 2-7: Run the full marketing agent workflow
            current_step = 1
            for step_name in steps[1:]:
                self._update_progress(campaign_id, step_name, steps, current_step)
                current_step += 1
                
                # Add a small delay to make progress visible
                await asyncio.sleep(0.1)
            
            # Execute the marketing agent
            self.logger.info(f"🎯 Running marketing agent for campaign {campaign_id}")
            result = self.marketing_agent.run(parsed_state)
            
            # Process results
            processing_time = time.time() - start_time
            campaign_results = self._process_results(campaign_id, result, request, processing_time)
            
            # Update campaign with results
            self.campaigns[campaign_id].update({
                "status": CampaignStatus.COMPLETED,
                "completed_at": datetime.now(timezone.utc),
                "results": campaign_results,
                "progress": None  # Clear progress when complete
            })
            
            self.logger.info(f"✅ Campaign {campaign_id} completed successfully in {processing_time:.1f}s")
            
            # Call webhook if provided
            if request.options.webhook_url:
                asyncio.create_task(self._call_webhook(campaign_id, request.options.webhook_url))
            
        except Exception as e:
            self.logger.error(f"❌ Campaign {campaign_id} failed: {str(e)}", exc_info=True)
            
            # Update campaign with error
            self.campaigns[campaign_id].update({
                "status": CampaignStatus.FAILED,
                "completed_at": datetime.now(timezone.utc),
                "error_message": str(e),
                "progress": None
            })

    def _update_progress(self, campaign_id: str, current_step: str, all_steps: list, step_index: int):
        """Update the progress tracking for a campaign."""
        progress = CampaignProgress(
            current_step=current_step,
            completed_steps=all_steps[:step_index],
            total_steps=len(all_steps),
            percentage=int((step_index / len(all_steps)) * 100)
        )
        
        self.campaigns[campaign_id]["progress"] = progress.dict()

    def _process_results(self, campaign_id: str, result: MessagesState, request: CampaignRequest, processing_time: float) -> Dict[str, Any]:
        """
        Process the marketing agent results into API response format.
        
        This converts the internal MessagesState into structured JSON
        suitable for API responses.
        """
        # Extract generated content
        generated_content = GeneratedContent(
            marketing_copy=result.get("post_content", ""),
            hashtags=result.get("hashtags", []),
            ctas=result.get("ctas", []),
            image_url=result.get("image_url", ""),
            image_prompt=result.get("image_prompt", "")
        )
        
        # Process delivery results
        delivery_data = result.get("delivery", {})
        delivery_results = []
        
        for channel, status in delivery_data.get("results", {}).items():
            delivery_results.append(DeliveryResult(
                channel=channel,
                status="success" if "Successfully" in status else "failed",
                message=status,
                file_path=f"/api/v1/campaigns/{campaign_id}/files/{channel}.txt"
            ))
        
        # Extract performance metrics
        meta = result.get("meta", {})
        total_tokens = 0
        llm_calls = 0
        models_used = set()
        
        for key, data in meta.items():
            if isinstance(data, dict) and "model" in data:
                llm_calls += 1
                models_used.add(data["model"])
                usage = data.get("usage", {})
                if hasattr(usage, 'total_tokens'):
                    total_tokens += usage.total_tokens
                elif isinstance(usage, dict):
                    total_tokens += usage.get("total_tokens", 0)
        
        performance_metrics = PerformanceMetrics(
            total_tokens=total_tokens,
            generation_time_seconds=round(processing_time, 1),
            llm_calls=llm_calls,
            models_used=list(models_used)
        )
        
        # Create file URLs
        files = CampaignFiles()
        if result.get("image_url"):
            files.image = f"/api/v1/campaigns/{campaign_id}/files/image.png"
        
        # Check if files were generated in delivery
        for channel in delivery_data.get("requested", []):
            file_attr = f"{channel.lower()}_post"
            if hasattr(files, file_attr):
                setattr(files, file_attr, f"/api/v1/campaigns/{campaign_id}/files/{channel.lower()}_post.txt")
        
        if "email" in delivery_data.get("requested", []):
            files.email_html = f"/api/v1/campaigns/{campaign_id}/files/email_post.html"
            files.email_text = f"/api/v1/campaigns/{campaign_id}/files/email_post.txt"
        
        return {
            "parsed_intent": result.get("parsed_intent", {}),
            "generated_content": generated_content.dict(),
            "delivery_results": [dr.dict() for dr in delivery_results],
            "performance_metrics": performance_metrics.dict(),
            "files": files.dict()
        }

    async def get_campaign(self, campaign_id: str) -> Optional[CampaignResponse]:
        """
        Get complete campaign information by ID.
        
        Args:
            campaign_id: The campaign identifier
            
        Returns:
            Campaign response object or None if not found
        """
        campaign_data = self.campaigns.get(campaign_id)
        if not campaign_data:
            return None
        
        # Build response object
        response_data = {
            "campaign_id": campaign_id,
            "status": campaign_data["status"],
            "created_at": campaign_data["created_at"],
            "user_input": campaign_data["user_input"],
            "options": campaign_data["options"]
        }
        
        # Add completion time if available
        if "completed_at" in campaign_data:
            response_data["completed_at"] = campaign_data["completed_at"]
        
        # Add progress if still processing
        if campaign_data.get("progress"):
            response_data["progress"] = campaign_data["progress"]
        
        # Add results if completed
        if campaign_data.get("results"):
            response_data.update(campaign_data["results"])
        
        # Add error message if failed
        if campaign_data.get("error_message"):
            response_data["error_message"] = campaign_data["error_message"]
        
        return CampaignResponse(**response_data)

    async def get_campaign_status(self, campaign_id: str) -> Optional[Dict[str, Any]]:
        """Get just the status and progress for a campaign."""
        campaign_data = self.campaigns.get(campaign_id)
        if not campaign_data:
            return None
        
        return {
            "campaign_id": campaign_id,
            "status": campaign_data["status"],
            "progress": campaign_data.get("progress"),
            "error_message": campaign_data.get("error_message")
        }

    async def cancel_campaign(self, campaign_id: str) -> bool:
        """
        Cancel a campaign (if it's still processing).
        
        Note: This is a simplified implementation. In production,
        you'd need proper task cancellation with Celery or similar.
        """
        campaign_data = self.campaigns.get(campaign_id)
        if not campaign_data:
            return False
        
        if campaign_data["status"] == CampaignStatus.PROCESSING:
            campaign_data["status"] = CampaignStatus.CANCELLED
            campaign_data["completed_at"] = datetime.now(timezone.utc)
            campaign_data["progress"] = None
            return True
        
        return False

    async def _call_webhook(self, campaign_id: str, webhook_url: str):
        """Call webhook URL when campaign completes (simplified implementation)."""
        try:
            import httpx
            
            campaign_data = await self.get_campaign(campaign_id)
            async with httpx.AsyncClient() as client:
                await client.post(webhook_url, json={
                    "event": "campaign_completed",
                    "campaign_id": campaign_id,
                    "status": campaign_data.status,
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }, timeout=10)
                
            self.logger.info(f"📞 Webhook called for campaign {campaign_id}")
            
        except Exception as e:
            self.logger.error(f"❌ Webhook call failed for campaign {campaign_id}: {str(e)}")


# Global service instance
campaign_service = CampaignService()
