"""
API routers for the Agri-Analytics platform.
"""
from app.api import auth, commodities, mandis, prices, forecasts, routing, webhooks, weather, crops, diseases, voice

__all__ = ["auth", "commodities", "mandis", "prices", "forecasts", "routing", "webhooks", "weather", "crops", "diseases", "voice"]
