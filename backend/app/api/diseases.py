
"""
Disease Detection API Router.
"""
from fastapi import APIRouter, UploadFile, File, HTTPException
from pydantic import BaseModel

from app.services.disease_service import DiseaseService

router = APIRouter(prefix="/diseases", tags=["diseases"])

class DiseaseResponse(BaseModel):
    disease_name: str
    confidence: float
    treatment: str
    severity: str

@router.post("/diagnose", response_model=DiseaseResponse)
async def diagnose_plant(file: UploadFile = File(...)):
    """
    Diagnose plant disease from an uploaded image.
    """
    service = DiseaseService()
    try:
        contents = await file.read()
        prediction = await service.predict(contents, file.filename)
        return DiseaseResponse(
            disease_name=prediction.disease_name,
            confidence=prediction.confidence,
            treatment=prediction.treatment,
            severity=prediction.severity
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
