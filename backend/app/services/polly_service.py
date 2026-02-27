"""
Amazon Polly Text-to-Speech Service.

Provides realtime TTS using AWS Polly with streaming support.
Supports Hindi and English with neural voices (Kajal).
Free tier: 5M standard chars + 1M neural chars/month for 12 months.
"""
import base64
import logging
import time
from typing import Optional, AsyncGenerator

import boto3
from botocore.exceptions import BotoCoreError, ClientError

from app.config import settings

logger = logging.getLogger(__name__)


# Language code mapping: internal codes -> Polly language codes
LANGUAGE_MAP = {
    "hi": "hi-IN",
    "hi-IN": "hi-IN",
    "en": "en-IN",
    "en-IN": "en-IN",
    "en-US": "en-US",
}

# Default voice per language
VOICE_MAP = {
    "hi-IN": {"neural": "Kajal", "standard": "Aditi"},
    "en-IN": {"neural": "Kajal", "standard": "Aditi"},
    "en-US": {"neural": "Joanna", "standard": "Joanna"},
}


class PollyService:
    """
    Amazon Polly TTS service with streaming support.
    
    Usage:
        polly = PollyService()
        
        # Full audio (base64)
        result = polly.synthesize("Namaste kisaan bhai", language="hi")
        
        # Streaming chunks for realtime playback
        for chunk in polly.synthesize_stream("Namaste", language="hi"):
            send_to_client(chunk)
    """

    def __init__(
        self,
        aws_access_key_id: Optional[str] = None,
        aws_secret_access_key: Optional[str] = None,
        aws_region: Optional[str] = None,
    ):
        self.aws_access_key_id = aws_access_key_id or settings.AWS_ACCESS_KEY_ID
        self.aws_secret_access_key = aws_secret_access_key or settings.AWS_SECRET_ACCESS_KEY
        self.aws_region = aws_region or getattr(settings, "AWS_REGION", "ap-south-1")
        self._client = None

    @property
    def client(self):
        """Lazy-initialize Polly client."""
        if self._client is None:
            self._client = boto3.client(
                "polly",
                region_name=self.aws_region,
                aws_access_key_id=self.aws_access_key_id,
                aws_secret_access_key=self.aws_secret_access_key,
            )
        return self._client

    def _resolve_language(self, language: str) -> str:
        """Convert internal language code to Polly language code."""
        return LANGUAGE_MAP.get(language, "hi-IN")

    def _resolve_voice(self, language: str, engine: str = "neural") -> str:
        """Get the best voice for a language and engine type."""
        polly_lang = self._resolve_language(language)
        voices = VOICE_MAP.get(polly_lang, VOICE_MAP["hi-IN"])
        return voices.get(engine, voices.get("neural", "Kajal"))

    def synthesize(
        self,
        text: str,
        language: str = "hi",
        output_format: str = "mp3",
        engine: str = "neural",
        sample_rate: str = "24000",
    ) -> dict:
        """
        Synthesize text to speech (full audio).

        Args:
            text: Text to convert to speech (max 3000 chars)
            language: Language code (hi, en, hi-IN, en-IN)
            output_format: mp3, ogg_vorbis, or pcm
            engine: neural or standard
            sample_rate: Audio sample rate

        Returns:
            dict with keys: success, audio_base64, audio_bytes, content_type, chars_used, duration_ms
        """
        start = time.time()

        try:
            polly_lang = self._resolve_language(language)
            voice_id = self._resolve_voice(language, engine)

            params = {
                "Text": text,
                "OutputFormat": output_format,
                "VoiceId": voice_id,
                "Engine": engine,
                "LanguageCode": polly_lang,
            }
            if output_format == "pcm":
                params["SampleRate"] = sample_rate

            response = self.client.synthesize_speech(**params)
            audio_bytes = response["AudioStream"].read()
            audio_b64 = base64.b64encode(audio_bytes).decode("utf-8")

            duration_ms = int((time.time() - start) * 1000)
            logger.info(
                f"Polly TTS: {len(text)} chars -> {len(audio_bytes)} bytes "
                f"({voice_id}/{engine}) in {duration_ms}ms"
            )

            return {
                "success": True,
                "audio_base64": audio_b64,
                "audio_bytes": audio_bytes,
                "content_type": response["ContentType"],
                "chars_used": response["RequestCharacters"],
                "duration_ms": duration_ms,
                "voice": voice_id,
                "engine": engine,
            }

        except (BotoCoreError, ClientError) as e:
            logger.error(f"Polly TTS error: {e}")
            return {
                "success": False,
                "error": str(e),
                "duration_ms": int((time.time() - start) * 1000),
            }

    def synthesize_stream(
        self,
        text: str,
        language: str = "hi",
        engine: str = "neural",
        sample_rate: str = "16000",
        chunk_size: int = 4096,
    ):
        """
        Stream synthesized audio in chunks for realtime playback.

        Args:
            text: Text to convert
            language: Language code
            engine: neural or standard
            sample_rate: Sample rate for PCM output
            chunk_size: Size of each audio chunk in bytes

        Yields:
            bytes: Raw PCM audio chunks
        """
        try:
            polly_lang = self._resolve_language(language)
            voice_id = self._resolve_voice(language, engine)

            response = self.client.synthesize_speech(
                Text=text,
                OutputFormat="pcm",
                SampleRate=sample_rate,
                VoiceId=voice_id,
                Engine=engine,
                LanguageCode=polly_lang,
            )

            stream = response["AudioStream"]
            while True:
                chunk = stream.read(chunk_size)
                if not chunk:
                    break
                yield chunk

        except (BotoCoreError, ClientError) as e:
            logger.error(f"Polly stream error: {e}")
            raise

    def get_available_voices(self, language: str = "hi") -> list:
        """List available voices for a language."""
        try:
            polly_lang = self._resolve_language(language)
            response = self.client.describe_voices(LanguageCode=polly_lang)
            return [
                {
                    "id": v["Id"],
                    "name": v["Name"],
                    "gender": v["Gender"],
                    "engines": v.get("SupportedEngines", []),
                }
                for v in response["Voices"]
            ]
        except (BotoCoreError, ClientError) as e:
            logger.error(f"Polly list voices error: {e}")
            return []


# Singleton instance
polly_service = PollyService()
