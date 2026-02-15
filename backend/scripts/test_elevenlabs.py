import requests
import os
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("ELEVENLABS_API_KEY")
BASE_URL = "https://api.elevenlabs.io/v1"

def test_api_key():
    print(f"Testing API Key: {API_KEY[:5]}...{API_KEY[-5:] if API_KEY else 'None'}")
    
    if not API_KEY:
        print("❌ No API Key found in .env")
        return

    headers = {
        "xi-api-key": API_KEY
    }
    
    # 1. Verify User (General API Check)
    try:
        response = requests.get(f"{BASE_URL}/user", headers=headers)
        if response.status_code == 200:
            user_data = response.json()
            print(f"✅ API Key Verified!")
            print(f"   User: {user_data.get('subscription', {}).get('tier', 'Unknown')}")
            print(f"   Credits: {user_data.get('subscription', {}).get('character_count', 0)} / {user_data.get('subscription', {}).get('character_limit', 0)}")
        else:
            print(f"❌ API Key Check Failed: {response.status_code} - {response.text}")
            return
    except Exception as e:
        print(f"❌ connection error: {e}")
        return

    # 2. Check for Agents (Conversational AI)
    # Note: Endpoint might be /convai/agents or similar based on new features
    print("\nChecking for configured Agents...")
    try:
        # Trying probable endpoints for Agents
        agent_endpoints = [
            f"{BASE_URL}/convai/agents",
            f"{BASE_URL}/agents", # Generic guess
        ]
        
        found = False
        for url in agent_endpoints:
            resp = requests.get(url, headers=headers)
            if resp.status_code == 200:
                agents = resp.json()
                print(f"✅ Found Agents Endpoint: {url}")
                print(f"   Agents Found: {len(agents.get('agents', []))}")
                for agent in agents.get('agents', []):
                    print(f"   - {agent.get('name')} (ID: {agent.get('agent_id')})")
                found = True
                break
            elif resp.status_code != 404:
                print(f"⚠️ Endpoint {url} returned {resp.status_code}")
        
        if not found:
            print("⚠️ Could not locate standard Agents list via API (might be experimental/private beta endpoint).")
            print("   Please check the documentation for the exact 'Get Agents' URL.")

    except Exception as e:
        print(f"❌ Agent check error: {e}")

if __name__ == "__main__":
    test_api_key()
