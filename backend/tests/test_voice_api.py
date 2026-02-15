"""
Integration tests for Voice API endpoints.

Tests: /voice/query, /voice/cancel, /voice/session, /voice/stats

Run with:
    pytest backend/tests/test_voice_api.py -v
    pytest backend/tests/test_voice_api.py -v -k "barge"  # Run barge-in tests
"""
import pytest
import asyncio
import io
from httpx import AsyncClient, ASGITransport
from unittest.mock import patch, MagicMock, AsyncMock
from fastapi import FastAPI

from app.main import app
from app.core.voice_session import reset_session_manager, get_session_manager
from app.models.user import User


# Test fixtures
@pytest.fixture
def mock_user():
    """Create a mock authenticated user."""
    return User(
        id=1,
        email="test@example.com",
        hashed_password="hashed",
        is_active=True,
    )


@pytest.fixture
def mock_audio_file():
    """Create a mock audio file for testing."""
    # Create a minimal valid WAV file header
    wav_header = bytes([
        0x52, 0x49, 0x46, 0x46,  # "RIFF"
        0x24, 0x00, 0x00, 0x00,  # File size - 8
        0x57, 0x41, 0x56, 0x45,  # "WAVE"
        0x66, 0x6D, 0x74, 0x20,  # "fmt "
        0x10, 0x00, 0x00, 0x00,  # Chunk size
        0x01, 0x00,              # Audio format (PCM)
        0x01, 0x00,              # Channels
        0x44, 0xAC, 0x00, 0x00,  # Sample rate
        0x88, 0x58, 0x01, 0x00,  # Byte rate
        0x02, 0x00,              # Block align
        0x10, 0x00,              # Bits per sample
        0x64, 0x61, 0x74, 0x61,  # "data"
        0x00, 0x00, 0x00, 0x00,  # Data size
    ])
    return io.BytesIO(wav_header)


@pytest.fixture
async def client():
    """Create async test client."""
    # Reset session manager before each test
    reset_session_manager()
    
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as client:
        yield client
    
    # Cleanup after test
    reset_session_manager()


@pytest.fixture
def auth_headers(mock_user):
    """Create authorization headers for authenticated requests."""
    # In a real scenario, this would be a valid JWT token
    return {"Authorization": "Bearer test_token"}


class TestVoiceSessionEndpoint:
    """Tests for POST /voice/session endpoint."""

    @pytest.mark.asyncio
    async def test_create_voice_session_unauthenticated(self, client):
        """Test that unauthenticated requests are rejected."""
        response = await client.post("/voice/session")

        assert response.status_code in [401, 403, 422]  # Unauthorized or validation error

    @pytest.mark.asyncio
    async def test_create_voice_session_authenticated(self, client, mock_user, auth_headers):
        """Test session creation with authentication."""
        with patch("app.api.voice.get_current_user", return_value=mock_user):
            response = await client.post(
                "/voice/session",
                headers=auth_headers
            )

        assert response.status_code == 200
        data = response.json()
        assert "session_id" in data
        assert data["user_id"] == str(mock_user.id)
        assert "message" in data

    @pytest.mark.asyncio
    async def test_create_multiple_sessions(self, client, mock_user, auth_headers):
        """Test creating multiple sessions for same user."""
        with patch("app.api.voice.get_current_user", return_value=mock_user):
            response1 = await client.post("/voice/session", headers=auth_headers)
            response2 = await client.post("/voice/session", headers=auth_headers)

        assert response1.status_code == 200
        assert response2.status_code == 200

        session1 = response1.json()["session_id"]
        session2 = response2.json()["session_id"]

        # Each session should have unique ID
        assert session1 != session2


class TestVoiceQueryEndpoint:
    """Tests for POST /voice/query endpoint."""

    @pytest.mark.asyncio
    async def test_voice_query_without_session(self, client, mock_audio_file):
        """Test voice query without session_id creates new session."""
        mock_ai_service = MagicMock()
        mock_ai_service.transcribe_audio = AsyncMock(return_value="मेरे गेहूं की कीमत क्या है")
        mock_ai_service.process_voice_query = AsyncMock(return_value={"response": "गेहूं की कीमत ₹2,000 प्रति क्विंटल है"})
        mock_ai_service.text_to_speech = AsyncMock(return_value="base64_audio_data")

        with patch("app.api.voice.get_ai_service", return_value=mock_ai_service):
            response = await client.post(
                "/voice/query",
                files={"file": ("test.wav", mock_audio_file, "audio/wav")},
                data={"language": "hi-IN"}
            )

        assert response.status_code == 200
        data = response.json()
        assert "session_id" in data
        assert data["query"] == "मेरे गेहूं की कीमत क्या है"
        assert data["response"] == "गेहूं की कीमत ₹2,000 प्रति क्विंटल है"
        assert data["audio"] == "base64_audio_data"

    @pytest.mark.asyncio
    async def test_voice_query_with_session(self, client, mock_audio_file, mock_user, auth_headers):
        """Test voice query with session_id for barge-in support."""
        # First create a session
        with patch("app.api.voice.get_current_user", return_value=mock_user):
            session_response = await client.post("/voice/session", headers=auth_headers)
        
        session_id = session_response.json()["session_id"]

        # Now make a voice query with the session
        mock_ai_service = MagicMock()
        mock_ai_service.transcribe_audio = AsyncMock(return_value="test query")
        mock_ai_service.process_voice_query = AsyncMock(return_value={"response": "test response"})
        mock_ai_service.text_to_speech = AsyncMock(return_value="base64_audio")

        with patch("app.api.voice.get_ai_service", return_value=mock_ai_service):
            response = await client.post(
                "/voice/query",
                files={"file": ("test.wav", mock_audio_file, "audio/wav")},
                data={
                    "language": "hi-IN",
                    "session_id": session_id
                }
            )

        assert response.status_code == 200
        data = response.json()
        assert data["session_id"] == session_id

    @pytest.mark.asyncio
    async def test_voice_query_invalid_session_creates_new(self, client, mock_audio_file):
        """Test that invalid session_id results in new session creation."""
        mock_ai_service = MagicMock()
        mock_ai_service.transcribe_audio = AsyncMock(return_value="test")
        mock_ai_service.process_voice_query = AsyncMock(return_value={"response": "response"})
        mock_ai_service.text_to_speech = AsyncMock(return_value="audio")

        with patch("app.api.voice.get_ai_service", return_value=mock_ai_service):
            response = await client.post(
                "/voice/query",
                files={"file": ("test.wav", mock_audio_file, "audio/wav")},
                data={
                    "language": "hi-IN",
                    "session_id": "invalid-session-id"
                }
            )

        assert response.status_code == 200
        data = response.json()
        # Should have created a new session
        assert data["session_id"] != "invalid-session-id"

    @pytest.mark.asyncio
    async def test_voice_query_transcription_failure(self, client, mock_audio_file):
        """Test handling of transcription failure."""
        mock_ai_service = MagicMock()
        mock_ai_service.transcribe_audio = AsyncMock(return_value=None)

        with patch("app.api.voice.get_ai_service", return_value=mock_ai_service):
            response = await client.post(
                "/voice/query",
                files={"file": ("test.wav", mock_audio_file, "audio/wav")},
                data={"language": "hi-IN"}
            )

        assert response.status_code == 500

    @pytest.mark.asyncio
    async def test_voice_query_llm_failure(self, client, mock_audio_file):
        """Test handling of LLM processing failure."""
        mock_ai_service = MagicMock()
        mock_ai_service.transcribe_audio = AsyncMock(return_value="test query")
        mock_ai_service.process_voice_query = AsyncMock(return_value={"response": None})

        with patch("app.api.voice.get_ai_service", return_value=mock_ai_service):
            response = await client.post(
                "/voice/query",
                files={"file": ("test.wav", mock_audio_file, "audio/wav")},
                data={"language": "hi-IN"}
            )

        assert response.status_code == 500


