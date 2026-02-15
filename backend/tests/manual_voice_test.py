
import requests
import wave
import struct

# 1. Create a dummy WAV file (1 sec of silence)
filename = "test_audio.wav"
try:
    with wave.open(filename, 'w') as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(16000)
        # Write 16000 frames of silence (0)
        wav_file.writeframes(struct.pack('<' + ('h'*16000), *([0]*16000)))
    print(f"Created dummy audio: {filename}")
except Exception as e:
    print(f"Failed to create wav: {e}")
    exit(1)

# 2. Send to API
url = "http://localhost:8000/api/v1/voice/query"
try:
    with open(filename, 'rb') as f:
        files = {'file': (filename, f, 'audio/wav')}
        data = {'language': 'hi-IN'}
        
        print(f"Sending request to {url}...")
        response = requests.post(url, files=files, data=data) 
        
        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            print("Response JSON:")
            res_json = response.json()
            print(f"Query: {res_json.get('query')}")
            print(f"Response: {res_json.get('response')}")
            print(f"Audio Length (Base64): {len(res_json.get('audio', ''))}")
        else:
            print("Error Response:")
            print(response.text)

except Exception as e:
    print(f"Request failed: {e}")
