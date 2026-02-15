"""
WhatsApp Bot Service with Twilio integration.

This module provides WhatsApp messaging capabilities for the agricultural
platform, enabling farmers to interact via WhatsApp for:
- Price queries and alerts
- Mandi recommendations
- Voice message processing
- Subscription management
"""
import asyncio
import base64
import hashlib
import hmac
import json
import logging
import re
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional, List, Dict, Any, Callable, Awaitable

from twilio.rest import Client
from twilio.twiml.messaging_response import MessagingResponse
from twilio.base.exceptions import TwilioRestException

from app.config import settings


logger = logging.getLogger(__name__)


# ============================================================================
# ENUMS AND MODELS
# ============================================================================

class MessageType(str, Enum):
    """Types of WhatsApp messages."""
    TEXT = "text"
    IMAGE = "image"
    AUDIO = "audio"
    VIDEO = "video"
    DOCUMENT = "document"
    LOCATION = "location"
    INTERACTIVE = "interactive"


class MessageStatus(str, Enum):
    """WhatsApp message status."""
    QUEUED = "queued"
    SENT = "sent"
    DELIVERED = "delivered"
    READ = "read"
    FAILED = "failed"
    UNDELIVERED = "undelivered"


class IntentType(str, Enum):
    """Recognized user intents."""
    PRICE_QUERY = "price_query"
    MANDI_RECOMMEND = "mandi_recommend"
    FORECAST_QUERY = "forecast_query"
    SUBSCRIBE = "subscribe"
    UNSUBSCRIBE = "unsubscribe"
    HELP = "help"
    LANGUAGE_CHANGE = "language_change"
    UNKNOWN = "unknown"


@dataclass
class WhatsAppMessage:
    """Incoming WhatsApp message."""
    message_id: str
    from_number: str
    to_number: str
    message_type: MessageType
    body: Optional[str] = None
    media_url: Optional[str] = None
    media_content_type: Optional[str] = None
    location: Optional[Dict[str, float]] = None
    timestamp: Optional[datetime] = None
    
    @classmethod
    def from_twilio_webhook(cls, data: Dict[str, Any]) -> "WhatsAppMessage":
        """Create message from Twilio webhook data."""
        message_type = MessageType.TEXT
        body = data.get("Body", "")
        media_url = None
        media_content_type = None
        location = None
        
        # Check for media
        num_media = int(data.get("NumMedia", 0))
        if num_media > 0:
            media_content_type = data.get("MediaContentType0", "")
            media_url = data.get("MediaUrl0", "")
            
            if "audio" in media_content_type:
                message_type = MessageType.AUDIO
            elif "image" in media_content_type:
                message_type = MessageType.IMAGE
            elif "video" in media_content_type:
                message_type = MessageType.VIDEO
        
        # Check for location
        if "Latitude" in data and "Longitude" in data:
            location = {
                "latitude": float(data["Latitude"]),
                "longitude": float(data["Longitude"]),
            }
            message_type = MessageType.LOCATION
        
        return cls(
            message_id=data.get("MessageSid", ""),
            from_number=data.get("From", ""),
            to_number=data.get("To", ""),
            message_type=message_type,
            body=body,
            media_url=media_url,
            media_content_type=media_content_type,
            location=location,
            timestamp=datetime.utcnow(),
        )


@dataclass
class ParsedIntent:
    """Parsed user intent from message."""
    intent: IntentType
    entities: Dict[str, Any] = field(default_factory=dict)
    confidence: float = 0.0
    original_message: str = ""


@dataclass
class BotResponse:
    """Response from the bot."""
    text: str
    media_url: Optional[str] = None
    media_caption: Optional[str] = None
    buttons: Optional[List[Dict[str, str]]] = None
    language: str = "hi"


# ============================================================================
# INTENT PARSER
# ============================================================================