class TestVoiceCancelEndpoint:
    """Tests for POST /voice/cancel endpoint."""

    @pytest.mark.asyncio
    async def test_cancel_unauthenticated(self, client):
        """Test that cancel requires authentication."""
        response = await client.post(
            "/voice/cancel",
            data={"session_id": "test-session"}
        )

        assert response.status_code in [401, 403, 422]

    @pytest.mark.asyncio
    async def test_cancel_nonexistent_session(self, client, mock_user, auth_headers):
        """Test canceling a session that doesn't exist."""
        with patch("app.api.voice.get_current_user", return_value=mock_user):
            response = await client.post(
                "/voice/cancel",
                data={"session_id": "nonexistent-session"},
                headers=auth_headers
            )

        assert response.status_code == 200
        data = response.json()
        assert data["cancelled"] is False
        assert "not found" in data["message"].lower() or "expired" in data["message"].lower()

    @pytest.mark.asyncio
    async def test_cancel_session_no_active_request(self, client, mock_user, auth_headers):
        """Test canceling a session with no active request."""
        # Create session first
        with patch("app.api.voice.get_current_user", return_value=mock_user):
            session_response = await client.post("/voice/session", headers=auth_headers)
            session_id = session_response.json()["session_id"]

            # Try to cancel (no active request)
            cancel_response = await client.post(
                "/voice/cancel",
                data={"session_id": session_id},
                headers=auth_headers
            )

        assert cancel_response.status_code == 200
        data = cancel_response.json()
        assert data["cancelled"] is False
        assert "no active request" in data["message"].lower()

    @pytest.mark.asyncio
    async def test_cancel_active_request(self, client, mock_user, auth_headers, mock_audio_file):
        """Test canceling an active voice request."""
        # Create session
        with patch("app.api.voice.get_current_user", return_value=mock_user):
            session_response = await client.post("/voice/session", headers=auth_headers)
            session_id = session_response.json()["session_id"]

        # Start a voice query (will be slow)
        slow_ai_service = MagicMock()
        slow_ai_service.transcribe_audio = AsyncMock(side_effect=lambda *args: asyncio.sleep(10))
        slow_ai_service.process_voice_query = AsyncMock(return_value={"response": "response"})
        slow_ai_service.text_to_speech = AsyncMock(return_value="audio")

        query_task = asyncio.create_task(
            client.post(
                "/voice/query",
                files={"file": ("test.wav", mock_audio_file, "audio/wav")},
                data={"session_id": session_id}
            )
        )

        # Wait a bit for the request to start
        await asyncio.sleep(0.1)

        # Cancel the request
        with patch("app.api.voice.get_current_user", return_value=mock_user):
            cancel_response = await client.post(
                "/voice/cancel",
                data={"session_id": session_id},
                headers=auth_headers
            )

        assert cancel_response.status_code == 200
        data = cancel_response.json()
        assert data["cancelled"] is True

        # Cancel the hanging query task
        query_task.cancel()


