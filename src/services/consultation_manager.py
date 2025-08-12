"""
Consultation Manager - Session Management for Stateful Marketing Consultations

This module provides session management capabilities for the stateful marketing
consultation flow, enabling concurrent users and persistent conversation state.

Key Features:
- Session lifecycle management (create, retrieve, update, cleanup)
- Memory-based session storage with optional persistence backends
- Automatic session expiration and cleanup
- Concurrent user support with session isolation
- Session state validation and recovery

Architecture Benefits:
- Stateful conversations across multiple user interactions
- Memory-efficient session storage with configurable backends
- Automatic cleanup prevents memory leaks in long-running applications
- Session isolation ensures user privacy and prevents state corruption
- Graceful handling of expired or corrupted sessions

Integration Points:
- Used by runnable scripts to manage consultation sessions
- Integrates with stateful marketing graph for persistent conversations
- Provides session hooks for analytics and monitoring
- Supports multiple storage backends (memory, Redis, database)

Session Lifecycle:
1. CREATE: New consultation session with unique ID
2. ACTIVE: Multiple conversation turns with state persistence
3. EXPIRE: Automatic cleanup after inactivity timeout
4. COMPLETE: Successful consultation ready for campaign creation
"""

import json
import time
from datetime import datetime, timedelta
from typing import Dict, Optional, List, Any
from threading import Lock
from dataclasses import dataclass, asdict
import uuid

from src.utils.marketing_state import MarketingConsultantState, ConsultationStage
from src.config import get_config
import logging

logger = logging.getLogger(__name__)


@dataclass
class SessionMetadata:
    """
    Metadata for consultation sessions.
    
    This tracks session lifecycle information and provides
    analytics data for consultation performance monitoring.
    """
    session_id: str
    created_at: datetime
    last_accessed: datetime
    question_count: int
    stage: str
    user_agent: Optional[str] = None
    ip_address: Optional[str] = None
    completion_percentage: float = 0.0
    is_expired: bool = False


