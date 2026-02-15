import os
import requests
import json
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("ELEVENLABS_API_KEY")
BASE_URL = "https://api.elevenlabs.io/v1/convai"

headers = {
    "xi-api-key": API_KEY,
    "Content-Type": "application/json"
}

def get_agents():
    url = f"{BASE_URL}/agents"
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            return response.json().get("agents", [])
        else:
            print(f"Error fetching agents: {response.text}")
            return []
    except Exception as e:
        print(f"Connection error: {e}")
        return []

def create_agribot():
    # Check if exists
    agents = get_agents()
    for agent in agents:
        if agent.get("name") == "AgriBot":
            print(f"✅ AgriBot already exists! Agent ID: {agent.get('agent_id')}")
            return agent.get("agent_id")

    print("Creating AgriBot...")
    url = f"{BASE_URL}/agents/create"
    
    # Configuration for AgriBot
    payload = {
        "name": "AgriBot",
        "conversation_config": {
            "agent": {
                "prompt": {
                    "prompt": "You are AgriBot, an expert agricultural advisor for Indian farmers. You help with crop advice, market prices from Mandis, and weather forecasts. You speak in a helpful, encouraging tone. Keep answers concise. If asked about prices, ask for the specific commodity and mandi. If asked about weather, ask for the location. You support Hindi and English.",
                    "llm": "gpt-4o-mini", # or gemini-1.5-flash if supported, trying standard
                    "temperature": 0.5
                },
                "first_message": "Namaste! I am AgriBot. How can I help you with your farming today?",
                "language": "hi" # Hindi support
            },
            "asr": {
                "quality": "high",
                "provider": "elevenlabs"
            },
            "tts": {
                "voice_id": "JBFqnCBsd6RMkjVDRZzb", # George - calm and reassuring
                "model_id": "eleven_turbo_v2_5" # Low latency
            }
        },
        "platform_settings": {
            "widget": {
                "variant": "compact",
                "expand_on_first_message": True
            }
        }
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload)
        if response.status_code == 200:
            data = response.json()
            agent_id = data.get("agent_id")
            print(f"🎉 Successfully created AgriBot! Agent ID: {agent_id}")
            return agent_id
        else:
            print(f"❌ Failed to create agent: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"❌ Error creating agent: {e}")
        return None

if __name__ == "__main__":
    if not API_KEY:
        print("❌ ELEVENLABS_API_KEY not found in .env")
    else:
        create_agribot()
