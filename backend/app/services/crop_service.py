
"""
Crop Recommendation Service.
Provides crop suggestions based on soil parameters (N, P, K, pH) and location.
"""
from typing import List, Optional
from pydantic import BaseModel

class CropRecommendation(BaseModel):
    crop_name: str
    confidence: float
    reason: str
    season: str
    
class CropService:
    """
    Service to recommend crops based on soil health and region.
    Currently uses rule-based logic.
    """
    
    def recommend_crops(self, n: float, p: float, k: float, ph: float, location: str) -> List[CropRecommendation]:
        recommendations = []
        
        # Simple rule-based logic (can be replaced by ML model later)
        
        # Nitrogen heavy
        if n > 120:
            recommendations.append(CropRecommendation(
                crop_name="Leafy Vegetables (Spinach)",
                confidence=0.85,
                reason="High Nitrogen content suitable for leafy growth.",
                season="Winter"
            ))
            
        # Phosphorus heavy
        if p > 50:
             recommendations.append(CropRecommendation(
                crop_name="Chickpea",
                confidence=0.80,
                reason="High Phosphorus supports root development.",
                season="Rabi"
            ))
            
        # Potassium heavy
        if k > 200:
             recommendations.append(CropRecommendation(
                crop_name="Potato",
                confidence=0.90,
                reason="High Potassium required for tuber formation.",
                season="Rabi"
            ))
            
        # Acidic Soil
        if ph < 6.0:
            recommendations.append(CropRecommendation(
                crop_name="Tea",
                confidence=0.95,
                reason="Acidic soil is ideal for tea plantations.",
                season="All Year"
            ))
        elif ph > 7.5:
             recommendations.append(CropRecommendation(
                crop_name="Barley",
                confidence=0.80,
                reason="Tolerant to alkaline soil conditions.",
                season="Rabi"
            ))
        else: # Neutral
             recommendations.append(CropRecommendation(
                crop_name="Wheat",
                confidence=0.92,
                reason="Neutral pH is optimal for wheat.",
                season="Rabi"
            ))
             recommendations.append(CropRecommendation(
                crop_name="Rice",
                confidence=0.88,
                reason="Suitable for neutral to slightly acidic soil.",
                season="Kharif"
            ))
            
        return recommendations

