
"""
Disease Detection Service.
Provides plant disease diagnosis from images.
Currently uses mock inference logic.
"""
from dataclasses import dataclass
from typing import Optional

@dataclass
class DiseasePrediction:
    disease_name: str
    confidence: float
    treatment: str
    severity: str

class DiseaseService:
    """
    Service for disease detection.
    """
    
    async def predict(self, image_bytes: bytes, filename: str) -> DiseasePrediction:
        # Mock Logic: Determine outcome based on filename or random
        # In real app, this would load a model and run inference
        
        if "blight" in filename.lower():
            return DiseasePrediction(
                disease_name="Early Blight",
                confidence=0.92,
                treatment="Apply Fungicide (Mancozeb 75 WP @ 2g/l). Ensure proper spacing between plants.",
                severity="High"
            )
        elif "rot" in filename.lower():
             return DiseasePrediction(
                disease_name="Root Rot",
                confidence=0.88,
                treatment="Improve drainage. Apply Copper Oxychloride.",
                severity="Critical"
            )
        else:
             return DiseasePrediction(
                disease_name="Healthy",
                confidence=0.98,
                treatment="No action needed. Maintain regular care.",
                severity="None"
            )
