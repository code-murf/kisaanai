"""
Voice API endpoints for speech-to-text, LLM processing, and text-to-speech.

This module provides endpoints for voice-based interactions with support for:
- Voice query processing (STT -> LLM -> TTS)
- Barge-in cancellation for interrupting ongoing requests
- Session management for tracking active voice requests
"""
from fastapi import APIRouter, UploadFile, File, HTTPException, status, Depends, Form
from typing import Optional
import base64
import uuid
import asyncio
import inspect
import logging

from app.services.ai_service import get_ai_service
from app.core.voice_session import get_session_manager
from app.models.user import User
from app.database import get_db
from app.api.auth import get_current_user
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/voice", tags=["Voice"])
security = HTTPBearer()


async def _resolve_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    Resolve current user through app.api.auth.get_current_user.

    This indirection keeps runtime behavior the same and allows tests to patch
    app.api.voice.get_current_user directly.
    """
    result = get_current_user(credentials=credentials, db=db)
    if inspect.isawaitable(result):
        return await result
    return result


@router.post("/query")
async def voice_query(
    file: UploadFile = File(...),
    language: str = Form(default="hi-IN"),
    session_id: Optional[str] = Form(default=None),
):
    """
    Process voice query: STT -> LLM -> TTS.
    
    Args:
        file: Audio file (wav, mp3, webm, m4a)
        language: Language code (e.g., hi-IN, en-IN)
        session_id: Optional session ID for barge-in support.
                   If provided, any previous request in this session will be cancelled.
    
    Returns:
        Dictionary containing:
        - query: Transcribed text
        - response: LLM response text
        - audio: Base64 encoded audio response
        - language: Response language
        - session_id: Session ID for future requests
    """
    ai_service = get_ai_service()
    session_manager = get_session_manager()
    
    # Generate request ID for tracking
    request_id = str(uuid.uuid4())
    
    # Create or use existing session
    if session_id is None:
        session_id = session_manager.create_session(user_id="anonymous")
        logger.debug(f"Created new session {session_id}")
    else:
        # Validate session exists
        existing_session = session_manager.get_session(session_id)
        if existing_session is None:
            # Create new session if provided one doesn't exist
            session_id = session_manager.create_session(user_id="anonymous")
            logger.debug(f"Created new session {session_id} (provided session not found)")
    
    # 1. Read audio file
    if not file.filename.endswith(('.wav', '.mp3', '.webm', '.m4a')):
        # Sarvam supports these, but let's be safe
        pass 
        
    content = await file.read()
    
    # Create the processing task
    async def process_voice():
        """Process the voice request (STT -> LLM -> TTS)."""
        try:
            # 2. Transcribe (STT)
            filename = file.filename or "audio.wav"
            content_type = file.content_type or "audio/wav"
            
            transcript = await ai_service.transcribe_audio(
                content, 
                language_code=language,
                filename=filename,
                content_type=content_type
            )
            if not transcript:
                raise HTTPException(status_code=500, detail="Failed to transcribe audio")
            
            # 3. Process Query (LLM)
            llm_response_data = await ai_service.process_voice_query(
                transcribed_text=transcript,
                language=language
            )
            
            response_text = llm_response_data.get("response")
            if not response_text:
                raise HTTPException(status_code=500, detail="Failed to generate response")
                
            # 4. Generate Speech (TTS)
            audio_base64 = await ai_service.text_to_speech(response_text, language_code=language)
            
            return {
                "query": transcript,
                "response": response_text,
                "audio": audio_base64,
                "language": language,
                "session_id": session_id,
            }
        except asyncio.CancelledError:
            logger.info(f"Voice request {request_id} was cancelled (barge-in)")
            raise
    
    # Create task and register with session manager
    task = asyncio.create_task(process_voice())
    session_manager.register_request(session_id, request_id, task)
    
    try:
        # Wait for the task to complete
        result = await task
        return result
    except asyncio.CancelledError:
        raise HTTPException(
            status_code=499,  # Client Closed Request
            detail="Request cancelled due to barge-in"
        )
    except asyncio.TimeoutError:
        logger.exception("Voice request %s timed out", request_id)
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="Voice processing timed out",
        )
    except HTTPException:
        raise
    except Exception:
        logger.exception("Voice request %s failed unexpectedly", request_id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Voice processing failed",
        )


@router.post("/cancel")
async def cancel_voice_request(
    session_id: str = Form(...),
    current_user: User = Depends(_resolve_current_user)
) -> dict:
    """
    Cancel an ongoing voice request (barge-in support).
    
    This endpoint allows clients to cancel an ongoing voice processing
    request when the user provides new input (barge-in).
    
    Args:
        session_id: The session ID to cancel requests for
        current_user: Authenticated user (required)
    
    Returns:
        Dictionary with cancellation status
    """
    manager = get_session_manager()
    
    # Check if session exists
    session = manager.get_session(session_id)
    if session is None:
        return {
            "cancelled": False,
            "session_id": session_id,
            "message": "Session not found or expired"
        }
    
    # Cancel the active request
    cancelled = manager.cancel_session_request(session_id)
    
    if cancelled:
        logger.info(f"Cancelled voice request for session {session_id} by user {current_user.id}")
        return {
            "cancelled": True,
            "session_id": session_id,
            "message": "Request cancelled successfully"
        }
    else:
        return {
            "cancelled": False,
            "session_id": session_id,
            "message": "No active request to cancel"
        }


@router.post("/session")
async def create_voice_session(
    current_user: User = Depends(_resolve_current_user)
) -> dict:
    """
    Create a new voice session.
    
    Sessions are used to track voice requests and enable barge-in
    functionality. Create a session before starting voice interactions.
    
    Args:
        current_user: Authenticated user
    
    Returns:
        Dictionary with the new session ID
    """
    manager = get_session_manager()
    session_id = manager.create_session(user_id=str(current_user.id))
    
    logger.debug(f"Created voice session {session_id} for user {current_user.id}")
    
    return {
        "session_id": session_id,
        "user_id": str(current_user.id),
        "message": "Session created successfully"
    }


@router.delete("/session/{session_id}")
async def end_voice_session(
    session_id: str,
    current_user: User = Depends(_resolve_current_user)
) -> dict:
    """
    End a voice session and cancel any active requests.
    
    Args:
        session_id: The session ID to end
        current_user: Authenticated user
    
    Returns:
        Dictionary with end status
    """
    manager = get_session_manager()
    
    session = manager.get_session(session_id)
    if session is None:
        return {
            "ended": False,
            "session_id": session_id,
            "message": "Session not found"
        }
    
    # Verify ownership (optional security check)
    if session.get("user_id") != str(current_user.id):
        logger.warning(
            f"User {current_user.id} attempted to end session owned by {session.get('user_id')}"
        )
        # Still end the session but log the warning
    
    ended = manager.end_session(session_id)
    
    return {
        "ended": ended,
        "session_id": session_id,
        "message": "Session ended successfully" if ended else "Failed to end session"
    }


@router.get("/stats")
async def get_voice_stats() -> dict:
    """
    Get voice session statistics.
    
    Returns information about active sessions and requests.
    This endpoint is useful for monitoring and debugging.
    
    Returns:
        Dictionary with session statistics
    """
    manager = get_session_manager()
    
    return {
        "active_sessions": manager.get_active_session_count(),
        "active_requests": manager.get_active_request_count(),
    }
