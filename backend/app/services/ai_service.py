"""
AI Service for AI-powered features.
Uses AWS Bedrock (Claude 3) as primary LLM with GROQ as fallback.
Provides crop disease diagnosis assistance, voice query processing,
and natural language recommendations.
"""
import aiohttp
import asyncio
import logging
import re
from typing import Optional, List, Dict, Any
from cachetools import TTLCache

from app.config import settings

logger = logging.getLogger(__name__)

# Global conversational state cache (TTL: 2 hours, max sessions: 1000)
conversational_memory = TTLCache(maxsize=1000, ttl=7200)

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

        # Voice/Chat uses GROQ only (fastest for text generation)
        # Bedrock Claude is reserved for Crop Doctor vision analysis
        self._bedrock = None
    
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
        urls = [
            "https://api.sarvam.ai/speech-to-text",          # Primary endpoint
            "https://api.sarvam.ai/speech-to-text/process",  # Fallback for API variations
        ]

        async with aiohttp.ClientSession() as session:
            headers = {"api-subscription-key": self.sarvam_api_key}

            if content_type == "audio/webm" or filename.endswith(".webm"):
                filename = filename.replace(".webm", ".ogg")
                content_type = "audio/ogg"

            for url in urls:
                data = aiohttp.FormData()
                data.add_field("file", audio_content, filename=filename, content_type=content_type)
                data.add_field("model", "saarika:v2.5")
                data.add_field("language_code", self._normalize_sarvam_language(language_code))

                try:
                    async with session.post(url, data=data, headers=headers) as response:
                        if response.status == 200:
                            res_json = await response.json()
                            transcript = (
                                res_json.get("transcript")
                                or res_json.get("text")
                                or res_json.get("result")
                            )
                            if transcript:
                                return transcript
                            logger.error(f"Sarvam STT Empty transcript from {url}: {res_json}")
                        else:
                            text = await response.text()
                            logger.error(f"Sarvam STT Error ({url}): {response.status} - {text}")
                except Exception as e:
                    logger.error(f"Sarvam STT Exception ({url}): {e}")

        logger.info("Falling back to Groq Whisper...")
        return await self.transcribe_audio_groq(audio_content, filename, content_type, language_code=language_code)

    async def transcribe_audio_groq(
        self,
        audio_content: bytes,
        filename: str,
        content_type: str,
        language_code: str = "hi-IN",
    ) -> Optional[str]:
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
            data.add_field("file", audio_content, filename=filename, content_type=content_type)
            data.add_field("model", "whisper-large-v3-turbo")
            data.add_field("response_format", "json")
            data.add_field("language", self._normalize_groq_language(language_code))
            
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
        Convert text to speech using Amazon Polly (primary) with Sarvam AI fallback.
        
        Args:
            text: Text to convert
            language_code: Target language code
            
        Returns:
            Base64 encoded audio string or None
        """
        cleaned_text = self._clean_tts_text(text)
        if not cleaned_text:
            return None

        # --- Primary: Amazon Polly (realtime, free tier) ---
        try:
            from app.services.polly_service import polly_service
            import asyncio

            # Map language code for Polly
            lang = (language_code or "hi-IN").strip()
            polly_lang = "hi" if lang.startswith("hi") else "en"

            # Run Polly (sync boto3) in executor to avoid blocking
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                lambda: polly_service.synthesize(
                    text=cleaned_text,
                    language=polly_lang,
                    output_format="mp3",
                    engine="neural",
                )
            )

            if result.get("success") and result.get("audio_base64"):
                logger.info(f"Polly TTS success: {result.get('duration_ms')}ms, "
                           f"{result.get('chars_used')} chars")
                return result["audio_base64"]
            else:
                logger.warning(f"Polly TTS returned no audio: {result.get('error')}")
        except Exception as e:
            logger.warning(f"Polly TTS failed, falling back to Sarvam: {e}")

        # --- Fallback: Sarvam AI ---
        return await self._text_to_speech_sarvam(cleaned_text, language_code)

    async def _text_to_speech_sarvam(self, cleaned_text: str, language_code: str = "hi-IN") -> Optional[str]:
        """Fallback TTS using Sarvam AI."""
        url = "https://api.sarvam.ai/text-to-speech"

        text_chunks = self._chunk_text(cleaned_text, max_len=450)
        if not text_chunks:
            return None

        payload = {
            "inputs": text_chunks,
            "target_language_code": self._normalize_sarvam_language(language_code),
            "speaker": "anushka",
            "pace": 1.0,
            "speech_sample_rate": 16000,
            "enable_preprocessing": True,
            "model": "bulbul:v2"
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
        Send a chat completion request.
        
        Uses AWS Bedrock Claude as primary, GROQ as fallback.
        
        Args:
            messages: List of message dictionaries with 'role' and 'content'
            temperature: Sampling temperature (0.0 to 2.0)
            max_tokens: Maximum tokens in response
            system_prompt: Optional system prompt to prepend
        
        Returns:
            The assistant's response content or None if failed
        """
        # --- Primary: AWS Bedrock Claude ---
        if self._bedrock:
            try:
                # Bedrock uses Messages API format (no 'system' role in messages)
                bedrock_messages = [
                    m for m in messages if m.get("role") != "system"
                ]
                loop = asyncio.get_event_loop()
                result = await loop.run_in_executor(
                    None,
                    lambda: self._bedrock.chat_completion(
                        messages=bedrock_messages,
                        temperature=temperature,
                        max_tokens=max_tokens,
                        system_prompt=system_prompt,
                    )
                )
                if result:
                    logger.info("Bedrock Claude response OK")
                    return result
                logger.warning("Bedrock returned empty, falling back to GROQ")
            except Exception as e:
                logger.warning(f"Bedrock failed, falling back to GROQ: {e}")

        # --- Fallback: GROQ ---
        if not self.is_configured():
            logger.warning("Neither Bedrock nor GROQ API is configured")
            return None
        
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
        lat: Optional[float] = None,
        lon: Optional[float] = None,
        session_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Process a voice query and generate a natural language response.
        
        Args:
            transcribed_text: The transcribed voice input
            context: Optional context (location, user preferences, etc.)
            language: Response language
            lat: User latitude
            lon: User longitude
        
        Returns:
            Dictionary with response and metadata
        """
        from app.services.weather_service import WeatherService
        from app.services.price_service import PriceService
        from app.database import async_session_maker
        from sqlalchemy import select
        from app.models.commodity import Commodity
        from app.models.mandi import Mandi
        import json

        system_prompt = """You are a helpful agricultural assistant for Indian farmers.
