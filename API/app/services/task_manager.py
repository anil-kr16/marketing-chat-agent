"""
Task Manager for background processing.

This module handles background task processing and resource management
for the marketing agent API. In production, this would be replaced with
a proper task queue like Celery + Redis.
"""

import asyncio
from typing import Dict, Set
from datetime import datetime, timezone

from app.utils.config import get_api_config
from app.utils.logging import setup_logging


class TaskManager:
    """
    Simple in-memory task manager for background campaign processing.
    
    For production use, replace this with:
    - Celery + Redis for distributed task processing
    - Database for persistent task storage
    - Proper worker scaling and monitoring
    """
    
    def __init__(self):
        """Initialize the task manager."""
        self.config = get_api_config()
        self.logger = setup_logging()
        
        # Track running tasks
        self.running_tasks: Set[str] = set()
        self.task_history: Dict[str, Dict] = {}
        
        # Resource limits
        self.max_concurrent_tasks = self.config.max_concurrent_campaigns
        self.started_at = None

    async def startup(self):
        """Initialize the task manager."""
        self.started_at = datetime.now(timezone.utc)
        self.logger.info("🔧 Task manager started")

    async def shutdown(self):
        """Shutdown the task manager and cleanup resources."""
        # Wait for running tasks to complete (with timeout)
        if self.running_tasks:
            self.logger.info(f"⏳ Waiting for {len(self.running_tasks)} tasks to complete...")
            
            # In production, you'd send cancellation signals to tasks
            # For now, just wait a short time
            await asyncio.sleep(2)
            
        self.logger.info("🛑 Task manager shutdown complete")

    def can_start_task(self) -> bool:
        """Check if we can start a new task based on resource limits."""
        return len(self.running_tasks) < self.max_concurrent_tasks

    def add_task(self, task_id: str):
        """Register a new task as running."""
        self.running_tasks.add(task_id)
        self.task_history[task_id] = {
            "started_at": datetime.now(timezone.utc),
            "status": "running"
        }
        
        self.logger.info(f"📋 Task {task_id} started ({len(self.running_tasks)}/{self.max_concurrent_tasks} slots used)")

    def complete_task(self, task_id: str, success: bool = True):
        """Mark a task as completed."""
        self.running_tasks.discard(task_id)
        
        if task_id in self.task_history:
            self.task_history[task_id].update({
                "completed_at": datetime.now(timezone.utc),
                "status": "completed" if success else "failed"
            })
        
        status_emoji = "✅" if success else "❌"
        self.logger.info(f"{status_emoji} Task {task_id} completed ({len(self.running_tasks)}/{self.max_concurrent_tasks} slots used)")

    def get_stats(self) -> Dict:
        """Get task manager statistics."""
        total_tasks = len(self.task_history)
        completed_tasks = sum(1 for task in self.task_history.values() if task["status"] in ["completed", "failed"])
        success_rate = (sum(1 for task in self.task_history.values() if task["status"] == "completed") / total_tasks * 100) if total_tasks > 0 else 0
        
        uptime = (datetime.now(timezone.utc) - self.started_at).total_seconds() if self.started_at else 0
        
        return {
            "running_tasks": len(self.running_tasks),
            "max_concurrent": self.max_concurrent_tasks,
            "total_tasks": total_tasks,
            "completed_tasks": completed_tasks,
            "success_rate": round(success_rate, 1),
            "uptime_seconds": round(uptime, 1)
        }

    def is_healthy(self) -> bool:
        """Check if the task manager is healthy."""
        # Simple health check - not overloaded
        return len(self.running_tasks) < self.max_concurrent_tasks


# Global task manager instance
task_manager = TaskManager()
