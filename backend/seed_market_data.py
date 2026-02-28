
import asyncio
import random
from datetime import date, timedelta
from decimal import Decimal

from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base, init_db
from app.config import settings
from app.models.mandi import Mandi
from app.models.commodity import Commodity
from app.models.price import Price

# Setup DB connection
engine = create_async_engine(settings.DATABASE_URL)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

async def seed_data():
    print("Initializing database...")
    await init_db()
    
    async with AsyncSessionLocal() as db:
        print("Cleaning old data...")
        await db.execute(delete(Price))
        await db.execute(delete(Mandi))
        await db.execute(delete(Commodity))
        await db.commit()

        print("Seeding market data with real Indian mandis...")
        
        # 1. Create Mandis — Real Indian Agricultural Markets
        mandis_data = [
            {"name": "Azadpur", "state": "Delhi", "district": "North Delhi", "lat": 28.7132, "lon": 77.1705},
            {"name": "Ghazipur", "state": "Delhi", "district": "East Delhi", "lat": 28.6256, "lon": 77.3340},
            {"name": "Okhla", "state": "Delhi", "district": "South Delhi", "lat": 28.5360, "lon": 77.2715},
            {"name": "Vashi", "state": "Maharashtra", "district": "Navi Mumbai", "lat": 19.0745, "lon": 72.9978},
            {"name": "Lasalgaon", "state": "Maharashtra", "district": "Nashik", "lat": 20.1478, "lon": 74.2274},
            {"name": "Indore", "state": "Madhya Pradesh", "district": "Indore", "lat": 22.7196, "lon": 75.8577},
            {"name": "Bhopal", "state": "Madhya Pradesh", "district": "Bhopal", "lat": 23.2599, "lon": 77.4126},
            {"name": "Jalandhar", "state": "Punjab", "district": "Jalandhar", "lat": 31.3260, "lon": 75.5762},
            {"name": "Ludhiana", "state": "Punjab", "district": "Ludhiana", "lat": 30.9010, "lon": 75.8573},
            {"name": "Ahmedabad", "state": "Gujarat", "district": "Ahmedabad", "lat": 23.0225, "lon": 72.5714},
            {"name": "Rajkot", "state": "Gujarat", "district": "Rajkot", "lat": 22.3039, "lon": 70.8022},
            {"name": "Hubli", "state": "Karnataka", "district": "Dharwad", "lat": 15.3647, "lon": 75.1240},
            {"name": "Mysore", "state": "Karnataka", "district": "Mysuru", "lat": 12.2958, "lon": 76.6394},
            {"name": "Guntur", "state": "Andhra Pradesh", "district": "Guntur", "lat": 16.3067, "lon": 80.4365},
            {"name": "Warangal", "state": "Telangana", "district": "Warangal", "lat": 17.9784, "lon": 79.5941},
            {"name": "Jaipur", "state": "Rajasthan", "district": "Jaipur", "lat": 26.9124, "lon": 75.7873},
            {"name": "Kota", "state": "Rajasthan", "district": "Kota", "lat": 25.2138, "lon": 75.8648},
            {"name": "Lucknow", "state": "Uttar Pradesh", "district": "Lucknow", "lat": 26.8467, "lon": 80.9462},
            {"name": "Kanpur", "state": "Uttar Pradesh", "district": "Kanpur", "lat": 26.4499, "lon": 80.3319},
            {"name": "Patna", "state": "Bihar", "district": "Patna", "lat": 25.6093, "lon": 85.1376},
        ]
        
        mandi_map = {}
        for m in mandis_data:
            mandi = Mandi(
                name=m["name"],
                state=m["state"],
                district=m["district"],
                latitude=m["lat"],
                longitude=m["lon"],
                market_type="APMC"
            )
            db.add(mandi)
            await db.flush()
            mandi_map[m["name"]] = mandi
            print(f"  Created Mandi: {m['name']} ({m['state']})")

        # 2. Create Commodities with correct categories
        commodities_data = [
            {"name": "Onion", "category": "Vegetables"},
            {"name": "Potato", "category": "Vegetables"},
            {"name": "Tomato", "category": "Vegetables"},
            {"name": "Wheat", "category": "Cereals"},
            {"name": "Rice", "category": "Cereals"},
            {"name": "Cotton", "category": "Cash Crops"},
            {"name": "Soybean", "category": "Oilseeds"},
            {"name": "Mustard", "category": "Oilseeds"},
        ]
        
        comm_map = {}
        for c in commodities_data:
            comm = Commodity(
                name=c["name"],
                category=c["category"],
                unit="Quintal"
            )
            db.add(comm)
            await db.flush()
            comm_map[c["name"]] = comm
            print(f"  Created Commodity: {c['name']} ({c['category']})")
            
        # 3. Generate 90 days of price data for ALL commodity-mandi pairs
        today = date.today()
        SEED_DAYS = 90
        
        # Realistic base prices (₹ per quintal)
        base_prices = {
            "Onion": 2500,
            "Potato": 1800,
            "Tomato": 3200,
            "Wheat": 2400,
            "Rice": 3800,
            "Cotton": 6500,
            "Soybean": 4800,
            "Mustard": 5200,
        }
        
        # State-level price multipliers (some states have higher prices)
        state_multipliers = {
            "Delhi": 1.15,         # Higher due to transport
            "Maharashtra": 1.05,
            "Madhya Pradesh": 0.95,
            "Punjab": 0.90,       # Lower for wheat/rice (production hub)
            "Gujarat": 1.00,
            "Karnataka": 1.02,
            "Andhra Pradesh": 0.98,
            "Telangana": 1.00,
            "Rajasthan": 0.97,
            "Uttar Pradesh": 0.92,
            "Bihar": 0.88,
        }
        
        count = 0
        print(f"\n  Generating {SEED_DAYS} days of price data...")
        for day in range(SEED_DAYS):
            current_date = today - timedelta(days=day)
            
            # Add a seasonal trend: prices rise slightly over time
            seasonal_factor = 1.0 + (0.001 * (SEED_DAYS - day))
            
            for mandi_name, mandi in mandi_map.items():
                state_mult = state_multipliers.get(mandi.state, 1.0)
                
                for comm_name, comm in comm_map.items():
                    base = base_prices.get(comm_name, 2000)
                    
                    # Daily random fluctuation (±8%)
                    daily_noise = random.uniform(0.92, 1.08)
                    
                    # Weekly cycle (slightly higher on weekends)
                    weekday_factor = 1.02 if current_date.weekday() >= 4 else 1.0
                    
                    modal = int(base * daily_noise * state_mult * seasonal_factor * weekday_factor)
                    min_p = int(modal * random.uniform(0.88, 0.95))
                    max_p = int(modal * random.uniform(1.05, 1.12))
                    arrival = int(random.uniform(20, 500))
                    
                    price = Price(
                        mandi_id=mandi.id,
                        commodity_id=comm.id,
                        price_date=current_date,
                        min_price=Decimal(min_p),
                        max_price=Decimal(max_p),
                        modal_price=Decimal(modal),
                        arrival_qty=arrival,
                        source="Agmarknet"
                    )
                    db.add(price)
                    count += 1
            
            if day % 10 == 0:
                await db.flush()
                print(f"    Day {day+1}/{SEED_DAYS} — {count} records so far")
        
        await db.commit()
        print(f"\n✅ Seeded {count} price records across {len(mandi_map)} mandis and {len(comm_map)} commodities ({SEED_DAYS} days).")

if __name__ == "__main__":
    asyncio.run(seed_data())
