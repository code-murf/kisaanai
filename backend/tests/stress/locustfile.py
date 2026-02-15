"""
Locust load testing configuration for Voice API.

This module provides load testing scenarios for the Voice API including:
- Basic voice query testing
- Session-based barge-in testing
- Cancel endpoint testing
- Mixed workload simulation

Run with:
    locust -f backend/tests/stress/locustfile.py
    locust -f backend/tests/stress/locustfile.py --host http://localhost:8000
    locust -f backend/tests/stress/locustfile.py --headless -u 100 -r 10 -t 60s

Requirements:
    pip install locust
"""
import os
import io
from locust import HttpUser, task, between, events
from locust.runners import MasterRunner, WorkerRunner


# Create a minimal valid WAV file header for testing
def create_test_audio() -> bytes:
    """Create a minimal valid WAV file for testing."""
    wav_header = bytes([
        0x52, 0x49, 0x46, 0x46,  # "RIFF"
        0x24, 0x00, 0x00, 0x00,  # File size - 8
        0x57, 0x41, 0x56, 0x45,  # "WAVE"
        0x66, 0x6D, 0x74, 0x20,  # "fmt "
        0x10, 0x00, 0x00, 0x00,  # Chunk size
        0x01, 0x00,              # Audio format (PCM)
        0x01, 0x00,              # Channels
        0x44, 0xAC, 0x00, 0x00,  # Sample rate (44100)
        0x88, 0x58, 0x01, 0x00,  # Byte rate
        0x02, 0x00,              # Block align
        0x10, 0x00,              # Bits per sample
        0x64, 0x61, 0x74, 0x61,  # "data"
        0x00, 0x00, 0x00, 0x00,  # Data size
    ])
    return wav_header


# Global test audio data
TEST_AUDIO = create_test_audio()

# Optional: Load auth token from environment
AUTH_TOKEN = os.environ.get("VOICE_API_TOKEN", None)


class VoiceAPIUser(HttpUser):
    """
    Simulates a voice API user performing various operations.
    
    This user class simulates realistic voice API usage patterns including:
    - Creating sessions
    - Sending voice queries
    - Canceling requests (barge-in)
    - Checking stats
    """
    
    # Wait between 1-3 seconds between tasks
    wait_time = between(1, 3)
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.session_id = None
        self.auth_headers = {}
        
        if AUTH_TOKEN:
            self.auth_headers["Authorization"] = f"Bearer {AUTH_TOKEN}"
    
    def on_start(self):
        """Called when a user starts. Create a session for this user."""
        self.create_session()
    
    def create_session(self):
        """Create a new voice session."""
        response = self.client.post(
            "/voice/session",
            headers=self.auth_headers,
            name="/voice/session",
            catch_response=True,
        )
        
        if response.status_code == 200:
            try:
                data = response.json()
                self.session_id = data.get("session_id")
                response.success()
            except Exception:
                response.failure("Failed to parse session response")
        else:
            response.failure(f"Session creation failed: {response.status_code}")
    
    @task(5)
    def voice_query_without_session(self):
        """Test voice query without session (creates new session each time)."""
        files = {
            "file": ("test.wav", io.BytesIO(TEST_AUDIO), "audio/wav"),
        }
        data = {
            "language": "hi-IN",
        }
        
        self.client.post(
            "/voice/query",
            files=files,
            data=data,
            headers=self.auth_headers,
            name="/voice/query [no session]",
        )
    
    @task(10)
    def voice_query_with_session(self):
        """Test voice query with session_id for barge-in support."""
        if not self.session_id:
            self.create_session()
            if not self.session_id:
                return
        
        files = {
            "file": ("test.wav", io.BytesIO(TEST_AUDIO), "audio/wav"),
        }
        data = {
            "language": "hi-IN",
            "session_id": self.session_id,
        }
        
        with self.client.post(
            "/voice/query",
            files=files,
            data=data,
            headers=self.auth_headers,
            name="/voice/query [with session]",
            catch_response=True,
        ) as response:
            if response.status_code == 200:
                response.success()
            elif response.status_code == 499:
                # Request cancelled due to barge-in - this is expected
                response.success()
            else:
                response.failure(f"Unexpected status: {response.status_code}")
    
    @task(2)
    def cancel_request(self):
        """Test cancel endpoint (barge-in simulation)."""
        if not self.session_id:
            self.create_session()
            if not self.session_id:
                return
        
        data = {"session_id": self.session_id}
        
        self.client.post(
            "/voice/cancel",
            data=data,
            headers=self.auth_headers,
            name="/voice/cancel",
        )
    
    @task(1)
    def get_stats(self):
        """Test stats endpoint."""
        self.client.get(
            "/voice/stats",
            headers=self.auth_headers,
            name="/voice/stats",
        )
    
    @task(1)
    def end_and_create_new_session(self):
        """End current session and create a new one."""
        if self.session_id:
            self.client.delete(
                f"/voice/session/{self.session_id}",
                headers=self.auth_headers,
                name="/voice/session/[id]",
            )
        
        self.create_session()


