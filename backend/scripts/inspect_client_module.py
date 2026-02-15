import elevenlabs
import pkgutil
import sys

print(f"Version: {elevenlabs.__version__}")

print("\nSubmodules:")
for _, name, _ in pkgutil.iter_modules(elevenlabs.__path__):
    print(f" - {name}")

print("\nAttempting to import elevenlabs.client...")
try:
    import elevenlabs.client
    print("✅ success")
    print(f"dir(elevenlabs.client): {[x for x in dir(elevenlabs.client) if not x.startswith('_')]}")
except ImportError as e:
    print(f"❌ failed: {e}")

print("\nAttempting to import elevenlabs.agents...")
try:
    import elevenlabs.agents
    print("✅ success")
    print(f"dir(elevenlabs.agents): {[x for x in dir(elevenlabs.agents) if not x.startswith('_')]}")
except ImportError as e:
    print(f"❌ failed: {e}")

print("\nAttempting to import elevenlabs.conversational_ai...")
try:
    import elevenlabs.conversational_ai
    print("✅ success")
    print(f"dir(elevenlabs.conversational_ai): {[x for x in dir(elevenlabs.conversational_ai) if not x.startswith('_')]}")
except ImportError as e:
    print(f"❌ failed: {e}")
