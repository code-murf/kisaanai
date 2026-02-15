
"""
Price API endpoints.
"""
from datetime import date
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status, Query, Body
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.services.price_service import PriceService
from app.schemas import (
    PriceCreate,
    PriceResponse,
    PriceWithDetailsResponse,
    PriceListResponse,
    PriceHistoryRequest,
    PriceTrendPoint,
    SuccessResponse,
    ErrorDetail,
)

router = APIRouter(prefix="/prices", tags=["Prices"])


@router.get(
    "",
    response_model=PriceListResponse,
    summary="Get price history",
    description="Get historical prices with optional filters.",
)
async def get_price_history(
    commodity_id: int = Query(..., description="Commodity ID"),
    mandi_id: Optional[int] = Query(None, description="Filter by mandi ID"),
    state: Optional[str] = Query(None, description="Filter by state"),
    start_date: Optional[date] = Query(None, description="Start date"),
    end_date: Optional[date] = Query(None, description="End date"),
    days: int = Query(30, ge=1, le=365, description="Days to look back if start_date not provided"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(100, ge=1, le=500, description="Items per page"),
    db: AsyncSession = Depends(get_db),
):
    """Get historical prices for a commodity."""
    price_service = PriceService(db)
    prices, total = await price_service.get_price_history(
        commodity_id=commodity_id,
        mandi_id=mandi_id,
        state=state,
        start_date=start_date,
        end_date=end_date,
        days=days,
        page=page,
        page_size=page_size,
    )
    return PriceService.to_list_response(prices, total, page, page_size)


@router.get(
    "/current/commodity/{commodity_id}",
    response_model=List[PriceWithDetailsResponse],
    summary="Get current prices by commodity",
    description="Get latest prices for a commodity across all mandis.",
)
async def get_current_prices_by_commodity(
    commodity_id: int,
    state: Optional[str] = Query(None, description="Filter by state"),
    limit: int = Query(20, ge=1, le=100, description="Maximum results"),
    db: AsyncSession = Depends(get_db),
):
    """Get current prices for a commodity across mandis."""
    price_service = PriceService(db)
    prices = await price_service.get_current_prices_by_commodity(
        commodity_id=commodity_id,
        state=state,
        limit=limit,
    )
    return [PriceService.to_detailed_response(p) for p in prices]


@router.get(
    "/current/mandi/{mandi_id}",
    response_model=List[PriceWithDetailsResponse],
    summary="Get current prices by mandi",
    description="Get latest prices for all commodities at a specific mandi.",
)
async def get_current_prices_by_mandi(
    mandi_id: int,
    category: Optional[str] = Query(None, description="Filter by commodity category"),
    limit: int = Query(50, ge=1, le=200, description="Maximum results"),
    db: AsyncSession = Depends(get_db),
):
    """Get current prices at a specific mandi."""
    price_service = PriceService(db)
    prices = await price_service.get_current_prices_by_mandi(
        mandi_id=mandi_id,
        category=category,
        limit=limit,
    )
    return [PriceService.to_detailed_response(p) for p in prices]


@router.get(
    "/trend/{commodity_id}",
    response_model=List[PriceTrendPoint],
    summary="Get price trend",
    description="Get daily price trend data for visualization.",
)
async def get_price_trend(
    commodity_id: int,
    mandi_id: Optional[int] = Query(None, description="Filter by mandi ID"),
    state: Optional[str] = Query(None, description="Filter by state"),
    days: int = Query(90, ge=7, le=365, description="Number of days"),
    db: AsyncSession = Depends(get_db),
):
    """Get price trend data for a commodity."""
    price_service = PriceService(db)
    return await price_service.get_price_trend(
        commodity_id=commodity_id,
        mandi_id=mandi_id,
        state=state,
        days=days,
    )


@router.post(
    "/compare",
    response_model=List[PriceWithDetailsResponse],
    summary="Compare prices across mandis",
    description="Compare current prices for a commodity across multiple mandis.",
)
async def compare_prices(
    commodity_id: int = Body(..., description="Commodity ID"),
    mandi_ids: List[int] = Body(..., description="List of mandi IDs to compare"),
    db: AsyncSession = Depends(get_db),
):
    """Compare prices for a commodity across mandis."""
    price_service = PriceService(db)
    prices = await price_service.get_price_comparison(
        commodity_id=commodity_id,
        mandi_ids=mandi_ids,
    )
    return [PriceService.to_detailed_response(p) for p in prices]


@router.get(
    "/gainers",
    response_model=List[dict],
    summary="Get top gainers",
    description="Get commodities with highest price increase.",
)
async def get_top_gainers(
    state: Optional[str] = Query(None, description="Filter by state"),
    days: int = Query(7, ge=1, le=30, description="Period in days"),
    limit: int = Query(10, ge=1, le=50, description="Maximum results"),
    db: AsyncSession = Depends(get_db),
):
    """Get top gaining commodities."""
    price_service = PriceService(db)
    return await price_service.get_top_gainers(
        state=state,
        days=days,
        limit=limit,
    )


@router.get(
    "/losers",
    response_model=List[dict],
    summary="Get top losers",
    description="Get commodities with highest price decrease.",
)
async def get_top_losers(
    state: Optional[str] = Query(None, description="Filter by state"),
    days: int = Query(7, ge=1, le=30, description="Period in days"),
    limit: int = Query(10, ge=1, le=50, description="Maximum results"),
    db: AsyncSession = Depends(get_db),
):
    """Get top losing commodities."""
    price_service = PriceService(db)
    return await price_service.get_top_losers(
        state=state,
        days=days,
        limit=limit,
    )


@router.get(
    "/state-average/{commodity_id}",
    response_model=List[dict],
    summary="Get state average prices",
    description="Get daily average prices for a commodity across all mandis in a state.",
)
async def get_state_average_prices(
    commodity_id: int,
    state: str = Query(..., description="State name"),
    days: int = Query(30, ge=7, le=365, description="Number of days"),
    db: AsyncSession = Depends(get_db),
):
    """Get state average prices for a commodity."""
    price_service = PriceService(db)
    return await price_service.get_state_average_prices(
        commodity_id=commodity_id,
        state=state,
        days=days,
    )


@router.get(
    "/{price_id}",
    response_model=PriceResponse,
    summary="Get price by ID",
    description="Get a specific price record.",
    responses={
        404: {"model": ErrorDetail, "description": "Price not found"},
    },
)
async def get_price(
    price_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Get a price by ID."""
    price_service = PriceService(db)
    price = await price_service.get_by_id(price_id)
    
    if not price:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Price not found",
        )
    
    return PriceService.to_response(price)


@router.post(
    "",
    response_model=PriceResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create price record",
    description="Create a new price record.",
)
async def create_price(
    price_data: PriceCreate,
    db: AsyncSession = Depends(get_db),
):
    """Create a new price record."""
    price_service = PriceService(db)
    price = await price_service.create(price_data)
    return PriceService.to_response(price)


@router.post(
    "/bulk",
    response_model=List[PriceResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Bulk create prices",
    description="Create or update multiple price records. Updates existing if price for same date/mandi/commodity exists.",
)
async def bulk_create_prices(
    prices: List[PriceCreate],
    db: AsyncSession = Depends(get_db),
):
    """Bulk create or update price records."""
    price_service = PriceService(db)
    created = await price_service.bulk_create(prices)
    return [PriceService.to_response(p) for p in created]