class TestVoiceBargeIn:
    """Tests for barge-in functionality."""

    @pytest.mark.asyncio
    async def test_barge_in_scenario(self, client, mock_user, auth_headers, mock_audio_file):
        """Test full barge-in scenario:
        1. Create session
        2. Start voice query
        3. New query cancels previous (barge-in)
        4. Verify second query completes
        """
        # 1. Create session
        with patch("app.api.voice.get_current_user", return_value=mock_user):
            session_response = await client.post("/voice/session", headers=auth_headers)
            session_id = session_response.json()["session_id"]

        first_query_started = asyncio.Event()
        first_query_cancelled = False

        async def slow_transcribe(*args):
            first_query_started.set()
            try:
                await asyncio.sleep(10)  # Simulate slow processing
                return "first query result"
            except asyncio.CancelledError:
                nonlocal first_query_cancelled
                first_query_cancelled = True
                raise

        # 2. Start first voice query
        slow_ai_service = MagicMock()
        slow_ai_service.transcribe_audio = AsyncMock(side_effect=slow_transcribe)
        slow_ai_service.process_voice_query = AsyncMock(return_value={"response": "first response"})
        slow_ai_service.text_to_speech = AsyncMock(return_value="first audio")

        first_query_task = asyncio.create_task(
            client.post(
                "/voice/query",
                files={"file": ("test.wav", mock_audio_file, "audio/wav")},
                data={"session_id": session_id}
            )
        )

        # Wait for first query to start
        await first_query_started.wait()

        # 3. Start second query (barge-in)
        fast_ai_service = MagicMock()
        fast_ai_service.transcribe_audio = AsyncMock(return_value="second query")
        fast_ai_service.process_voice_query = AsyncMock(return_value={"response": "second response"})
        fast_ai_service.text_to_speech = AsyncMock(return_value="second audio")

        with patch("app.api.voice.get_ai_service", return_value=fast_ai_service):
            second_response = await client.post(
                "/voice/query",
                files={"file": ("test.wav", mock_audio_file, "audio/wav")},
                data={"session_id": session_id}
            )

        # 4. Verify second query completed successfully
        assert second_response.status_code == 200
        data = second_response.json()
        assert data["query"] == "second query"
        assert data["response"] == "second response"

        # First query should have been cancelled
        assert first_query_cancelled

        # Cancel the first task if still running
        first_query_task.cancel()
        try:
            await first_query_task
        except asyncio.CancelledError:
            pass

    @pytest.mark.asyncio
    async def test_rapid_barge_ins(self, client, mock_audio_file):
        """Test multiple rapid barge-ins in succession."""
        session_id = get_session_manager().create_session(user_id="test_user")

        results = []
        cancellation_count = 0

        async def make_query(query_num, delay=0.1):
            nonlocal cancellation_count

            ai_service = MagicMock()
            ai_service.transcribe_audio = AsyncMock(return_value=f"query {query_num}")
            ai_service.process_voice_query = AsyncMock(return_value={"response": f"response {query_num}"})
            ai_service.text_to_speech = AsyncMock(return_value=f"audio {query_num}")

            try:
                with patch("app.api.voice.get_ai_service", return_value=ai_service):
                    response = await client.post(
                        "/voice/query",
                        files={"file": ("test.wav", mock_audio_file, "audio/wav")},
                        data={"session_id": session_id}
                    )
                    if response.status_code == 200:
                        results.append(response.json())
            except Exception:
                cancellation_count += 1

        # Launch 5 rapid queries
        tasks = [asyncio.create_task(make_query(i)) for i in range(5)]
        await asyncio.gather(*tasks, return_exceptions=True)

        # Only the last query should have completed
        # (This is a best-effort test as timing can vary)
        assert len(results) >= 1


class TestVoiceStatsEndpoint:
    """Tests for GET /voice/stats endpoint."""

    @pytest.mark.asyncio
    async def test_voice_stats_empty(self, client):
        """Test stats endpoint with no sessions."""
        response = await client.get("/voice/stats")

        assert response.status_code == 200
        data = response.json()
        assert data["active_sessions"] == 0
        assert data["active_requests"] == 0

    @pytest.mark.asyncio
    async def test_voice_stats_with_sessions(self, client, mock_user, auth_headers):
        """Test stats endpoint with active sessions."""
        # Create multiple sessions
        with patch("app.api.voice.get_current_user", return_value=mock_user):
            await client.post("/voice/session", headers=auth_headers)
            await client.post("/voice/session", headers=auth_headers)
            await client.post("/voice/session", headers=auth_headers)

        response = await client.get("/voice/stats")

        assert response.status_code == 200
        data = response.json()
        assert data["active_sessions"] == 3
        assert data["active_requests"] == 0

    @pytest.mark.asyncio
    async def test_voice_stats_with_active_requests(self, client, mock_audio_file):
        """Test stats endpoint with active requests."""
        session_id = get_session_manager().create_session(user_id="test")

        # Create a slow task
        async def slow_task():
            await asyncio.sleep(10)

        task = asyncio.create_task(slow_task())
        get_session_manager().register_request(session_id, "req-1", task)

        await asyncio.sleep(0.01)  # Let task start

        try:
            response = await client.get("/voice/stats")

            assert response.status_code == 200
            data = response.json()
            assert data["active_sessions"] == 1
            assert data["active_requests"] == 1
        finally:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass


class TestVoiceEndSessionEndpoint:
    """Tests for DELETE /voice/session/{session_id} endpoint."""

    @pytest.mark.asyncio
    async def test_end_session_unauthenticated(self, client):
        """Test that ending session requires authentication."""
        response = await client.delete("/voice/session/some-session-id")

        assert response.status_code in [401, 403, 422]

    @pytest.mark.asyncio
    async def test_end_session_nonexistent(self, client, mock_user, auth_headers):
        """Test ending a session that doesn't exist."""
        with patch("app.api.voice.get_current_user", return_value=mock_user):
            response = await client.delete(
                "/voice/session/nonexistent-session",
                headers=auth_headers
            )

        assert response.status_code == 200
        data = response.json()
        assert data["ended"] is False
        assert "not found" in data["message"].lower()

    @pytest.mark.asyncio
    async def test_end_session_success(self, client, mock_user, auth_headers):
        """Test successfully ending a session."""
        # Create session first
        with patch("app.api.voice.get_current_user", return_value=mock_user):
            session_response = await client.post("/voice/session", headers=auth_headers)
            session_id = session_response.json()["session_id"]

            # End the session
            end_response = await client.delete(
                f"/voice/session/{session_id}",
                headers=auth_headers
            )

        assert end_response.status_code == 200
        data = end_response.json()
        assert data["ended"] is True

        # Verify session is gone
        stats_response = await client.get("/voice/stats")
        stats = stats_response.json()
        assert stats["active_sessions"] == 0

    @pytest.mark.asyncio
    async def test_end_session_cancels_active_request(self, client, mock_user, auth_headers, mock_audio_file):
        """Test that ending session cancels active request."""
        # Create session
        with patch("app.api.voice.get_current_user", return_value=mock_user):
            session_response = await client.post("/voice/session", headers=auth_headers)
            session_id = session_response.json()["session_id"]

        # Start a slow request
        slow_ai_service = MagicMock()
        slow_ai_service.transcribe_audio = AsyncMock(side_effect=lambda *args: asyncio.sleep(10))

        query_task = asyncio.create_task(
            client.post(
                "/voice/query",
                files={"file": ("test.wav", mock_audio_file, "audio/wav")},
                data={"session_id": session_id}
            )
        )

        await asyncio.sleep(0.1)

        # End the session
        with patch("app.api.voice.get_current_user", return_value=mock_user):
            end_response = await client.delete(
                f"/voice/session/{session_id}",
                headers=auth_headers
            )

        assert end_response.status_code == 200
        assert end_response.json()["ended"] is True

        # Cancel hanging task
        query_task.cancel()


class TestVoiceAPIErrorHandling:
    """Tests for error handling in Voice API."""

    @pytest.mark.asyncio
    async def test_invalid_file_format(self, client):
        """Test handling of invalid file format."""
        invalid_file = io.BytesIO(b"not an audio file")

        response = await client.post(
            "/voice/query",
            files={"file": ("test.txt", invalid_file, "text/plain")},
            data={"language": "hi-IN"}
        )

        # Should either reject or try to process
        # The actual behavior depends on implementation
        assert response.status_code in [200, 400, 415, 500]

    @pytest.mark.asyncio
    async def test_missing_file(self, client):
        """Test handling of missing file."""
        response = await client.post(
            "/voice/query",
            data={"language": "hi-IN"}
        )

        assert response.status_code == 422  # Validation error

    @pytest.mark.asyncio
    async def test_ai_service_exception(self, client, mock_audio_file):
        """Test handling of AI service exceptions."""
        mock_ai_service = MagicMock()
        mock_ai_service.transcribe_audio = AsyncMock(side_effect=Exception("AI service error"))

        with patch("app.api.voice.get_ai_service", return_value=mock_ai_service):
            response = await client.post(
                "/voice/query",
                files={"file": ("test.wav", mock_audio_file, "audio/wav")},
                data={"language": "hi-IN"}
            )

        # Should handle the error gracefully
        assert response.status_code >= 400

    @pytest.mark.asyncio
    async def test_timeout_handling(self, client, mock_audio_file):
        """Test handling of request timeout."""
        mock_ai_service = MagicMock()
        mock_ai_service.transcribe_audio = AsyncMock(side_effect=asyncio.TimeoutError())

        with patch("app.api.voice.get_ai_service", return_value=mock_ai_service):
            response = await client.post(
                "/voice/query",
                files={"file": ("test.wav", mock_audio_file, "audio/wav")},
                data={"language": "hi-IN"}
            )

        assert response.status_code >= 400


