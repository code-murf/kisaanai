"""
Routing API endpoints for optimal mandi selection.
"""
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status, Query, Body
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.services.routing_service import (
    RoutingService,
    RoutingRequest,
    RoutingResponse,
    MandiRecommendation,
    OptimizationGoal,
    TransportMode,
    get_routing_service,
)
from app.schemas import ErrorDetail

router = APIRouter(prefix="/routing", tags=["Routing"])


@router.post(
    "/recommend",
    response_model=RoutingResponse,
    summary="Get mandi recommendations",
    description="Find optimal mandis for selling a commodity based on price, distance, and transport costs.",
)
async def get_mandi_recommendations(
    commodity_id: int = Body(..., description="Commodity ID to sell"),
    latitude: float = Body(..., description="Farmer's latitude", ge=-90, le=90),
    longitude: float = Body(..., description="Farmer's longitude", ge=-180, le=180),
    quantity_quintals: float = Body(1.0, description="Quantity in quintals", gt=0),
    transport_mode: TransportMode = Body(
        TransportMode.THREE_WHEELER,
        description="Mode of transport",
    ),
    max_distance_km: float = Body(100.0, description="Maximum distance to consider", gt=0, le=500),
    optimization_goal: OptimizationGoal = Body(
        OptimizationGoal.MAXIMIZE_PROFIT,
        description="Optimization goal",
    ),
    forecast_horizon_days: int = Body(7, description="Days to forecast", ge=1, le=30),
    include_forecasts: bool = Body(True, description="Include price forecasts"),
    limit: int = Body(10, description="Maximum recommendations", ge=1, le=50),
    db: AsyncSession = Depends(get_db),
):
    """
    Get optimal mandi recommendations for selling a commodity.
    
    Analyzes nearby mandis based on:
    - Current and forecasted prices
    - Distance and transport costs
    - User's optimization goal (maximize profit, price, or minimize distance)
    
    Returns a ranked list of recommended mandis with detailed analysis.
    """
    routing_service = await get_routing_service(db)
    
    request = RoutingRequest(
        commodity_id=commodity_id,
        latitude=latitude,
        longitude=longitude,
        quantity_quintals=quantity_quintals,
        transport_mode=transport_mode,
        max_distance_km=max_distance_km,
        optimization_goal=optimization_goal,
        forecast_horizon_days=forecast_horizon_days,
        include_forecasts=include_forecasts,
        limit=limit,
    )
    
    response = await routing_service.find_optimal_mandis(request)
    
    if not response.recommendations:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No mandis found within {max_distance_km}km with price data for this commodity",
        )
    
    return response


@router.get(
    "/route-summary/{commodity_id}/{mandi_id}",
    response_model=dict,
    summary="Get route summary",
    description="Get a summary of the route to a specific mandi.",
)
async def get_route_summary(
    commodity_id: int,
    mandi_id: int,
    latitude: float = Query(..., description="Farmer's latitude", ge=-90, le=90),
    longitude: float = Query(..., description="Farmer's longitude", ge=-180, le=180),
    quantity_quintals: float = Query(1.0, description="Quantity in quintals", gt=0),
    transport_mode: TransportMode = Query(
        TransportMode.THREE_WHEELER,
        description="Mode of transport",
    ),
    db: AsyncSession = Depends(get_db),
):
    """
    Get a summary of the route to a specific mandi.
    
    Includes:
    - Distance to mandi
    - Current price
    - Transport cost
    - Net profit calculation
    """
    routing_service = await get_routing_service(db)
    
    summary = await routing_service.get_route_summary(
        commodity_id=commodity_id,
        mandi_id=mandi_id,
        latitude=latitude,
        longitude=longitude,
        quantity_quintals=quantity_quintals,
        transport_mode=transport_mode,
    )
    
    if not summary:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Mandi or price data not found",
        )
    
    return summary


@router.get(
    "/transport-modes",
    response_model=dict,
    summary="Get transport modes",
    description="Get available transport modes and their costs.",
)
async def get_transport_modes():
    """
    Get available transport modes and their costs per km.
    
    Returns a dictionary of transport modes with their costs in INR per km.
    """
    from app.services.routing_service import TRANSPORT_COSTS
    
    return {
        "transport_modes": [
            {
                "mode": mode.value,
                "cost_per_km_inr": cost,
                "description": _get_transport_description(mode),
            }
            for mode, cost in TRANSPORT_COSTS.items()
        ]
    }


@router.get(
    "/optimization-goals",
    response_model=dict,
    summary="Get optimization goals",
    description="Get available optimization goals for routing.",
)
async def get_optimization_goals():
    """
    Get available optimization goals for mandi routing.
    
    Each goal uses different weights for price and distance scoring.
    """
    return {
        "optimization_goals": [
            {
                "goal": OptimizationGoal.MAXIMIZE_PROFIT.value,
                "description": "Balance price and transport cost for maximum net profit",
                "price_weight": 0.6,
                "distance_weight": 0.4,
            },
            {
                "goal": OptimizationGoal.MAXIMIZE_PRICE.value,
                "description": "Prioritize highest price regardless of distance",
                "price_weight": 0.9,
                "distance_weight": 0.1,
            },
            {
                "goal": OptimizationGoal.MINIMIZE_DISTANCE.value,
                "description": "Find closest mandi with reasonable prices",
                "price_weight": 0.1,
                "distance_weight": 0.9,
            },
            {
                "goal": OptimizationGoal.BALANCED.value,
                "description": "Equal weight to price and distance",
                "price_weight": 0.5,
                "distance_weight": 0.5,
            },
        ]
    }


def _get_transport_description(mode: TransportMode) -> str:
    """Get human-readable description for transport mode."""
    descriptions = {
        TransportMode.TWO_WHEELER: "Motorcycle or scooter - best for small quantities",
        TransportMode.THREE_WHEELER: "Auto-rickshaw or tempo - good for medium quantities",
        TransportMode.FOUR_WHEELER: "Truck or tractor - for large quantities",
        TransportMode.TRAILER: "Tractor with trailer - maximum capacity",
    }
    return descriptions.get(mode, "")
