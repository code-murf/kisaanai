from datetime import timedelta
from typing import List, Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.commodity import Commodity
from app.models.price import Price

router = APIRouter()


class NewsItem(BaseModel):
    id: int
    title: str
    excerpt: str
    date: str
    source: str
    category: str
    color: str
    image_url: str
    video_url: Optional[str] = None


@router.get('/news', response_model=List[NewsItem])
async def get_news(db: AsyncSession = Depends(get_db)):
    latest_date = await db.scalar(select(func.max(Price.price_date)))
    if not latest_date:
        return []

    previous_date = await db.scalar(
        select(func.max(Price.price_date)).where(Price.price_date < latest_date)
    )

    latest_rows = await db.execute(
        select(Price.commodity_id, func.avg(Price.modal_price).label('avg_price'))
        .where(Price.price_date == latest_date)
        .group_by(Price.commodity_id)
    )
    latest_map = {row.commodity_id: float(row.avg_price) for row in latest_rows if row.avg_price is not None}

    prev_map = {}
    if previous_date:
        prev_rows = await db.execute(
            select(Price.commodity_id, func.avg(Price.modal_price).label('avg_price'))
            .where(Price.price_date == previous_date)
            .group_by(Price.commodity_id)
        )
        prev_map = {row.commodity_id: float(row.avg_price) for row in prev_rows if row.avg_price is not None}

    if not latest_map:
        return []

    commodity_ids = list(latest_map.keys())
    commodity_rows = await db.execute(select(Commodity.id, Commodity.name).where(Commodity.id.in_(commodity_ids)))
    commodity_name_map = {row.id: row.name for row in commodity_rows}

    insights = []
    for commodity_id, current_price in latest_map.items():
        prev_price = prev_map.get(commodity_id)
        if prev_price and prev_price > 0:
            change_pct = ((current_price - prev_price) / prev_price) * 100.0
        else:
            change_pct = 0.0
        insights.append((commodity_id, current_price, change_pct))

    insights.sort(key=lambda item: abs(item[2]), reverse=True)

    palette = [
        'bg-emerald-100 text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-400',
        'bg-blue-100 text-blue-700 dark:bg-blue-900/30 dark:text-blue-400',
        'bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400',
        'bg-rose-100 text-rose-700 dark:bg-rose-900/30 dark:text-rose-400',
    ]
    image_urls = [
        'https://images.unsplash.com/photo-1464226184884-fa280b87c399?q=80&w=800&auto=format&fit=crop',
        'https://images.unsplash.com/photo-1500382017468-9049fed747ef?q=80&w=800&auto=format&fit=crop',
        'https://images.unsplash.com/photo-1488459716781-31db52582fe9?q=80&w=800&auto=format&fit=crop',
        'https://images.unsplash.com/photo-1589923158776-cb4485d99fd6?q=80&w=800&auto=format&fit=crop',
    ]

    items: List[NewsItem] = []
    for idx, (commodity_id, current_price, change_pct) in enumerate(insights[:4], start=1):
        commodity_name = commodity_name_map.get(commodity_id, f'Commodity {commodity_id}')
        direction = 'rose' if change_pct >= 0 else 'fell'
        abs_change = abs(change_pct)
        title = f'{commodity_name} prices {direction} {abs_change:.1f}% in mandi markets'
        excerpt = (
            f'Average mandi modal price for {commodity_name} is Rs. {current_price:,.0f}/quintal on {latest_date.isoformat()}. '
            f'Change versus previous trading day: {change_pct:+.1f}%.'
        )

        items.append(
            NewsItem(
                id=idx,
                title=title,
                excerpt=excerpt,
                date=latest_date.isoformat(),
                source='KisaanAI Market Data',
                category='Market Trend',
                color=palette[(idx - 1) % len(palette)],
                image_url=image_urls[(idx - 1) % len(image_urls)],
                video_url=None,
            )
        )

    return items
