"""
Amazon Polly TTS Test Script
Tests realtime text-to-speech with Hindi and English voices.
"""
import boto3
import os
import sys

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

# AWS Credentials
AWS_ACCESS_KEY_ID = "AKIA3C7X6BGV764OTVIP"
AWS_SECRET_ACCESS_KEY = "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"
AWS_REGION = "ap-south-1"

polly = boto3.client(
    "polly",
    region_name=AWS_REGION,
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
)

# Test 1: List Hindi voices
print("=" * 50)
print("TEST 1: List Hindi Voices")
print("=" * 50)
try:
    voices = polly.describe_voices(LanguageCode="hi-IN")
    for v in voices["Voices"]:
        vid = v["Id"]
        gender = v["Gender"]
        engines = ", ".join(v.get("SupportedEngines", []))
        print(f"  {vid:12} | {gender:8} | {engines}")
    print(f"\n  Total Hindi voices: {len(voices['Voices'])}")
    print("  >>> PASS <<<")
except Exception as e:
    print(f"  >>> FAIL: {e} <<<")

# Test 2: Hindi TTS (Neural)
print()
print("=" * 50)
print("TEST 2: Hindi TTS (Kajal - Neural)")
print("=" * 50)
try:
    response = polly.synthesize_speech(
        Text="Namaste, main KisaanAI hoon. Aaj ka mandi bhav suniye.",
        OutputFormat="mp3",
        VoiceId="Kajal",
        Engine="neural",
        LanguageCode="hi-IN",
    )
    audio = response["AudioStream"].read()
    with open("test_polly_hindi.mp3", "wb") as f:
        f.write(audio)
    print(f"  Audio saved: test_polly_hindi.mp3 ({len(audio):,} bytes)")
    print(f"  Content-Type: {response['ContentType']}")
    print(f"  Chars used: {response['RequestCharacters']}")
    print("  >>> PASS <<<")
except Exception as e:
    print(f"  >>> FAIL: {e} <<<")

# Test 3: English TTS (Neural)
print()
print("=" * 50)
print("TEST 3: English TTS (Kajal - Neural)")
print("=" * 50)
try:
    response = polly.synthesize_speech(
        Text="Hello farmer! Today wheat price is 2500 rupees per quintal in Indore mandi.",
        OutputFormat="mp3",
        VoiceId="Kajal",
        Engine="neural",
        LanguageCode="hi-IN",
    )
    audio = response["AudioStream"].read()
    with open("test_polly_english.mp3", "wb") as f:
        f.write(audio)
    print(f"  Audio saved: test_polly_english.mp3 ({len(audio):,} bytes)")
    print("  >>> PASS <<<")
except Exception as e:
    print(f"  >>> FAIL: {e} <<<")

# Test 4: Streaming PCM (lowest latency for realtime)
print()
print("=" * 50)
print("TEST 4: Streaming PCM Audio (Realtime)")
print("=" * 50)
try:
    response = polly.synthesize_speech(
        Text="Kisaan bhai, aapka sawaal sunkar hum jawaab dete hain.",
        OutputFormat="pcm",
        SampleRate="16000",
        VoiceId="Kajal",
        Engine="neural",
        LanguageCode="hi-IN",
    )
    # Stream the audio
    stream = response["AudioStream"]
    chunks = []
    chunk_count = 0
    while True:
        chunk = stream.read(4096)
        if not chunk:
            break
        chunks.append(chunk)
        chunk_count += 1

    total_bytes = sum(len(c) for c in chunks)
    with open("test_polly_stream.pcm", "wb") as f:
        for c in chunks:
            f.write(c)
    print(f"  Chunks received: {chunk_count}")
    print(f"  Total audio: {total_bytes:,} bytes")
    print(f"  Format: PCM 16kHz (raw audio, lowest latency)")
    print(f"  Audio saved: test_polly_stream.pcm")
    print("  >>> PASS <<<")
except Exception as e:
    print(f"  >>> FAIL: {e} <<<")

print()
print("=" * 50)
print("ALL POLLY TESTS COMPLETED")
print("=" * 50)
