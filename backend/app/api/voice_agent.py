from fastapi import APIRouter, HTTPException
from app.services.elevenlabs_service import elevenlabs_service

router = APIRouter()

@router.get("/agent-token")
async def get_agent_token():
    """
    Get a signed URL for connecting to the ElevenLabs Agent.
    This allows the frontend to connect via WebSocket without exposing the API key.
    """
    try:
        signed_url = elevenlabs_service.get_signed_url()
        return {"signed_url": signed_url}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
