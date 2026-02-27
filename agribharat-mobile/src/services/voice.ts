import { Audio } from 'expo-av';
import axios from 'axios';
import { Platform } from 'react-native';
import * as FileSystem from 'expo-file-system';

// API Keys
const SARVAM_API_KEY = process.env.EXPO_PUBLIC_SARVAM_API_KEY ?? '';
const GROQ_API_KEY = process.env.EXPO_PUBLIC_GROQ_API_KEY ?? '';
const ELEVENLABS_API_KEY = process.env.EXPO_PUBLIC_ELEVENLABS_API_KEY ?? '';

// API Endpoints
const SARVAM_STT_URL = 'https://api.sarvam.ai/speech-to-text/process'; // Updated endpoint
const GROQ_CHAT_URL = 'https://api.groq.com/openai/v1/chat/completions';
const GROQ_STT_URL = 'https://api.groq.com/openai/v1/audio/transcriptions'; // Fallback STT
const ELEVENLABS_TTS_URL = 'https://api.elevenlabs.io/v1/text-to-speech';

// ElevenLabs Voice IDs (optimized for Indian languages)
// Hindi: Use a voice that handles Hindi well
// English: Standard clear voice
const VOICE_IDS = {
  hindi: '21m00Tcm4TlvDq8ikWAM', // Rachel - works well with multilingual
  english: '21m00Tcm4TlvDq8ikWAM', // Rachel - clear and natural
  // Alternative voices to try:
  // 'EXAVITQu4vr4xnSDxMaL' - Bella
  // 'AZnzlk1XvdvUeBnXmlld' - Dom
  // 'MF3mGyEZry7jI5vI9Q7N' - Elastic (male)
};

// Enhanced system prompt for better agricultural responses
const AGRI_SYSTEM_PROMPT = `You are KisaanAI, an intelligent agricultural assistant for Indian farmers.

YOUR CAPABILITIES:
1. Mandi Prices - Provide current market rates for crops (potato, wheat, rice, onion, tomato, etc.)
2. Weather Advice - Give farming-related weather guidance
3. Crop Recommendations - Suggest crops based on season and soil
4. Pest Management - Advice on common pests and solutions
5. Government Schemes - Information about farmer welfare schemes
6. Fertilizer Tips - Recommend fertilizers for specific crops

RESPONSE GUIDELINES:
- Keep responses under 80 words
- Be friendly and conversational
- Use simple language farmers can understand
- Provide practical, actionable advice
- Include approximate prices when asked (in â‚¹ per quintal)

CURRENT REFERENCE PRICES (per quintal):
- Potato: â‚¹1250-1450 | Wheat: â‚¹2150-2350 | Rice: â‚¹3250-3550
- Onion: â‚¹1550-1850 | Tomato: â‚¹850-1250 | Maize: â‚¹1900-2200

Respond in the same language as the user's query (Hindi or English).`;

interface ChatMessage {
  role: 'system' | 'user' | 'assistant';
  content: string;
}

// Enhanced intent detection
function detectIntent(text: string): string {
  const lowerText = text.toLowerCase();

  // Greetings
  if (lowerText.includes('à¤¨à¤®à¤¸à¥à¤¤à¥‡') || lowerText.includes('hello') || lowerText.includes('hi') ||
      lowerText.includes('hey') || lowerText.includes('à¤°à¤¾à¤® à¤°à¤¾à¤®')) {
    return 'greeting';
  }

  // Mandi/Market prices
  if (lowerText.includes('à¤®à¤‚à¤¡à¥€') || lowerText.includes('à¤¬à¤¾à¤œà¤¾à¤°') || lowerText.includes('mandi') ||
      lowerText.includes('market') || lowerText.includes('à¤­à¤¾à¤µ')) {
    return 'mandi';
  }

  // Price queries
  if (lowerText.includes('à¤•à¥€à¤®à¤¤') || lowerText.includes('price') || lowerText.includes('rate') ||
      lowerText.includes('à¤°à¥‡à¤Ÿ') || lowerText.includes('à¤•à¤¿à¤¤à¤¨à¤¾') || lowerText.includes('how much')) {
    return 'price';
  }

  // Weather
  if (lowerText.includes('à¤®à¥Œà¤¸à¤®') || lowerText.includes('weather') || lowerText.includes('à¤¬à¤¾à¤°à¤¿à¤¶') ||
      lowerText.includes('rain') || lowerText.includes('à¤¬à¤¾à¤¦à¤²')) {
    return 'weather';
  }

  // Crops
  if (lowerText.includes('à¤«à¤¸à¤²') || lowerText.includes('crop') || lowerText.includes('à¤–à¥‡à¤¤à¥€') ||
      lowerText.includes('à¤‰à¤—à¤¾à¤¨à¤¾') || lowerText.includes('à¤¬à¥‹à¤¨à¥€')) {
    return 'crop';
  }

  // Pests
  if (lowerText.includes('à¤•à¥€à¤Ÿ') || lowerText.includes('pest') || lowerText.includes('à¤‡à¤²à¤¾à¤¯à¤šà¥€') ||
      lowerText.includes('disease')) {
    return 'pest';
  }

  // Fertilizers
  if (lowerText.includes('à¤–à¤¾à¤¦') || lowerText.includes('fertilizer') || lowerText.includes('à¤¯à¥‚à¤°à¤¿à¤¯à¤¾')) {
    return 'fertilizer';
  }

  return 'general';
}

