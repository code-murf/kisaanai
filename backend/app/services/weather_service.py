
"""
Weather Service for KisaanAI.

Fetches weather forecasts from external providers and returns normalized output.
"""
from datetime import date
from typing import List
from dataclasses import dataclass

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
    Service to fetch weather data.
    """

    async def get_forecast(self, lat: float, lon: float, days: int = 14) -> List[WeatherForecast]:
        """
        Get weather forecast for a location from Open-Meteo API.
        """
        import aiohttp

        url = "https://api.open-meteo.com/v1/forecast"
        params = {
            "latitude": lat,
            "longitude": lon,
            "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum,weather_code",
            "timezone": "auto",
            "forecast_days": days,
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params, timeout=15) as response:
                    if response.status != 200:
                        body = await response.text()
                        raise RuntimeError(f"Weather provider error {response.status}: {body[:200]}")
                    data = await response.json()
        except Exception as e:
            raise RuntimeError(f"Weather fetch failed: {e}") from e

        forecasts = self._parse_open_meteo_response(data)
        if not forecasts:
            raise RuntimeError("Weather provider returned empty forecast")
        return forecasts

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

            # Open-Meteo daily endpoint does not provide humidity directly.
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
        if code == 0:
            cond = "sunny"
            icon = "sun"
            adv = "Clear skies. Good for field operations."
            if temp_max > 35:
                adv = "High heat expected. Ensure irrigation."
        elif code in [1, 2, 3]:
            cond = "cloudy"
            icon = "cloud"
            adv = "Partly cloudy. Suitable for spraying."
        elif code in [45, 48]:
            cond = "foggy"
            icon = "cloud"
            adv = "Poor visibility. Caution advised."
        elif code in [51, 53, 55, 61, 63, 65, 80, 81, 82]:
            cond = "rain"
            icon = "cloud-rain"
            adv = "Rain expected. Delay fertilizer application."
            if rain > 20:
                adv = "Heavy rain. Check drainage systems."
        elif code in [71, 73, 75, 77, 85, 86]:
            cond = "snow"
            icon = "cloud"  # No snow icon in frontend yet
            adv = "Freezing conditions. Protect sensitive crops."
        elif code in [95, 96, 99]:
            cond = "storm"
            icon = "cloud-rain"
            adv = "Thunderstorm alert. Stay indoors."
        else:
            cond = "unknown"
            icon = "sun"
            adv = "Monitor local conditions."
        return cond, icon, adv
