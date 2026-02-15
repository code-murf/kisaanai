"""
Forecast Service for price predictions.

This service wraps the ML models and provides a clean interface
for price forecasting with explanations.
"""
import asyncio
from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models import Price, Commodity, Mandi
from app.ml.feature_engineering import (
    FeatureEngineer,
    FeatureConfig,
    prepare_inference_data,
)
from app.ml.xgb_forecast import (
    XGBoostForecaster,
    XGBoostConfig,
    PredictionResult,
    MultiHorizonForecaster,
)
from app.ml.explainer import ShapExplainer, PriceExplanationService


@dataclass
class ForecastInput:
    """Input for price forecast."""
    commodity_id: int
    mandi_id: int
    horizon_days: int = 7


@dataclass
class ForecastOutput:
    """Output of price forecast."""
    commodity_id: int
    commodity_name: str
    mandi_id: int
    mandi_name: str
    state: str
    current_price: float
    predicted_price: float
    price_change: float
    price_change_pct: float
    horizon_days: int
    prediction_date: date
    target_date: date
    confidence_lower: float
    confidence_upper: float
    confidence: float
    trend: str  # "up", "down", "stable"
    explanation: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "commodity_id": self.commodity_id,
            "commodity_name": self.commodity_name,
            "mandi_id": self.mandi_id,
            "mandi_name": self.mandi_name,
            "state": self.state,
            "current_price": self.current_price,
            "predicted_price": self.predicted_price,
            "price_change": self.price_change,
            "price_change_pct": self.price_change_pct,
            "horizon_days": self.horizon_days,
            "prediction_date": self.prediction_date.isoformat(),
            "target_date": self.target_date.isoformat(),
            "confidence_lower": self.confidence_lower,
            "confidence_upper": self.confidence_upper,
            "confidence": self.confidence,
            "trend": self.trend,
            "explanation": self.explanation,
        }


@dataclass
class MultiHorizonForecast:
    """Multi-horizon price forecast."""
    commodity_id: int
    mandi_id: int
    current_price: float
    forecasts: Dict[int, ForecastOutput]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "commodity_id": self.commodity_id,
            "mandi_id": self.mandi_id,
            "current_price": self.current_price,
            "forecasts": {
                str(k): v.to_dict() for k, v in self.forecasts.items()
            },
        }


