import asyncio
from app.services.ai_service import get_ai_service
from app.config import settings

async def main():
    service = get_ai_service()
    
    with open("test_out2.txt", "w", encoding="utf-8") as f:
        # 1. Test Weather Tool
        f.write("Testing Weather Request...\n")
        weather_res = await service.process_voice_query(
            transcribed_text="What is the weather like today?",
            lat=28.7041,  # Delhi
            lon=77.1025
        )
        f.write("WEATHER RESPONSE:\n")
        f.write(weather_res["response"] + "\n")
        f.write("-" * 50 + "\n")
        
        # 3. Test Hindi Crop Names (Should invoke Mandi prices after translating to English)
        f.write("Testing Hindi Price Request...\n")
        hindi_price_res = await service.process_voice_query(
            transcribed_text="गाजर का मंडी मूल्य क्या है?", # Carrots
            lat=28.7041,
            lon=77.1025
        )
        f.write("HINDI PRICE RESPONSE:\n")
        f.write(hindi_price_res["response"] + "\n")
        f.write("-" * 50 + "\n")
        
        # 4. Test Web Search Tool
        f.write("Testing Web Search Request...\n")
        search_res = await service.process_voice_query(
            transcribed_text="What is the latest PM Kisan Yojana 18th installment release date?",
            lat=28.7041,
            lon=77.1025
        )
        f.write("SEARCH RESPONSE:\n")
        f.write(search_res["response"] + "\n")
        f.write("-" * 50 + "\n")
        
        # 3. Test General Knowledge (No Tool)
        f.write("Testing General Request...\n")
        general_res = await service.process_voice_query(
            transcribed_text="How should I use fertilizer for wheat?",
        )
        f.write("GENERAL RESPONSE:\n")
        f.write(general_res["response"] + "\n")

if __name__ == "__main__":
    asyncio.run(main())
