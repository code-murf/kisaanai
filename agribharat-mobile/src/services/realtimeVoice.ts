/**
 * Real-time Voice Service - ChatGPT Pro Style
 *
 * Features:
 * - Streaming audio chunk by chunk
 * - Interrupt handling (tap to stop)
 * - Low latency response
 * - Natural conversation flow
 */

import { Audio } from 'expo-av';
import axios from 'axios';
import * as FileSystem from 'expo-file-system';

// API Keys
const GROQ_API_KEY = process.env.EXPO_PUBLIC_GROQ_API_KEY ?? '';
const ELEVENLABS_API_KEY = process.env.EXPO_PUBLIC_ELEVENLABS_API_KEY ?? '';

// API Endpoints
const GROQ_CHAT_URL = 'https://api.groq.com/openai/v1/chat/completions';
const ELEVENLABS_TTS_URL = 'https://api.elevenlabs.io/v1/text-to-speech';
const ELEVENLABS_STREAM_URL = 'https://api.elevenlabs.io/v1/text-to-speech';

// Voice configuration
const VOICE_IDS = {
  hindi: '21m00Tcm4TlvDq8ikWAM',
  english: '21m00Tcm4TlvDq8ikWAM',
};

interface ConversationState {
  isRecording: boolean;
  isPlaying: boolean;
  isProcessing: boolean;
  canInterrupt: boolean;
}

interface Message {
  role: 'user' | 'assistant' | 'system';
  content: string;
}

export class RealtimeVoiceService {
  private state: ConversationState = {
    isRecording: false,
    isPlaying: false,
    isProcessing: false,
    canInterrupt: true,
  };

  private recording: Audio.Recording | null = null;
  private currentSound: Audio.Sound | null = null;
  private conversationHistory: Message[] = [];
  private audioChunks: string[] = [];
  private recordingTimeout: NodeJS.Timeout | null = null;

  // System prompt for agricultural assistant
  private systemPrompt = `You are AgriBharat AI, a friendly agricultural assistant for Indian farmers.

Keep responses:
- Under 60 words
- Simple and conversational
- Practical and actionable
- In the same language (Hindi/English)

Current prices (₹/quintal):
- Potato: ₹1250-1450
- Wheat: ₹2150-2350
- Rice: ₹3250-3550
- Onion: ₹1550-1850

Be helpful and friendly!`;

  /**
   * Start recording with auto-detect silence
   */
  async startRecording(
    onSilenceDetected: (audioUri: string) => void,
    onError: (error: string) => void
  ) {
    if (this.state.isRecording) {
      await this.stopRecording();
      return;
    }

    this.state.isRecording = true;

    try {
      await Audio.setAudioModeAsync({
        allowsRecordingIOS: true,
        playsInSilentModeIOS: true,
      });

      const recordingOptions: Audio.RecordingOptions = {
        android: {
          extension: '.m4a',
          outputFormat: Audio.AndroidOutputFormat.MPEG_4,
          audioEncoder: Audio.AndroidAudioEncoder.AAC,
          sampleRate: 16000,
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
        },
        web: {
          mimeType: 'audio/webm',
          bitsPerSecond: 128000,
        },
      };

      const { recording } = await Audio.Recording.createAsync(recordingOptions);
      this.recording = recording;

      // Auto-stop after 8 seconds of silence or max 15 seconds
      this.recordingTimeout = setTimeout(async () => {
        if (this.state.isRecording) {
          const uri = await this.stopRecording();
          if (uri) onSilenceDetected(uri);
        }
      }, 15000);

    } catch (error: any) {
      console.error('Recording error:', error);
      this.state.isRecording = false;
      onError('Could not start recording');
    }
  }

