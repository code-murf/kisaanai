"""
Sarvam AI Text-to-Speech API Test
Tests REST (v2 & v3) and WebSocket Stream endpoints.

Run: python test_sarvam_tts.py
"""

import requests
import json
import base64
import asyncio
import os
import sys

# Fix Windows console encoding
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

# --- Configuration ---
API_KEY = "sk_9hghn088_oNUlhYwS6Pj5UizXcMWurSqI"
REST_URL = "https://api.sarvam.ai/text-to-speech"
WS_URL = "wss://api.sarvam.ai/text-to-speech/ws"

HEADERS = {
    "Content-Type": "application/json",
    "API-Subscription-Key": API_KEY,
}


def test_rest_tts_v2():
    """Test the REST Text-to-Speech endpoint with bulbul:v2."""
    print("=" * 60)
    print("TEST 1: REST Text-to-Speech API (bulbul:v2)")
    print("=" * 60)

    payload = {
        "inputs": ["Hello, this is a test of the Sarvam AI text to speech API."],
        "target_language_code": "en-IN",
        "speaker": "anushka",       # lowercase required!
        "model": "bulbul:v2",
        "pace": 1.0,
        "pitch": 0.0,
        "loudness": 1.0,
    }

    try:
        print(f"  Endpoint : {REST_URL}")
        print(f"  Model    : {payload['model']}")
        print(f"  Speaker  : {payload['speaker']}")
        print(f"  Text     : {payload['inputs'][0]}")
        print()

        response = requests.post(REST_URL, headers=HEADERS, json=payload, timeout=30)
        print(f"  Status Code : {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            print(f"  Request ID  : {data.get('request_id', 'N/A')}")
            audios = data.get("audios", [])
            if audios and audios[0]:
                audio_bytes = base64.b64decode(audios[0])
                output_file = "test_output_rest_v2.wav"
                with open(output_file, "wb") as f:
                    f.write(audio_bytes)
                file_size = os.path.getsize(output_file)
                print(f"  Audio saved : {output_file} ({file_size:,} bytes)")
                print("\n  >>> RESULT: PASS <<<")
                return True
            else:
                print("  No audio data in response.")
                return False
        else:
            print(f"  >>> RESULT: FAIL <<<")
            print(f"  Error: {response.text[:500]}")
            return False
    except Exception as e:
        print(f"  >>> RESULT: FAIL ({type(e).__name__}: {e}) <<<")
        return False
    finally:
        print()


def test_rest_tts_v3():
    """Test the REST Text-to-Speech endpoint with bulbul:v3."""
    print("=" * 60)
    print("TEST 2: REST Text-to-Speech API (bulbul:v3)")
    print("=" * 60)

    payload = {
        "inputs": ["Namaste, yeh Sarvam AI ka text to speech test hai."],
        "target_language_code": "hi-IN",
        "speaker": "shubh",         # lowercase required!
        "model": "bulbul:v3",
        "pace": 1.0,
        "temperature": 0.6,
    }

    try:
        print(f"  Endpoint : {REST_URL}")
        print(f"  Model    : {payload['model']}")
        print(f"  Speaker  : {payload['speaker']}")
        print(f"  Language : {payload['target_language_code']}")
        print(f"  Text     : {payload['inputs'][0]}")
        print()

        response = requests.post(REST_URL, headers=HEADERS, json=payload, timeout=30)
        print(f"  Status Code : {response.status_code}")

        if response.status_code == 200:
            data = response.json()
            print(f"  Request ID  : {data.get('request_id', 'N/A')}")
            audios = data.get("audios", [])
            if audios and audios[0]:
                audio_bytes = base64.b64decode(audios[0])
                output_file = "test_output_rest_v3.wav"
                with open(output_file, "wb") as f:
                    f.write(audio_bytes)
                file_size = os.path.getsize(output_file)
                print(f"  Audio saved : {output_file} ({file_size:,} bytes)")
                print("\n  >>> RESULT: PASS <<<")
                return True
            else:
                print("  No audio data in response.")
                return False
        else:
            print(f"  >>> RESULT: FAIL <<<")
            print(f"  Error: {response.text[:500]}")
            return False
    except Exception as e:
        print(f"  >>> RESULT: FAIL ({type(e).__name__}: {e}) <<<")
        return False
    finally:
        print()


async def test_websocket_stream():
    """Test the WebSocket TTS Stream endpoint.
    
    WebSocket message format (from Sarvam API explorer):
    1. Config:  {"type": "config", "data": {"target_language_code": "en-IN", "speaker": "anushka", ...}}
    2. Text:    {"type": "text", "data": {"text": "hello"}}
    3. Receive: {"type": "audio", "data": {...}} or {"type": "error", "data": {...}}
    """
    print("=" * 60)
    print("TEST 3: WebSocket Text-to-Speech Stream")
    print("=" * 60)

    try:
        import websockets
    except ImportError:
        print("  Installing 'websockets' package...")
        os.system("pip install websockets -q")
        import websockets

    ws_url = f"{WS_URL}?model=bulbul:v2&send_completion_event=true"
    print(f"  Endpoint : {ws_url}")
    print()

    try:
        extra_headers = {"API-Subscription-Key": API_KEY}

        async with websockets.connect(
            ws_url,
            extra_headers=extra_headers,
            open_timeout=15,
        ) as ws:
            print("  WebSocket connected!")

            # Step 1: Send config message
            config_msg = {
                "type": "config",
                "data": {
                    "target_language_code": "en-IN",
                    "speaker": "anushka",
                    "pace": 1.0,
                    "pitch": 0.0,
                    "loudness": 1.0,
                },
            }
            print(f"  Sending config...")
            await ws.send(json.dumps(config_msg))

            # Step 2: Send text message
            text_msg = {
                "type": "text",
                "data": {
                    "text": "Hello, this is a streaming text to speech test.",
                },
            }
            print(f"  Sending text: '{text_msg['data']['text']}'")
            await ws.send(json.dumps(text_msg))

            # Step 3: Collect responses with timeout
            audio_chunks = []
            chunk_count = 0
            print("  Waiting for audio (15s timeout)...")

            try:
                while True:
                    message = await asyncio.wait_for(ws.recv(), timeout=15)
                    if isinstance(message, bytes):
                        audio_chunks.append(message)
                        chunk_count += 1
                        print(f"    Chunk #{chunk_count} ({len(message):,} bytes)")
                    else:
                        data = json.loads(message)
                        msg_type = data.get("type", "unknown")
                        print(f"    Event [{msg_type}]: {json.dumps(data)[:200]}")

                        if msg_type == "audio":
                            audio_b64 = data.get("data", {}).get("audio", "")
                            if audio_b64:
                                audio_chunks.append(base64.b64decode(audio_b64))
                                chunk_count += 1
                                print(f"    Decoded audio chunk #{chunk_count}")
                        elif msg_type in ("completion",):
                            print("    Completion event received!")
                            break
                        elif msg_type == "error":
                            err_msg = data.get("data", {}).get("message", "unknown")
                            print(f"    Server error: {err_msg}")
                            break
            except asyncio.TimeoutError:
                print("    Timed out waiting for response.")
            except websockets.exceptions.ConnectionClosed as e:
                print(f"    Connection closed: {e}")

            if audio_chunks:
                output_file = "test_output_stream.raw"
                with open(output_file, "wb") as f:
                    for chunk in audio_chunks:
                        f.write(chunk)
                file_size = os.path.getsize(output_file)
                print(f"\n  Total chunks : {chunk_count}")
                print(f"  Audio saved  : {output_file} ({file_size:,} bytes)")
                print("\n  >>> RESULT: PASS <<<")
                return True
            else:
                print("\n  No audio chunks received (server did not respond with audio).")
                return False

    except Exception as e:
        print(f"  >>> RESULT: FAIL ({type(e).__name__}: {e}) <<<")
        return False
    finally:
        print()


def main():
    print()
    print("+" + "-" * 58 + "+")
    print("|       Sarvam AI Text-to-Speech API Test Suite           |")
    print("+" + "-" * 58 + "+")
    print(f"  API Key: {API_KEY[:15]}...{API_KEY[-6:]}")
    print()

    results = {}

    # Test 1: REST API v2
    results["REST v2 (bulbul:v2)"] = test_rest_tts_v2()

    # Test 2: REST API v3
    results["REST v3 (bulbul:v3)"] = test_rest_tts_v3()

    # Test 3: WebSocket Stream
    try:
        results["WebSocket Stream"] = asyncio.run(test_websocket_stream())
    except Exception as e:
        print(f"  WebSocket test error: {e}")
        results["WebSocket Stream"] = False

    # Summary
    print()
    print("=" * 60)
    print("  RESULTS SUMMARY")
    print("=" * 60)
    for test_name, passed in results.items():
        status = "PASS" if passed else "FAIL"
        print(f"  [{status}] {test_name}")

    total_passed = sum(1 for v in results.values() if v)
    total = len(results)
    print(f"\n  {total_passed}/{total} tests passed")
    print("=" * 60)


if __name__ == "__main__":
    main()
