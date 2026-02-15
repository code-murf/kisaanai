
import asyncio
import random
from datetime import date, timedelta
from decimal import Decimal

from sqlalchemy import select
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
        print("Seeding market data...")
        
        # 1. Create Mandis
        mandis_data = [
            {"name": "Azadpur", "state": "Delhi", "district": "North Delhi", "lat": 28.7132, "lon": 77.1705},
            {"name": "Ghazipur", "state": "Delhi", "district": "East Delhi", "lat": 28.6256, "lon": 77.3340},
            {"name": "Okhla", "state": "Delhi", "district": "South Delhi", "lat": 28.5360, "lon": 77.2715},
            {"name": "Vashi", "state": "Maharashtra", "district": "Mumbai", "lat": 19.0745, "lon": 72.9978},
            {"name": "Lasalgaon", "state": "Maharashtra", "district": "Nashik", "lat": 20.1478, "lon": 74.2274},
        ]
        
        mandi_map = {}
        for m in mandis_data:
            result = await db.execute(select(Mandi).where(Mandi.name == m["name"]))
            mandi = result.scalar_one_or_none()
            if not mandi:
                mandi = Mandi(
                    name=m["name"],
                    state=m["state"],
                    district=m["district"],
                    latitude=m["lat"],
                    longitude=m["lon"],
                    market_type="Regulated"
                )
                db.add(mandi)
                await db.commit()
                await db.refresh(mandi)
                print(f"Created Mandi: {m['name']}")
            else:
                print(f"Mandi exists: {m['name']}")
            mandi_map[m["name"]] = mandi

        # 2. Create Commodities
        commodities_data = [
            {"name": "Onion", "category": "Vegetables"},
            {"name": "Potato", "category": "Vegetables"},
            {"name": "Tomato", "category": "Vegetables"},
            {"name": "Wheat", "category": "Cereals"},
            {"name": "Rice", "category": "Cereals"},
        ]
        
        comm_map = {}
        for c in commodities_data:
            result = await db.execute(select(Commodity).where(Commodity.name == c["name"]))
            comm = result.scalar_one_or_none()
            if not comm:
                comm = Commodity(
                    name=c["name"],
                    category=c["category"],
                    unit="Quintal"
                )
                db.add(comm)
                await db.commit()
                await db.refresh(comm)
                print(f"Created Commodity: {c['name']}")
            else:
                print(f"Commodity exists: {c['name']}")
            comm_map[c["name"]] = comm
            
        # 3. Generate Prices for last 30 days
        today = date.today()
        
        # Price ranges (Base price)
        base_prices = {
            "Onion": 2500,
            "Potato": 1200,
            "Tomato": 3000,
            "Wheat": 2200,
            "Rice": 3500
        }
        
        count = 0
        for day in range(30):
            current_date = today - timedelta(days=day)
            
            for mandi_name, mandi in mandi_map.items():
                for comm_name, comm in comm_map.items():
                    # Check if price exists
                    result = await db.execute(
                        select(Price).where(
                            Price.mandi_id == mandi.id,
                            Price.commodity_id == comm.id,
                            Price.price_date == current_date
                        )
                    )
                    if result.scalar_one_or_none():
                        continue
                        
                    # Generate random fluctuation
                    base = base_prices.get(comm_name, 2000)
                    # Add some randomness (+- 10%)
                    fluctuation = random.uniform(0.9, 1.1)
                    # Add some slight location variance
                    loc_var = 1.05 if mandi.state == "Maharashtra" and comm_name == "Onion" else 1.0
                    
                    modal = int(base * fluctuation * loc_var)
                    min_p = int(modal * 0.95)
                    max_p = int(modal * 1.05)
                    arrival = int(random.uniform(50, 500))
                    
                    price = Price(
                        mandi_id=mandi.id,
                        commodity_id=comm.id,
                        price_date=current_date,
                        min_price=Decimal(min_p),
                        max_price=Decimal(max_p),
                        modal_price=Decimal(modal),
                        arrival_qty=arrival,
                        source="Simulated"
                    )
                    db.add(price)
                    count += 1
        
        await db.commit()
        print(f"Seeded {count} price records.")

if __name__ == "__main__":
    asyncio.run(seed_data())
