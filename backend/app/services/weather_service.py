
"""
Weather Service for Agri-Analytics Platform.

Provides 14-day weather forecasts and agricultural advisories.
Currently uses simulated data for demonstration purposes.
"""
import random
from datetime import date, timedelta
from typing import List, Optional
from dataclasses import dataclass

from app.config import settings

@dataclass
class WeatherForecast:
    """Weather forecast for a single day."""
    date: date
    temp_min: float
    temp_max: float
    rainfall_mm: float
    humidity_pct: float
    condition: str
    advisory: str
    icon: str

class WeatherService:
    """
    Service to fetch/generate weather data.
    """
    
    def __init__(self):
        self._advisories = {
            "rain": [
                "Heavy rain expected. Ensure proper drainage in fields.",
                "Avoid spraying pesticides due to expected rain.",
                "Delay irrigation as rainfall is sufficient."
            ],
            "sunny": [
                "High temperatures expected. Ensure adequate irrigation.",
                "Good conditions for harvesting.",
                "Monitor soil moisture levels closely."
            ],
            "cloudy": [
                "Moderate conditions. Routine monitoring recommended.",
                "Suitable weather for fertilizer application.",
                "Checking for pest activity is advised."
            ]
        }
        
    async def get_forecast(self, lat: float, lon: float, days: int = 14) -> List[WeatherForecast]:
        """
        Get weather forecast for a location from Open-Meteo API.
        """
        try:
            import aiohttp
            
            url = "https://api.open-meteo.com/v1/forecast"
            params = {
                "latitude": lat,
                "longitude": lon,
                "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum,weather_code",
                "timezone": "auto",
                "forecast_days": days
            }

            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as response:
                    if response.status != 200:
                        print(f"Error fetching weather: {await response.text()}")
                        return self._generate_mock_forecast(days) # Fallback
                    
                    data = await response.json()
                    return self._parse_open_meteo_response(data)
                    
        except Exception as e:
            print(f"Weather API failed: {e}")
            return self._generate_mock_forecast(days) # Fallback

    def _parse_open_meteo_response(self, data: dict) -> List[WeatherForecast]:
        daily = data.get("daily", {})
        times = daily.get("time", [])
        max_temps = daily.get("temperature_2m_max", [])
        min_temps = daily.get("temperature_2m_min", [])
        precip = daily.get("precipitation_sum", [])
        codes = daily.get("weather_code", []) # Note: OpenMeteo uses weather_code (underscore)
        
        forecasts = []
        for i, date_str in enumerate(times):
            # Safe access
            t_max = max_temps[i] if i < len(max_temps) else 30.0
            t_min = min_temps[i] if i < len(min_temps) else 20.0
            rain = precip[i] if i < len(precip) else 0.0
            code = codes[i] if i < len(codes) else 0
            
            condition, icon, advisory = self._map_wmo_code(code, rain, t_max)
            
            # humidity is not in the basic daily set, mocking valid range based on rain
            humidity = 80.0 if rain > 0 else 40.0 

            forecasts.append(WeatherForecast(
                date=date.fromisoformat(date_str),
                temp_min=t_min,
                temp_max=t_max,
                rainfall_mm=rain,
                humidity_pct=humidity,
                condition=condition,
                advisory=advisory,
                icon=icon
            ))
            
        return forecasts

    def _map_wmo_code(self, code: int, rain: float, temp_max: float) -> tuple[str, str, str]:
        """Map WMO code to condition, icon, and advisory."""
        # WMO Code logic
        if code == 0:
            cond = "Sunny"
            icon = "sun"
            adv = "Clear skies. Good for field operations."
            if temp_max > 35:
                adv = "High heat expected. Ensure irrigation."
        elif code in [1, 2, 3]:
            cond = "Cloudy"
            icon = "cloud"
            adv = "Partly cloudy. Suitable for spraying."
        elif code in [45, 48]:
            cond = "Foggy"
            icon = "cloud"
            adv = "Poor visibility. Caution advised."
        elif code in [51, 53, 55, 61, 63, 65, 80, 81, 82]:
            cond = "Rain"
            icon = "cloud-rain"
            adv = "Rain expected. Delay fertilizer application."
            if rain > 20:
                adv = "Heavy rain. Check drainage systems."
        elif code in [71, 73, 75, 77, 85, 86]:
            cond = "Snow"
            icon = "cloud" # No snow icon in frontend yet
            adv = "Freezing conditions. Protect sensitive crops."
        elif code in [95, 96, 99]:
            cond = "Storm"
            icon = "cloud-rain"
            adv = "Thunderstorm alert. Stay indoors."
        else:
            cond = "Unknown"
            icon = "sun"
            adv = "Monitor local conditions."
            
        return cond, icon, adv

    def _generate_mock_forecast(self, days: int) -> List[WeatherForecast]:
        """Generate mock weather data."""
        forecasts = []
        base_date = date.today()
        
        # Simulate a weather trend (e.g., cloudy then rainy)
        current_condition = random.choice(["sunny", "cloudy", "rain"])
        
        for i in range(days):
            day_date = base_date + timedelta(days=i)
            
            # Slight random variation per day
            if random.random() > 0.7:
                current_condition = random.choice(["sunny", "cloudy", "rain"])
            
            temp_variation = random.uniform(-2, 2)
            
            if current_condition == "sunny":
                temp_max = 35 + temp_variation
                temp_min = 25 + temp_variation
                rainfall = 0.0
                humidity = random.uniform(30, 50)
                icon = "sun"
            elif current_condition == "rain":
                temp_max = 28 + temp_variation
                temp_min = 22 + temp_variation
                rainfall = random.uniform(5, 50)
                humidity = random.uniform(70, 90)
                icon = "cloud-rain"
            else:  # cloudy
                temp_max = 30 + temp_variation
                temp_min = 24 + temp_variation
                rainfall = random.uniform(0, 2)
                humidity = random.uniform(50, 70)
                icon = "cloud"
                
            # Generate advisory
            advisory = random.choice(self._advisories.get(current_condition, ["Monitor field conditions."]))
            
            forecasts.append(WeatherForecast(
                date=day_date,
                temp_min=round(temp_min, 1),
                temp_max=round(temp_max, 1),
                rainfall_mm=round(rainfall, 1),
                humidity_pct=round(humidity, 1),
                condition=current_condition,
                advisory=advisory,
                icon=icon
            ))
            
        return forecasts