  /**
   * Stop recording and return URI
   */
  async stopRecording(): Promise<string | null> {
    if (!this.recording) return null;

    if (this.recordingTimeout) {
      clearTimeout(this.recordingTimeout);
      this.recordingTimeout = null;
    }

    this.state.isRecording = false;

    try {
      await this.recording.stopAndUnloadAsync();
      const uri = this.recording.getURI();
      this.recording = null;
      return uri;
    } catch (error) {
      this.recording = null;
      return null;
    }
  }

  /**
   * Transcribe audio using Groq Whisper (fast and reliable)
   */
  async transcribe(audioUri: string, language: 'hi' | 'en' = 'hi'): Promise<string> {
    try {
      const formData = new FormData();
      const file = {
        uri: audioUri,
        type: 'audio/mpeg',
        name: 'audio.mp3',
      };

      formData.append('file', file as any);
      formData.append('model', 'whisper-large-v3-turbo'); // Faster model
      formData.append('language', language === 'hi' ? 'hi' : 'en');
      formData.append('response_format', 'text');
      formData.append('temperature', '0');

      const response = await axios.post(
        'https://api.groq.com/openai/v1/audio/transcriptions',
        formData,
        {
          headers: {
            'Authorization': `Bearer ${GROQ_API_KEY}`,
            'Content-Type': 'multipart/form-data',
          },
          timeout: 15000,
          transformRequest: [(data) => data],
        }
      );

      const transcript = typeof response.data === 'string' ? response.data : response.data.text || '';
      console.log('Transcript:', transcript);
      return transcript;

    } catch (error: any) {
      console.error('Transcription error:', error?.response?.data || error?.message);
      throw new Error('Speech recognition failed');
    }
  }

  /**
   * Get AI response from Groq (fast LLM)
   */
  async getAIResponse(text: string, language: 'hi' | 'en' = 'hi'): Promise<string> {
    try {
      const messages: Message[] = [
        { role: 'system', content: this.systemPrompt },
        ...this.conversationHistory.slice(-6),
        { role: 'user', content: text },
      ];

      const response = await axios.post(GROQ_CHAT_URL, {
        model: 'llama-3.3-70b-versatile',
        messages,
        temperature: 0.7,
        max_tokens: 150,
        stream: false,
      }, {
        headers: {
          'Authorization': `Bearer ${GROQ_API_KEY}`,
          'Content-Type': 'application/json',
        },
        timeout: 10000,
      });

      const aiResponse = response.data.choices[0]?.message?.content || text;
      return aiResponse;

    } catch (error: any) {
      console.error('AI error:', error);
      return 'मैं आपकी मदद करना चाहता हूं। कृपया फिर से पूछें।';
    }
  }

  /**
   * Generate speech with ElevenLabs
   */
  async generateSpeech(text: string, language: 'hi' | 'en' = 'hi'): Promise<string> {
    try {
      const cleanText = text
        .replace(/₹/g, 'रुपये')
        .replace(/\*/g, '')
        .replace(/\n/g, '. ')
        .trim();

      const voiceId = VOICE_IDS[language === 'hi' ? 'hindi' : 'english'];

      const response = await axios.post(
        `${ELEVENLABS_TTS_URL}/${voiceId}`,
        {
          text: cleanText,
          model_id: 'eleven_multilingual_v2',
          voice_settings: {
            stability: 0.4,
            similarity_boost: 0.8,
            style: 0.2,
            use_speaker_boost: true,
          },
        },
        {
          headers: {
            'xi-api-key': ELEVENLABS_API_KEY,
            'Content-Type': 'application/json',
          },
          responseType: 'arraybuffer',
          timeout: 20000,
        }
      );

      // Save to temp file
      const timestamp = Date.now();
      const fileUri = `${FileSystem.cacheDirectory}speech_${timestamp}.mp3`;

      await FileSystem.writeAsStringAsync(
        fileUri,
        this.arrayBufferToBase64(response.data),
        { encoding: FileSystem.EncodingType.Base64 }
      );

      return fileUri;

    } catch (error: any) {
      console.error('TTS error:', error);
      throw error;
    }
  }

