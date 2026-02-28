"""
AWS Bedrock Service.

Provides AI capabilities using AWS Bedrock (Claude 3) for:
- Chat/LLM completions (replaces GROQ)
- Image analysis for crop disease detection (replaces HuggingFace)
- Works with same AWS credentials as Polly TTS.
"""
import base64
import json
import logging
from typing import Optional, List, Dict, Any

import boto3
from botocore.exceptions import BotoCoreError, ClientError

from app.config import settings

logger = logging.getLogger(__name__)


class BedrockService:
    """
    AWS Bedrock service for Claude 3 LLM and Vision.
    
    Usage:
        bedrock = BedrockService()
        
        # Chat completion
        response = bedrock.chat_completion([{"role": "user", "content": "Hello"}])
        
        # Image analysis
        result = bedrock.analyze_image(image_bytes, "Diagnose this plant disease")
    """

    def __init__(
        self,
        aws_access_key_id: Optional[str] = None,
        aws_secret_access_key: Optional[str] = None,
        aws_region: Optional[str] = None,
    ):
        self.aws_access_key_id = aws_access_key_id or settings.AWS_ACCESS_KEY_ID
        self.aws_secret_access_key = aws_secret_access_key or settings.AWS_SECRET_ACCESS_KEY
        self.aws_region = aws_region or getattr(settings, "AWS_BEDROCK_REGION", settings.AWS_REGION)
        self._client = None

    @property
    def client(self):
        """Lazy-initialize Bedrock Runtime client."""
        if self._client is None:
            self._client = boto3.client(
                "bedrock-runtime",
                region_name=self.aws_region,
                aws_access_key_id=self.aws_access_key_id,
                aws_secret_access_key=self.aws_secret_access_key,
            )
        return self._client

    def is_configured(self) -> bool:
        """Check if AWS credentials are available for Bedrock."""
        return bool(self.aws_access_key_id and self.aws_secret_access_key)

    def chat_completion(
        self,
        messages: List[Dict[str, Any]],
        temperature: float = 0.7,
        max_tokens: int = 1024,
        system_prompt: Optional[str] = None,
        model_id: Optional[str] = None,
    ) -> Optional[str]:
        """Send a chat completion request using the Bedrock Converse API."""
        if not self.is_configured():
            logger.warning("AWS credentials not configured for Bedrock")
            return None

        model = model_id or settings.AWS_BEDROCK_MODEL_ID
        
        # Convert simple {"role": "user", "content": "text"} to Converse format
        formatted_msgs = []
        for m in messages:
            content = m["content"]
            if isinstance(content, str):
                formatted_msgs.append({"role": m["role"], "content": [{"text": content}]})
            else:
                formatted_msgs.append(m)

        kwargs = {
            "modelId": model,
            "messages": formatted_msgs,
            "inferenceConfig": {"maxTokens": max_tokens, "temperature": temperature}
        }
        if system_prompt:
            kwargs["system"] = [{"text": system_prompt}]

        try:
            response = self.client.converse(**kwargs)
            text = response["output"]["message"]["content"][0]["text"]
            logger.info(f"Bedrock chat OK: {model}")
            return text
        except Exception as e:
            logger.error(f"Bedrock chat error ({model}): {e}")
            return None

    def analyze_image(
        self,
        image_bytes: bytes,
        prompt: str,
        max_tokens: int = 1024,
        model_id: Optional[str] = None,
    ) -> Optional[str]:
        """Analyze an image using Bedrock Converse API with fallback."""
        if not self.is_configured():
            logger.warning("AWS credentials not configured for Bedrock Vision")
            return None

        primary = model_id or settings.AWS_BEDROCK_VISION_MODEL_ID
        fallback = getattr(settings, "AWS_BEDROCK_VISION_FALLBACK_ID", None)

        result = self._invoke_vision(image_bytes, prompt, primary, max_tokens)
        if result:
            return result

        if fallback and fallback != primary:
            logger.info(f"Primary vision failed, trying fallback: {fallback}")
            return self._invoke_vision(image_bytes, prompt, fallback, max_tokens)

        return None

    def _invoke_vision(
        self, image_bytes: bytes, prompt: str, model_id: str, max_tokens: int
    ) -> Optional[str]:
        """Invoke a vision model using the Converse API."""
        fmt = "jpeg"
        if image_bytes[:4] == b'\x89PNG':
            fmt = "png"
        elif image_bytes[:4] == b'RIFF':
            fmt = "webp"

        messages = [
            {
                "role": "user",
                "content": [
                    {
                        "image": {
                            "format": fmt,
                            "source": {"bytes": image_bytes},
                        }
                    },
                    {"text": prompt},
                ],
            }
        ]

        try:
            response = self.client.converse(
                modelId=model_id,
                messages=messages,
                inferenceConfig={"maxTokens": max_tokens},
            )
            text = response["output"]["message"]["content"][0]["text"]
            logger.info(f"Bedrock vision OK: {model_id}")
            return text
        except Exception as e:
            logger.error(f"Bedrock vision error ({model_id}): {e}")
            return None


class TranscribeService:
    """
    AWS Transcribe for Speech-to-Text (replaces Sarvam STT).
    
    Uses real-time streaming or batch transcription.
    """

    def __init__(
        self,
        aws_access_key_id: Optional[str] = None,
        aws_secret_access_key: Optional[str] = None,
        aws_region: Optional[str] = None,
    ):
        self.aws_access_key_id = aws_access_key_id or settings.AWS_ACCESS_KEY_ID
        self.aws_secret_access_key = aws_secret_access_key or settings.AWS_SECRET_ACCESS_KEY
        self.aws_region = aws_region or settings.AWS_REGION
        self._client = None

    @property
    def client(self):
        """Lazy-initialize Transcribe client."""
        if self._client is None:
            self._client = boto3.client(
                "transcribe",
                region_name=self.aws_region,
                aws_access_key_id=self.aws_access_key_id,
                aws_secret_access_key=self.aws_secret_access_key,
            )
        return self._client

    def is_configured(self) -> bool:
        return bool(self.aws_access_key_id and self.aws_secret_access_key)


# Singleton instances
bedrock_service = BedrockService()
transcribe_service = TranscribeService()
