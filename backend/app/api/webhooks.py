"""
Webhook endpoints for WhatsApp and Voice services.

This module provides API endpoints for:
- Twilio WhatsApp webhook
- Voice processing webhook
- Bhashini callback handling
"""
import logging
from typing import Dict, Any, Optional

from fastapi import APIRouter, Request, Response, HTTPException, Depends, Form
from fastapi.responses import PlainTextResponse, JSONResponse
from pydantic import BaseModel, Field

from app.config import settings
from app.services.whatsapp_service import (
    WhatsAppBotService,
    WhatsAppMessage,
    handle_whatsapp_webhook,
)
from app.services.voice_service import VoiceService


logger = logging.getLogger(__name__)


router = APIRouter(prefix="/webhooks", tags=["webhooks"])


# ============================================================================
# REQUEST/RESPONSE MODELS
# ============================================================================

class VoiceWebhookRequest(BaseModel):
    """Voice webhook request model."""
    call_sid: str = Field(..., description="Twilio call SID")
    from_number: str = Field(..., description="Caller phone number")
    to_number: str = Field(..., description="Called number")
    call_status: str = Field(default="ringing", description="Call status")
    audio_url: Optional[str] = Field(None, description="URL to audio recording")
    speech_result: Optional[str] = Field(None, description="Transcribed speech")
    language: str = Field(default="hi", description="Language code")


class VoiceProcessingRequest(BaseModel):
    """Request for processing voice audio."""
    audio_base64: str = Field(..., description="Base64 encoded audio")
    language: str = Field(default="hi", description="Audio language")
    audio_format: str = Field(default="wav", description="Audio format")


class VoiceProcessingResponse(BaseModel):
    """Response from voice processing."""
    success: bool
    transcript: Optional[str] = None
    confidence: Optional[float] = None
    response_audio_base64: Optional[str] = None
    error: Optional[str] = None


# ============================================================================
# WHATSAPP WEBHOOK
# ============================================================================

@router.post("/whatsapp")
async def whatsapp_webhook(request: Request):
    """
    Handle incoming WhatsApp messages from Twilio.
    
    This endpoint receives webhook requests from Twilio when a user
    sends a message to the WhatsApp business number.
    
    Returns:
        TwiML response or empty string
    """
    try:
        # Parse form data from Twilio
        form_data = await request.form()
        data = dict(form_data)
        
        logger.info(f"Received WhatsApp webhook: {data.get('MessageSid', 'unknown')}")
        
        # Verify webhook signature (optional, for production)
        # signature = request.headers.get("X-Twilio-Signature", "")
        # if not verify_signature(str(request.url), data, signature):
        #     raise HTTPException(status_code=401, detail="Invalid signature")
        
        # Process message
        bot_service = WhatsAppBotService()
        result = await handle_whatsapp_webhook(data, bot_service)
        
        # Return empty TwiML (we send async response)
        return PlainTextResponse(content=result, media_type="application/xml")
        
    except Exception as e:
        logger.error(f"Error processing WhatsApp webhook: {e}")
        return PlainTextResponse(
            content="<Response></Response>",
            media_type="application/xml",
            status_code=200,  # Always return 200 to Twilio
        )


@router.get("/whatsapp")
async def whatsapp_webhook_verify(hub_mode: str = None, hub_challenge: str = None):
    """
    Verify WhatsApp webhook endpoint.
    
    Meta/Facebook requires webhook verification for WhatsApp Business API.
    """
    # For Twilio, verification is not needed
    # For Meta WhatsApp API, verify hub.challenge
    if hub_mode == "subscribe" and hub_challenge:
        verify_token = settings.TWILIO_AUTH_TOKEN  # Or a dedicated verify token
        # In production, verify hub.verify_token matches your token
        return PlainTextResponse(content=hub_challenge)
    
    return JSONResponse(content={"status": "ok"})


@router.post("/whatsapp/status")
async def whatsapp_status_callback(request: Request):
    """
    Handle WhatsApp message status callbacks.
    
    Twilio sends status updates when messages are sent, delivered, or read.
    """
    try:
        form_data = await request.form()
        data = dict(form_data)
        
        message_sid = data.get("MessageSid", "unknown")
        status = data.get("MessageStatus", "unknown")
        
        logger.info(f"Message {message_sid} status: {status}")
        
        # In production, update message status in database
        # await update_message_status(message_sid, status)
        
        return PlainTextResponse(content="OK")
        
    except Exception as e:
        logger.error(f"Error processing status callback: {e}")
        return PlainTextResponse(content="OK")