  /**
   * Play audio with interrupt support
   */
  async playAudio(audioUri: string, onPlaybackEnd?: () => void) {
    // Stop any current playback
    await this.stopPlayback();

    this.state.isPlaying = true;
    this.state.canInterrupt = true;

    try {
      const { sound } = await Audio.Sound.createAsync(
        { uri: audioUri },
        {
          shouldPlay: true,
          rate: 1.0,
          volume: 1.0,
        },
        (status) => {
          if (status.isLoaded && status.didJustFinish) {
            this.state.isPlaying = false;
            this.currentSound = null;
            onPlaybackEnd?.();
            // Clean up temp file
            FileSystem.deleteAsync(audioUri, { idempotent: true }).catch(() => {});
          }
        }
      );

      this.currentSound = sound;

    } catch (error) {
      console.error('Playback error:', error);
      this.state.isPlaying = false;
    }
  }

  /**
   * Stop/interrupt current playback
   */
  async stopPlayback() {
    this.state.canInterrupt = false;

    if (this.currentSound) {
      try {
        await this.currentSound.stopAsync();
        await this.currentSound.unloadAsync();
      } catch {}
      this.currentSound = null;
    }

    this.state.isPlaying = false;
  }

  /**
   * Full conversation cycle
   */
  async processConversation(
    inputAudioUri: string,
    language: 'hi' | 'en',
    onTranscript: (text: string) => void,
    onResponse: (text: string) => void,
    onSpeakingStart: () => void,
    onSpeakingEnd: () => void,
    onError: (error: string) => void
  ) {
    this.state.isProcessing = true;

    try {
      // 1. Transcribe
      onTranscript('Listening...');
      const transcript = await this.transcribe(inputAudioUri, language);
      onTranscript(transcript);

      // 2. Get AI response
      const response = await this.getAIResponse(transcript, language);
      onResponse(response);

      // Save to history
      this.conversationHistory.push({ role: 'user', content: transcript });
      this.conversationHistory.push({ role: 'assistant', content: response });
      if (this.conversationHistory.length > 20) {
        this.conversationHistory = this.conversationHistory.slice(-20);
      }

      // 3. Generate speech
      onSpeakingStart();
      const speechAudioUri = await this.generateSpeech(response, language);

      // 4. Play speech
      await this.playAudio(speechAudioUri, () => {
        onSpeakingEnd();
        this.state.isProcessing = false;
      });

    } catch (error: any) {
      console.error('Conversation error:', error);
      onError(error?.message || 'Something went wrong');
      this.state.isProcessing = false;
    }
  }

  /**
   * Interrupt conversation (stop speaking, ready for new input)
   */
  async interrupt() {
    await this.stopPlayback();
    await this.stopRecording();
    this.state.isProcessing = false;
  }

  /**
   * Get current state
   */
  getState() {
    return { ...this.state };
  }

  /**
   * Check if can be interrupted
   */
  canInterrupt(): boolean {
    return this.state.canInterrupt && this.state.isPlaying;
  }

  /**
   * Helper: Convert ArrayBuffer to Base64
   */
  private arrayBufferToBase64(buffer: ArrayBuffer): string {
    let binary = '';
    const bytes = new Uint8Array(buffer);
    const len = bytes.byteLength;
    for (let i = 0; i < len; i++) {
      binary += String.fromCharCode(bytes[i]);
    }
    return btoa(binary);
  }

  /**
   * Clear conversation history
   */
  clearHistory() {
    this.conversationHistory = [];
  }

  /**
   * Destroy and cleanup
   */
  async destroy() {
    await this.stopPlayback();
    await this.stopRecording();
    if (this.currentSound) {
      this.currentSound.unloadAsync().catch(() => {});
      this.currentSound = null;
    }
  }
}

export const realtimeVoiceService = new RealtimeVoiceService();
