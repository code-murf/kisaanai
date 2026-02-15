"""
Bhashini Voice Service for ASR (Automatic Speech Recognition) and TTS (Text-to-Speech).

This module provides integration with the Bhashini AI platform for:
- Speech-to-text conversion in multiple Indian languages
- Text-to-speech synthesis for voice responses
- Language detection and translation support
"""
import asyncio
import base64
import hashlib
import json
import logging
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, List, Dict, Any, AsyncGenerator
from pathlib import Path

import aiohttp
from pydantic import BaseModel, Field

from app.config import settings


logger = logging.getLogger(__name__)


# ============================================================================
# ENUMS AND MODELS
# ============================================================================

class SupportedLanguage(str, Enum):
    """Supported languages for voice processing."""
    HINDI = "hi"
    ENGLISH = "en"
    BENGALI = "bn"
    TELUGU = "te"
    MARATHI = "mr"
    TAMIL = "ta"
    GUJARATI = "gu"
    KANNADA = "kn"
    MALAYALAM = "ml"
    PUNJABI = "pa"
    ODIA = "or"
    ASSAMESE = "as"
    URDU = "ur"


class AudioFormat(str, Enum):
    """Supported audio formats."""
    WAV = "wav"
    MP3 = "mp3"
    FLAC = "flac"
    OGG = "ogg"
    WEBM = "webm"


class VoiceGender(str, Enum):
    """Voice gender options for TTS."""
    MALE = "male"
    FEMALE = "female"


@dataclass
class ASRResult:
    """Result from ASR (Speech-to-Text) operation."""
    success: bool
    transcript: str
    language: str
    confidence: float = 0.0
    alternatives: List[Dict[str, Any]] = field(default_factory=list)
    duration_seconds: float = 0.0
    error: Optional[str] = None


@dataclass
class TTSResult:
    """Result from TTS (Text-to-Speech) operation."""
    success: bool
    audio_data: Optional[bytes] = None
    audio_format: str = "wav"
    duration_seconds: float = 0.0
    sample_rate: int = 22050
    error: Optional[str] = None


@dataclass
class TranslationResult:
    """Result from translation operation."""
    success: bool
    translated_text: str
    source_language: str
    target_language: str
    error: Optional[str] = None


class ASRRequest(BaseModel):
    """Request model for ASR."""
    audio_base64: str = Field(..., description="Base64 encoded audio data")
    language: str = Field(default="hi", description="Language code")
    audio_format: str = Field(default="wav", description="Audio format")
    sample_rate: int = Field(default=16000, description="Sample rate in Hz")
    enable_punctuation: bool = Field(default=True, description="Add punctuation")
    enable_itn: bool = Field(default=True, description="Inverse text normalization")


class TTSRequest(BaseModel):
    """Request model for TTS."""
    text: str = Field(..., description="Text to synthesize", max_length=1000)
    language: str = Field(default="hi", description="Language code")
    gender: str = Field(default="female", description="Voice gender")
    speed: float = Field(default=1.0, ge=0.5, le=2.0, description="Speech speed")
    pitch: float = Field(default=1.0, ge=0.5, le=2.0, description="Voice pitch")
    output_format: str = Field(default="wav", description="Output audio format")


class TranslationRequest(BaseModel):
    """Request model for translation."""
    text: str = Field(..., description="Text to translate", max_length=5000)
    source_language: str = Field(..., description="Source language code")
    target_language: str = Field(..., description="Target language code")


# ============================================================================
# BHASHINI CLIENT
# ============================================================================

