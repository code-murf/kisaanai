
import asyncio
import logging
from app.scraper.agmarknet_scraper import run_scraper

# Configure logging
logging.basicConfig(level=logging.INFO)

async def test_scraper():
    print("Starting scraper test...")
    try:
        # Test 1: Fetch Onion prices in Delhi (usually available)
        result = await run_scraper(
            state="Delhi", # Agmarknet specific state name? usually "Delhi" or "NCT of Delhi"
            commodity="Onion"
        )
        
        if result.success:
            print(f"Success! Scraped {len(result.prices)} records.")
            if result.prices:
                print("Sample Price:", result.prices[0])
        else:
            print("Scraper reported failure.")
            print("Errors:", result.errors)
            
    except Exception as e:
        print(f"Test failed with exception: {e}")

if __name__ == "__main__":
    asyncio.run(test_scraper())