class IntentParser:
    """
    Parse user messages to extract intents and entities.
    
    Uses pattern matching and keyword extraction for intent detection.
    Can be extended with NLU models for better accuracy.
    """
    
    # Intent patterns for different languages
    PATTERNS = {
        IntentType.PRICE_QUERY: {
            "hi": [r"भाव", r"दाम", r"कीमत", r"rate", r"price", r"मूल्य"],
            "en": [r"price", r"rate", r"cost", r"how much", r"what.*price"],
        },
        IntentType.MANDI_RECOMMEND: {
            "hi": [r"मंडी", r"बाजार", r"बेचने", r"कहाँ बेचू", r"best mandi", r"nearest"],
            "en": [r"mandi", r"market", r"sell", r"where.*sell", r"best.*market"],
        },
        IntentType.FORECAST_QUERY: {
            "hi": [r"भविष्य", r"आने वाला", r"prediction", r"forecast", r"उम्मीद"],
            "en": [r"forecast", r"predict", r"future", r"will.*price", r"expected"],
        },
        IntentType.SUBSCRIBE: {
            "hi": [r"सब्सक्राइब", r"अलर्ट", r"सूचना", r"subscribe", r"updates"],
            "en": [r"subscribe", r"alert", r"notify", r"updates", r"notification"],
        },
        IntentType.UNSUBSCRIBE: {
            "hi": [r"अनसब्सक्राइब", r"बंद", r"हटाना", r"unsubscribe", r"stop"],
            "en": [r"unsubscribe", r"stop", r"remove", r"cancel"],
        },
        IntentType.HELP: {
            "hi": [r"मदद", r"सहायता", r"help", r"कैसे", r"क्या करे"],
            "en": [r"help", r"how to", r"guide", r"assist"],
        },
        IntentType.LANGUAGE_CHANGE: {
            "hi": [r"भाषा", r"language", r"english", r"हिंदी"],
            "en": [r"language", r"hindi", r"english", r"change language"],
        },
    }
    
    # Commodity keywords
    COMMODITY_KEYWORDS = {
        "hi": {
            "प्याज": "onion",
            "आलू": "potato",
            "टमाटर": "tomato",
            "गेहूं": "wheat",
            "धान": "paddy",
            "चावल": "rice",
            "मक्का": "maize",
            "बाजरा": "bajra",
            "चना": "gram",
            "मसूर": "lentil",
            "हल्दी": "turmeric",
            "मिर्च": "chilli",
            "लहसुन": "garlic",
            "अदरक": "ginger",
            "सरसों": "mustard",
            "सोयाबीन": "soyabean",
            "मूंगफली": "groundnut",
            "गन्ना": "sugarcane",
            "कपास": "cotton",
        },
        "en": {
            "onion": "onion",
            "potato": "potato",
            "tomato": "tomato",
            "wheat": "wheat",
            "paddy": "paddy",
            "rice": "rice",
            "maize": "maize",
            "bajra": "bajra",
            "gram": "gram",
            "lentil": "lentil",
            "turmeric": "turmeric",
            "chilli": "chilli",
            "garlic": "garlic",
            "ginger": "ginger",
            "mustard": "mustard",
            "soyabean": "soyabean",
            "groundnut": "groundnut",
            "sugarcane": "sugarcane",
            "cotton": "cotton",
        }
    }
    
    def __init__(self, default_language: str = "hi"):
        """Initialize intent parser."""
        self.default_language = default_language
    
    def parse(self, message: str, language: Optional[str] = None) -> ParsedIntent:
        """
        Parse message to extract intent and entities.
        
        Args:
            message: User message text
            language: Message language code
        
        Returns:
            ParsedIntent with detected intent and entities
        """
        language = language or self.default_language
        message_lower = message.lower()
        
        # Detect intent
        best_intent = IntentType.UNKNOWN
        best_confidence = 0.0
        
        for intent_type, patterns_by_lang in self.PATTERNS.items():
            patterns = patterns_by_lang.get(language, patterns_by_lang.get("en", []))
            for pattern in patterns:
                if re.search(pattern, message_lower):
                    confidence = 0.8 if language in patterns_by_lang else 0.6
                    if confidence > best_confidence:
                        best_intent = intent_type
                        best_confidence = confidence
        
        # Extract entities
        entities = {}
        
        # Extract commodity
        commodity_keywords = self.COMMODITY_KEYWORDS.get(language, {})
        for keyword, commodity in commodity_keywords.items():
            if keyword in message_lower:
                entities["commodity"] = commodity
                break
        
        # Extract state/city names (basic extraction)
        entities["location"] = self._extract_location(message)
        
        # Extract numbers (could be quantities or prices)
        numbers = re.findall(r'\d+(?:\.\d+)?', message)
        if numbers:
            entities["numbers"] = [float(n) for n in numbers]
        
        return ParsedIntent(
            intent=best_intent,
            entities=entities,
            confidence=best_confidence,
            original_message=message,
        )
    
    def _extract_location(self, message: str) -> Optional[str]:
        """Extract location from message."""
        # Common Indian states and cities
        locations = [
            "maharashtra", "karnataka", "tamil nadu", "gujarat", "rajasthan",
            "madhya pradesh", "uttar pradesh", "punjab", "haryana",
            "delhi", "mumbai", "bangalore", "chennai", "hyderabad",
            "महाराष्ट्र", "कर्नाटक", "तमिलनाडु", "गुजरात", "राजस्थान",
            "मध्य प्रदेश", "उत्तर प्रदेश", "पंजाब", "हरियाणा",
            "दिल्ली", "मुंबई", "बैंगलोर", "चेन्नई", "हैदराबाद",
        ]
        message_lower = message.lower()
        for location in locations:
            if location in message_lower:
                return location
        return None


