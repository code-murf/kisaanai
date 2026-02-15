
"""
Crop Recommendation API Endpoints.
"""
from typing import List
from fastapi import APIRouter, Query, HTTPException
from pydantic import BaseModel

from app.services.crop_service import CropService, CropRecommendation

router = APIRouter(prefix="/crops", tags=["crops"])

@router.get("/recommend", response_model=List[CropRecommendation])
async def recommend_crops(
    n: float = Query(..., description="Nitrogen content (kg/ha)"),
    p: float = Query(..., description="Phosphorus content (kg/ha)"),
    k: float = Query(..., description="Potassium content (kg/ha)"),
    ph: float = Query(..., description="Soil pH level"),
    location: str = Query("General", description="Location/Region")
):
    """
    Get crop recommendations based on soil parameters.
    """
    service = CropService()
    try:
        return service.recommend_crops(n, p, k, ph, location)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
