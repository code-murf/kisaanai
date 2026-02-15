"""
Groq AI Service for AI-powered features.
Provides crop disease diagnosis assistance, voice query processing,
and natural language recommendations.
"""
import aiohttp
import logging
from typing import Optional, List, Dict, Any

from app.config import settings

logger = logging.getLogger(__name__)


class GroqAIService:
    """
    Service for interacting with Groq API for AI-powered features.
    
    Uses a shared aiohttp session with connection pooling for better
    performance under load. This addresses BOTTLENECK-003 from the
    stress test analysis.
    """
    
    # Class-level shared session for connection pooling
    _shared_session: Optional[aiohttp.ClientSession] = None
    _connector: Optional[aiohttp.TCPConnector] = None
    
    def __init__(self):
        self.api_key = settings.GROQ_API_KEY
        self.sarvam_api_key = settings.SARVAM_API_KEY
        
        self.model = settings.GROQ_MODEL
        self.base_url = "https://api.groq.com/openai/v1/chat/completions"
        self._session: Optional[aiohttp.ClientSession] = None
    
    @classmethod
    async def get_shared_session(cls) -> aiohttp.ClientSession:
        """
        Get or create a shared aiohttp session with connection pooling.
        
        This method provides a class-level shared session that maintains
        a connection pool for all HTTP requests, significantly improving
        performance for concurrent requests.
        
        Returns:
            aiohttp.ClientSession: A shared session with connection pooling
        """
        if cls._shared_session is None or cls._shared_session.closed:
            # Configure connection pool for optimal performance
            cls._connector = aiohttp.TCPConnector(
                limit=100,  # Total connection pool size
                limit_per_host=20,  # Per-host limit
                ttl_dns_cache=300,  # DNS cache TTL (5 minutes)
                enable_cleanup_closed=True,
                force_close=False,  # Allow connection reuse
            )
            
            # Configure timeouts based on voice API settings
            timeout = aiohttp.ClientTimeout(
                total=30,
                connect=5,
                sock_read=10
            )
            
            cls._shared_session = aiohttp.ClientSession(
                connector=cls._connector,
                timeout=timeout,
                raise_for_status=False  # Handle status codes manually
            )
            
            logger.info(
                "Initialized shared aiohttp session with connection pooling "
                f"(limit=100, per_host=20)"
            )
        
        return cls._shared_session
    
    @classmethod
    async def close_session(cls) -> None:
        """
        Close the shared aiohttp session.
        
        This should be called during application shutdown to properly
        release all connection resources.
        """
        if cls._shared_session is not None and not cls._shared_session.closed:
            await cls._shared_session.close()
            cls._shared_session = None
            cls._connector = None
            logger.info("Closed shared aiohttp session")
    
    @property
    def session(self) -> aiohttp.ClientSession:
        """
        Get or create an instance-level aiohttp session.
        
        Note: For better performance, prefer using get_shared_session()
        for operations that can share a connection pool.
        """
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                }
            )
        return self._session

    async def transcribe_audio(self, audio_content: bytes, language_code: str = "hi-IN", filename: str = "audio.wav", content_type: str = "audio/wav") -> Optional[str]:
        """
        Transcribe audio using Sarvam AI.
        
        Args:
            audio_content: Audio file bytes
            language_code: Language code (e.g., hi-IN)
            filename: Name of the audio file
            content_type: MIME type of the audio file
            
        Returns:
            Transcribed text or None
        """
        url = "https://api.sarvam.ai/speech-to-text"
        
        # Create a new session for Sarvam as it needs different headers (multipart)
        # and we don't want to mess up the Groq session headers
        async with aiohttp.ClientSession() as session:
            headers = {
                "api-subscription-key": self.sarvam_api_key,
            }
            
            # Handle WebM (common from browsers) by treating as OGG/Opus which Sarvam supports
            # content_type 'audio/webm' -> 'audio/ogg' mapping might help if Sarvam checks mime
            if content_type == 'audio/webm' or filename.endswith('.webm'):
                filename = filename.replace('.webm', '.ogg')
                content_type = 'audio/ogg'
            
            data = aiohttp.FormData()
            data.add_field('file', audio_content, filename=filename, content_type=content_type)
            data.add_field('model', 'saarika:v2.5')
            # data.add_field('language_code', language_code) # Optional for v2.5
            
            try:
                async with session.post(url, data=data, headers=headers) as response:
                    # Log the request details for debugging
                    # logger.info(f"Sent audio to Sarvam: {filename} ({content_type}) - {len(audio_content)} bytes")
                    
                    if response.status == 200:
                        res_json = await response.json()
                        return res_json.get("transcript")
                    else:
                        text = await response.text()
                        logger.error(f"Sarvam STT Error: {response.status} - {text}")
                        logger.info("Falling back to Groq Whisper...")
                        return await self.transcribe_audio_groq(audio_content, filename, content_type)
            except Exception as e:
                logger.error(f"Sarvam STT Exception: {e}")
                logger.info("Falling back to Groq Whisper...")
                return await self.transcribe_audio_groq(audio_content, filename, content_type)

    async def transcribe_audio_groq(self, audio_content: bytes, filename: str, content_type: str) -> Optional[str]:
        """
        Transcribe audio using Groq Whisper (Fallback).
        """
        url = "https://api.groq.com/openai/v1/audio/transcriptions"
        headers = {
            "Authorization": f"Bearer {self.api_key}"
        }
        
        # Groq supports: flac, mp3, mp4, mpeg, mpga, m4a, ogg, wav, webm
        # We can send webm directly!
        
        async with aiohttp.ClientSession() as session:
            data = aiohttp.FormData()
            data.add_field('file', audio_content, filename=filename, content_type=content_type)
            data.add_field('model', 'whisper-large-v3')
            data.add_field('response_format', 'json')
            
            try:
                async with session.post(url, data=data, headers=headers) as response:
                    if response.status == 200:
                        res_json = await response.json()
                        return res_json.get("text")
                    else:
                        text = await response.text()
                        logger.error(f"Groq STT Error: {response.status} - {text}")
                        return None
            except Exception as e:
                logger.error(f"Groq STT Exception: {e}")
                return None

    async def text_to_speech(self, text: str, language_code: str = "hi-IN") -> Optional[str]:
        """
        Convert text to speech using Sarvam AI.
        
        Args:
            text: Text to convert
            language_code: Target language code
            
        Returns:
            Base64 encoded audio string or None
        """
        url = "https://api.sarvam.ai/text-to-speech"
        
        payload = {
            "inputs": [text],
            "target_language_code": language_code,
            "speaker": "meera", # Default speaker
            "pitch": 0,
            "pace": 1.0,
            "loudness": 1.5,
            "speech_sample_rate": 16000,
            "enable_preprocessing": True,
            "model": "bulbul:v1"
        }
        
        headers = {
            "api-subscription-key": self.sarvam_api_key,
            "Content-Type": "application/json"
        }
        
        async with aiohttp.ClientSession() as session:
            try:
                async with session.post(url, json=payload, headers=headers) as response:
                    if response.status == 200:
                        res_json = await response.json()
                        audios = res_json.get("audios", [])
                        if audios:
                            return audios[0]
                        return None
                    else:
                        text = await response.text()
                        logger.error(f"Sarvam TTS Error: {response.status} - {text}")
                        return None
            except Exception as e:
                logger.error(f"Sarvam TTS Exception: {e}")
                return None

    
    async def close(self):
        """Close the aiohttp session."""
        if self._session and not self._session.closed:
            await self._session.close()
    
    def is_configured(self) -> bool:
        """Check if Groq API is properly configured."""
        return bool(self.api_key)
    
    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 1024,
        system_prompt: Optional[str] = None,
    ) -> Optional[str]:
        """
        Send a chat completion request to Groq API.
        
        Args:
            messages: List of message dictionaries with 'role' and 'content'
            temperature: Sampling temperature (0.0 to 2.0)
            max_tokens: Maximum tokens in response
            system_prompt: Optional system prompt to prepend
        
        Returns:
            The assistant's response content or None if failed
        """
        if not self.is_configured():
            logger.warning("Groq API key not configured")
            return None
        
        # Prepare messages
        formatted_messages = []
        if system_prompt:
            formatted_messages.append({
                "role": "system",
                "content": system_prompt
            })
        formatted_messages.extend(messages)
        
        payload = {
            "model": self.model,
            "messages": formatted_messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        
        try:
            async with self.session.post(self.base_url, json=payload) as response:
                if response.status == 200:
                    data = await response.json()
                    return data["choices"][0]["message"]["content"]
                else:
                    error_text = await response.text()
                    logger.error(f"Groq API error: {response.status} - {error_text}")
                    return None
        except aiohttp.ClientError as e:
            logger.error(f"Groq API request failed: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error in Groq API call: {e}")
            return None
    
    async def diagnose_crop_disease(
        self,
        crop_name: str,
        symptoms: List[str],
        location: Optional[str] = None,
        language: str = "en",
    ) -> Dict[str, Any]:
        """
        Assist in crop disease diagnosis based on symptoms.
        
        Args:
            crop_name: Name of the crop
            symptoms: List of observed symptoms
            location: Optional location for regional context
            language: Response language (en, hi, etc.)
        
        Returns:
            Dictionary with diagnosis information and recommendations
        """
        system_prompt = """You are an expert agricultural scientist specializing in crop disease diagnosis.
Provide clear, actionable advice for farmers. Include:
1. Likely disease/condition based on symptoms
2. Severity assessment (low/medium/high)
3. Treatment recommendations (organic and chemical options)
4. Prevention measures
5. When to consult a local expert

Always be helpful and practical. If unsure, recommend consulting a local agricultural expert."""

        symptoms_text = ", ".join(symptoms)
        location_context = f" in {location}" if location else ""
        
        user_message = f"""Please help diagnose my {crop_name} crop{location_context}.

Symptoms observed:
{symptoms_text}

Please provide diagnosis and treatment recommendations."""

        response = await self.chat_completion(
            messages=[{"role": "user", "content": user_message}],
            temperature=0.5,
            max_tokens=1500,
            system_prompt=system_prompt,
        )
        
        return {
            "crop": crop_name,
            "symptoms": symptoms,
            "location": location,
            "diagnosis": response,
            "language": language,
            "success": response is not None,
        }
    
    async def process_voice_query(
        self,
        transcribed_text: str,
        context: Optional[Dict[str, Any]] = None,
        language: str = "en",
    ) -> Dict[str, Any]:
        """
        Process a voice query and generate a natural language response.
        
        Args:
            transcribed_text: The transcribed voice input
            context: Optional context (location, user preferences, etc.)
            language: Response language
        
        Returns:
            Dictionary with response and metadata
        """
        system_prompt = """You are a helpful agricultural assistant for Indian farmers.
Respond in a conversational, easy-to-understand manner.
Keep responses concise but informative.
If the question is about:
- Prices: Mention checking local mandi rates
- Weather: Suggest checking weather forecasts
- Diseases: Provide initial guidance but recommend expert consultation for serious issues
- Government schemes: Provide general information but suggest visiting official sources

Always be respectful and helpful. Use simple language that farmers can understand."""

        context_str = ""
        if context:
            context_parts = []
            if "location" in context:
                context_parts.append(f"Location: {context['location']}")
            if "crops" in context:
                context_parts.append(f"Grown crops: {', '.join(context['crops'])}")
            if context_parts:
                context_str = f"\n\nContext: {'; '.join(context_parts)}"

        user_message = f"{transcribed_text}{context_str}"

        response = await self.chat_completion(
            messages=[{"role": "user", "content": user_message}],
            temperature=0.7,
            max_tokens=500,
            system_prompt=system_prompt,
        )
        
        return {
            "query": transcribed_text,
            "response": response,
            "context": context,
            "language": language,
            "success": response is not None,
        }
    
    async def get_farming_recommendations(
        self,
        crop: str,
        growth_stage: Optional[str] = None,
        location: Optional[str] = None,
        season: Optional[str] = None,
        soil_type: Optional[str] = None,
        language: str = "en",
    ) -> Dict[str, Any]:
        """
        Generate personalized farming recommendations.
        
        Args:
            crop: The crop name
            growth_stage: Current growth stage of the crop
            location: Farm location
            season: Current season
            soil_type: Type of soil
            language: Response language
        
        Returns:
            Dictionary with recommendations
        """
        system_prompt = """You are an expert agricultural advisor for Indian farmers.
Provide practical, actionable farming recommendations including:
1. Water management advice
2. Fertilizer recommendations
3. Pest control measures
4. Harvest timing tips
5. Market timing advice

Be specific and practical. Consider sustainable farming practices.
Keep responses organized and easy to follow."""

        context_parts = [f"Crop: {crop}"]
        if growth_stage:
            context_parts.append(f"Growth stage: {growth_stage}")
        if location:
            context_parts.append(f"Location: {location}")
        if season:
            context_parts.append(f"Season: {season}")
        if soil_type:
            context_parts.append(f"Soil type: {soil_type}")

        user_message = f"""Please provide farming recommendations for:
{chr(10).join(context_parts)}

Include specific advice for current farming operations."""

        response = await self.chat_completion(
            messages=[{"role": "user", "content": user_message}],
            temperature=0.6,
            max_tokens=1200,
            system_prompt=system_prompt,
        )
        
        return {
            "crop": crop,
            "growth_stage": growth_stage,
            "location": location,
            "season": season,
            "soil_type": soil_type,
            "recommendations": response,
            "language": language,
            "success": response is not None,
        }
    
    async def translate_text(
        self,
        text: str,
        source_language: str,
        target_language: str,
    ) -> Dict[str, Any]:
        """
        Translate text between languages.
        
        Args:
            text: Text to translate
            source_language: Source language code
            target_language: Target language code
        
        Returns:
            Dictionary with translation result
        """
        system_prompt = f"""You are a professional translator.
Translate the given text from {source_language} to {target_language}.
Maintain the tone and meaning of the original text.
Only provide the translation, no explanations."""

        response = await self.chat_completion(
            messages=[{"role": "user", "content": f"Translate: {text}"}],
            temperature=0.3,
            max_tokens=500,
            system_prompt=system_prompt,
        )
        
        return {
            "original_text": text,
            "source_language": source_language,
            "target_language": target_language,
            "translated_text": response,
            "success": response is not None,
        }


# Singleton instance
_ai_service: Optional[GroqAIService] = None


def get_ai_service() -> GroqAIService:
    """Get or create the AI service singleton."""
    global _ai_service
    if _ai_service is None:
        _ai_service = GroqAIService()
    return _ai_service