// Improved Sarvam Speech-to-Text with better configuration
async function transcribeAudio(audioUri: string, languageHint: string = 'unknown'): Promise<string> {
  // Try Sarvam first (best for Hindi)
  try {
    const formData = new FormData();

    // Proper file object for React Native
    const file = {
      uri: audioUri,
      type: 'audio/mpeg',
      name: 'audio.mp3',
    };

    formData.append('file', file as any);
    formData.append('model', 'saarika:v2');
    formData.append('language_code', languageHint === 'hi-IN' ? 'hi-IN' : 'en-IN');

    const response = await axios.post(SARVAM_STT_URL, formData, {
      headers: {
        'api-subscription-key': SARVAM_API_KEY,
        'Content-Type': 'multipart/form-data',
      },
      timeout: 35000,
      transformRequest: [(data) => data],
    });

    const transcript = response.data.transcript || response.data.text || '';

    if (!transcript) {
      throw new Error('No transcript returned');
    }

    console.log('Sarvam STT Success:', transcript);
    return transcript;

  } catch (error: any) {
    console.error('Sarvam STT Error:', error?.response?.data || error?.message);
  }

  // Fallback to Groq Whisper API
  try {
    console.log('Trying Groq Whisper fallback...');
    const formData = new FormData();

    const file = {
      uri: audioUri,
      type: 'audio/mpeg',
      name: 'audio.mp3',
    };

    formData.append('file', file as any);
    formData.append('model', 'whisper-large-v3');
    formData.append('language', languageHint === 'hi-IN' ? 'hi' : 'en');
    formData.append('response_format', 'text');

    const response = await axios.post(GROQ_STT_URL, formData, {
      headers: {
        'Authorization': `Bearer ${GROQ_API_KEY}`,
        'Content-Type': 'multipart/form-data',
      },
      timeout: 35000,
      transformRequest: [(data) => data],
    });

    // Groq returns text directly
    const transcript = typeof response.data === 'string' ? response.data : response.data.text || '';

    if (!transcript) {
      throw new Error('No transcript returned');
    }

    console.log('Groq Whisper Success:', transcript);
    return transcript;

  } catch (groqError: any) {
    console.error('Groq Whisper Error:', groqError?.response?.data || groqError?.message);
  }

  throw new Error('Speech recognition failed. Please try again.');
}

// ElevenLabs TTS - Natural Voice Synthesis
async function synthesizeWithElevenLabs(text: string, language: 'hi' | 'en'): Promise<string> {
  try {
    // Clean text for better synthesis
    const cleanText = text
      .replace(/â‚¹/g, 'à¤°à¥à¤ªà¤¯à¥‡')
      .replace(/\*/g, '')
      .replace(/\n/g, '. ')
      .replace(/  /g, ' ')
      .trim();

    const voiceId = VOICE_IDS[language === 'hi' ? 'hindi' : 'english'];

    console.log('ElevenLabs TTS Request:', cleanText.substring(0, 50) + '...');

    const response = await axios.post(
      `${ELEVENLABS_TTS_URL}/${voiceId}`,
      {
        text: cleanText,
        model_id: 'eleven_multilingual_v2',
        voice_settings: {
          stability: 0.5,
          similarity_boost: 0.75,
          style: 0.0,
          use_speaker_boost: true,
        },
      },
      {
        headers: {
          'xi-api-key': ELEVENLABS_API_KEY,
          'Content-Type': 'application/json',
          'Accept': 'audio/mpeg',
        },
        responseType: 'arraybuffer',
        timeout: 30000,
      }
    );

    // Save audio to temp file
    const timestamp = Date.now();
    const fileUri = `${FileSystem.cacheDirectory}tts_${timestamp}.mp3`;

    await FileSystem.writeAsStringAsync(
      fileUri,
      arrayBufferToBase64(response.data),
      { encoding: FileSystem.EncodingType.Base64 }
    );

    console.log('ElevenLabs TTS Success:', fileUri);
    return fileUri;

  } catch (error: any) {
    console.error('ElevenLabs TTS Error:', error?.response?.data || error?.message);

    // Check if it's a quota error
    if (error?.response?.status === 401 || error?.response?.status === 403) {
      console.warn('ElevenLabs quota exceeded or invalid key, will use fallback');
    }

    throw error;
  }
}

