import shutil
import os
from typing import List, Optional
from uuid import uuid4
from fastapi import UploadFile
from app.schemas.community import AudioNote, AudioNoteCreate

# In-memory storage for hackathon demo
# In production, this would be a database
NOTE_STORE: List[AudioNote] = []

class CommunityService:
    def __init__(self):
        self.upload_dir = "static/audio"
        os.makedirs(self.upload_dir, exist_ok=True)

    async def create_note(self, note_data: AudioNoteCreate, audio_file: UploadFile) -> AudioNote:
        # Save audio file
        file_ext = audio_file.filename.split('.')[-1]
        file_name = f"{uuid4()}.{file_ext}"
        file_path = os.path.join(self.upload_dir, file_name)
        
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(audio_file.file, buffer)
            
        # Create note object
        note = AudioNote(
            **note_data.model_dump(),
            audio_url=f"/static/audio/{file_name}",
            id=uuid4()
        )
        
        NOTE_STORE.append(note)
        return note

    async def get_notes(self, lat: float, lng: float, radius_km: float = 50.0) -> List[AudioNote]:
        # Mock geo-filtering: Return all notes for now, or filter simply
        # In real app, use PostGIS or Haversine formula
        return sorted(NOTE_STORE, key=lambda x: x.created_at, reverse=True)

    async def like_note(self, note_id: str) -> Optional[AudioNote]:
        for note in NOTE_STORE:
            if str(note.id) == note_id:
                note.likes += 1
                return note
        return None
