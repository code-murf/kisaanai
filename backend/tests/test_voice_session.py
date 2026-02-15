"""
Unit tests for VoiceSessionManager barge-in functionality.

Tests: session creation, request registration, cancellation, cleanup.

Run with:
    pytest backend/tests/test_voice_session.py -v
    pytest backend/tests/test_voice_session.py -v -k "barge_in"  # Run specific tests
"""
import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import MagicMock, AsyncMock, patch

from app.core.voice_session import (
    VoiceSessionManager,
    get_session_manager,
    reset_session_manager,
)


class TestVoiceSessionManager:
    """Test suite for VoiceSessionManager barge-in functionality."""

    @pytest.fixture
    def manager(self):
        """Create fresh session manager for each test."""
        return VoiceSessionManager(session_timeout=60)

    @pytest.fixture
    def manager_with_short_timeout(self):
        """Create session manager with short timeout for expiry tests."""
        return VoiceSessionManager(session_timeout=1)

    # ==================== Session Creation Tests ====================

    def test_create_session(self, manager):
        """Test session creation returns valid session ID."""
        session_id = manager.create_session(user_id="user123")

        assert session_id is not None
        assert isinstance(session_id, str)
        assert len(session_id) == 36  # UUID format

    def test_create_session_stores_user_id(self, manager):
        """Test that session stores user_id correctly."""
        session_id = manager.create_session(user_id="user456")
        session = manager.get_session(session_id)

        assert session is not None
        assert session["user_id"] == "user456"

    def test_create_session_initializes_empty_request(self, manager):
        """Test that new session has no active request."""
        session_id = manager.create_session(user_id="user123")
        session = manager.get_session(session_id)

        assert session["active_request_id"] is None
        assert session["active_task"] is None

    def test_create_session_sets_timestamps(self, manager):
        """Test that session timestamps are set correctly."""
        before = datetime.utcnow()
        session_id = manager.create_session(user_id="user123")
        after = datetime.utcnow()

        session = manager.get_session(session_id)

        assert before <= session["created_at"] <= after
        assert before <= session["last_activity"] <= after

    def test_create_multiple_sessions(self, manager):
        """Test creating multiple sessions for different users."""
        session_id_1 = manager.create_session(user_id="user1")
        session_id_2 = manager.create_session(user_id="user2")
        session_id_3 = manager.create_session(user_id="user3")

        assert session_id_1 != session_id_2 != session_id_3
        assert manager.get_active_session_count() == 3

    # ==================== Request Registration Tests ====================

    @pytest.mark.asyncio
    async def test_register_request(self, manager):
        """Test request registration for a session."""
        session_id = manager.create_session(user_id="user123")

        # Create a mock task
        async def mock_task():
            await asyncio.sleep(10)

        task = asyncio.create_task(mock_task())
        request_id = "req-001"

        result = manager.register_request(session_id, request_id, task)

        assert result is True
        session = manager.get_session(session_id)
        assert session["active_request_id"] == request_id
        assert session["active_task"] == task

        # Cleanup
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass

    @pytest.mark.asyncio
    async def test_register_request_updates_activity(self, manager):
        """Test that registering a request updates last_activity."""
        session_id = manager.create_session(user_id="user123")
        original_activity = manager.get_session(session_id)["last_activity"]

        # Wait a bit to ensure time difference
        await asyncio.sleep(0.01)

        async def mock_task():
            await asyncio.sleep(10)

        task = asyncio.create_task(mock_task())
        manager.register_request(session_id, "req-001", task)

        new_activity = manager.get_session(session_id)["last_activity"]
        assert new_activity > original_activity

        # Cleanup
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass

    @pytest.mark.asyncio
    async def test_register_request_nonexistent_session(self, manager):
        """Test registering request for non-existent session fails."""
        async def mock_task():
            await asyncio.sleep(10)

        task = asyncio.create_task(mock_task())
        try:
            result = manager.register_request("nonexistent-session", "req-001", task)
        finally:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass

        assert result is False

    # ==================== Barge-In Tests ====================

    @pytest.mark.asyncio
    async def test_barge_in_cancels_previous(self, manager):
        """Test that new request cancels previous request (barge-in)."""
        session_id = manager.create_session(user_id="user123")

        # Create first task
        first_task_cancelled = False

        async def first_task():
            nonlocal first_task_cancelled
            try:
                await asyncio.sleep(10)
            except asyncio.CancelledError:
                first_task_cancelled = True
                raise

        task1 = asyncio.create_task(first_task())
        manager.register_request(session_id, "req-001", task1)

        # Give task time to start and event loop to register it
        await asyncio.sleep(0.1)

        # Create second task (barge-in)
        async def second_task():
            await asyncio.sleep(10)

        task2 = asyncio.create_task(second_task())
        manager.register_request(session_id, "req-002", task2)

        # Wait for cancellation to propagate with proper timeout
        await asyncio.sleep(0.2)

        # Verify first task was cancelled
        assert first_task_cancelled is True
        assert task1.cancelled() or task1.done()

        # Verify second task is registered
        session = manager.get_session(session_id)
        assert session["active_request_id"] == "req-002"

        # Cleanup
        task2.cancel()
        try:
            await task2
        except asyncio.CancelledError:
            pass

    @pytest.mark.asyncio
    async def test_barge_in_multiple_times(self, manager):
        """Test multiple sequential barge-ins."""
        session_id = manager.create_session(user_id="user123")

        cancelled_count = 0

        async def create_task(task_num):
            nonlocal cancelled_count
            try:
                await asyncio.sleep(10)
            except asyncio.CancelledError:
                cancelled_count += 1
                raise

        # Create and register 5 tasks, each cancelling the previous
        tasks = []
        for i in range(5):
            task = asyncio.create_task(create_task(i))
            manager.register_request(session_id, f"req-{i}", task)
            tasks.append(task)
            await asyncio.sleep(0.01)

        # Wait for cancellations to propagate
        await asyncio.sleep(0.1)

        # All but the last task should be cancelled
        assert cancelled_count == 4

        # Last task should be the active one
        session = manager.get_session(session_id)
        assert session["active_request_id"] == "req-4"

        # Cleanup
        tasks[-1].cancel()
        try:
            await tasks[-1]
        except asyncio.CancelledError:
            pass

    @pytest.mark.asyncio
    async def test_barge_in_does_not_affect_completed_task(self, manager):
        """Test that completed tasks don't cause issues on barge-in."""
        session_id = manager.create_session(user_id="user123")

        # Create and complete first task
        async def first_task():
            return "completed"

        task1 = asyncio.create_task(first_task())
        manager.register_request(session_id, "req-001", task1)

        # Wait for task to complete
        await task1

        # Create second task (should not try to cancel completed task)
        async def second_task():
            await asyncio.sleep(10)

        task2 = asyncio.create_task(second_task())
        result = manager.register_request(session_id, "req-002", task2)

        assert result is True
        session = manager.get_session(session_id)
        assert session["active_request_id"] == "req-002"

        # Cleanup
        task2.cancel()
        try:
            await task2
        except asyncio.CancelledError:
            pass

    # ==================== Cancellation Tests ====================

    @pytest.mark.asyncio
    async def test_cancel_session_request(self, manager):
        """Test explicit session request cancellation."""
        session_id = manager.create_session(user_id="user123")

        async def mock_task():
            await asyncio.sleep(10)

        task = asyncio.create_task(mock_task())
        manager.register_request(session_id, "req-001", task)

        # Give task time to start
        await asyncio.sleep(0.01)

        # Cancel the request
        result = manager.cancel_session_request(session_id)
        await asyncio.sleep(0.05)

        assert result is True
        assert task.cancelled() or task.done()

        # Session should have no active request
        session = manager.get_session(session_id)
        assert session["active_request_id"] is None
        assert session["active_task"] is None

    def test_cancel_nonexistent_session(self, manager):
        """Test canceling a session that doesn't exist."""
        result = manager.cancel_session_request("nonexistent-session")
        assert result is False

    @pytest.mark.asyncio
    async def test_cancel_session_without_active_request(self, manager):
        """Test canceling a session with no active request."""
        session_id = manager.create_session(user_id="user123")

        result = manager.cancel_session_request(session_id)

        assert result is False

    @pytest.mark.asyncio
    async def test_cancel_already_completed_request(self, manager):
        """Test canceling a request that already completed."""
        session_id = manager.create_session(user_id="user123")

        async def quick_task():
            return "done"

        task = asyncio.create_task(quick_task())
        manager.register_request(session_id, "req-001", task)

        # Wait for task to complete
        await task

        # Try to cancel completed task
        result = manager.cancel_session_request(session_id)

        assert result is False

    # ==================== Session End Tests ====================

    @pytest.mark.asyncio
    async def test_end_session(self, manager):
        """Test ending a session."""
        session_id = manager.create_session(user_id="user123")

        # Give event loop time to register the session
        await asyncio.sleep(0.05)

        result = manager.end_session(session_id)

        assert result is True
        assert manager.get_session(session_id) is None

    @pytest.mark.asyncio
    async def test_end_session_cancels_active_request(self, manager):
        """Test that ending a session cancels active request."""
        session_id = manager.create_session(user_id="user123")

        task_cancelled = False

        async def mock_task():
            nonlocal task_cancelled
            try:
                await asyncio.sleep(10)
            except asyncio.CancelledError:
                task_cancelled = True
                raise

        task = asyncio.create_task(mock_task())
        manager.register_request(session_id, "req-001", task)

        # Give task time to start and event loop to register it
        await asyncio.sleep(0.1)

        # End the session
        manager.end_session(session_id)

        # Wait for cancellation to propagate with proper timeout
        await asyncio.sleep(0.2)

        assert task_cancelled is True
        assert manager.get_session(session_id) is None

    def test_end_nonexistent_session(self, manager):
        """Test ending a session that doesn't exist."""
        result = manager.end_session("nonexistent-session")
        assert result is False

    # ==================== Cleanup Tests ====================

    @pytest.mark.asyncio
    async def test_cleanup_expired_sessions(self, manager_with_short_timeout):
        """Test that expired sessions are cleaned up."""
        manager = manager_with_short_timeout

        # Create a session
        session_id = manager.create_session(user_id="user123")

        # Wait for session to expire
        await asyncio.sleep(1.5)

        # Run cleanup
        cleaned = manager.cleanup_expired_sessions()

        assert cleaned == 1
        assert manager.get_session(session_id) is None

    @pytest.mark.asyncio
    async def test_cleanup_preserves_active_sessions(self, manager):
        """Test that cleanup doesn't remove active sessions."""
        session_id = manager.create_session(user_id="user123")

        # Run cleanup immediately (session should not be expired)
        cleaned = manager.cleanup_expired_sessions()

        assert cleaned == 0
        assert manager.get_session(session_id) is not None

    @pytest.mark.asyncio
    async def test_cleanup_expired_sessions_with_active_request(self, manager_with_short_timeout):
        """Test cleanup cancels active requests in expired sessions."""
        manager = manager_with_short_timeout

        session_id = manager.create_session(user_id="user123")

        task_cancelled = False

        async def mock_task():
            nonlocal task_cancelled
            try:
                await asyncio.sleep(10)
            except asyncio.CancelledError:
                task_cancelled = True
                raise

        task = asyncio.create_task(mock_task())
        manager.register_request(session_id, "req-001", task)

        # Wait for session to expire
        await asyncio.sleep(1.5)

        # Run cleanup
        cleaned = manager.cleanup_expired_sessions()
        await asyncio.sleep(0.05)

        assert cleaned == 1
        assert task_cancelled is True

    # ==================== Statistics Tests ====================

    def test_get_active_session_count(self, manager):
        """Test getting active session count."""
        assert manager.get_active_session_count() == 0

        manager.create_session(user_id="user1")
        assert manager.get_active_session_count() == 1

        manager.create_session(user_id="user2")
        assert manager.get_active_session_count() == 2

    @pytest.mark.asyncio
    async def test_get_active_request_count(self, manager):
        """Test getting active request count."""
        assert manager.get_active_request_count() == 0

        session_id = manager.create_session(user_id="user1")

        async def mock_task():
            await asyncio.sleep(10)

        task = asyncio.create_task(mock_task())
        manager.register_request(session_id, "req-001", task)

        await asyncio.sleep(0.01)

        assert manager.get_active_request_count() == 1

        # Cleanup
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass

        await asyncio.sleep(0.01)
        assert manager.get_active_request_count() == 0

    # ==================== Concurrent Access Tests ====================

    @pytest.mark.asyncio
    async def test_concurrent_session_requests(self, manager):
        """Test multiple concurrent requests to same session."""
        session_id = manager.create_session(user_id="user123")

        results = []
        cancelled_count = 0

        async def create_request(req_id):
            nonlocal cancelled_count
            try:
                async def task_func():
                    await asyncio.sleep(0.5)
                    return f"result-{req_id}"

                task = asyncio.create_task(task_func())
                manager.register_request(session_id, f"req-{req_id}", task)

                # Give event loop time to register the task
                await asyncio.sleep(0.05)

                result = await task
                results.append(result)
            except asyncio.CancelledError:
                cancelled_count += 1

        # Launch concurrent requests with small delays between them
        tasks = []
        for i in range(5):
            tasks.append(asyncio.create_task(create_request(i)))
            await asyncio.sleep(0.02)  # Small delay to ensure proper ordering

        # Wait for all to complete or be cancelled with timeout
        await asyncio.gather(*tasks, return_exceptions=True)

        # Give extra time for cancellation to propagate
        await asyncio.sleep(0.1)

        # Only one should complete (the last one registered)
        assert len(results) <= 1
        # Rest should be cancelled due to barge-in
        assert cancelled_count >= 4

    @pytest.mark.asyncio
    async def test_concurrent_different_sessions(self, manager):
        """Test concurrent requests to different sessions."""
        results = []

        async def create_session_request(session_num):
            session_id = manager.create_session(user_id=f"user{session_num}")

            async def task_func():
                await asyncio.sleep(0.1)
                return f"result-{session_num}"

            task = asyncio.create_task(task_func())
            manager.register_request(session_id, f"req-{session_num}", task)

            result = await task
            results.append(result)

        # Launch concurrent requests to different sessions
        tasks = [asyncio.create_task(create_session_request(i)) for i in range(5)]
        await asyncio.gather(*tasks)

        # All should complete
        assert len(results) == 5

    # ==================== Edge Cases ====================

    def test_get_session_nonexistent(self, manager):
        """Test getting a session that doesn't exist."""
        session = manager.get_session("nonexistent-session")
        assert session is None

    @pytest.mark.asyncio
    async def test_register_none_task(self, manager):
        """Test registering None as a task."""
        session_id = manager.create_session(user_id="user123")

        result = manager.register_request(session_id, "req-001", None)

        # Should succeed but with None task
        assert result is True
        session = manager.get_session(session_id)
        assert session["active_task"] is None

    @pytest.mark.asyncio
    async def test_session_manager_with_zero_timeout(self):
        """Test session manager with zero timeout."""
        manager = VoiceSessionManager(session_timeout=0)
        session_id = manager.create_session(user_id="user123")

        # Session should be immediately expired
        await asyncio.sleep(0.1)

        cleaned = manager.cleanup_expired_sessions()
        assert cleaned == 1