class BargeInUser(HttpUser):
    """
    Simulates a user who frequently interrupts (barge-in) their own requests.
    
    This user class simulates the barge-in pattern where users start
    a voice query and then immediately start a new one, cancelling
    the previous request.
    """
    
    # Short wait time to simulate rapid interactions
    wait_time = between(0.5, 1.5)
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.session_id = None
        self.auth_headers = {}
        
        if AUTH_TOKEN:
            self.auth_headers["Authorization"] = f"Bearer {AUTH_TOKEN}"
    
    def on_start(self):
        """Create session on start."""
        self.create_session()
    
    def create_session(self):
        """Create a new voice session."""
        response = self.client.post(
            "/voice/session",
            headers=self.auth_headers,
            name="/voice/session [barge-in]",
            catch_response=True,
        )
        
        if response.status_code == 200:
            try:
                data = response.json()
                self.session_id = data.get("session_id")
                response.success()
            except Exception:
                response.failure("Failed to parse session response")
    
    @task(3)
    def rapid_barge_in(self):
        """Send rapid requests to simulate barge-in behavior."""
        if not self.session_id:
            self.create_session()
            if not self.session_id:
                return
        
        # Send first request (will likely be cancelled)
        files = {
            "file": ("test.wav", io.BytesIO(TEST_AUDIO), "audio/wav"),
        }
        data = {
            "language": "hi-IN",
            "session_id": self.session_id,
        }
        
        # Don't wait for response - immediately send another request
        # This simulates barge-in
        self.client.post(
            "/voice/query",
            files=files,
            data=data,
            headers=self.auth_headers,
            name="/voice/query [barge-in 1]",
            catch_response=True,
        )
        
        # Immediately send second request (barge-in)
        files2 = {
            "file": ("test.wav", io.BytesIO(TEST_AUDIO), "audio/wav"),
        }
        data2 = {
            "language": "hi-IN",
            "session_id": self.session_id,
        }
        
        self.client.post(
            "/voice/query",
            files=files2,
            data=data2,
            headers=self.auth_headers,
            name="/voice/query [barge-in 2]",
        )
    
    @task(1)
    def explicit_cancel(self):
        """Explicitly cancel the current request."""
        if not self.session_id:
            return
        
        data = {"session_id": self.session_id}
        
        self.client.post(
            "/voice/cancel",
            data=data,
            headers=self.auth_headers,
            name="/voice/cancel [barge-in]",
        )


class StatsMonitoringUser(HttpUser):
    """
    A lightweight user that only monitors stats.
    
    Useful for continuous monitoring during load tests.
    """
    
    wait_time = between(5, 10)
    
    @task
    def get_stats(self):
        """Get voice API stats."""
        self.client.get(
            "/voice/stats",
            name="/voice/stats [monitor]",
        )


# Event listeners for custom metrics
@events.request.add_listener
def on_request(request_type, name, response_time, response_length, exception, **kwargs):
    """Log request details for analysis."""
    if exception:
        # Could integrate with external monitoring here
        pass


@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    """Called when test starts."""
    print("\n" + "=" * 60)
    print("🎤 Voice API Load Test Starting")
    print("=" * 60)
    
    if isinstance(environment.runner, MasterRunner):
        print("Running in distributed mode (master)")
    elif isinstance(environment.runner, WorkerRunner):
        print("Running in distributed mode (worker)")
    else:
        print("Running in standalone mode")
    
    print(f"Target host: {environment.host}")
    print("=" * 60 + "\n")


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """Called when test stops."""
    print("\n" + "=" * 60)
    print("🎤 Voice API Load Test Complete")
    print("=" * 60 + "\n")


# Custom arguments for the load test
@events.init_command_line_parser.add_listener
def _(parser):
    """Add custom command line arguments."""
    parser.add_argument(
        "--voice-token",
        type=str,
        env_var="VOICE_API_TOKEN",
        default="",
        help="Authentication token for Voice API",
    )
    parser.add_argument(
        "--session-timeout",
        type=int,
        default=300,
        help="Session timeout in seconds",
    )


# Additional task sets for specific test scenarios
class HighVolumeUser(HttpUser):
    """
    Simulates a high-volume user with rapid requests.
    
    Use this for stress testing the system under heavy load.
    """
    
    wait_time = between(0.1, 0.5)
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.session_id = None
        self.request_count = 0
        self.auth_headers = {}
        
        if AUTH_TOKEN:
            self.auth_headers["Authorization"] = f"Bearer {AUTH_TOKEN}"
    
    def on_start(self):
        """Create session on start."""
        response = self.client.post(
            "/voice/session",
            headers=self.auth_headers,
            name="/voice/session [high-volume]",
        )
        if response.status_code == 200:
            self.session_id = response.json().get("session_id")
    
    @task
    def rapid_query(self):
        """Send rapid queries."""
        if not self.session_id:
            return
        
        files = {
            "file": ("test.wav", io.BytesIO(TEST_AUDIO), "audio/wav"),
        }
        data = {
            "language": "hi-IN",
            "session_id": self.session_id,
        }
        
        self.client.post(
            "/voice/query",
            files=files,
            data=data,
            headers=self.auth_headers,
            name="/voice/query [high-volume]",
        )
        
        self.request_count += 1
        
        # Every 10 requests, create a new session
        if self.request_count % 10 == 0:
            response = self.client.post(
                "/voice/session",
                headers=self.auth_headers,
                name="/voice/session [high-volume]",
            )
            if response.status_code == 200:
                self.session_id = response.json().get("session_id")


# Export user classes for Locust discovery
__all__ = [
    "VoiceAPIUser",
    "BargeInUser",
    "StatsMonitoringUser",
    "HighVolumeUser",
]
