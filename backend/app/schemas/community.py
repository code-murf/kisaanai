from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from uuid import UUID, uuid4

class AudioNoteBase(BaseModel):
    user_id: str
    user_name: str
    location_lat: float
    location_lng: float
    tags: List[str] = []

class AudioNoteCreate(AudioNoteBase):
    pass

class AudioNote(AudioNoteBase):
    id: UUID = Field(default_factory=uuid4)
    audio_url: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    likes: int = 0
    is_helpful: bool = False

    class Config:
        from_attributes = True
