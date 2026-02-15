"""
Routing Service for optimal mandi selection.

This service helps farmers find the best mandi to sell their produce based on:
- Current and forecasted prices
- Distance from farmer's location
- Transportation costs
- User preferences
"""
import math
from dataclasses import dataclass, field
from datetime import date, timedelta
from enum import Enum
from typing import List, Optional, Tuple

from pydantic import BaseModel, Field
from sqlalchemy import select, and_, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import Mandi, Commodity, Price
from app.services.mandi_service import MandiService
from app.services.price_service import PriceService
from app.services.forecast_service import ForecastService, ForecastOutput


class OptimizationGoal(str, Enum):
    """Optimization goal for routing."""
    MAXIMIZE_PROFIT = "maximize_profit"  # Balance price and transport cost
    MAXIMIZE_PRICE = "maximize_price"  # Highest price regardless of distance
    MINIMIZE_DISTANCE = "minimize_distance"  # Closest mandi
    BALANCED = "balanced"  # Equal weight to price and distance


class TransportMode(str, Enum):
    """Transport mode for cost calculation."""
    TWO_WHEELER = "two_wheeler"  # Motorcycle/scooter
    THREE_WHEELER = "three_wheeler"  # Auto-rickshaw/tempo
    FOUR_WHEELER = "four_wheeler"  # Truck/tractor
    TRAILER = "trailer"  # Tractor with trailer


# Transport cost per km in INR (approximate values)
TRANSPORT_COSTS = {
    TransportMode.TWO_WHEELER: 2.0,
    TransportMode.THREE_WHEELER: 5.0,
    TransportMode.FOUR_WHEELER: 12.0,
    TransportMode.TRAILER: 15.0,
}

# Default weights for scoring
DEFAULT_PRICE_WEIGHT = 0.6
DEFAULT_DISTANCE_WEIGHT = 0.4


@dataclass
class RoutingRequest:
    """Request for optimal mandi routing."""
    commodity_id: int
    latitude: float
    longitude: float
    quantity_quintals: float = 1.0
    transport_mode: TransportMode = TransportMode.THREE_WHEELER
    max_distance_km: float = 100.0
    optimization_goal: OptimizationGoal = OptimizationGoal.MAXIMIZE_PROFIT
    forecast_horizon_days: int = 7
    include_forecasts: bool = True
    limit: int = 10


@dataclass
class MandiRecommendation:
    """Recommended mandi with routing details."""
    mandi_id: int
    mandi_name: str
    mandi_state: str
    mandi_district: str
    latitude: float
    longitude: float
    distance_km: float
    
    # Price information
    current_price: float
    forecasted_price: Optional[float]
    price_change_pct: Optional[float]
    price_trend: str  # "rising", "falling", "stable"
    
    # Cost analysis
    transport_cost: float
    net_profit: float
    profit_per_quintal: float
    
    # Scoring
    price_score: float  # 0-100 normalized price score
    distance_score: float  # 0-100 normalized distance score
    overall_score: float  # Weighted combination
    
    # Additional info
    arrival_quantity: Optional[float] = None
    price_volatility: Optional[float] = None
    
    # Explanation
    recommendation_reason: str = ""


class RoutingResponse(BaseModel):
    """Response for routing request."""
    commodity_id: int
    commodity_name: str
    recommendations: List[MandiRecommendation]
    best_mandi: Optional[MandiRecommendation]
    total_mandis_analyzed: int
    optimization_goal: OptimizationGoal
    transport_mode: TransportMode
    quantity_quintals: float
    created_at: str = Field(default_factory=lambda: date.today().isoformat())