class ConsultationManager:
    """
    Manages stateful marketing consultation sessions.
    
    This class provides a complete session management solution for
    the stateful consultation flow, handling multiple concurrent users
    and maintaining conversation state across interactions.
    
    Key Responsibilities:
    - Session creation and unique ID generation
    - State persistence and retrieval
    - Automatic session expiration and cleanup
    - Session validation and error recovery
    - Analytics and monitoring support
    
    Example Usage:
        manager = ConsultationManager()
        
        # Start new consultation
        session_id = manager.create_session("promote my coffee shop")
        
        # Continue consultation
        state = manager.get_session_state(session_id)
        # ... process user interaction ...
        manager.update_session_state(session_id, updated_state)
        
        # Session automatically expires after timeout
        # Cleanup happens automatically in background
    """
    
    def __init__(self, session_timeout_minutes: int = 30):
        """
        Initialize the consultation manager.
        
        Args:
            session_timeout_minutes: How long sessions remain active without interaction
        """
        self.session_timeout = timedelta(minutes=session_timeout_minutes)
        self.sessions: Dict[str, MarketingConsultantState] = {}
        self.session_metadata: Dict[str, SessionMetadata] = {}
        self.session_lock = Lock()  # Thread safety for concurrent access
        
        # Get configuration
        self.config = get_config()
        
        # Initialize cleanup tracking
        self.last_cleanup = datetime.now()
        self.cleanup_interval = timedelta(minutes=5)  # Run cleanup every 5 minutes
        
        logger.info(f"Consultation manager initialized with {session_timeout_minutes}min timeout")
    
    def create_session(
        self, 
        user_input: str,
        user_context: Optional[Dict[str, str]] = None
    ) -> str:
        """
        Create a new consultation session.
        
        This initializes a new stateful consultation with a unique session ID
        and sets up the initial state for the conversation flow.
        
        Args:
            user_input: Initial user request that triggered consultation
            user_context: Optional context (IP, user agent, etc.) for analytics
            
        Returns:
            Unique session ID for this consultation
            
        Example:
            session_id = manager.create_session("market my coffee shop")
        """
        with self.session_lock:
            # Generate unique session ID
            session_id = self._generate_session_id()
            
            # Create initial consultation state
            initial_state = MarketingConsultantState(
                user_input=user_input,
                session_id=session_id,
                timestamp=datetime.now(),
                stage=ConsultationStage.INITIAL
            )
            
            # Create session metadata
            metadata = SessionMetadata(
                session_id=session_id,
                created_at=datetime.now(),
                last_accessed=datetime.now(),
                question_count=0,
                stage=ConsultationStage.INITIAL.value,
                user_agent=user_context.get("user_agent") if user_context else None,
                ip_address=user_context.get("ip_address") if user_context else None
            )
            
            # Store session
            self.sessions[session_id] = initial_state
            self.session_metadata[session_id] = metadata
            
            # Trigger cleanup if needed
            self._maybe_cleanup_expired_sessions()
            
            logger.info(f"Created consultation session: {session_id}")
            return session_id
    
    def get_session_state(self, session_id: str) -> Optional[MarketingConsultantState]:
        """
        Retrieve consultation state for a session.
        
        This fetches the current state of a consultation session,
        handling validation and expiration checking.
        
        Args:
            session_id: The session ID to retrieve
            
        Returns:
            Current consultation state or None if session not found/expired
            
        Example:
            state = manager.get_session_state("consultation_20240812_143022")
            if state:
                # Continue consultation
            else:
                # Session expired or invalid
        """
        with self.session_lock:
            # Check if session exists
            if session_id not in self.sessions:
                logger.warning(f"Session not found: {session_id}")
                return None
            
            # Check if session is expired
            if self._is_session_expired(session_id):
                logger.info(f"Session expired: {session_id}")
                self._cleanup_session(session_id)
                return None
            
            # Update last accessed time
            if session_id in self.session_metadata:
                self.session_metadata[session_id].last_accessed = datetime.now()
            
            # Return session state
            state = self.sessions[session_id]
            logger.debug(f"Retrieved session state: {session_id}")
            return state
    
    def update_session_state(
        self, 
        session_id: str, 
        updated_state: MarketingConsultantState
    ) -> bool:
        """
        Update consultation state for a session.
        
        This persists the updated consultation state and refreshes
        session metadata for analytics and monitoring.
        
        Args:
            session_id: The session ID to update
            updated_state: The new consultation state
            
        Returns:
            True if update successful, False if session not found/expired
            
        Example:
            success = manager.update_session_state(session_id, new_state)
            if not success:
                # Session expired or invalid
        """
        with self.session_lock:
            # Validate session exists and is not expired
            if session_id not in self.sessions:
                logger.warning(f"Cannot update non-existent session: {session_id}")
                return False
            
            if self._is_session_expired(session_id):
                logger.warning(f"Cannot update expired session: {session_id}")
                self._cleanup_session(session_id)
                return False
            
            # Update session state
            self.sessions[session_id] = updated_state
            
            # Update metadata
            if session_id in self.session_metadata:
                metadata = self.session_metadata[session_id]
                metadata.last_accessed = datetime.now()
                metadata.question_count = updated_state.question_count
                # Handle both enum and string stage values
                if hasattr(updated_state.stage, 'value'):
                    metadata.stage = updated_state.stage.value
                else:
                    metadata.stage = str(updated_state.stage) if updated_state.stage else "unknown"
                metadata.completion_percentage = self._calculate_completion_percentage(updated_state)
            
            logger.debug(f"Updated session state: {session_id}")
            return True
    
    def complete_session(self, session_id: str) -> bool:
        """
        Mark a session as completed and prepare for cleanup.
        
        This is called when a consultation successfully completes
        and is ready for campaign creation handoff.
        
        Args:
            session_id: The session ID to mark as complete
            
        Returns:
            True if session was marked complete, False if not found
        """
        with self.session_lock:
            if session_id not in self.sessions:
                return False
            
            # Update state and metadata
            state = self.sessions[session_id]
            state.stage = ConsultationStage.COMPLETED
            
            if session_id in self.session_metadata:
                metadata = self.session_metadata[session_id]
                metadata.stage = ConsultationStage.COMPLETED.value
                metadata.completion_percentage = 1.0
                metadata.last_accessed = datetime.now()
            
            logger.info(f"Session completed: {session_id}")
            return True
    
    def cleanup_expired_sessions(self) -> int:
        """
        Clean up all expired sessions.
        
        This removes sessions that have exceeded the timeout period
        and frees up memory resources.
        
        Returns:
            Number of sessions cleaned up
        """
        cleaned_count = 0
        
        with self.session_lock:
            # Get list of expired sessions
            expired_sessions = []
            for session_id in list(self.sessions.keys()):
                if self._is_session_expired(session_id):
                    expired_sessions.append(session_id)
            
            # Clean up expired sessions
            for session_id in expired_sessions:
                self._cleanup_session(session_id)
                cleaned_count += 1
            
            # Update last cleanup time
            self.last_cleanup = datetime.now()
        
        if cleaned_count > 0:
            logger.info(f"Cleaned up {cleaned_count} expired sessions")
        
        return cleaned_count
    
    def get_session_analytics(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Get analytics information for a session.
        
        This provides detailed information about consultation progress
        and performance for monitoring and optimization.
        
        Args:
            session_id: The session ID to analyze
            
        Returns:
            Dict with analytics data or None if session not found
        """
        with self.session_lock:
            if session_id not in self.sessions or session_id not in self.session_metadata:
                return None
            
            state = self.sessions[session_id]
            metadata = self.session_metadata[session_id]
            
            # Calculate analytics metrics
            duration = datetime.now() - metadata.created_at
            
            analytics = {
                "session_id": session_id,
                "created_at": metadata.created_at.isoformat(),
                "duration_minutes": duration.total_seconds() / 60,
                "question_count": metadata.question_count,
                "current_stage": metadata.stage,
                "completion_percentage": metadata.completion_percentage,
                "information_gathered": {
                    field: bool(value) for field, value in state.parsed_intent.items()
                },
                "conversation_turns": len(state.qa_history),
                "average_response_length": self._calculate_avg_response_length(state),
                "is_active": not self._is_session_expired(session_id),
                "user_context": {
                    "user_agent": metadata.user_agent,
                    "ip_address": metadata.ip_address
                }
            }
            
            return analytics
    
    def get_all_active_sessions(self) -> List[str]:
        """
        Get list of all active (non-expired) session IDs.
        
        Returns:
            List of active session IDs
        """
        with self.session_lock:
            active_sessions = []
            for session_id in list(self.sessions.keys()):
                if not self._is_session_expired(session_id):
                    active_sessions.append(session_id)
            return active_sessions
    
    def get_manager_statistics(self) -> Dict[str, Any]:
        """
        Get overall manager statistics for monitoring.
        
        Returns:
            Dict with manager performance and usage statistics
        """
        with self.session_lock:
            active_sessions = self.get_all_active_sessions()
            completed_sessions = [
                sid for sid in self.sessions.keys() 
                if self.sessions[sid].stage == ConsultationStage.COMPLETED
            ]
            
            return {
                "total_sessions": len(self.sessions),
                "active_sessions": len(active_sessions),
                "completed_sessions": len(completed_sessions),
                "memory_usage_mb": self._estimate_memory_usage(),
                "last_cleanup": self.last_cleanup.isoformat(),
                "session_timeout_minutes": self.session_timeout.total_seconds() / 60,
                "cleanup_interval_minutes": self.cleanup_interval.total_seconds() / 60
            }
    
    # === PRIVATE HELPER METHODS ===
    
    def _generate_session_id(self) -> str:
        """Generate a unique session ID."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_suffix = str(uuid.uuid4())[:8]
        return f"consultation_{timestamp}_{unique_suffix}"
    
    def _is_session_expired(self, session_id: str) -> bool:
        """Check if a session has expired."""
        if session_id not in self.session_metadata:
            return True
        
        metadata = self.session_metadata[session_id]
        time_since_last_access = datetime.now() - metadata.last_accessed
        return time_since_last_access > self.session_timeout
    
    def _cleanup_session(self, session_id: str) -> None:
        """Remove a session and its metadata."""
        if session_id in self.sessions:
            del self.sessions[session_id]
        if session_id in self.session_metadata:
            del self.session_metadata[session_id]
        logger.debug(f"Cleaned up session: {session_id}")
    
    def _maybe_cleanup_expired_sessions(self) -> None:
        """Trigger cleanup if enough time has passed since last cleanup."""
        time_since_cleanup = datetime.now() - self.last_cleanup
        if time_since_cleanup > self.cleanup_interval:
            self.cleanup_expired_sessions()
    
    def _calculate_completion_percentage(self, state: MarketingConsultantState) -> float:
        """Calculate how complete a consultation is (0.0 to 1.0)."""
        if state.stage == ConsultationStage.COMPLETED:
            return 1.0
        elif state.stage == ConsultationStage.READY:
            return 0.9
        elif state.stage == ConsultationStage.VALIDATING:
            return 0.8
        elif state.stage == ConsultationStage.GATHERING:
            # Base completion on filled fields and questions asked
            filled_fields = sum(1 for v in state.parsed_intent.values() if v)
            total_fields = len(state.parsed_intent)
            field_completion = filled_fields / total_fields if total_fields > 0 else 0
            
            # Factor in question progress
            question_completion = min(state.question_count / 6.0, 1.0)  # Assume 6 questions is complete
            
            return (field_completion * 0.7 + question_completion * 0.3) * 0.7  # Max 70% in gathering
        else:
            return 0.1  # Initial stage
    
    def _calculate_avg_response_length(self, state: MarketingConsultantState) -> float:
        """Calculate average length of user responses."""
        if not state.qa_history:
            return 0.0
        
        response_lengths = []
        for qa in state.qa_history:
            if qa.get("answer"):
                response_lengths.append(len(qa["answer"]))
        
        return sum(response_lengths) / len(response_lengths) if response_lengths else 0.0
    
    def _estimate_memory_usage(self) -> float:
        """Estimate memory usage in MB (rough calculation)."""
        # Very rough estimate based on session data size
        total_size = 0
        for session_id in self.sessions:
            state = self.sessions[session_id]
            # Estimate size of state object
            state_size = len(str(state.parsed_intent)) + len(str(state.qa_history)) + len(state.user_input)
            total_size += state_size
        
        # Convert to MB (very rough approximation)
        return total_size / (1024 * 1024)


# === GLOBAL SESSION MANAGER INSTANCE ===

# Create a global instance for use across the application
# This ensures session consistency across different modules
_global_manager: Optional[ConsultationManager] = None


def get_consultation_manager() -> ConsultationManager:
    """
    Get the global consultation manager instance.
    
    This provides a singleton pattern for session management,
    ensuring consistency across the application.
    
    Returns:
        Global ConsultationManager instance
    """
    global _global_manager
    
    if _global_manager is None:
        # Get timeout from configuration
        config = get_config()
        timeout_minutes = getattr(config, 'consultation_timeout_minutes', 30)
        
        _global_manager = ConsultationManager(session_timeout_minutes=timeout_minutes)
        logger.info("Global consultation manager initialized")
    
    return _global_manager


def reset_consultation_manager() -> None:
    """
    Reset the global consultation manager.
    
    This is primarily used for testing and cleanup.
    In production, this should be used carefully as it
    will clear all active sessions.
    """
    global _global_manager
    
    if _global_manager:
        # Clean up all sessions
        _global_manager.cleanup_expired_sessions()
        logger.info("Consultation manager reset")
    
    _global_manager = None
