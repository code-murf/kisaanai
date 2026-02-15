from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from typing import List
from app.services.community_service import CommunityService
from app.schemas.community import AudioNote, AudioNoteCreate
import json

router = APIRouter(prefix="/community", tags=["Community"])
service = CommunityService()

@router.get("/notes", response_model=List[AudioNote])
async def get_notes(lat: float = 28.61, lng: float = 77.23, radius: float = 50):
    """Get voice notes from nearby farmers."""
    return await service.get_notes(lat, lng, radius)

@router.post("/notes", response_model=AudioNote, status_code=status.HTTP_201_CREATED)
async def create_note(
    audio: UploadFile = File(...),
    user_id: str = Form(...),
    user_name: str = Form(...),
    location_lat: float = Form(...),
    location_lng: float = Form(...),
    tags: str = Form("[]") # JSON string
):
    """Upload a new voice note."""
    try:
        tag_list = json.loads(tags)
    except:
        tag_list = []
        
    note_data = AudioNoteCreate(
        user_id=user_id,
        user_name=user_name,
        location_lat=location_lat,
        location_lng=location_lng,
        tags=tag_list
    )
    
    return await service.create_note(note_data, audio)

@router.post("/notes/{note_id}/like", response_model=AudioNote)
async def like_note(note_id: str):
    """Like a voice note."""
    note = await service.like_note(note_id)
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    return note