class RoutingService:
    """Service for optimal mandi routing."""
    
    def __init__(
        self,
        db: AsyncSession,
        mandi_service: MandiService,
        price_service: PriceService,
        forecast_service: ForecastService,
    ):
        self.db = db
        self.mandi_service = mandi_service
        self.price_service = price_service
        self.forecast_service = forecast_service
    
    async def find_optimal_mandis(
        self,
        request: RoutingRequest,
    ) -> RoutingResponse:
        """
        Find optimal mandis for selling a commodity.
        
        Analyzes nearby mandis based on:
        - Current prices
        - Price forecasts
        - Distance and transport costs
        - User's optimization goal
        """
        # Get nearby mandis
        nearby_mandis = await self.mandi_service.get_nearby(
            latitude=request.latitude,
            longitude=request.longitude,
            radius_km=request.max_distance_km,
            limit=50,  # Get more for analysis
        )
        
        if not nearby_mandis:
            return RoutingResponse(
                commodity_id=request.commodity_id,
                commodity_name="",
                recommendations=[],
                best_mandi=None,
                total_mandis_analyzed=0,
                optimization_goal=request.optimization_goal,
                transport_mode=request.transport_mode,
                quantity_quintals=request.quantity_quintals,
            )
        
        # Get commodity info
        commodity = await self._get_commodity(request.commodity_id)
        commodity_name = commodity.name if commodity else ""
        
        # Get transport cost per km
        transport_cost_per_km = TRANSPORT_COSTS[request.transport_mode]
        
        # Analyze each mandi
        recommendations: List[MandiRecommendation] = []
        
        for mandi, distance in nearby_mandis:
            recommendation = await self._analyze_mandi(
                mandi=mandi,
                distance_km=distance,
                commodity_id=request.commodity_id,
                quantity_quintals=request.quantity_quintals,
                transport_cost_per_km=transport_cost_per_km,
                forecast_horizon_days=request.forecast_horizon_days,
                include_forecasts=request.include_forecasts,
            )
            if recommendation:
                recommendations.append(recommendation)
        
        if not recommendations:
            return RoutingResponse(
                commodity_id=request.commodity_id,
                commodity_name=commodity_name,
                recommendations=[],
                best_mandi=None,
                total_mandis_analyzed=len(nearby_mandis),
                optimization_goal=request.optimization_goal,
                transport_mode=request.transport_mode,
                quantity_quintals=request.quantity_quintals,
            )
        
        # Normalize scores
        recommendations = self._normalize_scores(
            recommendations,
            request.optimization_goal,
        )
        
        # Sort by overall score
        recommendations.sort(key=lambda x: x.overall_score, reverse=True)
        
        # Get best mandi
        best_mandi = recommendations[0] if recommendations else None
        
        # Generate recommendation reasons
        for rec in recommendations:
            rec.recommendation_reason = self._generate_recommendation_reason(
                rec, request.optimization_goal
            )
        
        return RoutingResponse(
            commodity_id=request.commodity_id,
            commodity_name=commodity_name,
            recommendations=recommendations[:request.limit],
            best_mandi=best_mandi,
            total_mandis_analyzed=len(nearby_mandis),
            optimization_goal=request.optimization_goal,
            transport_mode=request.transport_mode,
            quantity_quintals=request.quantity_quintals,
        )
    
    async def _analyze_mandi(
        self,
        mandi: Mandi,
        distance_km: float,
        commodity_id: int,
        quantity_quintals: float,
        transport_cost_per_km: float,
        forecast_horizon_days: int,
        include_forecasts: bool,
    ) -> Optional[MandiRecommendation]:
        """Analyze a single mandi for recommendation."""
        # Get current price
        current_price = await self.price_service.get_current_price(
            commodity_id=commodity_id,
            mandi_id=mandi.id,
        )
        
        if not current_price or not current_price.modal_price:
            return None
        
        modal_price = current_price.modal_price
        
        # Get forecast if requested
        forecasted_price = None
        price_change_pct = None
        price_trend = "stable"
        
        if include_forecasts:
            try:
                forecast = await self.forecast_service.forecast(
                    commodity_id=commodity_id,
                    mandi_id=mandi.id,
                    horizon_days=forecast_horizon_days,
                    include_explanation=False,
                )
                if forecast:
                    forecasted_price = forecast.predicted_price
                    if modal_price > 0:
                        price_change_pct = ((forecasted_price - modal_price) / modal_price) * 100
                    
                    # Determine trend
                    if price_change_pct is not None:
                        if price_change_pct > 2:
                            price_trend = "rising"
                        elif price_change_pct < -2:
                            price_trend = "falling"
                        else:
                            price_trend = "stable"
            except Exception:
                pass  # Forecast not available
        
        # Calculate transport cost (round trip)
        transport_cost = distance_km * 2 * transport_cost_per_km
        
        # Calculate net profit
        gross_revenue = modal_price * quantity_quintals
        net_profit = gross_revenue - transport_cost
        profit_per_quintal = net_profit / quantity_quintals if quantity_quintals > 0 else 0
        
        return MandiRecommendation(
            mandi_id=mandi.id,
            mandi_name=mandi.name,
            mandi_state=mandi.state,
            mandi_district=mandi.district,
            latitude=float(mandi.latitude) if mandi.latitude else 0.0,
            longitude=float(mandi.longitude) if mandi.longitude else 0.0,
            distance_km=round(distance_km, 2),
            current_price=modal_price,
            forecasted_price=round(forecasted_price, 2) if forecasted_price else None,
            price_change_pct=round(price_change_pct, 2) if price_change_pct else None,
            price_trend=price_trend,
            transport_cost=round(transport_cost, 2),
            net_profit=round(net_profit, 2),
            profit_per_quintal=round(profit_per_quintal, 2),
            price_score=0.0,  # Will be normalized later
            distance_score=0.0,  # Will be normalized later
            overall_score=0.0,  # Will be calculated later
            arrival_quantity=current_price.arrival_qty,
        )
    
    def _normalize_scores(
        self,
        recommendations: List[MandiRecommendation],
        optimization_goal: OptimizationGoal,
    ) -> List[MandiRecommendation]:
        """Normalize price and distance scores to 0-100 scale."""
        if not recommendations:
            return recommendations
        
        # Find min/max for normalization
        prices = [r.current_price for r in recommendations]
        distances = [r.distance_km for r in recommendations]
        profits = [r.net_profit for r in recommendations]
        
        min_price, max_price = min(prices), max(prices)
        min_distance, max_distance = min(distances), max(distances)
        min_profit, max_profit = min(profits), max(profits)
        
        price_range = max_price - min_price if max_price > min_price else 1
        distance_range = max_distance - min_distance if max_distance > min_distance else 1
        profit_range = max_profit - min_profit if max_profit > min_profit else 1
        
        # Calculate weights based on optimization goal
        if optimization_goal == OptimizationGoal.MAXIMIZE_PROFIT:
            price_weight, distance_weight = 0.6, 0.4
        elif optimization_goal == OptimizationGoal.MAXIMIZE_PRICE:
            price_weight, distance_weight = 0.9, 0.1
        elif optimization_goal == OptimizationGoal.MINIMIZE_DISTANCE:
            price_weight, distance_weight = 0.1, 0.9
        else:  # BALANCED
            price_weight, distance_weight = 0.5, 0.5
        
        for rec in recommendations:
            # Normalize price (higher is better)
            rec.price_score = ((rec.current_price - min_price) / price_range) * 100
            
            # Normalize distance (lower is better, so invert)
            rec.distance_score = (1 - (rec.distance_km - min_distance) / distance_range) * 100
            
            # Calculate overall score
            rec.overall_score = (
                rec.price_score * price_weight +
                rec.distance_score * distance_weight
            )
            
            # Adjust score based on price trend
            if rec.price_trend == "rising":
                rec.overall_score *= 1.05  # 5% bonus for rising prices
            elif rec.price_trend == "falling":
                rec.overall_score *= 0.95  # 5% penalty for falling prices
        
        return recommendations
    
    def _generate_recommendation_reason(
        self,
        recommendation: MandiRecommendation,
        optimization_goal: OptimizationGoal,
    ) -> str:
        """Generate a human-readable recommendation reason."""
        reasons = []
        
        # Price reason
        if recommendation.price_trend == "rising":
            reasons.append(f"Prices are rising ({recommendation.price_change_pct:+.1f}% expected)")
        elif recommendation.price_trend == "falling":
            reasons.append(f"Prices may fall ({recommendation.price_change_pct:+.1f}% expected)")
        else:
            reasons.append("Prices are stable")
        
        # Distance reason
        if recommendation.distance_km <= 20:
            reasons.append("very close to your location")
        elif recommendation.distance_km <= 50:
            reasons.append("moderately close")
        else:
            reasons.append("further away but may offer better prices")
        
        # Profit reason
        if recommendation.net_profit > 0:
            reasons.append(f"expected net profit of ₹{recommendation.net_profit:,.0f}")
        
        # Goal-specific reason
        if optimization_goal == OptimizationGoal.MAXIMIZE_PROFIT:
            return f"Best balance of price and transport cost. {' '.join(reasons)}."
        elif optimization_goal == OptimizationGoal.MAXIMIZE_PRICE:
            return f"Highest price potential. {' '.join(reasons)}."
        elif optimization_goal == OptimizationGoal.MINIMIZE_DISTANCE:
            return f"Closest option with reasonable prices. {' '.join(reasons)}."
        else:
            return f"Balanced recommendation. {' '.join(reasons)}."
    
    async def _get_commodity(self, commodity_id: int) -> Optional[Commodity]:
        """Get commodity by ID."""
        result = await self.db.execute(
            select(Commodity).where(Commodity.id == commodity_id)
        )
        return result.scalar_one_or_none()
    
    async def get_route_summary(
        self,
        commodity_id: int,
        mandi_id: int,
        latitude: float,
        longitude: float,
        quantity_quintals: float = 1.0,
        transport_mode: TransportMode = TransportMode.THREE_WHEELER,
    ) -> Optional[dict]:
        """Get a summary of route to a specific mandi."""
        # Get mandi
        mandi = await self.mandi_service.get_by_id(mandi_id)
        if not mandi:
            return None
        
        # Calculate distance
        distance = self._haversine_distance(
            lat1=latitude,
            lon1=longitude,
            lat2=float(mandi.latitude) if mandi.latitude else 0,
            lon2=float(mandi.longitude) if mandi.longitude else 0,
        )
        
        # Get current price
        current_price = await self.price_service.get_current_price(
            commodity_id=commodity_id,
            mandi_id=mandi_id,
        )
        
        if not current_price:
            return None
        
        # Calculate costs
        transport_cost_per_km = TRANSPORT_COSTS[transport_mode]
        transport_cost = distance * 2 * transport_cost_per_km
        gross_revenue = current_price.modal_price * quantity_quintals
        net_profit = gross_revenue - transport_cost
        
        return {
            "mandi_id": mandi.id,
            "mandi_name": mandi.name,
            "distance_km": round(distance, 2),
            "current_price": current_price.modal_price,
            "quantity_quintals": quantity_quintals,
            "gross_revenue": round(gross_revenue, 2),
            "transport_cost": round(transport_cost, 2),
            "net_profit": round(net_profit, 2),
            "profit_per_quintal": round(net_profit / quantity_quintals, 2),
        }
    
    @staticmethod
    def _haversine_distance(
        lat1: float,
        lon1: float,
        lat2: float,
        lon2: float,
    ) -> float:
        """Calculate distance between two points using Haversine formula."""
        R = 6371  # Earth's radius in kilometers
        
        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        delta_lat = math.radians(lat2 - lat1)
        delta_lon = math.radians(lon2 - lon1)
        
        a = (
            math.sin(delta_lat / 2) ** 2 +
            math.cos(lat1_rad) * math.cos(lat2_rad) *
            math.sin(delta_lon / 2) ** 2
        )
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        
        return R * c


async def get_routing_service(db: AsyncSession) -> RoutingService:
    """Factory function to create RoutingService instance."""
    from app.services.mandi_service import MandiService
    from app.services.price_service import PriceService
    from app.services.forecast_service import ForecastService
    
    mandi_service = MandiService(db)
    price_service = PriceService(db)
    forecast_service = await ForecastService.create(db)
    
    return RoutingService(
        db=db,
        mandi_service=mandi_service,
        price_service=price_service,
        forecast_service=forecast_service,
    )