// Helper: Convert ArrayBuffer to Base64
function arrayBufferToBase64(buffer: ArrayBuffer): string {
  let binary = '';
  const bytes = new Uint8Array(buffer);
  const len = bytes.byteLength;
  for (let i = 0; i < len; i++) {
    binary += String.fromCharCode(bytes[i]);
  }
  return btoa(binary);
}

// Fallback TTS using Expo Speech (when ElevenLabs fails)
async function fallbackTTS(text: string, language: 'hi-IN' | 'en-US'): Promise<void> {
  try {
    // Import dynamically to avoid issues when ElevenLabs works
    const Speech = require('expo-speech');

    const cleanText = text
      .replace(/â‚¹/g, 'à¤°à¥à¤ªà¤¯à¥‡')
      .replace(/\*/g, '')
      .replace(/\n/g, '. ')
      .replace(/  /g, ' ');

    await Speech.speak(cleanText, {
      language,
      pitch: 1.0,
      rate: 0.85,
      volume: 1.0,
    });
  } catch (error) {
    console.error('Fallback TTS error:', error);
  }
}
async function getAIResponse(userMessage: string, conversationHistory: ChatMessage[] = []): Promise<string> {
  try {
    const messages: ChatMessage[] = [
      { role: 'system', content: AGRI_SYSTEM_PROMPT },
      ...conversationHistory.slice(-8), // Keep last 8 for better context
      { role: 'user', content: userMessage },
    ];

    const response = await axios.post(GROQ_CHAT_URL, {
      model: 'llama-3.3-70b-versatile',
      messages,
      temperature: 0.6, // Lower for more consistent responses
      max_tokens: 250,
      top_p: 0.9,
    }, {
      headers: {
        'Authorization': `Bearer ${GROQ_API_KEY}`,
        'Content-Type': 'application/json',
      },
      timeout: 20000,
    });

    const aiResponse = response.data.choices[0]?.message?.content;

    if (!aiResponse) {
      throw new Error('No response from AI');
    }

    console.log('Groq AI Response:', aiResponse);
    return aiResponse;

  } catch (error: any) {
    console.error('Groq API Error:', error?.response?.data || error?.message);
    throw new Error('AI service unavailable');
  }
}

export class VoiceService {
  private isListening: boolean = false;
  private isSpeaking: boolean = false;
  private recording: Audio.Recording | null = null;
  private currentSound: Audio.Sound | null = null;
  private conversationHistory: ChatMessage[] = [];
  private recordingTimeout: NodeJS.Timeout | null = null;
  private useElevenLabs: boolean = true; // Enable/disable ElevenLabs

  async startListening(
    onResult: (transcript: string, intent: string, response: string) => void,
    onError: (error: string) => void,
    language: 'hi-IN' | 'en-US' = 'hi-IN'
  ) {
    if (this.isListening) {
      await this.stopListening();
      return;
    }

    this.isListening = true;

    try {
      // Configure audio recording for better quality
      await Audio.setAudioModeAsync({
        allowsRecordingIOS: true,
        playsInSilentModeIOS: true,
      });

      // Custom recording options for better speech recognition
      const recordingOptions = {
        android: {
          extension: '.m4a',
          outputFormat: Audio.AndroidOutputFormat.MPEG_4,
          audioEncoder: Audio.AndroidAudioEncoder.AAC,
          sampleRate: 16000, // 16kHz is optimal for Sarvam
          numberOfChannels: 1,
          bitRate: 128000,
        },
        ios: {
          extension: '.m4a',
          outputFormat: Audio.IOSOutputFormat.MPEG4AAC,
          audioQuality: Audio.IOSAudioQuality.HIGH,
          sampleRate: 16000,
          numberOfChannels: 1,
          bitRate: 128000,
          linearPCMBitDepth: 16,
          linearPCMIsBigEndian: false,
          linearPCMIsFloat: false,
        },
        web: {
          mimeType: 'audio/webm',
          bitsPerSecond: 128000,
        },
      };

      const { recording } = await Audio.Recording.createAsync(recordingOptions);
      this.recording = recording;

      // Auto-stop after 12 seconds for longer speech
      this.recordingTimeout = setTimeout(async () => {
        if (this.isListening) {
          await this.processRecording(onResult, onError, language);
        }
      }, 12000);

    } catch (error: any) {
      console.error('Recording start error:', error);
      this.isListening = false;
      onError('à¤®à¤¾à¤‡à¤•à¥à¤°à¥‹à¤«à¥‹à¤¨ à¤…à¤¨à¥à¤®à¤¤à¤¿ à¤•à¥€ à¤œà¤¾à¤‚à¤š à¤•à¤°à¥‡à¤‚à¥¤');
    }
  }

