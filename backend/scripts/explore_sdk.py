import elevenlabs
from elevenlabs import client

print("elevenlabs dir:", dir(elevenlabs))
try:
    print("elevenlabs.client dir:", dir(client))
except:
    pass

try:
    c = client.ElevenLabs(api_key="foo")
    print("ElevenLabs client dir:", dir(c))
    if hasattr(c, 'conversational_ai'):
        print("conversational_ai dir:", dir(c.conversational_ai))
    if hasattr(c, 'convai'):
        print("convai dir:", dir(c.convai))
except Exception as e:
    print(e)