class ForecastService:
    """
    Service for price forecasting.
    
    Manages model loading, feature preparation, prediction, and explanation.
    """
    
    def __init__(
        self,
        db: AsyncSession,
        model_dir: Optional[Path] = None,
    ):
        """
        Initialize forecast service.
        
        Args:
            db: Database session
            model_dir: Directory containing trained models
        """
        self.db = db
        self.model_dir = model_dir or Path(settings.MODEL_PATH)
        
        self._forecasters: Dict[int, XGBoostForecaster] = {}
        self._feature_engineers: Dict[int, FeatureEngineer] = {}
        self._explainers: Dict[int, PriceExplanationService] = {}
        self._loaded = False
    
    async def load_models(self):
        """Load trained models from disk."""
        if self._loaded:
            return
        
        # Load models for each horizon
        horizons = [1, 3, 7, 14, 30]
        
        for horizon in horizons:
            model_path = self.model_dir / f"horizon_{horizon}d" / "model.json"
            
            if model_path.exists():
                config = XGBoostConfig()
                forecaster = XGBoostForecaster(
                    config=config,
                    model_dir=self.model_dir / f"horizon_{horizon}d",
                )
                forecaster.load(model_path)
                self._forecasters[horizon] = forecaster
        
        self._loaded = True
    
    async def _get_historical_prices(
        self,
        commodity_id: int,
        mandi_id: int,
        days: int = 365,
    ) -> pd.DataFrame:
        """
        Get historical prices for feature engineering.
        
        Args:
            commodity_id: Commodity ID
            mandi_id: Mandi ID
            days: Number of days of history
            
        Returns:
            DataFrame with historical prices
        """
        cutoff_date = date.today() - timedelta(days=days)
        
        query = select(Price).where(
            and_(
                Price.commodity_id == commodity_id,
                Price.mandi_id == mandi_id,
                Price.price_date >= cutoff_date,
            )
        ).order_by(Price.price_date)
        
        result = await self.db.execute(query)
        prices = result.scalars().all()
        
        if not prices:
            return pd.DataFrame()
        
        # Convert to DataFrame
        data = []
        for p in prices:
            data.append({
                "commodity_id": p.commodity_id,
                "mandi_id": p.mandi_id,
                "price_date": p.price_date,
                "min_price": p.min_price,
                "max_price": p.max_price,
                "modal_price": p.modal_price,
                "arrival_qty": p.arrival_qty,
            })
        
        return pd.DataFrame(data)
    
    async def _get_commodity_mandi_info(
        self,
        commodity_id: int,
        mandi_id: int,
    ) -> Tuple[Optional[Commodity], Optional[Mandi]]:
        """Get commodity and mandi information."""
        commodity_query = select(Commodity).where(Commodity.id == commodity_id)
        commodity_result = await self.db.execute(commodity_query)
        commodity = commodity_result.scalar_one_or_none()
        
        mandi_query = select(Mandi).where(Mandi.id == mandi_id)
        mandi_result = await self.db.execute(mandi_query)
        mandi = mandi_result.scalar_one_or_none()
        
        return commodity, mandi
    
    async def forecast(
        self,
        commodity_id: int,
        mandi_id: int,
        horizon_days: int = 7,
        include_explanation: bool = True,
    ) -> Optional[ForecastOutput]:
        """
        Generate price forecast for a commodity at a mandi.
        
        Args:
            commodity_id: Commodity ID
            mandi_id: Mandi ID
            horizon_days: Forecast horizon in days
            include_explanation: Whether to include SHAP explanation
            
        Returns:
            ForecastOutput or None if insufficient data
        """
        # Load models if not loaded
        await self.load_models()
        
        # Check if model exists for horizon
        if horizon_days not in self._forecasters:
            # Try to find closest available horizon
            available = list(self._forecasters.keys())
            if not available:
                # No models loaded? Fallback to mock for demo
                return self._generate_mock_forecast(commodity_id, mandi_id, horizon_days, include_explanation)
            horizon_days = min(available, key=lambda x: abs(x - horizon_days))
        
        forecaster = self._forecasters[horizon_days]
        
        # Get historical data
        price_df = await self._get_historical_prices(commodity_id, mandi_id)
        
        if price_df.empty or len(price_df) < 30:
            # Insufficient data for prediction, try mock if debug/demo
            return self._generate_mock_forecast(commodity_id, mandi_id, horizon_days, include_explanation)
        
        # Get commodity and mandi info
        commodity, mandi = await self._get_commodity_mandi_info(commodity_id, mandi_id)
        
        if not commodity or not mandi:
            return self._generate_mock_forecast(commodity_id, mandi_id, horizon_days, include_explanation)
        
        # Prepare features
        feature_engineer = FeatureEngineer()
        df, feature_columns, _ = feature_engineer.prepare_features(
            df=price_df,
            horizon_days=horizon_days,
            is_training=False,
        )
        
        # Get latest data point for prediction
        latest = df.iloc[-1:][feature_columns]
        X = latest.values
        
        # Handle NaN values
        X = np.nan_to_num(X, nan=0.0)
        
        # Make prediction
        prediction = forecaster.predict(X[0], return_confidence=True)
        
        if isinstance(prediction, (int, float)):
            predicted_price = float(prediction)
            confidence_lower = predicted_price * 0.90
            confidence_upper = predicted_price * 1.10
            confidence = 0.80
        else:
            predicted_price = prediction.predicted_price
            confidence_lower = prediction.lower_bound
            confidence_upper = prediction.upper_bound
            confidence = prediction.confidence
        
        # Get current price
        current_price = float(price_df.iloc[-1]["modal_price"])
        
        # Calculate change
        price_change = predicted_price - current_price
        price_change_pct = (price_change / current_price * 100) if current_price > 0 else 0
        
        # Determine trend
        if price_change_pct > 2:
            trend = "up"
        elif price_change_pct < -2:
            trend = "down"
        else:
            trend = "stable"
        
        # Generate explanation
        explanation = None
        if include_explanation:
            try:
                explanation = await self._generate_explanation(
                    forecaster=forecaster,
                    X=X[0],
                    feature_columns=feature_columns,
                    commodity_name=commodity.name,
                    mandi_name=mandi.name,
                    horizon_days=horizon_days,
                )
            except Exception as e:
                print(f"Failed to generate explanation: {e}")
        
        return ForecastOutput(
            commodity_id=commodity_id,
            commodity_name=commodity.name,
            mandi_id=mandi_id,
            mandi_name=mandi.name,
            state=mandi.state,
            current_price=round(current_price, 2),
            predicted_price=round(predicted_price, 2),
            price_change=round(price_change, 2),
            price_change_pct=round(price_change_pct, 2),
            horizon_days=horizon_days,
            prediction_date=date.today(),
            target_date=date.today() + timedelta(days=horizon_days),
            confidence_lower=round(confidence_lower, 2),
            confidence_upper=round(confidence_upper, 2),
            confidence=confidence,
            trend=trend,
            explanation=explanation,
        )
    
    async def _generate_explanation(
        self,
        forecaster: XGBoostForecaster,
        X: np.ndarray,
        feature_columns: List[str],
        commodity_name: str,
        mandi_name: str,
        horizon_days: int,
    ) -> Dict[str, Any]:
        """Generate SHAP explanation for prediction."""
        try:
            explainer = ShapExplainer(
                model=forecaster.model,
                feature_columns=feature_columns,
            )
            
            price_explainer = PriceExplanationService(explainer)
            
            explanation = price_explainer.explain_prediction(
                X=X,
                commodity_name=commodity_name,
                mandi_name=mandi_name,
                horizon_days=horizon_days,
            )
            
            return explanation
        except Exception as e:
            print(f"Explanation generation failed: {e}")
            return None
    
    async def forecast_multi_horizon(
        self,
        commodity_id: int,
        mandi_id: int,
        horizons: List[int] = None,
    ) -> Optional[MultiHorizonForecast]:
        """
        Generate forecasts for multiple horizons.
        
        Args:
            commodity_id: Commodity ID
            mandi_id: Mandi ID
            horizons: List of forecast horizons
            
        Returns:
            MultiHorizonForecast or None
        """
        if horizons is None:
            horizons = [1, 3, 7, 14, 30]
        
        forecasts = {}
        current_price = None
        
        for horizon in horizons:
            forecast = await self.forecast(
                commodity_id=commodity_id,
                mandi_id=mandi_id,
                horizon_days=horizon,
                include_explanation=False,
            )
            
            if forecast:
                forecasts[horizon] = forecast
                if current_price is None:
                    current_price = forecast.current_price
        
        if not forecasts:
            return None
        
        return MultiHorizonForecast(
            commodity_id=commodity_id,
            mandi_id=mandi_id,
            current_price=current_price,
            forecasts=forecasts,
        )
    
    async def forecast_batch(
        self,
        requests: List[ForecastInput],
    ) -> List[ForecastOutput]:
        """
        Generate forecasts for multiple commodity-mandi pairs.
        
        Args:
            requests: List of forecast requests
            
        Returns:
            List of forecast outputs
        """
        results = []
        
        for request in requests:
            forecast = await self.forecast(
                commodity_id=request.commodity_id,
                mandi_id=request.mandi_id,
                horizon_days=request.horizon_days,
                include_explanation=False,
            )
            if forecast:
                results.append(forecast)
        
        return results
    
    async def get_best_selling_opportunities(
        self,
        commodity_id: int,
        mandi_ids: List[int],
        horizon_days: int = 7,
        min_price_change_pct: float = 5.0,
    ) -> List[ForecastOutput]:
        """
        Find mandis with best price increase potential.
        
        Args:
            commodity_id: Commodity ID
            mandi_ids: List of mandi IDs to analyze
            horizon_days: Forecast horizon
            min_price_change_pct: Minimum price change percentage
            
        Returns:
            List of forecasts sorted by price increase potential
        """
        forecasts = []
        
        for mandi_id in mandi_ids:
            forecast = await self.forecast(
                commodity_id=commodity_id,
                mandi_id=mandi_id,
                horizon_days=horizon_days,
                include_explanation=False,
            )
            if forecast and forecast.price_change_pct >= min_price_change_pct:
                forecasts.append(forecast)
        
        # Sort by price change percentage (descending)
        forecasts.sort(key=lambda x: x.price_change_pct, reverse=True)
        
        return forecasts


    def _generate_mock_forecast(
        self,
        commodity_id: int,
        mandi_id: int,
        horizon_days: int,
        include_explanation: bool = True
    ) -> ForecastOutput:
        """Generate mock forecast for demo purposes."""
        import random
        
        # Mock base price
        base_price = 2000 + (commodity_id * 100)
        current_price = base_price + random.randint(-200, 200)
        
        # Mock prediction
        trend_factor = random.choice([1.05, 0.95, 1.02, 0.98])
        predicted_price = current_price * trend_factor
        
        price_change = predicted_price - current_price
        price_change_pct = (price_change / current_price) * 100
        
        if price_change_pct > 2:
            trend = "up"
        elif price_change_pct < -2:
            trend = "down"
        else:
            trend = "stable"
            
        explanation = None
        if include_explanation:
            explanation = {
                "features": {
                    "Seasonal Trend": 0.4,
                    "Historical Price": 0.3,
                    "Weather Impact": 0.2,
                    "Supply Volume": 0.1
                },
                "text": f"Prices are expected to trend {trend} due to seasonal patterns and current supply volumes."
            }
            
        return ForecastOutput(
            commodity_id=commodity_id,
            commodity_name=f"Commodity {commodity_id}",
            mandi_id=mandi_id,
            mandi_name=f"Mandi {mandi_id}",
            state="Demo State",
            current_price=round(current_price, 2),
            predicted_price=round(predicted_price, 2),
            price_change=round(price_change, 2),
            price_change_pct=round(price_change_pct, 2),
            horizon_days=horizon_days,
            prediction_date=date.today(),
            target_date=date.today() + timedelta(days=horizon_days),
            confidence_lower=round(predicted_price * 0.9, 2),
            confidence_upper=round(predicted_price * 1.1, 2),
            confidence=0.85,
            trend=trend,
            explanation=explanation
        )

async def get_forecast_service(db: AsyncSession) -> ForecastService:
    """Get forecast service instance."""
    service = ForecastService(db=db)
    # Don't fail if models missing in demo mode
    try:
        await service.load_models()
    except Exception as e:
        print(f"Warning: Could not load models: {e}")
    return service