class BhashiniClient:
    """
    Client for interacting with Bhashini AI services.
    
    Bhashini is India's AI-led language translation platform providing
    ASR, TTS, and translation services for Indian languages.
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        user_id: Optional[str] = None,
        base_url: str = "https://dhruva-api.bhashini.gov.in",
        timeout: int = 30,
    ):
        """
        Initialize Bhashini client.
        
        Args:
            api_key: Bhashini API key
            user_id: User ID for authentication
            base_url: Base URL for Bhashini API
            timeout: Request timeout in seconds
        """
        self.api_key = api_key or settings.BHASHINI_API_KEY
        self.user_id = user_id or settings.BHASHINI_USER_ID
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self._session: Optional[aiohttp.ClientSession] = None
        
        # Service endpoints (these may vary based on Bhashini's actual API)
        self.endpoints = {
            "asr": f"{self.base_url}/services/inference/asr",
            "tts": f"{self.base_url}/services/inference/tts",
            "translation": f"{self.base_url}/services/inference/translation",
            "pipeline": f"{self.base_url}/services/inference/pipeline",
        }
    
    async def __aenter__(self) -> "BhashiniClient":
        """Create aiohttp session on context entry."""
        if self._session is None:
            self._session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=self.timeout),
                headers=self._get_headers(),
            )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        """Close aiohttp session on context exit."""
        if self._session:
            await self._session.close()
            self._session = None
    
    def _get_headers(self) -> Dict[str, str]:
        """Get common headers for API requests."""
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
    
    async def _make_request(
        self,
        endpoint: str,
        payload: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Make API request to Bhashini.
        
        Args:
            endpoint: API endpoint URL
            payload: Request payload
        
        Returns:
            Response data
        
        Raises:
            Exception: If request fails
        """
        if not self._session:
            raise RuntimeError("Session not initialized. Use async context manager.")
        
        try:
            async with self._session.post(endpoint, json=payload) as response:
                if response.status == 200:
                    return await response.json()
                elif response.status == 401:
                    raise Exception("Authentication failed. Check API key.")
                elif response.status == 429:
                    raise Exception("Rate limit exceeded. Please retry later.")
                else:
                    error_text = await response.text()
                    raise Exception(f"API error: {response.status} - {error_text}")
        except aiohttp.ClientError as e:
            raise Exception(f"Network error: {str(e)}")
    
    async def speech_to_text(
        self,
        audio_data: bytes,
        language: str = "hi",
        audio_format: str = "wav",
        sample_rate: int = 16000,
    ) -> ASRResult:
        """
        Convert speech to text using Bhashini ASR.
        
        Args:
            audio_data: Raw audio bytes
            language: Language code (e.g., 'hi' for Hindi)
            audio_format: Audio format
            sample_rate: Sample rate in Hz
        
        Returns:
            ASRResult with transcript
        """
        start_time = time.time()
        
        try:
            # Encode audio to base64
            audio_base64 = base64.b64encode(audio_data).decode("utf-8")
            
            # Get model ID for language
            model_id = self._get_asr_model_id(language)
            
            payload = {
                "pipelineTasks": [
                    {
                        "taskType": "asr",
                        "config": {
                            "language": {
                                "sourceLanguage": language,
                            },
                            "serviceId": model_id,
                            "audioFormat": audio_format,
                            "samplingRate": sample_rate,
                        }
                    }
                ],
                "inputData": {
                    "audio": [
                        {
                            "audioContent": audio_base64,
                        }
                    ]
                }
            }
            
            response = await self._make_request(self.endpoints["pipeline"], payload)
            
            # Parse response
            output = response.get("pipelineResponse", [{}])[0]
            output_data = output.get("output", [{}])[0]
            
            transcript = output_data.get("source", "")
            confidence = output_data.get("confidence", 0.0)
            
            return ASRResult(
                success=True,
                transcript=transcript,
                language=language,
                confidence=confidence,
                duration_seconds=time.time() - start_time,
            )
            
        except Exception as e:
            logger.error(f"ASR failed: {e}")
            return ASRResult(
                success=False,
                transcript="",
                language=language,
                error=str(e),
                duration_seconds=time.time() - start_time,
            )
    
    async def text_to_speech(
        self,
        text: str,
        language: str = "hi",
        gender: str = "female",
        speed: float = 1.0,
        output_format: str = "wav",
    ) -> TTSResult:
        """
        Convert text to speech using Bhashini TTS.
        
        Args:
            text: Text to synthesize
            language: Language code
            gender: Voice gender
            speed: Speech speed multiplier
            output_format: Output audio format
        
        Returns:
            TTSResult with audio data
        """
        start_time = time.time()
        
        try:
            # Get model ID for language
            model_id = self._get_tts_model_id(language, gender)
            
            payload = {
                "pipelineTasks": [
                    {
                        "taskType": "tts",
                        "config": {
                            "language": {
                                "sourceLanguage": language,
                            },
                            "serviceId": model_id,
                            "gender": gender,
                            "speed": speed,
                            "audioFormat": output_format,
                        }
                    }
                ],
                "inputData": {
                    "text": [
                        {
                            "source": text,
                        }
                    ]
                }
            }
            
            response = await self._make_request(self.endpoints["pipeline"], payload)
            
            # Parse response
            output = response.get("pipelineResponse", [{}])[0]
            output_data = output.get("output", [{}])[0]
            
            audio_base64 = output_data.get("audio", "")
            if audio_base64:
                audio_data = base64.b64decode(audio_base64)
            else:
                audio_data = None
            
            return TTSResult(
                success=True,
                audio_data=audio_data,
                audio_format=output_format,
                duration_seconds=time.time() - start_time,
            )
            
        except Exception as e:
            logger.error(f"TTS failed: {e}")
            return TTSResult(
                success=False,
                error=str(e),
                duration_seconds=time.time() - start_time,
            )
    
    async def translate(
        self,
        text: str,
        source_language: str,
        target_language: str,
    ) -> TranslationResult:
        """
        Translate text between languages.
        
        Args:
            text: Text to translate
            source_language: Source language code
            target_language: Target language code
        
        Returns:
            TranslationResult with translated text
        """
        try:
            model_id = self._get_translation_model_id(source_language, target_language)
            
            payload = {
                "pipelineTasks": [
                    {
                        "taskType": "translation",
                        "config": {
                            "language": {
                                "sourceLanguage": source_language,
                                "targetLanguage": target_language,
                            },
                            "serviceId": model_id,
                        }
                    }
                ],
                "inputData": {
                    "text": [
                        {
                            "source": text,
                        }
                    ]
                }
            }
            
            response = await self._make_request(self.endpoints["pipeline"], payload)
            
            # Parse response
            output = response.get("pipelineResponse", [{}])[0]
            output_data = output.get("output", [{}])[0]
            
            translated_text = output_data.get("target", "")
            
            return TranslationResult(
                success=True,
                translated_text=translated_text,
                source_language=source_language,
                target_language=target_language,
            )
            
        except Exception as e:
            logger.error(f"Translation failed: {e}")
            return TranslationResult(
                success=False,
                translated_text="",
                source_language=source_language,
                target_language=target_language,
                error=str(e),
            )
    
    async def transcribe_and_translate(
        self,
        audio_data: bytes,
        source_language: str,
        target_language: str,
        audio_format: str = "wav",
    ) -> Dict[str, Any]:
        """
        Transcribe audio and translate to target language in one pipeline.
        
        Args:
            audio_data: Raw audio bytes
            source_language: Source language code
            target_language: Target language code
            audio_format: Audio format
        
        Returns:
            Dictionary with transcript and translation
        """
        try:
            asr_model = self._get_asr_model_id(source_language)
            translation_model = self._get_translation_model_id(source_language, target_language)
            
            audio_base64 = base64.b64encode(audio_data).decode("utf-8")
            
            payload = {
                "pipelineTasks": [
                    {
                        "taskType": "asr",
                        "config": {
                            "language": {"sourceLanguage": source_language},
                            "serviceId": asr_model,
                        }
                    },
                    {
                        "taskType": "translation",
                        "config": {
                            "language": {
                                "sourceLanguage": source_language,
                                "targetLanguage": target_language,
                            },
                            "serviceId": translation_model,
                        }
                    }
                ],
                "inputData": {
                    "audio": [{"audioContent": audio_base64}]
                }
            }
            
            response = await self._make_request(self.endpoints["pipeline"], payload)
            
            # Parse response
            results = {}
            for task in response.get("pipelineResponse", []):
                task_type = task.get("taskType")
                output = task.get("output", [{}])[0]
                
                if task_type == "asr":
                    results["transcript"] = output.get("source", "")
                    results["transcript_language"] = source_language
                elif task_type == "translation":
                    results["translation"] = output.get("target", "")
                    results["translation_language"] = target_language
            
            return {
                "success": True,
                **results
            }
            
        except Exception as e:
            logger.error(f"Pipeline failed: {e}")
            return {
                "success": False,
                "error": str(e),
            }
    
    def _get_asr_model_id(self, language: str) -> str:
        """Get ASR model ID for language."""
        # These are example model IDs - actual IDs depend on Bhashini's offerings
        model_map = {
            "hi": "ai4bharat/conformer-hindi-gpu",
            "en": "ai4bharat/conformer-indo-aryan-gpu",
            "bn": "ai4bharat/conformer-bengali-gpu",
            "te": "ai4bharat/conformer-telugu-gpu",
            "mr": "ai4bharat/conformer-marathi-gpu",
            "ta": "ai4bharat/conformer-tamil-gpu",
            "gu": "ai4bharat/conformer-gujarati-gpu",
            "kn": "ai4bharat/conformer-kannada-gpu",
            "ml": "ai4bharat/conformer-malayalam-gpu",
            "pa": "ai4bharat/conformer-punjabi-gpu",
            "or": "ai4bharat/conformer-odia-gpu",
            "as": "ai4bharat/conformer-assamese-gpu",
            "ur": "ai4bharat/conformer-urdu-gpu",
        }
        return model_map.get(language, model_map["hi"])
    
    def _get_tts_model_id(self, language: str, gender: str = "female") -> str:
        """Get TTS model ID for language and gender."""
        # These are example model IDs
        model_map = {
            "hi": {"female": "ai4bharat/tts-hindi-female", "male": "ai4bharat/tts-hindi-male"},
            "en": {"female": "ai4bharat/tts-indianenglish-female", "male": "ai4bharat/tts-indianenglish-male"},
            "bn": {"female": "ai4bharat/tts-bengali-female", "male": "ai4bharat/tts-bengali-male"},
            "te": {"female": "ai4bharat/tts-telugu-female", "male": "ai4bharat/tts-telugu-male"},
            "mr": {"female": "ai4bharat/tts-marathi-female", "male": "ai4bharat/tts-marathi-male"},
            "ta": {"female": "ai4bharat/tts-tamil-female", "male": "ai4bharat/tts-tamil-male"},
        }
        lang_models = model_map.get(language, model_map["hi"])
        return lang_models.get(gender, lang_models["female"])
    
    def _get_translation_model_id(self, source: str, target: str) -> str:
        """Get translation model ID for language pair."""
        # These are example model IDs
        return f"ai4bharat/indictrans-{source}-{target}"


