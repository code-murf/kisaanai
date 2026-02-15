import os
import requests
from app.config import settings

class ElevenLabsService:
    BASE_URL = "https://api.elevenlabs.io/v1/convai"

    def __init__(self):
        self.api_key = settings.ELEVENLABS_API_KEY
        self.agent_id = settings.ELEVENLABS_AGENT_ID
    
    def get_signed_url(self) -> str:
        """
        Get a signed URL for the frontend to connect to the agent via WebSocket.
        """
        url = f"{self.BASE_URL}/conversation/get_signed_url"
        params = {"agent_id": self.agent_id}
        headers = {"xi-api-key": self.api_key}
        
        try:
            response = requests.get(url, params=params, headers=headers)
            response.raise_for_status()
            data = response.json()
            return data.get("signed_url")
        except requests.exceptions.RequestException as e:
            print(f"Error getting signed URL: {e}")
            raise Exception("Failed to get signed URL from ElevenLabs")

elevenlabs_service = ElevenLabsService()
