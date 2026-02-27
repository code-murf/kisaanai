import json
import os
import shutil
from pathlib import Path
from typing import List, Optional
from uuid import uuid4

from fastapi import UploadFile

from app.schemas.community import AudioNote, AudioNoteCreate

NOTE_STORE: List[AudioNote] = []


class CommunityService:
    def __init__(self):
        self.upload_dir = Path('static/audio')
        self.upload_dir.mkdir(parents=True, exist_ok=True)

        self.data_path = Path('static/community_notes.json')
        global NOTE_STORE
        if not NOTE_STORE:
            NOTE_STORE.extend(self._load_notes())
        self._notes = NOTE_STORE

    def _load_notes(self) -> List[AudioNote]:
        if not self.data_path.exists():
            return []

        try:
            payload = json.loads(self.data_path.read_text(encoding='utf-8'))
            if not isinstance(payload, list):
                return []
            return [AudioNote.model_validate(item) for item in payload]
        except Exception:
            return []

    def _save_notes(self) -> None:
        payload = [note.model_dump(mode='json') for note in self._notes]
        self.data_path.parent.mkdir(parents=True, exist_ok=True)
        self.data_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding='utf-8')

    async def create_note(self, note_data: AudioNoteCreate, audio_file: UploadFile) -> AudioNote:
        file_ext = (audio_file.filename or 'audio.mp3').split('.')[-1]
        file_name = f"{uuid4()}.{file_ext}"
        file_path = self.upload_dir / file_name

        with file_path.open('wb') as buffer:
            shutil.copyfileobj(audio_file.file, buffer)

        note = AudioNote(
            **note_data.model_dump(),
            audio_url=f"/static/audio/{file_name}",
            id=uuid4(),
        )

        self._notes.append(note)
        self._save_notes()
        return note

    async def get_notes(self, lat: float, lng: float, radius_km: float = 50.0) -> List[AudioNote]:
        # Return newest notes first.
        return sorted(self._notes, key=lambda x: x.created_at, reverse=True)

    async def like_note(self, note_id: str) -> Optional[AudioNote]:
        for note in self._notes:
            if str(note.id) == note_id:
                note.likes += 1
                self._save_notes()
                return note
        return None
