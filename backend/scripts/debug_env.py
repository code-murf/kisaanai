import sys
import os

print(f"Python Executable: {sys.executable}")
print(f"Current Working Directory: {os.getcwd()}")
print("System Path:")
for p in sys.path:
    print(f"  - {p}")

try:
    import elevenlabs
    print(f"✅ elevenlabs imported successfully from {elevenlabs.__file__}")
except ImportError as e:
    print(f"❌ ImportError: {e}")

try:
    import pydantic
    print(f"✅ pydantic imported successfully version {pydantic.VERSION}")
except ImportError:
    print("❌ pydantic not found")
except AttributeError:
    print("✅ pydantic imported (version unknown)")