# ============================================================================
# VOICE WEBHOOKS
# ============================================================================

@router.post("/voice/incoming")
async def voice_incoming_call(request: Request):
    """
    Handle incoming voice calls.
    
    Returns TwiML to handle the call, typically:
    - Play greeting
    - Gather speech input
    - Process and respond
    """
    try:
        form_data = await request.form()
        data = dict(form_data)
        
        call_sid = data.get("CallSid", "unknown")
        from_number = data.get("From", "unknown")
        
        logger.info(f"Incoming call: {call_sid} from {from_number}")
        
        # Generate TwiML response
        twiml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say language="hi-IN">नमस्ते, कृषि मित्र में आपका स्वागत है। भाव जानने के लिए फसल का नाम बोलें।</Say>
    <Gather input="speech" action="/webhooks/voice/process" method="POST" language="hi-IN" timeout="5">
        <Say language="hi-IN">कृपया फसल का नाम बोलें।</Say>
    </Gather>
    <Say language="hi-IN">धन्यवाद।</Say>
</Response>"""
        
        return PlainTextResponse(content=twiml, media_type="application/xml")
        
    except Exception as e:
        logger.error(f"Error handling incoming call: {e}")
        twiml = """<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say>Sorry, there was an error. Please try again later.</Say>
</Response>"""
        return PlainTextResponse(content=twiml, media_type="application/xml")


@router.post("/voice/process")
async def voice_process_speech(request: Request):
    """
    Process speech gathered from voice call.
    
    Receives transcribed speech from Twilio and generates response.
    """
    try:
        form_data = await request.form()
        data = dict(form_data)
        
        call_sid = data.get("CallSid", "unknown")
        speech_result = data.get("SpeechResult", "")
        confidence = float(data.get("Confidence", 0))
        from_number = data.get("From", "")
        
        logger.info(f"Speech result: {speech_result} (confidence: {confidence})")
        
        # Process the speech (in production, use bot service)
        response_text = await process_voice_query(speech_result, from_number)
        
        # Generate TwiML with response
        twiml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say language="hi-IN">{response_text}</Say>
    <Gather input="speech" action="/webhooks/voice/process" method="POST" language="hi-IN" timeout="5">
        <Say language="hi-IN">क्या आप कुछ और जानना चाहेंगे?</Say>
    </Gather>
    <Say language="hi-IN">धन्यवाद। दोबारा मिलेंगे।</Say>
</Response>"""
        
        return PlainTextResponse(content=twiml, media_type="application/xml")
        
    except Exception as e:
        logger.error(f"Error processing speech: {e}")
        twiml = """<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Say language="hi-IN">माफ कीजिये, कुछ तकनीकी समस्या है। कृपया बाद में कॉल करें।</Say>
</Response>"""
        return PlainTextResponse(content=twiml, media_type="application/xml")


@router.post("/voice/process-audio", response_model=VoiceProcessingResponse)
async def process_audio_file(request: VoiceProcessingRequest):
    """
    Process audio file and return transcription with optional TTS response.
    
    This endpoint accepts base64-encoded audio and returns:
    - Transcribed text
    - Optional audio response
    """
    import base64
    
    try:
        # Decode audio
        audio_data = base64.b64decode(request.audio_base64)
        
        # Initialize voice service
        voice_service = VoiceService()
        
        # Transcribe audio
        asr_result = await voice_service.transcribe(
            audio_data=audio_data,
            language=request.language,
            audio_format=request.audio_format,
        )
        
        if not asr_result.success:
            return VoiceProcessingResponse(
                success=False,
                error=asr_result.error,
            )
        
        # Process the query (in production, use bot/NLU)
        response_text = await process_voice_query(asr_result.transcript, None)
        
        # Generate TTS response
        tts_result = await voice_service.synthesize(
            text=response_text,
            language=request.language,
        )
        
        response_audio = None
        if tts_result.success and tts_result.audio_data:
            response_audio = base64.b64encode(tts_result.audio_data).decode()
        
        return VoiceProcessingResponse(
            success=True,
            transcript=asr_result.transcript,
            confidence=asr_result.confidence,
            response_audio_base64=response_audio,
        )
        
    except Exception as e:
        logger.error(f"Error processing audio: {e}")
        return VoiceProcessingResponse(
            success=False,
            error=str(e),
        )


