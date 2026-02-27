
"""
Disease Detection Service.
Uses a real image classification model via Hugging Face Inference API.
"""
from dataclasses import dataclass
from typing import Optional, Any

import aiohttp

from app.config import settings

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

    def __init__(self):
        self._model_id = settings.HF_DISEASE_MODEL_ID
        self._token = settings.HF_TOKEN
        self._timeout = settings.HF_TIMEOUT_SECONDS

    async def predict(self, image_bytes: bytes, filename: str) -> DiseasePrediction:
        if not image_bytes:
            raise ValueError("Uploaded image is empty")
        if not self._token:
            raise RuntimeError("HF_TOKEN is not configured for disease diagnosis")

        url = f"https://api-inference.huggingface.co/models/{self._model_id}"
        headers = {
            "Authorization": f"Bearer {self._token}",
            "Content-Type": "application/octet-stream",
        }

        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self._timeout)) as session:
                async with session.post(url, headers=headers, data=image_bytes) as response:
                    if response.status >= 400:
                        body = await response.text()
                        raise RuntimeError(f"Disease inference failed ({response.status}): {body[:200]}")
                    payload: Any = await response.json()
        except Exception as e:
            raise RuntimeError(f"Disease inference request failed: {e}") from e

        label, score = self._extract_top_prediction(payload)
        if not label:
            raise RuntimeError("Disease inference returned no classification labels")

        treatment = self._get_treatment_for_label(label)
        severity = self._severity_from_confidence(score)

        return DiseasePrediction(
            disease_name=label,
            confidence=round(score, 4),
            treatment=treatment,
            severity=severity,
        )

    def _extract_top_prediction(self, payload: Any) -> tuple[Optional[str], float]:
        # Hugging Face image-classification can return either:
        # - [{"label": "...", "score": ...}, ...]
        # - [[{"label": "...", "score": ...}, ...]]
        candidates = payload
        if isinstance(payload, list) and payload and isinstance(payload[0], list):
            candidates = payload[0]

        if not isinstance(candidates, list) or not candidates:
            return None, 0.0

        valid = [item for item in candidates if isinstance(item, dict) and "label" in item and "score" in item]
        if not valid:
            return None, 0.0

        top = max(valid, key=lambda x: float(x.get("score", 0.0)))
        label = str(top.get("label", "")).replace("_", " ").strip()
        score = float(top.get("score", 0.0))
        return label or None, score

    def _severity_from_confidence(self, confidence: float) -> str:
        if confidence >= 0.85:
            return "High"
        if confidence >= 0.65:
            return "Moderate"
        return "Low"

    def _get_treatment_for_label(self, label: str) -> str:
        normalized = label.lower()

        if "healthy" in normalized:
            return "No disease detected. Continue regular crop monitoring and preventive care."
        if "blight" in normalized:
            return "Remove infected leaves, avoid overhead irrigation, and apply a recommended fungicide as per local agri advisory."
        if "rust" in normalized:
            return "Use resistant varieties where possible and apply a suitable rust fungicide as recommended locally."
        if "mildew" in normalized:
            return "Improve airflow in the crop canopy and apply targeted fungicide based on agronomist guidance."
        if "rot" in normalized:
            return "Improve drainage, reduce overwatering, and treat with appropriate fungicidal/bactericidal control."

        return "Consult a local agronomist/KVK with this diagnosis label before treatment application."