Respond in a conversational, easy-to-understand manner.
Keep responses concise but informative.
Keep your final answer under 120 words and avoid markdown formatting.
CRITICAL: You have access to tools for weather, mandi prices, and web search. The location is automatically injected, so DO NOT ask the user for their location; just invoke the tools.
Always be respectful and helpful. Use simple language that farmers can understand."""

        context_str = ""
        if context:
            context_parts = []
            if "location" in context:
                context_parts.append(f"Location: {context['location']}")
            if "crops" in context:
                context_parts.append(f"Grown crops: {', '.join(context['crops'])}")
            if context_parts:
                context_str = f" Context: {'; '.join(context_parts)}"

        user_message = f"{transcribed_text}{context_str}"

        tools = [
            {
                "type": "function",
                "function": {
                    "name": "get_current_weather",
                    "description": "Get current weather forecast for the user's location",
                    "parameters": {
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_mandi_prices",
                    "description": "Get latest market (mandi) prices for commodities near the user",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "commodity_name": {
                                "type": "string",
                                "description": "Name of the crop/commodity MUST be in English (e.g., 'Potato', 'Cauliflower'). Translate from regional language if necessary."
                            }
                        },
                        "required": ["commodity_name"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "search_web",
                    "description": "Search the internet for general information, news, or farming techniques when internal knowledge is insufficient.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {"type": "string", "description": "The search query to look up on the internet"}
                        },
                        "required": ["query"]
                    }
                }
            }
        ]
        
        # Load conversation history for current session
        chat_history = []
        if session_id and session_id in conversational_memory:
            chat_history = conversational_memory.get(session_id, [])
        
        # Build messages list: System -> History -> New User Query
        messages = [{"role": "system", "content": system_prompt}]
        messages.extend(chat_history)
        messages.append({"role": "user", "content": user_message})
        
        max_iterations = 3
        final_response = None
        
        for _ in range(max_iterations):
            payload = {
                "model": self.model,
                "messages": messages,
                "temperature": 0.7,
                "max_tokens": 250,
                "tools": tools,
                "tool_choice": "auto"
            }
            
            try:
                async with self.session.post(self.base_url, json=payload) as response:
                    if response.status == 200:
                        data = await response.json()
                        message = data["choices"][0]["message"]
                        messages.append(message)
                        
                        if message.get("tool_calls"):
                            for tool_call in message["tool_calls"]:
                                function_name = tool_call["function"]["name"]
                                
                                tool_result = "Tool execution failed."
                                try:
                                    function_args = json.loads(tool_call["function"]["arguments"])
                                except Exception as e:
                                    logger.error(f"JSON parsing error for {function_name}: {e}")
                                    messages.append({
                                        "tool_call_id": tool_call["id"],
                                        "role": "tool",
                                        "name": function_name,
                                        "content": "Failed to parse tool arguments. Ensure valid JSON."
                                    })
                                    continue
                                
                                try:
                                    if function_name == "get_current_weather":
                                        if lat is None or lon is None:
                                            tool_result = "Location (lat/lon) not provided by user device, cannot fetch weather."
                                        else:
                                            weather_service = WeatherService()
                                            forecast = await weather_service.get_forecast(lat, lon, days=1)
                                            if forecast:
                                                today = forecast[0]
                                                tool_result = f"Weather: {today.condition}, Max Temp: {today.temp_max}°C, Min Temp: {today.temp_min}°C, Rain: {today.rainfall_mm}mm. Advisory: {today.advisory}"
                                                
                                    elif function_name == "get_mandi_prices":
                                        commodity_name = function_args.get("commodity_name", "").strip()
                                        if not commodity_name:
                                            tool_result = "Please specify a commodity."
                                        else:
                                            async with async_session_maker() as db:
                                                comm_result = await db.execute(select(Commodity).where(Commodity.name.ilike(f"%{commodity_name}%")).limit(1))
                                                commodity = comm_result.scalar_one_or_none()
                                                
                                                if not commodity:
                                                    tool_result = f"Commodity '{commodity_name}' not found in database. Try standard English names."
                                                else:
                                                    price_service = PriceService(db)
                                                    latest_prices = await price_service.get_current_prices_by_commodity(commodity_id=commodity.id, limit=3)
                                                    if latest_prices:
                                                        prices_info = []
                                                        for p in latest_prices:
                                                            prices_info.append(f"{p.commodity.name} at {p.mandi.name} ({p.mandi.district}): ₹{p.modal_price}/{p.commodity.unit}")
                                                        tool_result = "\n".join(prices_info)
                                                    else:
                                                        tool_result = f"No recent prices found for {commodity.name}."
                                                        
                                    elif function_name == "search_web":
                                        query = function_args.get("query", "")
                                        if not query:
                                            tool_result = "Empty search query."
                                        else:
                                            from duckduckgo_search import DDGS
                                            results = DDGS().text(query, max_results=3)
                                            if results:
                                                tool_result = "\n".join([f"- {r['title']}: {r['body']}" for r in results])
                                            else:
                                                tool_result = "No web search results found."
                                                
                                except Exception as e:
                                    logger.error(f"Error executing tool {function_name}: {e}")
                                    tool_result = f"Error during tool execution: {str(e)}"
                                                
                                messages.append({
                                    "tool_call_id": tool_call["id"],
                                    "role": "tool",
                                    "name": function_name,
                                    "content": tool_result
                                })
                            # Continue loop to send tool results back to LLM
                        else:
                            final_response = message.get("content")
                            break
                    else:
                        error_text = await response.text()
                        logger.error(f"Groq tool call failed: {error_text}")
                        # Fallback: if model failed to do tool calling (e.g. 400 Bad Request for JSON),
                        # just ask the model for a regular completion without tools.
                        payload.pop("tools", None)
                        payload.pop("tool_choice", None)
                        
                        # Strip any tool roles from messages, as fallback doesn't support them if tools aren't provided
                        clean_messages = [m for m in messages if m["role"] not in ["tool", "function", "assistant_tool_call"]]
                        # Further clean assistant messages that have tool_calls
                        for m in clean_messages:
                            if m["role"] == "assistant" and "tool_calls" in m:
                                m.pop("tool_calls", None)
                        payload["messages"] = clean_messages
                        
                        try:
                            async with self.session.post(self.base_url, json=payload) as fallback_response:
                                if fallback_response.status == 200:
                                    fallback_data = await fallback_response.json()
                                    final_response = fallback_data["choices"][0]["message"].get("content")
                                else:
                                    logger.error(f"Fallback Groq call failed: {await fallback_response.text()}")
                        except Exception as e:
                            logger.error(f"Error during fallback request: {e}")
                        break
            except Exception as e:
                logger.error(f"Error in tool calling loop: {e}")
                break
                
        # If max iterations reached without getting a final natural language response
        if final_response is None:
            logger.warning("Max tool iterations reached or final_response is None. Forcing fallback completion.")
            payload = {
                "model": self.model,
                "messages": [{"role": "system", "content": system_prompt}, {"role": "user", "content": user_message}],
                "temperature": 0.7,
                "max_tokens": 250
            }
            try:
                async with self.session.post(self.base_url, json=payload) as response:
                    if response.status == 200:
                        data = await response.json()
                        final_response = data["choices"][0]["message"].get("content")
            except Exception as e:
                logger.error(f"Error in final forced fallback: {e}")

        if final_response is None:
            final_response = "I encountered an error trying to process your request."

        # Save to memory cache
        if session_id and final_response:
            # Append interaction
            chat_history.append({"role": "user", "content": transcribed_text})
            chat_history.append({"role": "assistant", "content": final_response})
            # Keep only the last 10 messages (5 turns) to prevent token context explosion
            if len(chat_history) > 10:
                chat_history = chat_history[-10:]
            conversational_memory[session_id] = chat_history

        return {
            "query": transcribed_text,
            "response": final_response,
            "context": context,
            "language": language,
            "success": final_response is not None and final_response != "I encountered an error trying to process your request.",
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


# Helper methods added to class via monkey-patch for minimal diff surface.
def _normalize_sarvam_language(self: GroqAIService, language_code: str) -> str:
    lang = (language_code or "hi-IN").strip()
    if "-" not in lang:
        if lang.lower() == "en":
            return "en-IN"
        return "hi-IN"
    return lang


def _normalize_groq_language(self: GroqAIService, language_code: str) -> str:
    lang = (language_code or "hi-IN").strip().lower()
    if lang.startswith("en"):
        return "en"
    return "hi"


def _clean_tts_text(self: GroqAIService, text: str) -> str:
    normalized = (text or "").strip()
    # Remove markdown bullets/formatting for better TTS output.
    normalized = re.sub(r"[*_`#>-]", " ", normalized)
    normalized = re.sub(r"\s+", " ", normalized).strip()
    return normalized


def _chunk_text(self: GroqAIService, text: str, max_len: int = 450) -> List[str]:
    if not text:
        return []
    if len(text) <= max_len:
        return [text]

    chunks: List[str] = []
    current = ""
    for sentence in re.split(r"(?<=[.!?])\s+", text):
        if not sentence:
            continue
        candidate = f"{current} {sentence}".strip() if current else sentence
        if len(candidate) <= max_len:
            current = candidate
            continue

        if current:
            chunks.append(current)
            current = ""

        if len(sentence) <= max_len:
            current = sentence
        else:
            # Hard split very long sentence
            start = 0
            while start < len(sentence):
                chunks.append(sentence[start:start + max_len])
                start += max_len
    if current:
        chunks.append(current)
    return chunks


GroqAIService._normalize_sarvam_language = _normalize_sarvam_language  # type: ignore[attr-defined]
GroqAIService._normalize_groq_language = _normalize_groq_language  # type: ignore[attr-defined]
GroqAIService._clean_tts_text = _clean_tts_text  # type: ignore[attr-defined]
GroqAIService._chunk_text = _chunk_text  # type: ignore[attr-defined]
