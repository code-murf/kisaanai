"""
Price Service for querying current and historical commodity prices.
"""
from datetime import date, datetime, timedelta
from decimal import Decimal
from typing import List, Optional, Tuple
import math

from sqlalchemy import select, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.models.price import Price
from app.models.commodity import Commodity
from app.models.mandi import Mandi
from app.schemas import (
    PriceCreate,
    PriceResponse,
    PriceWithDetailsResponse,
    PriceListResponse,
    PriceHistoryRequest,
    PriceTrendPoint,
)


class PriceService:
    """Service class for price operations."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_by_id(self, price_id: int) -> Optional[Price]:
        """Get a price record by ID."""
        result = await self.db.execute(
            select(Price).where(Price.id == price_id)
        )
        return result.scalar_one_or_none()
    
    async def get_current_price(
        self,
        commodity_id: int,
        mandi_id: int,
    ) -> Optional[Price]:
        """Get the latest price for a commodity at a specific mandi."""
        result = await self.db.execute(
            select(Price)
            .where(
                and_(
                    Price.commodity_id == commodity_id,
                    Price.mandi_id == mandi_id,
                )
            )
            .order_by(Price.price_date.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()
    
    async def get_current_prices_by_commodity(
        self,
        commodity_id: int,
        state: Optional[str] = None,
        limit: int = 20,
    ) -> List[Price]:
        """
        Get latest prices for a commodity across all mandis.
        
        Uses a subquery to get the latest price date for each mandi,
        then joins to get the actual price records.
        """
        # Subquery to get latest price date per mandi for this commodity
        latest_dates_subq = (
            select(
                Price.mandi_id,
                func.max(Price.price_date).label("latest_date")
            )
            .where(Price.commodity_id == commodity_id)
            .group_by(Price.mandi_id)
            .subquery()
        )
        
        # Main query joining with the subquery
        query = (
            select(Price)
            .join(
                latest_dates_subq,
                and_(
                    Price.mandi_id == latest_dates_subq.c.mandi_id,
                    Price.price_date == latest_dates_subq.c.latest_date,
                )
            )
            .where(Price.commodity_id == commodity_id)
            .options(joinedload(Price.mandi), joinedload(Price.commodity))
        )
        
        if state:
            query = query.join(Mandi).where(Mandi.state == state)
        
        query = query.limit(limit)
        
        try:
            result = await self.db.execute(query)
            prices = result.unique().scalars().all()
            if not prices:
                return self._get_mock_prices_by_commodity(commodity_id)
            return prices
        except Exception as e:
            print(f"DB Error: {e}")
            return self._get_mock_prices_by_commodity(commodity_id)

    def _get_mock_prices_by_commodity(self, commodity_id: int) -> List[Price]:
        """Generate mock prices if DB is empty or fails."""
        # Mock Mandis
        mandis = [
            Mandi(id=1, name="Azadpur", state="Delhi", district="North Delhi", latitude=28.7, longitude=77.1),
            Mandi(id=2, name="Ghazipur", state="Delhi", district="East Delhi", latitude=28.6, longitude=77.3),
            Mandi(id=3, name="Vashi", state="Maharashtra", district="Mumbai", latitude=19.0, longitude=73.0),
            Mandi(id=4, name="Lasalgaon", state="Maharashtra", district="Nashik", latitude=20.1, longitude=74.2),
            Mandi(id=5, name="Kolar", state="Karnataka", district="Kolar", latitude=13.1, longitude=78.1),
        ]
        
        # Mock Commodity
        # We don't have the name from ID easily without query, so generic
        comm = Commodity(id=commodity_id, name=f"Commodity {commodity_id}", category="Vegetables", unit="Quintal")
        
        prices = []
        import random
        base_price = 2000 + (commodity_id * 100)
        
        for mandi in mandis:
            modal = base_price + random.randint(-200, 200)
            prices.append(Price(
                id=random.randint(1000, 9999),
                mandi_id=mandi.id,
                commodity_id=commodity_id,
                price_date=date.today(),
                min_price=Decimal(modal * 0.9),
                max_price=Decimal(modal * 1.1),
                modal_price=Decimal(modal),
                arrival_qty=random.randint(50, 500),
                source="Mock",
                mandi=mandi,
                commodity=comm
            ))
        return prices
    
    async def get_current_prices_by_mandi(
        self,
        mandi_id: int,
        category: Optional[str] = None,
        limit: int = 50,
    ) -> List[Price]:
        """
        Get latest prices for all commodities at a specific mandi.
        """
        # Subquery to get latest price date per commodity for this mandi
        latest_dates_subq = (
            select(
                Price.commodity_id,
                func.max(Price.price_date).label("latest_date")
            )
            .where(Price.mandi_id == mandi_id)
            .group_by(Price.commodity_id)
            .subquery()
        )
        
        # Main query
        query = (
            select(Price)
            .join(
                latest_dates_subq,
                and_(
                    Price.commodity_id == latest_dates_subq.c.commodity_id,
                    Price.price_date == latest_dates_subq.c.latest_date,
                )
            )
            .where(Price.mandi_id == mandi_id)
            .options(joinedload(Price.mandi), joinedload(Price.commodity))
        )
        
        if category:
            query = query.join(Commodity).where(Commodity.category == category)
        
        query = query.limit(limit)
        
        result = await self.db.execute(query)
        return result.unique().scalars().all()
    
    async def get_price_history(
        self,
        commodity_id: int,
        mandi_id: Optional[int] = None,
        state: Optional[str] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        days: int = 30,
        page: int = 1,
        page_size: int = 100,
    ) -> Tuple[List[Price], int]:
        """
        Get historical prices for a commodity with optional filters.
        
        Args:
            commodity_id: Required commodity ID
            mandi_id: Optional specific mandi ID
            state: Optional state filter (averages across mandis in state)
            start_date: Optional start date
            end_date: Optional end date
            days: Number of days to look back if start_date not provided
            page: Page number
            page_size: Items per page
        
        Returns:
            Tuple of (list of prices, total count)
        """
        # Default date range
        if not start_date:
            start_date = date.today() - timedelta(days=days)
        if not end_date:
            end_date = date.today()
        
        query = (
            select(Price)
            .where(
                and_(
                    Price.commodity_id == commodity_id,
                    Price.price_date >= start_date,
                    Price.price_date <= end_date,
                )
            )
            .options(joinedload(Price.mandi), joinedload(Price.commodity))
        )
        
        count_query = (
            select(func.count(Price.id))
            .where(
                and_(
                    Price.commodity_id == commodity_id,
                    Price.price_date >= start_date,
                    Price.price_date <= end_date,
                )
            )
        )
        
        if mandi_id:
            query = query.where(Price.mandi_id == mandi_id)
            count_query = count_query.where(Price.mandi_id == mandi_id)
        elif state:
            query = query.join(Mandi).where(Mandi.state == state)
            count_query = count_query.join(Mandi).where(Mandi.state == state)
        
        # Get total count
        total_result = await self.db.execute(count_query)
        total = total_result.scalar()
        
        # Apply pagination and ordering
        offset = (page - 1) * page_size
        query = query.offset(offset).limit(page_size).order_by(Price.price_date.desc())
        
        try:
            result = await self.db.execute(query)
            prices = result.unique().scalars().all()
            
            if not prices:
                 return self._get_mock_price_history(commodity_id, days), 30
            
            return list(prices), total
        except Exception as e:
            print(f"DB Error (History): {e}")
            return self._get_mock_price_history(commodity_id, days), 30

    def _get_mock_price_history(self, commodity_id: int, days: int) -> List[Price]:
        """Generate mock history."""
        prices = []
        import random
        today = date.today()
        base_price = 2500
        
        # Mock Mandi and Commodity
        mandi = Mandi(id=1, name="Azadpur", state="Delhi", district="North Delhi", latitude=28.7, longitude=77.1)
        comm = Commodity(id=commodity_id, name="Onion", category="Vegetables", unit="Quintal")

        for i in range(days):
            d = today - timedelta(days=i)
            # Add trend
            trend = math.sin(i / 5) * 200
            modal = base_price + trend + random.randint(-50, 50)
            
            prices.append(Price(
                id=i+1,
                mandi_id=1,
                commodity_id=commodity_id,
                price_date=d,
                min_price=Decimal(modal * 0.95),
                max_price=Decimal(modal * 1.05),
                modal_price=Decimal(modal),
                arrival_qty=random.randint(100, 1000),
                source="Mock",
                mandi=mandi,
                commodity=comm
            ))
        return prices
        
        return list(prices), total
    
    async def get_price_trend(
        self,
        commodity_id: int,
        mandi_id: Optional[int] = None,
        state: Optional[str] = None,
        days: int = 90,
    ) -> List[PriceTrendPoint]:
        """
        Get price trend data points for visualization.
        
        Returns daily modal prices aggregated by date.
        If multiple mandis, returns average modal price.
        """
        start_date = date.today() - timedelta(days=days)
        
        query = (
            select(
                Price.price_date,
                func.avg(Price.modal_price).label("avg_modal"),
                func.min(Price.min_price).label("min_price"),
                func.max(Price.max_price).label("max_price"),
                func.sum(Price.arrival_qty).label("total_arrival"),
            )
            .where(
                and_(
                    Price.commodity_id == commodity_id,
                    Price.price_date >= start_date,
                )
            )
            .group_by(Price.price_date)
            .order_by(Price.price_date)
        )
        
        if mandi_id:
            query = query.where(Price.mandi_id == mandi_id)
        elif state:
            query = query.join(Mandi).where(Mandi.state == state)
        
        try:
            result = await self.db.execute(query)
            rows = result.all()
            
            trends = []
            for row in rows:
                trends.append(
                    PriceTrendPoint(
                        date=row.price_date,
                        modal_price=Decimal(str(row.avg_modal)),
                        min_price=row.min_price,
                        max_price=row.max_price,
                        arrival_qty=row.total_arrival,
                    )
                )
            
            if not trends:
                return self._get_mock_price_trend(days)
            
            return trends
        except Exception as e:
             print(f"DB Error (Trend): {e}")
             return self._get_mock_price_trend(days)

    def _get_mock_price_trend(self, days: int) -> List[PriceTrendPoint]:
        """Generate mock trend."""
        trends = []
        import random
        today = date.today()
        
        for i in range(days):
            d = today - timedelta(days=days-1-i) # Ascending order
            # Add sinusoidal trend
            val = 2000 + math.sin(i / 3) * 300 + random.randint(-50, 50)
            
            trends.append(PriceTrendPoint(
                date=d,
                modal_price=Decimal(int(val)),
                min_price=Decimal(int(val * 0.9)),
                max_price=Decimal(int(val * 1.1)),
                arrival_qty=random.randint(100, 1000)
            ))
        return trends
    
    async def get_price_comparison(
        self,
        commodity_id: int,
        mandi_ids: List[int],
    ) -> List[PriceWithDetailsResponse]:
        """
        Compare current prices for a commodity across multiple mandis.
        """
        prices = []
        for mandi_id in mandi_ids:
            price = await self.get_current_price(commodity_id, mandi_id)
            if price:
                prices.append(price)
        
        return prices
    
    async def get_top_gainers(
        self,
        state: Optional[str] = None,
        days: int = 7,
        limit: int = 10,
    ) -> List[dict]:
        """
        Get commodities with highest price increase in the given period.
        
        Returns list of dicts with commodity info and price change percentage.
        """
        end_date = date.today()
        start_date = end_date - timedelta(days=days)
        
        # Get latest prices
        latest_subq = (
            select(
                Price.commodity_id,
                Price.mandi_id,
                Price.modal_price.label("latest_price")
            )
            .where(Price.price_date == end_date)
            .subquery()
        )
        
        # Get oldest prices in the period
        oldest_subq = (
            select(
                Price.commodity_id,
                Price.mandi_id,
                Price.modal_price.label("old_price")
            )
            .where(Price.price_date == start_date)
            .subquery()
        )
        
        # Calculate percentage change
        query = (
            select(
                Commodity.id.label("commodity_id"),
                Commodity.name.label("commodity_name"),
                Commodity.category,
                func.avg(latest_subq.c.latest_price).label("latest_price"),
                func.avg(oldest_subq.c.old_price).label("old_price"),
                func.avg(
                    (latest_subq.c.latest_price - oldest_subq.c.old_price) 
                    * 100.0 / oldest_subq.c.old_price
                ).label("change_percent"),
            )
            .select_from(latest_subq)
            .join(oldest_subq, and_(
                latest_subq.c.commodity_id == oldest_subq.c.commodity_id,
                latest_subq.c.mandi_id == oldest_subq.c.mandi_id,
            ))
            .join(Commodity, Commodity.id == latest_subq.c.commodity_id)
            .group_by(Commodity.id, Commodity.name, Commodity.category)
            .order_by(func.avg(
                (latest_subq.c.latest_price - oldest_subq.c.old_price) 
                * 100.0 / oldest_subq.c.old_price
            ).desc())
            .limit(limit)
        )
        
        if state:
            query = query.join(Mandi, Mandi.id == latest_subq.c.mandi_id)
            query = query.where(Mandi.state == state)
        
        result = await self.db.execute(query)
        
        gainers = []
        for row in result:
            gainers.append({
                "commodity_id": row.commodity_id,
                "commodity_name": row.commodity_name,
                "category": row.category,
                "latest_price": float(row.latest_price),
                "old_price": float(row.old_price),
                "change_percent": round(float(row.change_percent), 2),
            })
        
        return gainers
    
    async def get_top_losers(
        self,
        state: Optional[str] = None,
        days: int = 7,
        limit: int = 10,
    ) -> List[dict]:
        """
        Get commodities with highest price decrease in the given period.
        """
        end_date = date.today()
        start_date = end_date - timedelta(days=days)
        
        # Similar to gainers but ordered ascending
        latest_subq = (
            select(
                Price.commodity_id,
                Price.mandi_id,
                Price.modal_price.label("latest_price")
            )
            .where(Price.price_date == end_date)
            .subquery()
        )
        
        oldest_subq = (
            select(
                Price.commodity_id,
                Price.mandi_id,
                Price.modal_price.label("old_price")
            )
            .where(Price.price_date == start_date)
            .subquery()
        )
        
        query = (
            select(
                Commodity.id.label("commodity_id"),
                Commodity.name.label("commodity_name"),
                Commodity.category,
                func.avg(latest_subq.c.latest_price).label("latest_price"),
                func.avg(oldest_subq.c.old_price).label("old_price"),
                func.avg(
                    (latest_subq.c.latest_price - oldest_subq.c.old_price) 
                    * 100.0 / oldest_subq.c.old_price
                ).label("change_percent"),
            )
            .select_from(latest_subq)
            .join(oldest_subq, and_(
                latest_subq.c.commodity_id == oldest_subq.c.commodity_id,
                latest_subq.c.mandi_id == oldest_subq.c.mandi_id,
            ))
            .join(Commodity, Commodity.id == latest_subq.c.commodity_id)
            .group_by(Commodity.id, Commodity.name, Commodity.category)
            .order_by(func.avg(
                (latest_subq.c.latest_price - oldest_subq.c.old_price) 
                * 100.0 / oldest_subq.c.old_price
            ).asc())
            .limit(limit)
        )
        
        if state:
            query = query.join(Mandi, Mandi.id == latest_subq.c.mandi_id)
            query = query.where(Mandi.state == state)
        
        result = await self.db.execute(query)
        
        losers = []
        for row in result:
            losers.append({
                "commodity_id": row.commodity_id,
                "commodity_name": row.commodity_name,
                "category": row.category,
                "latest_price": float(row.latest_price),
                "old_price": float(row.old_price),
                "change_percent": round(float(row.change_percent), 2),
            })
        
        return losers
    
    async def create(self, price_data: PriceCreate) -> Price:
        """Create a new price record."""
        price = Price(
            commodity_id=price_data.commodity_id,
            mandi_id=price_data.mandi_id,
            price_date=price_data.price_date,
            min_price=price_data.min_price,
            max_price=price_data.max_price,
            modal_price=price_data.modal_price,
            arrival_qty=price_data.arrival_qty,
            source=price_data.source,
        )
        
        self.db.add(price)
        await self.db.commit()
        await self.db.refresh(price)
        return price
    
    async def bulk_create(self, prices: List[PriceCreate]) -> List[Price]:
        """Bulk create price records."""
        created_prices = []
        
        for price_data in prices:
            # Check if price already exists for this date/mandi/commodity
            existing = await self.db.execute(
                select(Price).where(
                    and_(
                        Price.commodity_id == price_data.commodity_id,
                        Price.mandi_id == price_data.mandi_id,
                        Price.price_date == price_data.price_date,
                    )
                )
            )
            existing_price = existing.scalar_one_or_none()
            
            if existing_price:
                # Update existing price
                existing_price.min_price = price_data.min_price
                existing_price.max_price = price_data.max_price
                existing_price.modal_price = price_data.modal_price
                existing_price.arrival_qty = price_data.arrival_qty
                existing_price.source = price_data.source
                existing_price.updated_at = datetime.utcnow()
                created_prices.append(existing_price)
            else:
                # Create new price
                price = Price(
                    commodity_id=price_data.commodity_id,
                    mandi_id=price_data.mandi_id,
                    price_date=price_data.price_date,
                    min_price=price_data.min_price,
                    max_price=price_data.max_price,
                    modal_price=price_data.modal_price,
                    arrival_qty=price_data.arrival_qty,
                    source=price_data.source,
                )
                self.db.add(price)
                created_prices.append(price)
        
        await self.db.commit()
        
        for price in created_prices:
            await self.db.refresh(price)
        
        return created_prices
    
    async def get_state_average_prices(
        self,
        commodity_id: int,
        state: str,
        days: int = 30,
    ) -> List[dict]:
        """
        Get daily average prices for a commodity across all mandis in a state.
        """
        start_date = date.today() - timedelta(days=days)
        
        query = (
            select(
                Price.price_date,
                Mandi.state,
                func.avg(Price.modal_price).label("avg_modal"),
                func.min(Price.min_price).label("min_price"),
                func.max(Price.max_price).label("max_price"),
                func.count(Price.id).label("num_listings"),
            )
            .join(Mandi)
            .where(
                and_(
                    Price.commodity_id == commodity_id,
                    Mandi.state == state,
                    Price.price_date >= start_date,
                )
            )
            .group_by(Price.price_date, Mandi.state)
            .order_by(Price.price_date)
        )
        
        result = await self.db.execute(query)
        
        averages = []
        for row in result:
            averages.append({
                "date": row.price_date,
                "state": row.state,
                "avg_modal_price": float(row.avg_modal),
                "min_price": float(row.min_price),
                "max_price": float(row.max_price),
                "num_listings": row.num_listings,
            })
        
        return averages
    
    @staticmethod
    def to_response(price: Price) -> PriceResponse:
        """Convert Price model to response schema."""
        return PriceResponse.model_validate(price)
    
    @staticmethod
    def to_detailed_response(price: Price) -> PriceWithDetailsResponse:
        """Convert Price model with relationships to detailed response."""
        return PriceWithDetailsResponse(
            id=price.id,
            commodity_id=price.commodity_id,
            mandi_id=price.mandi_id,
            price_date=price.price_date,
            min_price=price.min_price,
            max_price=price.max_price,
            modal_price=price.modal_price,
            arrival_qty=price.arrival_qty,
            source=price.source,
            created_at=price.created_at,
            updated_at=price.updated_at,
            commodity={
                "id": price.commodity.id,
                "name": price.commodity.name,
                "category": price.commodity.category,
                "unit": price.commodity.unit,
            } if price.commodity else None,
            mandi={
                "id": price.mandi.id,
                "name": price.mandi.name,
                "state": price.mandi.state,
                "district": price.mandi.district,
            } if price.mandi else None,
        )
    
    @staticmethod
    def to_list_response(
        prices: List[Price],
        total: int,
        page: int,
        page_size: int,
    ) -> PriceListResponse:
        """Convert list of prices to paginated response."""
        total_pages = (total + page_size - 1) // page_size
        return PriceListResponse(
            items=[PriceService.to_response(p) for p in prices],
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )
