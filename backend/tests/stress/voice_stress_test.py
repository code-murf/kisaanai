"""
Stress test script for Voice API barge-in handling.

This script provides comprehensive stress testing for the Voice API including:
- Concurrent request handling
- Barge-in cancellation scenarios
- Rapid-fire request testing
- Latency measurement

Run with:
    python -m backend.tests.stress.voice_stress_test
    python backend/tests/stress/voice_stress_test.py

Requirements:
    pip install aiohttp statistics
"""
import asyncio
import aiohttp
import time
import statistics
import io
import json
import argparse
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path


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


@dataclass
class TestResult:
    """Result of a single test request."""
    success: bool
    status_code: int
    latency_ms: float
    error: Optional[str] = None
    session_id: Optional[str] = None
    cancelled: bool = False


@dataclass
class TestSummary:
    """Summary of test results."""
    test_name: str
    total_requests: int
    successful_requests: int
    failed_requests: int
    avg_latency_ms: float
    p50_latency_ms: float
    p95_latency_ms: float
    p99_latency_ms: float
    min_latency_ms: float
    max_latency_ms: float
    errors: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "test_name": self.test_name,
            "total_requests": self.total_requests,
            "successful_requests": self.successful_requests,
            "failed_requests": self.failed_requests,
            "success_rate": f"{(self.successful_requests / self.total_requests * 100):.2f}%",
            "latency": {
                "avg_ms": round(self.avg_latency_ms, 2),
                "p50_ms": round(self.p50_latency_ms, 2),
                "p95_ms": round(self.p95_latency_ms, 2),
                "p99_ms": round(self.p99_latency_ms, 2),
                "min_ms": round(self.min_latency_ms, 2),
                "max_ms": round(self.max_latency_ms, 2),
            },
            "errors": self.errors[:10],  # First 10 errors
        }