@router.post("/voice/tts")
async def text_to_speech_endpoint(request: Request):
    """
    Convert text to speech and return audio.
    
    Accepts text and returns audio file.
    """
    import base64
    
    try:
        body = await request.json()
        text = body.get("text", "")
        language = body.get("language", "hi")
        gender = body.get("gender", "female")
        
        if not text:
            raise HTTPException(status_code=400, detail="Text is required")
        
        # Generate TTS
        voice_service = VoiceService()
        result = await voice_service.synthesize(
            text=text,
            language=language,
            gender=gender,
        )
        
        if not result.success:
            raise HTTPException(status_code=500, detail=result.error)
        
        # Return audio as base64
        audio_base64 = base64.b64encode(result.audio_data).decode()
        
        return JSONResponse(content={
            "success": True,
            "audio_base64": audio_base64,
            "audio_format": result.audio_format,
        })
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating TTS: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# BHASHINI CALLBACK
# ============================================================================

@router.post("/bhashini/callback")
async def bhashini_callback(request: Request):
    """
    Handle callbacks from Bhashini API.
    
    For long-running ASR/TTS operations.
    """
    try:
        body = await request.json()
        
        request_id = body.get("requestId", "unknown")
        status = body.get("status", "unknown")
        
        logger.info(f"Bhashini callback: {request_id} - {status}")
        
        # In production, update job status and notify user
        # await update_bhashini_job(request_id, body)
        
        return JSONResponse(content={"status": "received"})
        
    except Exception as e:
        logger.error(f"Error processing Bhashini callback: {e}")
        return JSONResponse(content={"status": "error"}, status_code=200)


# ============================================================================
# HEALTH CHECK
# ============================================================================

@router.get("/health")
async def webhook_health():
    """Health check for webhook endpoints."""
    return {
        "status": "healthy",
        "services": {
            "whatsapp": "available",
            "voice": "available",
            "bhashini": "available",
        }
    }


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

async def process_voice_query(query: str, phone_number: Optional[str]) -> str:
    """
    Process voice query and generate response.
    
    Args:
        query: Transcribed speech query
        phone_number: Caller phone number
    
    Returns:
        Response text in Hindi
    """
    query_lower = query.lower()
    
    # Simple pattern matching for demo
    # In production, use NLU/bot service
    
    if any(word in query_lower for word in ["भाव", "दाम", "कीमत", "price", "rate"]):
        # Price query
        if "प्याज" in query_lower or "onion" in query_lower:
            return "प्याज का वर्तमान भाव ढाई हजार से तीन हजार रुपये प्रति क्विंटल है।"
        elif "आलू" in query_lower or "potato" in query_lower:
            return "आलू का वर्तमान भाव एक हजार से डेढ़ हजार रुपये प्रति क्विंटल है।"
        elif "टमाटर" in query_lower or "tomato" in query_lower:
            return "टमाटर का वर्तमान भाव दो हजार से ढाई हजार रुपये प्रति क्विंटल है।"
        else:
            return "कृपया फसल का नाम बताएं। जैसे: प्याज का भाव।"
    
    elif any(word in query_lower for word in ["मंडी", "बाजार", "बेचने", "mandi", "market"]):
        return "नजदीकी मंडी जानने के लिए अपना स्थान साझा करें या जिले का नाम बताएं।"
    
    elif any(word in query_lower for word in ["भविष्य", "forecast", "prediction"]):
        return "अगले सात दिनों में कीमतों में थोड़ी वृद्धि की संभावना है। विस्तृत जानकारी के लिए WhatsApp पर संदेश भेजें।"
    
    elif any(word in query_lower for word in ["मदद", "help", "सहायता"]):
        return "मैं आपकी मदद कर सकता हूं: भाव जानने के लिए फसल का नाम बोलें, मंडी खोजने के लिए अपना जिला बताएं।"
    
    else:
        return "माफ कीजिये, मैं समझ नहीं पाया। भाव जानने के लिए फसल का नाम बोलें।"


def _verify_twilio_signature(url: str, params: Dict[str, Any], signature: str) -> bool:
    """
    Verify Twilio webhook signature.
    
    Args:
        url: Webhook URL
        params: Request parameters
        signature: X-Twilio-Signature header
    
    Returns:
        True if signature is valid
    """
    import hmac
    import hashlib
    import base64
    
    try:
        # Sort and concatenate parameters
        sorted_params = sorted(params.items())
        data = url + "".join(f"{k}{v}" for k, v in sorted_params)
        
        # Calculate HMAC
        computed = hmac.new(
            settings.TWILIO_AUTH_TOKEN.encode(),
            data.encode(),
            hashlib.sha1,
        ).digest()
        
        computed_signature = base64.b64encode(computed).decode()
        
        return hmac.compare(computed_signature, signature)
        
    except Exception as e:
        logger.error(f"Error verifying signature: {e}")
        return False
