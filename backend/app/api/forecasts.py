"""
Forecast API endpoints.
"""
from datetime import date
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status, Query, Body
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.services.forecast_service import (
    ForecastService,
    ForecastOutput,
    MultiHorizonForecast,
    get_forecast_service,
)
from app.schemas import ErrorDetail

router = APIRouter(prefix="/forecasts", tags=["Forecasts"])


@router.get(
    "/{commodity_id}/{mandi_id}",
    response_model=ForecastOutput,
    summary="Get price forecast",
    description="Generate price forecast for a commodity at a specific mandi.",
    responses={
        404: {"model": ErrorDetail, "description": "Insufficient data for forecast"},
    },
)
async def get_forecast(
    commodity_id: int,
    mandi_id: int,
    horizon_days: int = Query(7, ge=1, le=30, description="Forecast horizon in days"),
    include_explanation: bool = Query(True, description="Include SHAP explanation"),
    db: AsyncSession = Depends(get_db),
):
    """
    Get price forecast for a commodity at a mandi.
    
    Returns predicted price, confidence bounds, and optional explanation.
    """
    forecast_service = await get_forecast_service(db)
    
    forecast = await forecast_service.forecast(
        commodity_id=commodity_id,
        mandi_id=mandi_id,
        horizon_days=horizon_days,
        include_explanation=include_explanation,
    )
    
    if not forecast:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Insufficient historical data for forecast. Need at least 30 days of price data.",
        )
    
    return forecast


@router.get(
    "/{commodity_id}/{mandi_id}/multi-horizon",
    response_model=MultiHorizonForecast,
    summary="Get multi-horizon forecasts",
    description="Generate price forecasts for multiple time horizons.",
    responses={
        404: {"model": ErrorDetail, "description": "Insufficient data for forecast"},
    },
)
async def get_multi_horizon_forecast(
    commodity_id: int,
    mandi_id: int,
    horizons: str = Query("1,3,7,14,30", description="Comma-separated list of horizon days"),
    db: AsyncSession = Depends(get_db),
):
    """
    Get price forecasts for multiple horizons.
    
    Returns forecasts for 1, 3, 7, 14, and 30 days by default.
    """
    # Parse horizons
    try:
        horizon_list = [int(h.strip()) for h in horizons.split(",")]
        horizon_list = [h for h in horizon_list if 1 <= h <= 90]
    except ValueError:
        horizon_list = [1, 3, 7, 14, 30]
    
    forecast_service = await get_forecast_service(db)
    
    forecast = await forecast_service.forecast_multi_horizon(
        commodity_id=commodity_id,
        mandi_id=mandi_id,
        horizons=horizon_list,
    )
    
    if not forecast:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Insufficient historical data for forecast",
        )
    
    return forecast


@router.post(
    "/batch",
    response_model=List[ForecastOutput],
    summary="Batch forecasts",
    description="Generate forecasts for multiple commodity-mandi pairs.",
)
async def batch_forecasts(
    requests: List[dict] = Body(
        ...,
        description="List of forecast requests",
        examples=[
            {"commodity_id": 1, "mandi_id": 1, "horizon_days": 7},
            {"commodity_id": 1, "mandi_id": 2, "horizon_days": 7},
        ],
    ),
    db: AsyncSession = Depends(get_db),
):
    """
    Generate forecasts for multiple commodity-mandi pairs.
    
    Maximum 20 requests per batch.
    """
    if len(requests) > 20:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Maximum 20 requests per batch",
        )
    
    from app.services.forecast_service import ForecastInput
    
    forecast_requests = [
        ForecastInput(
            commodity_id=r.get("commodity_id"),
            mandi_id=r.get("mandi_id"),
            horizon_days=r.get("horizon_days", 7),
        )
        for r in requests
        if r.get("commodity_id") and r.get("mandi_id")
    ]
    
    forecast_service = await get_forecast_service(db)
    
    forecasts = await forecast_service.forecast_batch(forecast_requests)
    
    return forecasts


@router.get(
    "/{commodity_id}/best-opportunities",
    response_model=List[ForecastOutput],
    summary="Find best selling opportunities",
    description="Find mandis with best price increase potential for a commodity.",
)
async def get_best_opportunities(
    commodity_id: int,
    mandi_ids: str = Query(..., description="Comma-separated mandi IDs"),
    horizon_days: int = Query(7, ge=1, le=30, description="Forecast horizon"),
    min_price_change: float = Query(5.0, description="Minimum price change percentage"),
    limit: int = Query(10, ge=1, le=50, description="Maximum results"),
    db: AsyncSession = Depends(get_db),
):
    """
    Find mandis with best price increase potential.
    
    Returns mandis sorted by expected price increase.
    """
    # Parse mandi IDs
    try:
        mandi_id_list = [int(m.strip()) for m in mandi_ids.split(",")]
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid mandi IDs format",
        )
    
    if len(mandi_id_list) > 50:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Maximum 50 mandis per request",
        )
    
    forecast_service = await get_forecast_service(db)
    
    opportunities = await forecast_service.get_best_selling_opportunities(
        commodity_id=commodity_id,
        mandi_ids=mandi_id_list,
        horizon_days=horizon_days,
        min_price_change_pct=min_price_change,
    )
    
    return opportunities[:limit]


@router.get(
    "/{commodity_id}/{mandi_id}/explanation",
    response_model=dict,
    summary="Get forecast explanation",
    description="Get detailed SHAP explanation for a price forecast.",
    responses={
        404: {"model": ErrorDetail, "description": "Forecast not available"},
    },
)
async def get_forecast_explanation(
    commodity_id: int,
    mandi_id: int,
    horizon_days: int = Query(7, ge=1, le=30, description="Forecast horizon"),
    db: AsyncSession = Depends(get_db),
):
    """
    Get detailed SHAP explanation for a forecast.
    
    Returns feature contributions and natural language explanation.
    """
    forecast_service = await get_forecast_service(db)
    
    forecast = await forecast_service.forecast(
        commodity_id=commodity_id,
        mandi_id=mandi_id,
        horizon_days=horizon_days,
        include_explanation=True,
    )
    
    if not forecast:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Insufficient data for forecast",
        )
    
    if not forecast.explanation:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Explanation service unavailable",
        )
    
    return forecast.explanation