  private async processRecording(
    onResult: (transcript: string, intent: string, response: string) => void,
    onError: (error: string) => void,
    language: 'hi-IN' | 'en-US'
  ) {
    if (!this.recording || !this.isListening) return;

    // Clear timeout
    if (this.recordingTimeout) {
      clearTimeout(this.recordingTimeout);
      this.recordingTimeout = null;
    }

    try {
      await this.recording.stopAndUnloadAsync();
      const uri = this.recording.getURI();
      this.recording = null;
      this.isListening = false;

      if (!uri) {
        onError('à¤°à¤¿à¤•à¥‰à¤°à¥à¤¡à¤¿à¤‚à¤— à¤µà¤¿à¤«à¤²à¥¤ à¤ªà¥à¤¨à¤ƒ à¤ªà¥à¤°à¤¯à¤¾à¤¸ à¤•à¤°à¥‡à¤‚à¥¤');
        return;
      }

      // Use language hint for better accuracy
      const langHint = language === 'hi-IN' ? 'hi-IN' : 'en-IN';

      // Transcribe with better error handling
      let transcript: string;
      try {
        transcript = await transcribeAudio(uri, langHint);
      } catch (transcribeError: any) {
        console.error('Transcription failed:', transcribeError);
        onError('à¤†à¤µà¤¾à¤œà¤¼ à¤ªà¤¹à¤šà¤¾à¤¨à¤¨à¥‡ à¤®à¥‡à¤‚ à¤µà¤¿à¤«à¤²à¥¤ à¤•à¥ƒà¤ªà¤¯à¤¾ à¤ªà¥à¤¨à¤ƒ à¤ªà¥à¤°à¤¯à¤¾à¤¸ à¤•à¤°à¥‡à¤‚à¥¤');
        return;
      }

      if (!transcript || transcript.trim().length === 0) {
        onError('à¤•à¥‹à¤ˆ à¤†à¤µà¤¾à¤œà¤¼ à¤¨à¤¹à¥€à¤‚ à¤®à¤¿à¤²à¥€à¥¤ à¤ªà¥à¤¨à¤ƒ à¤ªà¥à¤°à¤¯à¤¾à¤¸ à¤•à¤°à¥‡à¤‚à¥¤');
        return;
      }

      // Detect intent
      const intent = detectIntent(transcript);

      // Get AI response
      let response: string;
      try {
        response = await getAIResponse(transcript, this.conversationHistory);
      } catch (aiError: any) {
        console.error('AI response failed:', aiError);
        response = 'à¤®à¥ˆà¤‚ à¤†à¤ªà¤•à¥€ à¤®à¤¦à¤¦ à¤•à¤°à¤¨à¤¾ à¤šà¤¾à¤¹à¤¤à¤¾ à¤¹à¥‚à¤‚à¥¤ à¤•à¥ƒà¤ªà¤¯à¤¾ à¤«à¤¿à¤° à¤¸à¥‡ à¤ªà¥‚à¤›à¥‡à¤‚à¥¤';
      }

      // Save to history
      this.conversationHistory.push({ role: 'user', content: transcript });
      this.conversationHistory.push({ role: 'assistant', content: response });

      // Keep only last 20
      if (this.conversationHistory.length > 20) {
        this.conversationHistory = this.conversationHistory.slice(-20);
      }

      // Speak the response
      this.speak(response, language);

      onResult(transcript, intent, response);

    } catch (error: any) {
      console.error('Processing error:', error);
      this.isListening = false;
      this.recording = null;
      onError(error?.message || 'à¤ªà¥à¤°à¥‹à¤¸à¥‡à¤¸à¤¿à¤‚à¤— à¤µà¤¿à¤«à¤²à¥¤ à¤ªà¥à¤¨à¤ƒ à¤ªà¥à¤°à¤¯à¤¾à¤¸ à¤•à¤°à¥‡à¤‚à¥¤');
    }
  }

