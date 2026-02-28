
"""
Disease Detection Service.
Uses Bedrock Vision (Nova Lite, cheapest) → Bedrock Text (Haiku) → HuggingFace fallback.
"""
import asyncio
import json
import logging
from dataclasses import dataclass
from typing import Optional, Any

import aiohttp

from app.config import settings

logger = logging.getLogger(__name__)


@dataclass
class DiseasePrediction:
    disease_name: str
    confidence: float
    treatment: str
    severity: str


class DiseaseService:
    """
    Service for crop disease detection.
    Primary: AWS Bedrock Claude 3 Vision
    Fallback: HuggingFace Inference API
    """

    def __init__(self):
        self._model_id = settings.HF_DISEASE_MODEL_ID
        self._token = settings.HF_TOKEN
        self._timeout = settings.HF_TIMEOUT_SECONDS

        # Try to init Bedrock
        self._bedrock = None
        try:
            from app.services.bedrock_service import bedrock_service
            if bedrock_service.is_configured():
                self._bedrock = bedrock_service
                logger.info("Disease service using Bedrock Claude Vision")
        except Exception as e:
            logger.warning(f"Bedrock init for disease service failed: {e}")

    async def predict(self, image_bytes: bytes, filename: str) -> DiseasePrediction:
        if not image_bytes:
            raise ValueError("Uploaded image is empty")

        # Try Bedrock Claude Vision first (if model access is approved)
        if self._bedrock:
            try:
                return await self._predict_bedrock_vision(image_bytes)
            except Exception as e:
                logger.info(f"Bedrock vision unavailable, trying text-based: {e}")
                try:
                    return await self._predict_bedrock_text(image_bytes, filename)
                except Exception as e2:
                    logger.warning(f"Bedrock text also failed: {e2}")

        # Fallback: HuggingFace image classification
        if self._token:
            try:
                return await self._predict_huggingface(image_bytes, filename)
            except Exception as e:
                logger.warning(f"HuggingFace failed: {e}")

        raise RuntimeError(
            "Disease detection unavailable. Please try again later."
        )

    async def _predict_bedrock_vision(self, image_bytes: bytes) -> DiseasePrediction:
        """Diagnose plant disease using Bedrock Vision (Nova Lite or Claude)."""
        prompt = """You are an expert agricultural scientist. Analyze this plant image and diagnose any disease.

Respond ONLY in this exact JSON format (no other text):
{
    "disease_name": "Name of the disease (or 'Healthy' if no disease)",
    "confidence": 0.85,
    "severity": "High/Moderate/Low",
    "treatment": "Brief treatment recommendation in 1-2 sentences"
}"""

        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None,
            lambda: self._bedrock.analyze_image(
                image_bytes=image_bytes,
                prompt=prompt,
                max_tokens=512,
            ),
        )

        if not result:
            raise RuntimeError("Bedrock Vision returned empty response")

        return self._parse_json_response(result)

    async def _predict_bedrock_text(self, image_bytes: bytes, filename: str) -> DiseasePrediction:
        """Fallback: Use Claude Haiku text model for basic diagnosis from filename."""
        prompt = f"""You are an expert agricultural scientist. A farmer uploaded a photo named '{filename}'.
Based on common crop diseases in India, provide a likely diagnosis.

Respond ONLY in this exact JSON format:
{{"disease_name": "Most likely disease name", "confidence": 0.6, "severity": "Moderate", "treatment": "Brief recommendation"}}"""

        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None,
            lambda: self._bedrock.chat_completion(
                messages=[{"role": "user", "content": prompt}],
                max_tokens=256,
            ),
        )

        if not result:
            raise RuntimeError("Bedrock text returned empty response")

        return self._parse_json_response(result)

    def _parse_json_response(self, result: str) -> DiseasePrediction:
        """Parse JSON response from Claude/Nova into DiseasePrediction."""
        try:
            text = result.strip()
            if text.startswith("```"):
                text = text.split("\n", 1)[1].rsplit("```", 1)[0].strip()
            data = json.loads(text)
        except json.JSONDecodeError:
            logger.warning(f"Non-JSON response, using raw text: {result[:200]}")
            return DiseasePrediction(
                disease_name="Unknown Disease",
                confidence=0.5,
                treatment=result[:300],
                severity="Moderate",
            )

        return DiseasePrediction(
            disease_name=data.get("disease_name", "Unknown"),
            confidence=float(data.get("confidence", 0.75)),
            treatment=data.get("treatment", "Consult a local agronomist."),
            severity=data.get("severity", "Moderate"),
        )

    async def _predict_huggingface(self, image_bytes: bytes, filename: str) -> DiseasePrediction:
        """Fallback: HuggingFace Inference API."""
        url = f"https://api-inference.huggingface.co/models/{self._model_id}"
        headers = {
            "Authorization": f"Bearer {self._token}",
            "Content-Type": "application/octet-stream",
        }

        try:
            async with aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=self._timeout)
            ) as session:
                async with session.post(url, headers=headers, data=image_bytes) as response:
                    if response.status >= 400:
                        body = await response.text()
                        raise RuntimeError(
                            f"HF inference failed ({response.status}): {body[:200]}"
                        )
                    payload: Any = await response.json()
        except Exception as e:
            raise RuntimeError(f"HF inference request failed: {e}") from e

        label, score = self._extract_top_prediction(payload)
        if not label:
            raise RuntimeError("HF returned no classification labels")

        treatment = self._get_treatment_for_label(label)
        severity = self._severity_from_confidence(score)

        return DiseasePrediction(
            disease_name=label,
            confidence=round(score, 4),
            treatment=treatment,
            severity=severity,
        )

    def _extract_top_prediction(self, payload: Any) -> tuple[Optional[str], float]:
        candidates = payload
        if isinstance(payload, list) and payload and isinstance(payload[0], list):
            candidates = payload[0]

        if not isinstance(candidates, list) or not candidates:
            return None, 0.0

        valid = [
            item
            for item in candidates
            if isinstance(item, dict) and "label" in item and "score" in item
        ]
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