class TestGlobalSessionManager:
    """Tests for global session manager singleton."""

    def setup_method(self):
        """Reset global session manager before each test."""
        reset_session_manager()

    def teardown_method(self):
        """Reset global session manager after each test."""
        reset_session_manager()

    def test_get_session_manager_singleton(self):
        """Test that get_session_manager returns singleton."""
        manager1 = get_session_manager()
        manager2 = get_session_manager()

        assert manager1 is manager2

    def test_reset_session_manager(self):
        """Test resetting the global session manager."""
        manager1 = get_session_manager()
        manager1.create_session(user_id="user1")

        reset_session_manager()

        manager2 = get_session_manager()

        assert manager1 is not manager2
        assert manager2.get_active_session_count() == 0

    @pytest.mark.asyncio
    async def test_reset_cancels_active_requests(self):
        """Test that reset cancels active requests."""
        manager = get_session_manager()
        session_id = manager.create_session(user_id="user1")

        task_cancelled = False

        async def mock_task():
            nonlocal task_cancelled
            try:
                await asyncio.sleep(10)
            except asyncio.CancelledError:
                task_cancelled = True
                raise

        task = asyncio.create_task(mock_task())
        manager.register_request(session_id, "req-001", task)

        await asyncio.sleep(0.01)

        # Reset should cancel the task
        reset_session_manager()

        await asyncio.sleep(0.05)

        assert task_cancelled is True

    @patch("app.core.voice_session.settings")
    def test_get_session_manager_uses_config_timeout(self, mock_settings):
        """Test that session manager uses timeout from config."""
        mock_settings.VOICE_SESSION_TIMEOUT = 600

        reset_session_manager()
        manager = get_session_manager()

        assert manager._session_timeout == 600


