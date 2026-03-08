import pytest
from pathlib import Path
from botocore.exceptions import ClientError
from fastapi.testclient import TestClient
from app.main import app
from app.api import diseases as diseases_api
from app.services.disease_service import DiseasePrediction, DiseaseService
from app.services.s3_service import S3Service

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

    def test_disease_diagnose_uses_local_storage_fallback_when_s3_fails(self, monkeypatch):
        """Diagnosis should still succeed and persist the image locally when S3 is unavailable."""

        async def fake_upload_image(*args, **kwargs):
            return {
                "success": True,
                "error": "NoSuchBucket",
                "url": "/static/uploads/crops/test/test_blight.png",
                "key": "uploads/crops/test/test_blight.png",
                "storage": "local",
            }

        async def fake_predict(self, image_bytes, filename):
            return DiseasePrediction(
                disease_name="Tomato Early Blight",
                confidence=0.91,
                treatment="Remove infected leaves and apply a recommended fungicide.",
                severity="Moderate",
            )

        async def fake_put_metric(*args, **kwargs):
            return None

        async def fake_put_metrics_batch(*args, **kwargs):
            return None

        monkeypatch.setattr(diseases_api.s3_service, "upload_image", fake_upload_image)
        monkeypatch.setattr(diseases_api.DiseaseService, "predict", fake_predict)
        monkeypatch.setattr(diseases_api.cloudwatch_service, "put_metric", fake_put_metric)
        monkeypatch.setattr(diseases_api.cloudwatch_service, "put_metrics_batch", fake_put_metrics_batch)

        test_image = Path(__file__).resolve().parents[1] / "test_blight.png"
        with test_image.open("rb") as image_file:
            response = client.post(
                "/api/v1/diseases/diagnose",
                files={"file": ("test_blight.png", image_file, "image/png")},
            )

        assert response.status_code == 200
        data = response.json()
        assert data["disease_name"] == "Tomato Early Blight"
        assert data["image_url"].endswith("/static/uploads/crops/test/test_blight.png")
        assert data["s3_key"] == "uploads/crops/test/test_blight.png"
        assert data["storage_mode"] == "local"
        assert data["confidence"] == pytest.approx(0.91)

    @pytest.mark.asyncio
    async def test_s3_service_falls_back_to_local_file_storage(self):
        """S3 service should store files locally when S3 returns NoSuchBucket."""

        class FakeS3Client:
            def put_object(self, **kwargs):
                raise ClientError(
                    {"Error": {"Code": "NoSuchBucket", "Message": "bucket missing"}},
                    "PutObject",
                )

        service = S3Service(
            aws_access_key_id="key",
            aws_secret_access_key="secret",
            bucket_name="missing-bucket",
            local_upload_dir="test-uploads",
        )
        service._client = FakeS3Client()

        result = await service.upload_image(b"fake-image-bytes", "leaf sample.jpg")

        assert result["success"] is True
        assert result["storage"] == "local"
        assert result["url"].startswith("/static/test-uploads/crops/")
        saved_file = Path(__file__).resolve().parents[1] / "static" / result["key"]
        assert saved_file.exists()

    @pytest.mark.asyncio
    async def test_disease_service_uses_offline_filename_fallback(self):
        """Disease service should still return a diagnosis in restricted environments."""

        service = DiseaseService()
        service._bedrock = None
        service._token = None

        result = await service.predict(b"image-bytes", "tomato-late_blight-web.jpg")

        assert result.disease_name == "Tomato Late Blight"
        assert result.confidence == pytest.approx(0.85)
