"""
Voice Session Manager for handling barge-in events and session management.

This module provides session management for voice API requests, enabling:
- Barge-in cancellation: Cancel ongoing requests when new input arrives
- Session tracking: Track active requests per user session
- Automatic cleanup: Remove expired sessions to prevent memory leaks
"""
from typing import Dict, Optional
import asyncio
from datetime import datetime, timedelta
import uuid
import logging

logger = logging.getLogger(__name__)


class VoiceSessionManager:
    """
    Manages voice sessions with barge-in support.
    
    Tracks active requests per session and cancels previous requests on new input.
    This enables "barge-in" functionality where users can interrupt ongoing
    voice processing by providing new input.
    
    Example:
        manager = VoiceSessionManager(session_timeout=300)
        
        # Create a session for a user
        session_id = manager.create_session(user_id="user123")
        
        # Register a request (automatically cancels any previous request)
        manager.register_request(session_id, request_id="req1", task=asyncio_task)
        
        # Cancel on barge-in
        cancelled = manager.cancel_session_request(session_id)
    """
    
    def __init__(self, session_timeout: int = 300):
        """
        Initialize the voice session manager.
        
        Args:
            session_timeout: Time in seconds before inactive sessions are expired.
                            Default is 300 seconds (5 minutes).
        """
        self._sessions: Dict[str, Dict] = {}
        self._session_timeout = session_timeout
        self._lock = asyncio.Lock()
    
    def create_session(self, user_id: str) -> str:
        """
        Create a new voice session for a user.
        
        Args:
            user_id: Unique identifier for the user
            
        Returns:
            session_id: Unique identifier for the created session
        """
        session_id = str(uuid.uuid4())
        now = datetime.utcnow()
        
        self._sessions[session_id] = {
            "user_id": user_id,
            "created_at": now,
            "last_activity": now,
            "active_request_id": None,
            "active_task": None,
        }
        
        logger.debug(f"Created voice session {session_id} for user {user_id}")
        return session_id
    
    def register_request(
        self, 
        session_id: str, 
        request_id: str, 
        task: asyncio.Task
    ) -> bool:
        """
        Register an active request for a session.
        
        If there's an existing active request for this session, it will be
        cancelled (barge-in behavior) before registering the new one.
        
        Args:
            session_id: The session identifier
            request_id: Unique identifier for this request
            task: The asyncio Task handling this request
            
        Returns:
            True if registration succeeded, False if session doesn't exist
        """
        if session_id not in self._sessions:
            logger.warning(f"Attempted to register request for unknown session {session_id}")
            return False
        
        session = self._sessions[session_id]
        
        # Cancel any existing active request (barge-in)
        if session["active_task"] is not None and not session["active_task"].done():
            logger.info(
                f"Cancelling previous request {session['active_request_id']} "
                f"for session {session_id} (barge-in)"
            )
            session["active_task"].cancel()
        
        # Register the new request
        session["active_request_id"] = request_id
        session["active_task"] = task
        session["last_activity"] = datetime.utcnow()
        
        logger.debug(f"Registered request {request_id} for session {session_id}")
        return True
    
    def cancel_session_request(self, session_id: str) -> bool:
        """
        Cancel the active request for a session (barge-in support).
        
        This is typically called when a user provides new input while
        a previous request is still being processed.
        
        Args:
            session_id: The session identifier
            
        Returns:
            True if a request was cancelled, False otherwise
        """
        if session_id not in self._sessions:
            logger.warning(f"Attempted to cancel request for unknown session {session_id}")
            return False
        
        session = self._sessions[session_id]
        
        if session["active_task"] is None or session["active_task"].done():
            logger.debug(f"No active request to cancel for session {session_id}")
            return False
        
        request_id = session["active_request_id"]
        logger.info(f"Cancelling request {request_id} for session {session_id}")
        
        session["active_task"].cancel()
        session["active_request_id"] = None
        session["active_task"] = None
        session["last_activity"] = datetime.utcnow()
        
        return True
    
    def get_session(self, session_id: str) -> Optional[Dict]:
        """
        Get session information.
        
        Args:
            session_id: The session identifier
            
        Returns:
            Session data dict or None if not found
        """
        return self._sessions.get(session_id)
    
    def end_session(self, session_id: str) -> bool:
        """
        End a session and cancel any active request.
        
        Args:
            session_id: The session identifier
            
        Returns:
            True if session was ended, False if not found
        """
        if session_id not in self._sessions:
            return False
        
        session = self._sessions[session_id]
        
        # Cancel any active request
        if session["active_task"] is not None and not session["active_task"].done():
            session["active_task"].cancel()
        
        del self._sessions[session_id]
        logger.debug(f"Ended session {session_id}")
        return True
    
    def cleanup_expired_sessions(self) -> int:
        """
        Remove expired sessions to free memory.
        
        Sessions are considered expired if they haven't had activity
        for longer than the session_timeout.
        
        Returns:
            Count of cleaned up sessions
        """
        now = datetime.utcnow()
        expired_threshold = now - timedelta(seconds=self._session_timeout)
        
        expired_sessions = [
            session_id
            for session_id, session in self._sessions.items()
            if session["last_activity"] < expired_threshold
        ]
        
        for session_id in expired_sessions:
            self.end_session(session_id)
        
        if expired_sessions:
            logger.info(f"Cleaned up {len(expired_sessions)} expired voice sessions")
        
        return len(expired_sessions)
    
    def get_active_session_count(self) -> int:
        """Get the number of active sessions."""
        return len(self._sessions)
    
    def get_active_request_count(self) -> int:
        """Get the number of sessions with active requests."""
        return sum(
            1 for session in self._sessions.values()
            if session["active_task"] is not None and not session["active_task"].done()
        )


# Global session manager instance
_session_manager: Optional[VoiceSessionManager] = None


def get_session_manager() -> VoiceSessionManager:
    """
    Get or create the global session manager.
    
    This singleton pattern ensures all voice requests share the same
    session manager for consistent barge-in behavior.
    
    Returns:
        The global VoiceSessionManager instance
    """
    global _session_manager
    if _session_manager is None:
        from app.config import settings
        timeout = getattr(settings, 'VOICE_SESSION_TIMEOUT', 300)
        _session_manager = VoiceSessionManager(session_timeout=timeout)
        logger.info(f"Initialized voice session manager with {timeout}s timeout")
    return _session_manager


def reset_session_manager() -> None:
    """
    Reset the global session manager.
    
    This is primarily useful for testing.
    """
    global _session_manager
    if _session_manager is not None:
        # Clean up all sessions
        for session_id in list(_session_manager._sessions.keys()):
            _session_manager.end_session(session_id)
    _session_manager = None
