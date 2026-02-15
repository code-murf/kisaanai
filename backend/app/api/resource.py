from fastapi import APIRouter, Query
from app.services.resource_service import ResourceService

router = APIRouter(prefix="/resources", tags=["Resources"])
service = ResourceService()

@router.get("/optimize")
async def optimize_resources(
    crop: str = "Potato",
    acres: float = 1.0,
    soil: str = "Loamy",
    days_sowing: int = 45,
    last_watered_days: int = 3
):
    """
    Calculate water and fertilizer requirements.
    """
    return service.calculate_needs(crop, acres, soil, days_sowing, last_watered_days)
