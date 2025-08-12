"""
WebSocket endpoints for real-time campaign updates.

Provides real-time progress updates for campaign generation
using WebSocket connections.
"""

import asyncio
import json
from typing import Dict, Set
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query, Path
from fastapi.websockets import WebSocketState

from app.services.campaign_service import campaign_service
from app.utils.logging import setup_logging

# Create router for WebSocket endpoints
router = APIRouter()
logger = setup_logging()

# Track active WebSocket connections
# In production, use Redis or similar for multi-instance support
active_connections: Dict[str, Set[WebSocket]] = {}


class ConnectionManager:
    """
    WebSocket connection manager for campaign updates.
    
    Manages multiple connections per campaign and broadcasts
    updates to all interested clients.
    """
    
    def __init__(self):
        """Initialize the connection manager."""
        self.logger = setup_logging()

    async def connect(self, websocket: WebSocket, campaign_id: str):
        """Accept a new WebSocket connection for a campaign."""
        await websocket.accept()
        
        # Add to active connections
        if campaign_id not in active_connections:
            active_connections[campaign_id] = set()
        
        active_connections[campaign_id].add(websocket)
        
        self.logger.info(f"🔌 WebSocket connected for campaign {campaign_id} ({len(active_connections[campaign_id])} total)")

    async def disconnect(self, websocket: WebSocket, campaign_id: str):
        """Remove a WebSocket connection."""
        if campaign_id in active_connections:
            active_connections[campaign_id].discard(websocket)
            
            # Clean up empty sets
            if not active_connections[campaign_id]:
                del active_connections[campaign_id]
        
        self.logger.info(f"🔌 WebSocket disconnected for campaign {campaign_id}")

    async def send_personal_message(self, message: dict, websocket: WebSocket):
        """Send a message to a specific WebSocket."""
        try:
            if websocket.client_state == WebSocketState.CONNECTED:
                await websocket.send_text(json.dumps(message))
        except Exception as e:
            self.logger.error(f"Failed to send WebSocket message: {str(e)}")

    async def broadcast_to_campaign(self, message: dict, campaign_id: str):
        """Broadcast a message to all connections for a campaign."""
        if campaign_id not in active_connections:
            return
        
        # Send to all connected clients for this campaign
        disconnected = set()
        for websocket in active_connections[campaign_id]:
            try:
                if websocket.client_state == WebSocketState.CONNECTED:
                    await websocket.send_text(json.dumps(message))
                else:
                    disconnected.add(websocket)
            except Exception as e:
                self.logger.error(f"Failed to broadcast to WebSocket: {str(e)}")
                disconnected.add(websocket)
        
        # Remove disconnected clients
        for websocket in disconnected:
            active_connections[campaign_id].discard(websocket)


# Global connection manager
manager = ConnectionManager()


@router.websocket("/campaigns/{campaign_id}/stream")
async def campaign_stream(
    websocket: WebSocket,
    campaign_id: str = Path(..., description="Campaign ID to stream updates for"),
    api_key: str = Query(..., description="API key for authentication")
):
    """
    WebSocket endpoint for real-time campaign updates.
    
    Provides live updates as the campaign progresses through different stages.
    
    **Message Types:**
    - `status_update`: Campaign status changes
    - `progress_update`: Processing progress updates  
    - `step_complete`: Individual step completions
    - `error`: Error notifications
    - `complete`: Final completion notification
    
    **Authentication:**
    API key must be provided as a query parameter since WebSocket
    headers are limited.
    
    **Usage Example:**
    ```javascript
    const ws = new WebSocket('ws://localhost:8000/api/v1/campaigns/camp_123/stream?api_key=your-key');
    
    ws.onmessage = function(event) {
        const data = JSON.parse(event.data);
        console.log('Campaign update:', data);
    };
    ```
    """
    # Simple API key validation for WebSocket
    # In production, use proper token validation
    from app.utils.config import get_api_config
    config = get_api_config()
    
    if api_key != config.default_api_key:
        await websocket.close(code=4001, reason="Invalid API key")
        return
    
    # Check if campaign exists
    campaign = await campaign_service.get_campaign(campaign_id)
    if not campaign:
        await websocket.close(code=4004, reason="Campaign not found")
        return
    
    # Connect WebSocket
    await manager.connect(websocket, campaign_id)
    
    try:
        # Send initial status
        await manager.send_personal_message({
            "type": "connected",
            "campaign_id": campaign_id,
            "status": campaign.status,
            "message": f"Connected to campaign {campaign_id} updates"
        }, websocket)
        
        # Send current status if available
        current_status = await campaign_service.get_campaign_status(campaign_id)
        if current_status:
            await manager.send_personal_message({
                "type": "status_update",
                "campaign_id": campaign_id,
                "data": current_status
            }, websocket)
        
        # Keep connection alive and handle incoming messages
        while True:
            try:
                # Wait for messages from client (keep-alive, etc.)
                message = await asyncio.wait_for(websocket.receive_text(), timeout=30.0)
                
                # Handle client messages if needed
                try:
                    client_data = json.loads(message)
                    if client_data.get("type") == "ping":
                        await manager.send_personal_message({
                            "type": "pong",
                            "timestamp": client_data.get("timestamp")
                        }, websocket)
                except json.JSONDecodeError:
                    # Ignore invalid JSON
                    pass
                    
            except asyncio.TimeoutError:
                # Send keep-alive ping
                await manager.send_personal_message({
                    "type": "ping",
                    "timestamp": asyncio.get_event_loop().time()
                }, websocket)
                
    except WebSocketDisconnect:
        logger.info(f"🔌 WebSocket client disconnected from campaign {campaign_id}")
    except Exception as e:
        logger.error(f"WebSocket error for campaign {campaign_id}: {str(e)}")
    finally:
        await manager.disconnect(websocket, campaign_id)


async def notify_campaign_update(campaign_id: str, update_type: str, data: dict):
    """
    Utility function to send updates to all connected clients for a campaign.
    
    This function should be called from the campaign service when
    status or progress changes occur.
    
    Args:
        campaign_id: The campaign identifier
        update_type: Type of update (status_update, progress_update, etc.)
        data: Update data to send
    """
    if campaign_id not in active_connections:
        return  # No one is listening
    
    message = {
        "type": update_type,
        "campaign_id": campaign_id,
        "timestamp": asyncio.get_event_loop().time(),
        "data": data
    }
    
    await manager.broadcast_to_campaign(message, campaign_id)


async def notify_campaign_progress(campaign_id: str, current_step: str, percentage: int):
    """Send a progress update to WebSocket clients."""
    await notify_campaign_update(campaign_id, "progress_update", {
        "current_step": current_step,
        "percentage": percentage,
        "message": f"Processing: {current_step}"
    })


async def notify_campaign_complete(campaign_id: str, success: bool, message: str = None):
    """Send a completion notification to WebSocket clients."""
    await notify_campaign_update(campaign_id, "complete", {
        "success": success,
        "message": message or ("Campaign completed successfully" if success else "Campaign failed")
    })


async def notify_campaign_error(campaign_id: str, error_message: str):
    """Send an error notification to WebSocket clients."""
    await notify_campaign_update(campaign_id, "error", {
        "error": error_message,
        "message": f"Campaign error: {error_message}"
    })


# Utility function to get connection stats
def get_websocket_stats() -> dict:
    """Get WebSocket connection statistics."""
    total_connections = sum(len(connections) for connections in active_connections.values())
    
    return {
        "active_campaigns": len(active_connections),
        "total_connections": total_connections,
        "campaigns_with_listeners": list(active_connections.keys())
    }
