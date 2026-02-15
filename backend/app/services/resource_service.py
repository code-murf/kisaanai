from datetime import date, timedelta
from typing import Dict, Any

class ResourceService:
    def __init__(self):
        # Mock Crop Coefficient (Kc) Data
        self.crop_data = {
            "Wheat": {"kc_mid": 1.15, "stage_days": 120, "npk_ratio": "4:2:1"},
            "Rice": {"kc_mid": 1.20, "stage_days": 150, "npk_ratio": "4:2:1"},
            "Potato": {"kc_mid": 1.10, "stage_days": 90, "npk_ratio": "3:1:1"},
            "Onion": {"kc_mid": 1.05, "stage_days": 110, "npk_ratio": "2:1:1"},
        }
    
    def calculate_needs(self, crop_name: str, acres: float, soil_type: str, days_since_sowing: int, last_watered: int) -> Dict[str, Any]:
        crop = self.crop_data.get(crop_name, self.crop_data["Wheat"])
        
        # 1. Water Calculation (Simplified Penman-Monteith logic)
        # ETo (Reference Evapotranspiration) approx 4-5 mm/day in India
        eto = 4.5 
        kc = crop["kc_mid"] if 30 < days_since_sowing < (crop["stage_days"] - 20) else 0.5
        
        # Crop Water Need (mm/day)
        etc = eto * kc
        
        # Total deficit since last watered
        deficit_mm = etc * last_watered
        
        # Convert mm/acre to Liters
        # 1 mm = 1 Liter/m2
        # 1 Acre = 4046.86 m2
        water_liters = deficit_mm * 4046.86 * acres
        
        # Adjust for Soil (Clay holds more, Sandy holds less)
        soil_factor = 1.0
        if "Sand" in soil_type: soil_factor = 1.2 # Needs more frequent
        if "Clay" in soil_type: soil_factor = 0.8 # Retains more
        
        recommended_water = water_liters * soil_factor
        
        # 2. Fertilizer Recommendation
        # Simplified rule based on crop
        fertilizer_msg = f"Apply NPK {crop['npk_ratio']} mix."
        if days_since_sowing < 30:
            fertilizer_msg += " Focus on Nitrogen for vegetative growth."
        elif days_since_sowing > (crop["stage_days"] - 30):
            fertilizer_msg += " Reduce Nitrogen, focus on Potassium for maturity."
        else:
             fertilizer_msg += " Ensure Phosphorus and Potassium for root/tuber development."
            
        return {
            "water_liters": int(recommended_water),
            "fertilizer_recommendation": fertilizer_msg,
            "crop_health_status": "Good" if last_watered < 7 else "Stress Risk",
            "next_action": "Irrigate Immediately" if last_watered > 5 else "Monitor Soil Moisture"
        }