class VoiceStressTester:
    """Stress tester for Voice API barge-in handling."""

    def __init__(
        self,
        base_url: str = "http://localhost:8000",
        auth_token: Optional[str] = None,
        timeout: float = 30.0,
    ):
        """
        Initialize the stress tester.

        Args:
            base_url: Base URL of the API server
            auth_token: Optional authentication token
            timeout: Request timeout in seconds
        """
        self.base_url = base_url.rstrip("/")
        self.auth_token = auth_token
        self.timeout = aiohttp.ClientTimeout(total=timeout)
        self.results: List[TestResult] = []
        self.audio_data = create_test_audio()

    def _get_headers(self) -> Dict[str, str]:
        """Get headers for requests."""
        headers = {}
        if self.auth_token:
            headers["Authorization"] = f"Bearer {self.auth_token}"
        return headers

    async def create_session(self, session: aiohttp.ClientSession) -> Optional[str]:
        """Create a new voice session."""
        try:
            async with session.post(
                f"{self.base_url}/voice/session",
                headers=self._get_headers(),
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get("session_id")
        except Exception as e:
            print(f"Error creating session: {e}")
        return None

    async def send_voice_query(
        self,
        session: aiohttp.ClientSession,
        session_id: Optional[str] = None,
        language: str = "hi-IN",
    ) -> TestResult:
        """Send a voice query request."""
        start_time = time.perf_counter()

        form_data = aiohttp.FormData()
        form_data.add_field(
            "file",
            self.audio_data,
            filename="test.wav",
            content_type="audio/wav",
        )
        form_data.add_field("language", language)
        if session_id:
            form_data.add_field("session_id", session_id)

        try:
            async with session.post(
                f"{self.base_url}/voice/query",
                data=form_data,
                headers=self._get_headers(),
            ) as response:
                latency_ms = (time.perf_counter() - start_time) * 1000
                data = await response.json() if response.content_type == "application/json" else {}

                return TestResult(
                    success=response.status == 200,
                    status_code=response.status,
                    latency_ms=latency_ms,
                    session_id=data.get("session_id"),
                )
        except asyncio.CancelledError:
            latency_ms = (time.perf_counter() - start_time) * 1000
            return TestResult(
                success=False,
                status_code=499,
                latency_ms=latency_ms,
                error="Request cancelled",
                cancelled=True,
            )
        except Exception as e:
            latency_ms = (time.perf_counter() - start_time) * 1000
            return TestResult(
                success=False,
                status_code=0,
                latency_ms=latency_ms,
                error=str(e),
            )

    async def cancel_request(
        self,
        session: aiohttp.ClientSession,
        session_id: str,
    ) -> Tuple[bool, Dict]:
        """Cancel an active voice request."""
        form_data = aiohttp.FormData()
        form_data.add_field("session_id", session_id)

        try:
            async with session.post(
                f"{self.base_url}/voice/cancel",
                data=form_data,
                headers=self._get_headers(),
            ) as response:
                data = await response.json() if response.content_type == "application/json" else {}
                return response.status == 200, data
        except Exception as e:
            return False, {"error": str(e)}

    async def get_stats(self, session: aiohttp.ClientSession) -> Dict:
        """Get voice API stats."""
        try:
            async with session.get(
                f"{self.base_url}/voice/stats",
                headers=self._get_headers(),
            ) as response:
                if response.status == 200:
                    return await response.json()
        except Exception:
            pass
        return {}

    def calculate_summary(self, test_name: str) -> TestSummary:
        """Calculate summary statistics from results."""
        if not self.results:
            return TestSummary(
                test_name=test_name,
                total_requests=0,
                successful_requests=0,
                failed_requests=0,
                avg_latency_ms=0,
                p50_latency_ms=0,
                p95_latency_ms=0,
                p99_latency_ms=0,
                min_latency_ms=0,
                max_latency_ms=0,
            )

        latencies = [r.latency_ms for r in self.results]
        successful = [r for r in self.results if r.success]
        failed = [r for r in self.results if not r.success]
        errors = [r.error for r in failed if r.error]

        return TestSummary(
            test_name=test_name,
            total_requests=len(self.results),
            successful_requests=len(successful),
            failed_requests=len(failed),
            avg_latency_ms=statistics.mean(latencies),
            p50_latency_ms=statistics.median(latencies),
            p95_latency_ms=statistics.quantiles(latencies, n=100)[94] if len(latencies) >= 100 else max(latencies),
            p99_latency_ms=statistics.quantiles(latencies, n=100)[98] if len(latencies) >= 100 else max(latencies),
            min_latency_ms=min(latencies),
            max_latency_ms=max(latencies),
            errors=errors,
        )

    async def run_concurrent_test(
        self,
        num_requests: int = 10,
        use_sessions: bool = True,
    ) -> TestSummary:
        """
        Run concurrent voice requests.

        Args:
            num_requests: Number of concurrent requests
            use_sessions: Whether to create sessions for each request
        """
        print(f"\n🔄 Running concurrent test with {num_requests} requests...")
        self.results = []

        async with aiohttp.ClientSession(timeout=self.timeout) as session:
            # Create sessions if needed
            session_ids = []
            if use_sessions:
                print("  Creating sessions...")
                session_ids = await asyncio.gather(*[
                    self.create_session(session) for _ in range(num_requests)
                ])

            # Run concurrent requests
            print("  Sending concurrent requests...")
            tasks = []
            for i in range(num_requests):
                sid = session_ids[i] if session_ids else None
                tasks.append(self.send_voice_query(session, sid))

            self.results = await asyncio.gather(*tasks)

        summary = self.calculate_summary("Concurrent Test")
        self._print_summary(summary)
        return summary

    async def run_barge_in_test(
        self,
        num_barge_ins: int = 5,
        delay_ms: int = 100,
    ) -> TestSummary:
        """
        Test rapid barge-in scenarios.

        This test creates a session and sends multiple requests in rapid
        succession, each cancelling the previous one.

        Args:
            num_barge_ins: Number of barge-in attempts per session
            delay_ms: Delay between requests in milliseconds
        """
        print(f"\n⚡ Running barge-in test with {num_barge_ins} rapid requests...")
        self.results = []

        async with aiohttp.ClientSession(timeout=self.timeout) as session:
            # Create a session
            session_id = await self.create_session(session)
            if not session_id:
                print("  ❌ Failed to create session")
                return self.calculate_summary("Barge-In Test")

            print(f"  Session: {session_id[:8]}...")

            # Send rapid requests
            for i in range(num_barge_ins):
                result = await self.send_voice_query(session, session_id)
                self.results.append(result)

                # Small delay between requests
                await asyncio.sleep(delay_ms / 1000)

                # Explicitly cancel if request is still running
                if not result.success and result.status_code not in [200, 499]:
                    await self.cancel_request(session, session_id)

        summary = self.calculate_summary("Barge-In Test")
        self._print_summary(summary)
        return summary

    async def run_rapid_fire_test(
        self,
        num_requests: int = 20,
        delay_ms: int = 50,
    ) -> TestSummary:
        """
        Test rapid sequential requests with same session.

        Args:
            num_requests: Number of requests to send
            delay_ms: Delay between requests in milliseconds
        """
        print(f"\n🔥 Running rapid-fire test with {num_requests} requests...")
        self.results = []

        async with aiohttp.ClientSession(timeout=self.timeout) as session:
            # Create a session
            session_id = await self.create_session(session)
            if not session_id:
                print("  ❌ Failed to create session")
                return self.calculate_summary("Rapid-Fire Test")

            print(f"  Session: {session_id[:8]}...")

            # Send rapid requests
            tasks = []
            for i in range(num_requests):
                tasks.append(self.send_voice_query(session, session_id))
                await asyncio.sleep(delay_ms / 1000)

            # Wait for all to complete
            self.results = await asyncio.gather(*tasks, return_exceptions=True)

            # Convert exceptions to TestResult
            processed_results = []
            for r in self.results:
                if isinstance(r, TestResult):
                    processed_results.append(r)
                else:
                    processed_results.append(TestResult(
                        success=False,
                        status_code=0,
                        latency_ms=0,
                        error=str(r),
                    ))
            self.results = processed_results

        summary = self.calculate_summary("Rapid-Fire Test")
        self._print_summary(summary)
        return summary

    async def run_latency_test(
        self,
        num_requests: int = 100,
        concurrent: int = 10,
    ) -> TestSummary:
        """
        Measure latency with sequential and concurrent requests.

        Args:
            num_requests: Total number of requests
            concurrent: Number of concurrent requests
        """
        print(f"\n📊 Running latency test with {num_requests} requests ({concurrent} concurrent)...")
        self.results = []

        async with aiohttp.ClientSession(timeout=self.timeout) as session:
            batches = num_requests // concurrent
            if num_requests % concurrent:
                batches += 1

            for batch in range(batches):
                batch_size = min(concurrent, num_requests - batch * concurrent)

                # Create sessions for this batch
                session_ids = await asyncio.gather(*[
                    self.create_session(session) for _ in range(batch_size)
                ])

                # Send batch requests
                batch_results = await asyncio.gather(*[
                    self.send_voice_query(session, sid)
                    for sid in session_ids
                ])
                self.results.extend(batch_results)

                print(f"  Batch {batch + 1}/{batches} complete")

        summary = self.calculate_summary("Latency Test")
        self._print_summary(summary)
        return summary

    async def run_session_isolation_test(
        self,
        num_sessions: int = 10,
    ) -> TestSummary:
        """
        Test that multiple sessions can operate independently.

        Args:
            num_sessions: Number of concurrent sessions to test
        """
        print(f"\n🔒 Running session isolation test with {num_sessions} sessions...")
        self.results = []

        async with aiohttp.ClientSession(timeout=self.timeout) as session:
            # Create multiple sessions
            print("  Creating sessions...")
            session_ids = await asyncio.gather(*[
                self.create_session(session) for _ in range(num_sessions)
            ])

            # Send 3 requests per session concurrently
            print("  Sending requests to each session...")
            all_tasks = []
            for sid in session_ids:
                if sid:
                    for _ in range(3):
                        all_tasks.append(self.send_voice_query(session, sid))

            self.results = await asyncio.gather(*all_tasks)

        summary = self.calculate_summary("Session Isolation Test")
        self._print_summary(summary)
        return summary

    async def run_stats_test(self) -> Dict:
        """Test the stats endpoint and verify counts."""
        print("\n📈 Running stats test...")

        async with aiohttp.ClientSession(timeout=self.timeout) as session:
            # Get initial stats
            initial_stats = await self.get_stats(session)
            print(f"  Initial stats: {initial_stats}")

            # Create some sessions
            session_ids = await asyncio.gather(*[
                self.create_session(session) for _ in range(5)
            ])

            # Get updated stats
            updated_stats = await self.get_stats(session)
            print(f"  After creating 5 sessions: {updated_stats}")

            # Clean up sessions
            for sid in session_ids:
                if sid:
                    async with session.delete(
                        f"{self.base_url}/voice/session/{sid}",
                        headers=self._get_headers(),
                    ) as response:
                        pass

            # Get final stats
            final_stats = await self.get_stats(session)
            print(f"  After cleanup: {final_stats}")

            return {
                "initial": initial_stats,
                "after_sessions": updated_stats,
                "after_cleanup": final_stats,
            }

    def _print_summary(self, summary: TestSummary):
        """Print test summary."""
        print(f"\n  📋 Results for {summary.test_name}:")
        print(f"     Total: {summary.total_requests}")
        print(f"     Successful: {summary.successful_requests}")
        print(f"     Failed: {summary.failed_requests}")
        if summary.total_requests > 0:
            print(f"     Success Rate: {(summary.successful_requests / summary.total_requests * 100):.2f}%")
        print(f"     Latency (ms):")
        print(f"       Avg: {summary.avg_latency_ms:.2f}")
        print(f"       P50: {summary.p50_latency_ms:.2f}")
        print(f"       P95: {summary.p95_latency_ms:.2f}")
        print(f"       P99: {summary.p99_latency_ms:.2f}")
        print(f"       Min: {summary.min_latency_ms:.2f}")
        print(f"       Max: {summary.max_latency_ms:.2f}")
        if summary.errors:
            print(f"     Errors: {len(summary.errors)}")
            for err in summary.errors[:3]:
                print(f"       - {err[:80]}")

    async def run_all_tests(
        self,
        concurrent_requests: int = 10,
        barge_in_count: int = 5,
        rapid_fire_count: int = 20,
        latency_requests: int = 100,
    ) -> Dict:
        """
        Run all stress tests.

        Returns:
            Dictionary with all test results
        """
        print("=" * 60)
        print("🎤 Voice API Stress Test Suite")
        print(f"   Base URL: {self.base_url}")
        print(f"   Time: {datetime.now().isoformat()}")
        print("=" * 60)

        results = {}

        # Test 1: Concurrent requests
        results["concurrent"] = (await self.run_concurrent_test(
            num_requests=concurrent_requests
        )).to_dict()

        # Test 2: Barge-in
        results["barge_in"] = (await self.run_barge_in_test(
            num_barge_ins=barge_in_count
        )).to_dict()

        # Test 3: Rapid-fire
        results["rapid_fire"] = (await self.run_rapid_fire_test(
            num_requests=rapid_fire_count
        )).to_dict()

        # Test 4: Latency measurement
        results["latency"] = (await self.run_latency_test(
            num_requests=latency_requests
        )).to_dict()

        # Test 5: Session isolation
        results["session_isolation"] = (await self.run_session_isolation_test(
            num_sessions=5
        )).to_dict()

        # Test 6: Stats
        results["stats"] = await self.run_stats_test()

        print("\n" + "=" * 60)
        print("✅ All tests completed!")
        print("=" * 60)

        return results

    def save_results(self, results: Dict, output_file: str = "stress_test_results.json"):
        """Save results to JSON file."""
        output_path = Path(output_file)
        with open(output_path, "w") as f:
            json.dump(results, f, indent=2, default=str)
        print(f"\n📄 Results saved to {output_path.absolute()}")


async def main():
    """Main entry point for stress tests."""
    parser = argparse.ArgumentParser(description="Voice API Stress Tester")
    parser.add_argument(
        "--url",
        default="http://localhost:8000",
        help="Base URL of the API server",
    )
    parser.add_argument(
        "--token",
        default=None,
        help="Authentication token",
    )
    parser.add_argument(
        "--concurrent",
        type=int,
        default=10,
        help="Number of concurrent requests",
    )
    parser.add_argument(
        "--barge-in",
        type=int,
        default=5,
        help="Number of barge-in attempts",
    )
    parser.add_argument(
        "--rapid-fire",
        type=int,
        default=20,
        help="Number of rapid-fire requests",
    )
    parser.add_argument(
        "--latency",
        type=int,
        default=100,
        help="Number of latency test requests",
    )
    parser.add_argument(
        "--output",
        default="stress_test_results.json",
        help="Output file for results",
    )

    args = parser.parse_args()

    tester = VoiceStressTester(
        base_url=args.url,
        auth_token=args.token,
    )

    results = await tester.run_all_tests(
        concurrent_requests=args.concurrent,
        barge_in_count=args.barge_in,
        rapid_fire_count=args.rapid_fire,
        latency_requests=args.latency,
    )

    tester.save_results(results, args.output)


if __name__ == "__main__":
    asyncio.run(main())
