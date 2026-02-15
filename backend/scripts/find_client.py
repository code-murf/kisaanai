import elevenlabs
import inspect

print(f"ElevenLabs Version: {getattr(elevenlabs, '__version__', 'Unknown')}")

# search for likely client classes
for name, obj in inspect.getmembers(elevenlabs):
    if "Client" in name or "ElevenLabs" in name:
        print(f"Found candidate: {name} -> {obj}")

# check if conversational_ai is exposed
if hasattr(elevenlabs, 'conversational_ai'):
    print("Found conversational_ai module directly on elevenlabs")

# check for agents
if hasattr(elevenlabs, 'agents'):
    print("Found agents module directly on elevenlabs")
