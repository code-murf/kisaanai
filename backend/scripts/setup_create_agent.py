import os
import time
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("ELEVENLABS_API_KEY")

try:
    from elevenlabs import ElevenLabs
    client = ElevenLabs(api_key=API_KEY)
    print("✅ ElevenLabs SDK imported.")
    
    # Check for Agents capabilities
    print("\n--- Inspecting Client ---")
    print("Client attributes:", [d for d in dir(client) if not d.startswith("_")])
    
    # Try to find Conversational AI / Agents
    agent_client = None
    if hasattr(client, 'conversational_ai'):
        print("Found 'conversational_ai' namespace")
        agent_client = client.conversational_ai
    elif hasattr(client, 'agents'):
        print("Found 'agents' namespace")
        agent_client = client.agents
    
    if agent_client:
        print("Agent Client attributes:", [d for d in dir(agent_client) if not d.startswith("_")])
        
        # Check if we can list or create
        # Note: Actual method names might differ, this is exploratory
        
        # Try listing first
        try:
            print("\nAttempting to list agents...")
            # Common patterns: get_all(), list(), etc.
            if hasattr(agent_client, 'get_all'):
                agents = agent_client.get_all()
                print(f"Agents found via get_all: {agents}")
            elif hasattr(agent_client, 'list'):
                agents = agent_client.list()
                print(f"Agents found via list: {agents}")
        except Exception as e:
            print(f"Error listing agents: {e}")

except ImportError as e:
    print(f"❌ Initial import failed: {e}")
    try:
        from elevenlabs.client import ElevenLabs
        print("✅ Found ElevenLabs in elevenlabs.client")
        client = ElevenLabs(api_key=API_KEY)
        # Check if conversational_ai is present
        if hasattr(client, 'conversational_ai'):
             print("✅ client.conversational_ai exists")
        else:
             print("⚠️ client.conversational_ai MISSING")
             # Try to manually attach or use sub-client if possible
             from elevenlabs.conversational_ai.client import ConversationalAiClient
             print("✅ Imported ConversationalAiClient directly")
    except ImportError as e2:
        print(f"❌ Import from elevenlabs.client failed: {e2}")
        # Debugging: check what IS in elevenlabs.client
        import elevenlabs.client
        print(f"DEBUG: dir(elevenlabs.client) = {[x for x in dir(elevenlabs.client) if not x.startswith('_')]}")
        try:
            import elevenlabs
            print(f"dir(elevenlabs): {dir(elevenlabs)[:20]}")
            if hasattr(elevenlabs, 'client'):
                 print(f"dir(elevenlabs.client): {dir(elevenlabs.client)[:20]}")
        except Exception as e3:
            print(f"Could not inspect module: {e3}")
except Exception as e:
    print(f"❌ Error during setup: {e}")
