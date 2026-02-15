import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

class TestHackathonFeatures:
    """
    Verification Suite for Phase 6 Features:
    1. Resource Optimization (Sustainability)
    2. Community Voice Feed (Social Value)
    """

    def test_resource_optimizer_potato(self):
        """Verify potato water needs calculation."""
        response = client.get("/api/v1/resources/optimize", params={
            "crop": "Potato",
            "acres": 1.0,
            "soil": "Loamy",
            "days_sowing": 45,
            "last_watered_days": 3
        })
        assert response.status_code == 200
        data = response.json()
        assert "water_liters" in data
        assert "fertilizer_recommendation" in data
        assert data["crop_health_status"] == "Good" 
        # Potato at 45 days is vegetative/tuber initiation
        assert "Nitrogen" in data["fertilizer_recommendation"] or "Potassium" in data["fertilizer_recommendation"]

    def test_resource_optimizer_stress(self):
        """Verify stress detection for delayed watering."""
        response = client.get("/api/v1/resources/optimize", params={
            "crop": "Rice",
            "acres": 2.0,
            "soil": "Sandy", # Sandy soil needs more water
            "days_sowing": 60,
            "last_watered_days": 8 # 8 days is high stress
        })
        assert response.status_code == 200
        data = response.json()
        assert data["crop_health_status"] == "Stress Risk"
        assert data["next_action"] == "Irrigate Immediately"

    def test_community_feed_upload(self):
        """Verify voice note upload logic."""
        # Create a dummy audio file
        files = {'audio': ('test_note.mp3', b'dummy_audio_content', 'audio/mpeg')}
        data = {
            'user_id': 'user_123',
            'user_name': 'Test Farmer',
            'location_lat': '28.61',
            'location_lng': '77.23',
            'tags': '["Test", "Market"]'
        }
        
        response = client.post("/api/v1/community/notes", files=files, data=data)
        assert response.status_code == 201
        note = response.json()
        assert note["user_name"] == "Test Farmer"
        assert len(note["tags"]) == 2
        assert note["audio_url"].startswith("/static/audio/")
        
        # Verify it appears in feed
        feed_response = client.get("/api/v1/community/notes", params={"lat": 28.61, "lng": 77.23})
        assert feed_response.status_code == 200
        feed = feed_response.json()
        assert any(n["id"] == note["id"] for n in feed)

    def test_community_like(self):
        """Verify liking a note."""
        # First upload
        files = {'audio': ('test_note_2.mp3', b'audio', 'audio/mpeg')}
        data = {
            'user_id': 'user_456',
            'user_name': 'Liker',
            'location_lat': '28.0',
            'location_lng': '77.0',
            'tags': '[]'
        }
        note = client.post("/api/v1/community/notes", files=files, data=data).json()
        
        # Then like
        like_response = client.post(f"/api/v1/community/notes/{note['id']}/like")
        assert like_response.status_code == 200
        updated_note = like_response.json()
        assert updated_note["likes"] == 1