# ============================================================================
# VOICE SERVICE
# ============================================================================

class VoiceService:
    """
    High-level voice service for agricultural platform.
    
    Provides convenient methods for voice interactions with
    caching, error handling, and fallback mechanisms.
    """
    
    def __init__(self, client: Optional[BhashiniClient] = None):
        """
        Initialize voice service.
        
        Args:
            client: Optional BhashiniClient instance
        """
        self._client = client
        self._default_language = "hi"
        self._cache: Dict[str, Any] = {}
    
    async def _get_client(self) -> BhashiniClient:
        """Get or create Bhashini client."""
        if self._client is None:
            self._client = BhashiniClient()
        return self._client
    
    async def transcribe(
        self,
        audio_data: bytes,
        language: Optional[str] = None,
        audio_format: str = "wav",
    ) -> ASRResult:
        """
        Transcribe audio to text.
        
        Args:
            audio_data: Raw audio bytes
            language: Language code (uses default if not provided)
            audio_format: Audio format
        
        Returns:
            ASRResult with transcript
        """
        language = language or self._default_language
        
        client = await self._get_client()
        async with client:
            return await client.speech_to_text(
                audio_data=audio_data,
                language=language,
                audio_format=audio_format,
            )
    
    async def synthesize(
        self,
        text: str,
        language: Optional[str] = None,
        gender: str = "female",
        speed: float = 1.0,
    ) -> TTSResult:
        """
        Synthesize text to speech.
        
        Args:
            text: Text to synthesize
            language: Language code
            gender: Voice gender
            speed: Speech speed
        
        Returns:
            TTSResult with audio data
        """
        language = language or self._default_language
        
        # Check cache
        cache_key = self._get_cache_key(text, language, gender, speed)
        if cache_key in self._cache:
            cached = self._cache[cache_key]
            return TTSResult(
                success=True,
                audio_data=cached["audio"],
                audio_format=cached["format"],
            )
        
        client = await self._get_client()
        async with client:
            result = await client.text_to_speech(
                text=text,
                language=language,
                gender=gender,
                speed=speed,
            )
            
            # Cache successful results
            if result.success and result.audio_data:
                self._cache[cache_key] = {
                    "audio": result.audio_data,
                    "format": result.audio_format,
                }
            
            return result
    
    async def translate_text(
        self,
        text: str,
        target_language: str,
        source_language: Optional[str] = None,
    ) -> TranslationResult:
        """
        Translate text between languages.
        
        Args:
            text: Text to translate
            target_language: Target language code
            source_language: Source language code (auto-detect if not provided)
        
        Returns:
            TranslationResult with translated text
        """
        source_language = source_language or self._default_language
        
        client = await self._get_client()
        async with client:
            return await client.translate(
                text=text,
                source_language=source_language,
                target_language=target_language,
            )
    
    async def process_voice_query(
        self,
        audio_data: bytes,
        language: str = "hi",
        response_language: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Process a voice query end-to-end.
        
        Args:
            audio_data: Raw audio bytes of the query
            language: Language of the input audio
            response_language: Language for response (defaults to input language)
        
        Returns:
            Dictionary with transcript and response audio
        """
        response_language = response_language or language
        
        # Transcribe
        asr_result = await self.transcribe(audio_data, language)
        
        if not asr_result.success:
            return {
                "success": False,
                "error": asr_result.error,
                "transcript": None,
                "response_audio": None,
            }
        
        # Here you would typically:
        # 1. Process the transcript (NLU/intent detection)
        # 2. Generate a response
        # 3. Synthesize the response
        
        # For now, return the transcript
        return {
            "success": True,
            "transcript": asr_result.transcript,
            "transcript_confidence": asr_result.confidence,
            "language": language,
        }
    
    async def generate_voice_response(
        self,
        text: str,
        language: str = "hi",
        gender: str = "female",
    ) -> Optional[bytes]:
        """
        Generate voice response for text.
        
        Args:
            text: Response text
            language: Language code
            gender: Voice gender
        
        Returns:
            Audio bytes or None if synthesis fails
        """
        result = await self.synthesize(text, language, gender)
        return result.audio_data if result.success else None
    
    def _get_cache_key(
        self,
        text: str,
        language: str,
        gender: str,
        speed: float,
    ) -> str:
        """Generate cache key for TTS."""
        content = f"{text}|{language}|{gender}|{speed}"
        return hashlib.md5(content.encode()).hexdigest()
    
    def clear_cache(self) -> None:
        """Clear TTS cache."""
        self._cache.clear()
    
    @staticmethod
    def get_supported_languages() -> List[Dict[str, str]]:
        """Get list of supported languages."""
        return [
            {"code": "hi", "name": "Hindi", "native": "हिंदी"},
            {"code": "en", "name": "English", "native": "English"},
            {"code": "bn", "name": "Bengali", "native": "বাংলা"},
            {"code": "te", "name": "Telugu", "native": "తెలుగు"},
            {"code": "mr", "name": "Marathi", "native": "मराठी"},
            {"code": "ta", "name": "Tamil", "native": "தமிழ்"},
            {"code": "gu", "name": "Gujarati", "native": "ગુજરાતી"},
            {"code": "kn", "name": "Kannada", "native": "ಕನ್ನಡ"},
            {"code": "ml", "name": "Malayalam", "native": "മലയാളം"},
            {"code": "pa", "name": "Punjabi", "native": "ਪੰਜਾਬੀ"},
            {"code": "or", "name": "Odia", "native": "ଓଡ଼ିଆ"},
            {"code": "as", "name": "Assamese", "native": "অসমীয়া"},
            {"code": "ur", "name": "Urdu", "native": "اردو"},
        ]


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

async def transcribe_audio_file(
    file_path: Path,
    language: str = "hi",
) -> ASRResult:
    """
    Convenience function to transcribe an audio file.
    
    Args:
        file_path: Path to audio file
        language: Language code
    
    Returns:
        ASRResult with transcript
    """
    with open(file_path, "rb") as f:
        audio_data = f.read()
    
    # Detect format from extension
    audio_format = file_path.suffix.lstrip(".").lower()
    if audio_format not in ["wav", "mp3", "flac", "ogg", "webm"]:
        audio_format = "wav"
    
    service = VoiceService()
    return await service.transcribe(audio_data, language, audio_format)


async def synthesize_to_file(
    text: str,
    output_path: Path,
    language: str = "hi",
    gender: str = "female",
) -> bool:
    """
    Convenience function to synthesize text and save to file.
    
    Args:
        text: Text to synthesize
        output_path: Path to save audio file
        language: Language code
        gender: Voice gender
    
    Returns:
        True if successful
    """
    service = VoiceService()
    result = await service.synthesize(text, language, gender)
    
    if result.success and result.audio_data:
        with open(output_path, "wb") as f:
            f.write(result.audio_data)
        return True
    
    return False
