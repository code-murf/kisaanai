import asyncio
import logging
import base64

from app.services.disease_service import DiseaseService
from app.services.bedrock_service import bedrock_service

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("app.services.disease_service")

async def test():
    image_bytes = base64.b64decode("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII=")
    
    svc = DiseaseService()
    try:
        print("Testing full prediction pipeline...")
        res = await svc.predict(image_bytes, "test.png")
        print("Success:", res)
    except Exception as e:
        print("Error:", e)
        
if __name__ == "__main__":
    asyncio.run(test())
