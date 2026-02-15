
"""
Weather API Endpoints.
"""
from typing import List, Optional
from datetime import date
from fastapi import APIRouter, Depends, Query, HTTPException
from pydantic import BaseModel

from app.services.weather_service import WeatherService, WeatherForecast as ServiceWeatherForecast

router = APIRouter(prefix="/weather", tags=["weather"])

# Pydantic models for API response
class WeatherForecastResponse(BaseModel):
    date: date
    temp_min: float
    temp_max: float
    rainfall_mm: float
    humidity_pct: float
    condition: str
    advisory: str
    icon: str

@router.get("/forecast", response_model=List[WeatherForecastResponse])
async def get_weather_forecast(
    lat: float = Query(..., description="Latitude"),
    lon: float = Query(..., description="Longitude"),
    days: int = Query(14, description="Number of days for forecast"),
):
    """
    Get 14-day weather forecast with agricultural advisories.
    """
    service = WeatherService()
    try:
        forecasts = await service.get_forecast(lat, lon, days)
        # Convert dataclass to Pydantic model
        return [
            WeatherForecastResponse(
                date=f.date,
                temp_min=f.temp_min,
                temp_max=f.temp_max,
                rainfall_mm=f.rainfall_mm,
                humidity_pct=f.humidity_pct,
                condition=f.condition,
                advisory=f.advisory,
                icon=f.icon
            ) for f in forecasts
        ]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