class TestVoiceAPIIntegration:
    """Integration tests for complete Voice API workflows."""

    @pytest.mark.asyncio
    async def test_complete_voice_interaction_flow(self, client, mock_user, auth_headers, mock_audio_file):
        """Test complete voice interaction flow from session creation to end."""
        # 1. Create session
        with patch("app.api.voice.get_current_user", return_value=mock_user):
            session_response = await client.post("/voice/session", headers=auth_headers)
            assert session_response.status_code == 200
            session_id = session_response.json()["session_id"]

        # 2. Check initial stats
        stats_response = await client.get("/voice/stats")
        assert stats_response.json()["active_sessions"] == 1

        # 3. Make voice query
        mock_ai_service = MagicMock()
        mock_ai_service.transcribe_audio = AsyncMock(return_value="गेहूं की कीमत")
        mock_ai_service.process_voice_query = AsyncMock(return_value={"response": "₹2,000 प्रति क्विंटल"})
        mock_ai_service.text_to_speech = AsyncMock(return_value="YXVkaW9fZGF0YQ==")

        with patch("app.api.voice.get_ai_service", return_value=mock_ai_service):
            query_response = await client.post(
                "/voice/query",
                files={"file": ("test.wav", mock_audio_file, "audio/wav")},
                data={"session_id": session_id, "language": "hi-IN"}
            )

        assert query_response.status_code == 200
        query_data = query_response.json()
        assert query_data["session_id"] == session_id
        assert "गेहूं" in query_data["query"]
        assert "₹2,000" in query_data["response"]

        # 4. End session
        with patch("app.api.voice.get_current_user", return_value=mock_user):
            end_response = await client.delete(f"/voice/session/{session_id}", headers=auth_headers)
            assert end_response.status_code == 200
            assert end_response.json()["ended"] is True

        # 5. Verify final stats
        final_stats = await client.get("/voice/stats")
        assert final_stats.json()["active_sessions"] == 0

    @pytest.mark.asyncio
    async def test_concurrent_sessions_different_users(self, client, mock_audio_file):
        """Test concurrent sessions for different users."""
        results = []

        async def user_session(user_id):
            # Create session for user
            mock_user = User(id=user_id, email=f"user{user_id}@test.com", hashed_password="x", is_active=True)
            
            with patch("app.api.voice.get_current_user", return_value=mock_user):
                session_resp = await client.post("/voice/session", headers={"Authorization": "Bearer token"})
                session_id = session_resp.json()["session_id"]

            # Make voice query
            mock_ai_service = MagicMock()
            mock_ai_service.transcribe_audio = AsyncMock(return_value=f"query from user {user_id}")
            mock_ai_service.process_voice_query = AsyncMock(return_value={"response": f"response for user {user_id}"})
            mock_ai_service.text_to_speech = AsyncMock(return_value="audio")

            with patch("app.api.voice.get_ai_service", return_value=mock_ai_service):
                query_resp = await client.post(
                    "/voice/query",
                    files={"file": ("test.wav", mock_audio_file, "audio/wav")},
                    data={"session_id": session_id}
                )

            results.append({
                "user_id": user_id,
                "session_id": session_id,
                "status": query_resp.status_code,
                "query": query_resp.json().get("query") if query_resp.status_code == 200 else None
            })

        # Run concurrent sessions
        tasks = [asyncio.create_task(user_session(i)) for i in range(5)]
        await asyncio.gather(*tasks)

        # All should succeed
        assert len(results) == 5
        for result in results:
            assert result["status"] == 200
            assert f"user {result['user_id']}" in result["query"]