  async stopListening() {
    if (this.recordingTimeout) {
      clearTimeout(this.recordingTimeout);
      this.recordingTimeout = null;
    }
    this.isListening = false;
    if (this.recording) {
      try {
        await this.recording.stopAndUnloadAsync();
      } catch (error) {
        // Ignore
      }
      this.recording = null;
    }
  }

  async speak(text: string, language: 'hi-IN' | 'en-US' = 'hi-IN') {
    // Stop any current playback
    await this.stopSpeaking();

    this.isSpeaking = true;

    const langCode = language === 'hi-IN' ? 'hi' : 'en';

    // Try ElevenLabs first (if enabled)
    if (this.useElevenLabs) {
      try {
        const audioUri = await synthesizeWithElevenLabs(text, langCode);

        // Play the audio file
        const { sound } = await Audio.Sound.createAsync(
          { uri: audioUri },
          {
            shouldPlay: true,
            rate: 1.0,
            volume: 1.0,
          },
          (status) => {
            if (status.isLoaded && status.didJustFinish) {
              this.isSpeaking = false;
              this.currentSound = null;
              // Clean up temp file
              FileSystem.deleteAsync(audioUri, { idempotent: true }).catch(() => {});
            }
          }
        );

        this.currentSound = sound;
        return;
      } catch (elevenLabsError) {
        console.warn('ElevenLabs TTS failed, falling back to Expo Speech:', elevenLabsError);
        // Fall through to fallback
      }
    }

    // Fallback to Expo Speech
    try {
      await fallbackTTS(text, language);

      // Estimate speaking duration for fallback
      const estimatedDuration = Math.min(text.length * 80, 10000);
      setTimeout(() => {
        this.isSpeaking = false;
      }, estimatedDuration);
    } catch (error) {
      console.error('All TTS methods failed:', error);
      this.isSpeaking = false;
    }
  }

  async stopSpeaking() {
    try {
      // Stop ElevenLabs audio
      if (this.currentSound) {
        await this.currentSound.stopAsync();
        await this.currentSound.unloadAsync();
        this.currentSound = null;
      }

      // Stop Expo Speech
      try {
        const Speech = require('expo-speech');
        await Speech.stop();
      } catch {}

      this.isSpeaking = false;
    } catch (error) {
      // Ignore
    }
  }

  isCurrentlyListening(): boolean {
    return this.isListening;
  }

  isCurrentlySpeaking(): boolean {
    return this.isSpeaking;
  }

  async processTextInput(
    text: string,
    onResult: (intent: string, response: string) => void,
    onError: (error: string) => void,
    language: 'hi-IN' | 'en-US' = 'hi-IN'
  ) {
    try {
      const intent = detectIntent(text);
      const response = await getAIResponse(text, this.conversationHistory);

      // Save to history
      this.conversationHistory.push({ role: 'user', content: text });
      this.conversationHistory.push({ role: 'assistant', content: response });

      // Keep only last 20
      if (this.conversationHistory.length > 20) {
        this.conversationHistory = this.conversationHistory.slice(-20);
      }

      // Speak the response
      this.speak(response, language);

      onResult(intent, response);
    } catch (error: any) {
      onError(error?.message || 'à¤ªà¥à¤°à¥‹à¤¸à¥‡à¤¸à¤¿à¤‚à¤— à¤µà¤¿à¤«à¤²à¥¤ à¤ªà¥à¤¨à¤ƒ à¤ªà¥à¤°à¤¯à¤¾à¤¸ à¤•à¤°à¥‡à¤‚à¥¤');
    }
  }

  getConversationHistory() {
    return this.conversationHistory;
  }

  clearHistory() {
    this.conversationHistory = [];
  }

  destroy() {
    this.stopListening();
    this.stopSpeaking();
    if (this.currentSound) {
      this.currentSound.unloadAsync().catch(() => {});
      this.currentSound = null;
    }
  }

  // Toggle ElevenLabs on/off
  setElevenLabsEnabled(enabled: boolean) {
    this.useElevenLabs = enabled;
  }

  isElevenLabsEnabled(): boolean {
    return this.useElevenLabs;
  }
}

export const voiceService = new VoiceService();