# ============================================================================
# WHATSAPP CLIENT
# ============================================================================

class WhatsAppClient:
    """
    Twilio WhatsApp API client.
    
    Handles sending and receiving WhatsApp messages via Twilio.
    """
    
    def __init__(
        self,
        account_sid: Optional[str] = None,
        auth_token: Optional[str] = None,
        phone_number: Optional[str] = None,
    ):
        """
        Initialize WhatsApp client.
        
        Args:
            account_sid: Twilio account SID
            auth_token: Twilio auth token
            phone_number: WhatsApp phone number
        """
        self.account_sid = account_sid or settings.TWILIO_ACCOUNT_SID
        self.auth_token = auth_token or settings.TWILIO_AUTH_TOKEN
        self.phone_number = phone_number or settings.TWILIO_PHONE_NUMBER
        
        self._client: Optional[Client] = None
    
    @property
    def client(self) -> Client:
        """Get or create Twilio client."""
        if self._client is None:
            self._client = Client(self.account_sid, self.auth_token)
        return self._client
    
    async def send_message(
        self,
        to: str,
        body: str,
        media_url: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Send a WhatsApp message.
        
        Args:
            to: Recipient phone number (whatsapp:+1234567890)
            body: Message body
            media_url: Optional list of media URLs
        
        Returns:
            Message details
        """
        try:
            # Ensure WhatsApp prefix
            if not to.startswith("whatsapp:"):
                to = f"whatsapp:{to}"
            
            # Build message parameters
            params = {
                "from_": f"whatsapp:{self.phone_number}",
                "to": to,
                "body": body,
            }
            
            if media_url:
                params["media_url"] = media_url
            
            # Send message (run in executor for async)
            loop = asyncio.get_event_loop()
            message = await loop.run_in_executor(
                None,
                lambda: self.client.messages.create(**params)
            )
            
            return {
                "success": True,
                "message_sid": message.sid,
                "status": message.status,
                "to": message.to,
                "from": message.from_,
            }
            
        except TwilioRestException as e:
            logger.error(f"Twilio error: {e}")
            return {
                "success": False,
                "error": str(e),
                "code": e.code,
            }
        except Exception as e:
            logger.error(f"Error sending message: {e}")
            return {
                "success": False,
                "error": str(e),
            }
    
    async def send_template_message(
        self,
        to: str,
        template_name: str,
        language: str = "en",
        components: Optional[List[Dict]] = None,
    ) -> Dict[str, Any]:
        """
        Send a WhatsApp template message.
        
        Args:
            to: Recipient phone number
            template_name: Template name
            language: Language code
            components: Template components
        
        Returns:
            Message details
        """
        try:
            if not to.startswith("whatsapp:"):
                to = f"whatsapp:{to}"
            
            # Build content for template
            content = {
                "type": "template",
                "template": {
                    "name": template_name,
                    "language": {"code": language},
                }
            }
            
            if components:
                content["template"]["components"] = components
            
            loop = asyncio.get_event_loop()
            message = await loop.run_in_executor(
                None,
                lambda: self.client.messages.create(
                    from_=f"whatsapp:{self.phone_number}",
                    to=to,
                    content_sid=template_name,
                    content_variables=json.dumps(components) if components else None,
                )
            )
            
            return {
                "success": True,
                "message_sid": message.sid,
                "status": message.status,
            }
            
        except Exception as e:
            logger.error(f"Error sending template: {e}")
            return {
                "success": False,
                "error": str(e),
            }
    
    async def download_media(self, media_url: str) -> Optional[bytes]:
        """
        Download media from Twilio.
        
        Args:
            media_url: Twilio media URL
        
        Returns:
            Media bytes or None
        """
        import aiohttp
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    media_url,
                    auth=aiohttp.BasicAuth(self.account_sid, self.auth_token),
                ) as response:
                    if response.status == 200:
                        return await response.read()
                    return None
        except Exception as e:
            logger.error(f"Error downloading media: {e}")
            return None
    
    def verify_webhook_signature(
        self,
        url: str,
        params: Dict[str, Any],
        signature: str,
    ) -> bool:
        """
        Verify Twilio webhook signature.
        
        Args:
            url: Webhook URL
            params: Request parameters
            signature: X-Twilio-Signature header
        
        Returns:
            True if signature is valid
        """
        try:
            # Sort and concatenate parameters
            sorted_params = sorted(params.items())
            data = url + "".join(f"{k}{v}" for k, v in sorted_params)
            
            # Calculate HMAC
            computed = hmac.new(
                self.auth_token.encode(),
                data.encode(),
                hashlib.sha1,
            ).digest()
            
            computed_signature = base64.b64encode(computed).decode()
            
            return hmac.compare(computed_signature, signature)
            
        except Exception as e:
            logger.error(f"Error verifying signature: {e}")
            return False
    
    def create_twiml_response(self, message: str) -> str:
        """
        Create TwiML response for webhook.
        
        Args:
            message: Response message
        
        Returns:
            TwiML XML string
        """
        response = MessagingResponse()
        response.message(message)
        return str(response)


# ============================================================================
# WHATSAPP BOT SERVICE
# ============================================================================

class WhatsAppBotService:
    """
    High-level WhatsApp bot service.
    
    Handles incoming messages, processes intents, and generates responses.
    """
    
    def __init__(
        self,
        client: Optional[WhatsAppClient] = None,
        intent_parser: Optional[IntentParser] = None,
        voice_service: Optional[Any] = None,
    ):
        """
        Initialize bot service.
        
        Args:
            client: WhatsApp client
            intent_parser: Intent parser
            voice_service: Voice service for audio processing
        """
        self.client = client or WhatsAppClient()
        self.intent_parser = intent_parser or IntentParser()
        self.voice_service = voice_service
        
        # User session storage (in production, use Redis)
        self._sessions: Dict[str, Dict[str, Any]] = {}
        
        # Response templates
        self._templates = self._load_templates()
    
    def _load_templates(self) -> Dict[str, Dict[str, str]]:
        """Load response templates."""
        return {
            "welcome": {
                "hi": "🌾 कृषि मित्र में आपका स्वागत है!\n\n"
                      "मैं आपकी मदद कर सकता हूं:\n"
                      "• भाव जानने के लिए: 'प्याज का भाव'\n"
                      "• मंडी खोजने के लिए: 'टमाटर कहाँ बेचू'\n"
                      "• भविष्य के भाव: 'आलू का forecast'\n\n"
                      "भाषा बदलने के लिए 'language' लिखें",
                "en": "🌾 Welcome to Krishi Mitra!\n\n"
                      "I can help you with:\n"
                      "• Price queries: 'onion price'\n"
                      "• Find mandis: 'where to sell tomato'\n"
                      "• Price forecast: 'potato forecast'\n\n"
                      "Type 'help' for more options",
            },
            "help": {
                "hi": "📝 उपलब्ध सेवाएं:\n\n"
                      "1. भाव पूछें: 'प्याज का भाव महाराष्ट्र में'\n"
                      "2. मंडी खोजें: 'टमाटर के लिए नजदीकी मंडी'\n"
                      "3. भविष्य के भाव: 'गेहूं का forecast'\n"
                      "4. अलर्ट सेट करें: 'subscribe प्याज'\n"
                      "5. अलर्ट हटाएं: 'unsubscribe'\n\n"
                      "अपना स्थान भेजने के लिए 📍 बटन दबाएं",
                "en": "📝 Available Services:\n\n"
                      "1. Price query: 'onion price in Maharashtra'\n"
                      "2. Find mandi: 'nearest mandi for tomato'\n"
                      "3. Price forecast: 'wheat forecast'\n"
                      "4. Set alerts: 'subscribe onion'\n"
                      "5. Remove alerts: 'unsubscribe'\n\n"
                      "Send your location using the 📍 button",
            },
            "unknown": {
                "hi": "माफ कीजिये, मैं समझ नहीं पाया।\n\n"
                      "कृपया 'help' लिखें या इस तरह पूछें:\n"
                      "• 'प्याज का भाव'\n• 'टमाटर कहाँ बेचू'",
                "en": "Sorry, I didn't understand that.\n\n"
                      "Please type 'help' or try:\n"
                      "• 'onion price'\n• 'where to sell tomato'",
            },
            "subscribe_success": {
                "hi": "✅ आपकी सदस्यता सफल!\n\n"
                      "आपको {commodity} के भाव अलर्ट मिलेंगे।",
                "en": "✅ Subscription successful!\n\n"
                      "You will receive price alerts for {commodity}.",
            },
            "unsubscribe_success": {
                "hi": "✅ आपकी सदस्यता रद्द कर दी गई है।",
                "en": "✅ Your subscription has been cancelled.",
            },
        }
    
    async def process_message(self, message: WhatsAppMessage) -> BotResponse:
        """
        Process incoming message and generate response.
        
        Args:
            message: Incoming WhatsApp message
        
        Returns:
            BotResponse with reply content
        """
        # Get or create user session
        session = self._get_session(message.from_number)
        language = session.get("language", "hi")
        
        # Handle different message types
        if message.message_type == MessageType.LOCATION:
            return await self._handle_location(message, session)
        
        if message.message_type == MessageType.AUDIO:
            return await self._handle_audio(message, session, language)
        
        if message.message_type != MessageType.TEXT or not message.body:
            return self._create_response("unknown", language)
        
        # Parse intent
        intent = self.intent_parser.parse(message.body, language)
        
        # Handle intents
        if intent.intent == IntentType.HELP:
            return self._create_response("help", language)
        
        if intent.intent == IntentType.LANGUAGE_CHANGE:
            return await self._handle_language_change(message.body, session)
        
        if intent.intent == IntentType.PRICE_QUERY:
            return await self._handle_price_query(intent, session, language)
        
        if intent.intent == IntentType.MANDI_RECOMMEND:
            return await self._handle_mandi_recommend(intent, session, language)
        
        if intent.intent == IntentType.FORECAST_QUERY:
            return await self._handle_forecast(intent, session, language)
        
        if intent.intent == IntentType.SUBSCRIBE:
            return await self._handle_subscribe(intent, session, language)
        
        if intent.intent == IntentType.UNSUBSCRIBE:
            return await self._handle_unsubscribe(intent, session, language)
        
        # Check if new user
        if not session.get("welcomed"):
            session["welcomed"] = True
            self._save_session(message.from_number, session)
            return self._create_response("welcome", language)
        
        return self._create_response("unknown", language)
    
    async def _handle_price_query(
        self,
        intent: ParsedIntent,
        session: Dict[str, Any],
        language: str,
    ) -> BotResponse:
        """Handle price query intent."""
        commodity = intent.entities.get("commodity")
        location = intent.entities.get("location")
        
        if not commodity:
            text = (
                "कृपया फसल का नाम बताएं। उदाहरण: 'प्याज का भाव'"
                if language == "hi" else
                "Please specify a crop. Example: 'onion price'"
            )
            return BotResponse(text=text, language=language)
        
        # In production, fetch actual prices from service
        text = (
            f"📊 {commodity} के भाव:\n\n"
            f"• मंडी 1: ₹ 2,500/क्विंटल\n"
            f"• मंडी 2: ₹ 2,400/क्विंटल\n"
            f"• मंडी 3: ₹ 2,350/क्विंटल\n\n"
            f"अधिक जानकारी के लिए 'mandi {commodity}' लिखें"
            if language == "hi" else
            f"📊 {commodity} prices:\n\n"
            f"• Mandi 1: ₹ 2,500/quintal\n"
            f"• Mandi 2: ₹ 2,400/quintal\n"
            f"• Mandi 3: ₹ 2,350/quintal\n\n"
            f"Type 'mandi {commodity}' for more details"
        )
        
        return BotResponse(text=text, language=language)
    
    async def _handle_mandi_recommend(
        self,
        intent: ParsedIntent,
        session: Dict[str, Any],
        language: str,
    ) -> BotResponse:
        """Handle mandi recommendation intent."""
        commodity = intent.entities.get("commodity")
        user_location = session.get("location")
        
        if not commodity:
            text = (
                "कृपया फसल का नाम बताएं। उदाहरण: 'टमाटर कहाँ बेचू'"
                if language == "hi" else
                "Please specify a crop. Example: 'where to sell tomato'"
            )
            return BotResponse(text=text, language=language)
        
        if not user_location:
            text = (
                "📍 अपना स्थान भेजने के लिए attachment बटन में 📍 का उपयोग करें"
                if language == "hi" else
                "📍 Please share your location using the 📍 button in attachment"
            )
            return BotResponse(text=text, language=language)
        
        # In production, use routing service
        text = (
            f"🏪 {commodity} के लिए सबसे अच्छी मंडियां:\n\n"
            f"1. मंडी A (10 km)\n"
            f"   भाव: ₹ 2,500/क्विंटल\n"
            f"   अनुमानित मुनाफा: ₹ 500\n\n"
            f"2. मंडी B (25 km)\n"
            f"   भाव: ₹ 2,600/क्विंटल\n"
            f"   अनुमानित मुनाफा: ₹ 450\n\n"
            f"विवरण के लिए 1 या 2 लिखें"
            if language == "hi" else
            f"🏪 Best mandis for {commodity}:\n\n"
            f"1. Mandi A (10 km)\n"
            f"   Price: ₹ 2,500/quintal\n"
            f"   Est. profit: ₹ 500\n\n"
            f"2. Mandi B (25 km)\n"
            f"   Price: ₹ 2,600/quintal\n"
            f"   Est. profit: ₹ 450\n\n"
            f"Type 1 or 2 for details"
        )
        
        return BotResponse(text=text, language=language)
    
    async def _handle_forecast(
        self,
        intent: ParsedIntent,
        session: Dict[str, Any],
        language: str,
    ) -> BotResponse:
        """Handle forecast query intent."""
        commodity = intent.entities.get("commodity")
        
        if not commodity:
            text = (
                "कृपया फसल का नाम बताएं। उदाहरण: 'गेहूं का forecast'"
                if language == "hi" else
                "Please specify a crop. Example: 'wheat forecast'"
            )
            return BotResponse(text=text, language=language)
        
        # In production, use forecast service
        text = (
            f"📈 {commodity} मूल्य पूर्वानुमान:\n\n"
            f"• 7 दिन: ₹ 2,550 (+2%)\n"
            f"• 14 दिन: ₹ 2,600 (+4%)\n"
            f"• 30 दिन: ₹ 2,700 (+8%)\n\n"
            f"💡 सुझाव: 14 दिन बाद बेचना फायदेमंद हो सकता है"
            if language == "hi" else
            f"📈 {commodity} price forecast:\n\n"
            f"• 7 days: ₹ 2,550 (+2%)\n"
            f"• 14 days: ₹ 2,600 (+4%)\n"
            f"• 30 days: ₹ 2,700 (+8%)\n\n"
            f"💡 Tip: Selling after 14 days may be profitable"
        )
        
        return BotResponse(text=text, language=language)
    
    async def _handle_subscribe(
        self,
        intent: ParsedIntent,
        session: Dict[str, Any],
        language: str,
    ) -> BotResponse:
        """Handle subscription intent."""
        commodity = intent.entities.get("commodity", "all")
        
        # Add to subscriptions
        subscriptions = session.get("subscriptions", [])
        if commodity not in subscriptions:
            subscriptions.append(commodity)
            session["subscriptions"] = subscriptions
        
        text = self._get_template("subscribe_success", language).format(
            commodity=commodity if commodity != "all" else "सभी फसलें/all crops"
        )
        
        return BotResponse(text=text, language=language)
    
    async def _handle_unsubscribe(
        self,
        intent: ParsedIntent,
        session: Dict[str, Any],
        language: str,
    ) -> BotResponse:
        """Handle unsubscription intent."""
        session["subscriptions"] = []
        
        text = self._get_template("unsubscribe_success", language)
        return BotResponse(text=text, language=language)
    
    async def _handle_location(
        self,
        message: WhatsAppMessage,
        session: Dict[str, Any],
    ) -> BotResponse:
        """Handle location message."""
        if message.location:
            session["location"] = message.location
            language = session.get("language", "hi")
            
            text = (
                "✅ आपका स्थान सेव हो गया!\n\n"
                "अब आप मंडी खोज सकते हैं। उदाहरण: 'टमाटर कहाँ बेचू'"
                if language == "hi" else
                "✅ Location saved!\n\n"
                "Now you can find mandis. Example: 'where to sell tomato'"
            )
            
            return BotResponse(text=text, language=language)
        
        return self._create_response("unknown", session.get("language", "hi"))
    
    async def _handle_audio(
        self,
        message: WhatsAppMessage,
        session: Dict[str, Any],
        language: str,
    ) -> BotResponse:
        """Handle audio message."""
        if not self.voice_service or not message.media_url:
            text = (
                "माफ कीजिये, आवाज संदेश प्रोसेस नहीं हो सका। कृपया टेक्स्ट में लिखें।"
                if language == "hi" else
                "Sorry, voice messages are not available. Please type your query."
            )
            return BotResponse(text=text, language=language)
        
        # Download and process audio
        audio_data = await self.client.download_media(message.media_url)
        if audio_data:
            # Transcribe audio
            result = await self.voice_service.transcribe(audio_data, language)
            
            if result.success:
                # Process transcribed text
                text_msg = WhatsAppMessage(
                    message_id=message.message_id,
                    from_number=message.from_number,
                    to_number=message.to_number,
                    message_type=MessageType.TEXT,
                    body=result.transcript,
                )
                return await self.process_message(text_msg)
        
        return self._create_response("unknown", language)
    
    async def _handle_language_change(
        self,
        body: str,
        session: Dict[str, Any],
    ) -> BotResponse:
        """Handle language change request."""
        body_lower = body.lower()
        
        if "english" in body_lower or "en" in body_lower:
            session["language"] = "en"
            return BotResponse(
                text="✅ Language changed to English",
                language="en",
            )
        elif "hindi" in body_lower or "हिंदी" in body_lower or "hi" in body_lower:
            session["language"] = "hi"
            return BotResponse(
                text="✅ भाषा हिंदी में बदल दी गई",
                language="hi",
            )
        else:
            return BotResponse(
                text="Choose language / भाषा चुनें:\n\n1. English\n2. हिंदी",
                language="en",
            )
    
    def _get_session(self, user_id: str) -> Dict[str, Any]:
        """Get user session."""
        return self._sessions.get(user_id, {})
    
    def _save_session(self, user_id: str, session: Dict[str, Any]) -> None:
        """Save user session."""
        self._sessions[user_id] = session
    
    def _get_template(self, name: str, language: str) -> str:
        """Get response template."""
        templates = self._templates.get(name, {})
        return templates.get(language, templates.get("en", ""))
    
    def _create_response(self, template_name: str, language: str) -> BotResponse:
        """Create response from template."""
        return BotResponse(
            text=self._get_template(template_name, language),
            language=language,
        )
    
    async def send_response(
        self,
        to: str,
        response: BotResponse,
    ) -> Dict[str, Any]:
        """
        Send bot response to user.
        
        Args:
            to: Recipient phone number
            response: Bot response
        
        Returns:
            Send result
        """
        return await self.client.send_message(
            to=to,
            body=response.text,
            media_url=[response.media_url] if response.media_url else None,
        )


# ============================================================================
# WEBHOOK HANDLER
# ============================================================================

async def handle_whatsapp_webhook(
    data: Dict[str, Any],
    bot_service: Optional[WhatsAppBotService] = None,
) -> str:
    """
    Handle incoming WhatsApp webhook.
    
    Args:
        data: Webhook data from Twilio
        bot_service: WhatsApp bot service instance
    
    Returns:
        TwiML response
    """
    bot = bot_service or WhatsAppBotService()
    
    # Parse message
    message = WhatsAppMessage.from_twilio_webhook(data)
    
    # Process message
    response = await bot.process_message(message)
    
    # Send response
    await bot.send_response(message.from_number, response)
    
    # Return empty TwiML (we're sending async)
    return ""