class TestVoiceSessionManagerIntegration:
    """Integration tests for VoiceSessionManager with asyncio."""

    @pytest.fixture
    def manager(self):
        """Create fresh session manager for each test."""
        return VoiceSessionManager(session_timeout=60)

    @pytest.mark.asyncio
    async def test_full_barge_in_scenario(self, manager):
        """Test complete barge-in scenario from start to finish."""
        # 1. Create session
        session_id = manager.create_session(user_id="farmer123")
        assert session_id is not None

        # 2. Start first voice request
        first_result = None
        first_cancelled = False

        async def first_voice_request():
            nonlocal first_result, first_cancelled
            try:
                # Simulate STT
                await asyncio.sleep(0.5)
                # Simulate LLM
                await asyncio.sleep(0.5)
                # Simulate TTS
                await asyncio.sleep(0.5)
                first_result = "response1"
                return first_result
            except asyncio.CancelledError:
                first_cancelled = True
                raise

        task1 = asyncio.create_task(first_voice_request())
        manager.register_request(session_id, "voice-req-1", task1)

        # 3. Wait a bit then barge-in with new request
        await asyncio.sleep(0.3)

        second_result = None

        async def second_voice_request():
            nonlocal second_result
            # Simulate faster processing
            await asyncio.sleep(0.2)
            second_result = "response2"
            return second_result

        task2 = asyncio.create_task(second_voice_request())
        manager.register_request(session_id, "voice-req-2", task2)

        # 4. Wait for second request to complete
        await task2

        # 5. Verify first was cancelled
        assert first_cancelled is True
        assert first_result is None
        assert second_result == "response2"

        # 6. Verify session state
        session = manager.get_session(session_id)
        assert session["active_request_id"] == "voice-req-2"

    @pytest.mark.asyncio
    async def test_rapid_fire_requests(self, manager):
        """Test rapid sequential requests (stress test)."""
        session_id = manager.create_session(user_id="user123")

        completed_results = []
        cancellation_count = 0

        async def process_request(req_id):
            nonlocal cancellation_count
            try:
                await asyncio.sleep(0.1)
                completed_results.append(req_id)
                return req_id
            except asyncio.CancelledError:
                cancellation_count += 1
                raise

        # Fire 20 rapid requests
        tasks = []
        for i in range(20):
            task = asyncio.create_task(process_request(i))
            manager.register_request(session_id, f"req-{i}", task)
            tasks.append(task)
            await asyncio.sleep(0.01)  # Small delay between requests

        # Wait for all to settle
        await asyncio.gather(*tasks, return_exceptions=True)

        # Only the last request should complete
        assert len(completed_results) <= 1
        if completed_results:
            assert completed_results[0] == 19  # Last request

        # Most should be cancelled
        assert cancellation_count >= 18

    @pytest.mark.asyncio
    async def test_session_lifecycle(self, manager):
        """Test complete session lifecycle."""
        # Create
        session_id = manager.create_session(user_id="lifecycle_user")
        assert manager.get_active_session_count() == 1

        # Give event loop time to register the session
        await asyncio.sleep(0.05)

        # Use
        async def task_func():
            await asyncio.sleep(0.1)
            return "done"

        task = asyncio.create_task(task_func())
        manager.register_request(session_id, "req-1", task)
        
        # Give event loop time to register the task
        await asyncio.sleep(0.05)
        
        await task

        # Wait for request count to update
        await asyncio.sleep(0.05)
        assert manager.get_active_request_count() == 0

        # End
        result = manager.end_session(session_id)
        assert result is True
        assert manager.get_active_session_count() == 0
