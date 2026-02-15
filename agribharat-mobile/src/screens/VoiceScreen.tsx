/**
 * Voice Assistant Screen - ChatGPT Pro Style
 *
 * Features:
 * - Tap and hold to speak
 * - Release to send
 * - Tap response to interrupt
 * - Visual feedback for all states
 * - Natural conversation flow
 */

import React, { useState, useRef, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  Animated,
  PanResponder,
  Dimensions,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Mic, Square, Waves, Sparkles, Volume2 } from 'lucide-react-native';
import { COLORS } from '../constants';
import { useAppStore } from '../store/useAppStore';
import { realtimeVoiceService } from '../services/realtimeVoice';

const { width, height } = Dimensions.get('window');

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  isSpeaking?: boolean;
}

export default function VoiceScreen() {
  const { selectedLanguage } = useAppStore();

  // State
  const [messages, setMessages] = useState<Message[]>([]);
  const [isRecording, setIsRecording] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [transcript, setTranscript] = useState('');
  const [lastResponse, setLastResponse] = useState('');

  // Animation refs
  const pulseAnim = useRef(new Animated.Value(1)).current;
  const rippleAnim = useRef(new Animated.Value(0)).current;
  const slideAnim = useRef(new Animated.Value(height)).current;

  const isMounted = useRef(true);

  // Pulse animation when recording
  useEffect(() => {
    if (isRecording) {
      Animated.loop(
        Animated.sequence([
          Animated.timing(pulseAnim, { toValue: 1.15, duration: 600, useNativeDriver: true }),
          Animated.timing(pulseAnim, { toValue: 1, duration: 600, useNativeDriver: true }),
        ])
      ).start();
    } else {
      pulseAnim.setValue(1);
    }
  }, [isRecording]);

  // Ripple animation when speaking
  useEffect(() => {
    if (isSpeaking) {
      Animated.loop(
        Animated.sequence([
          Animated.timing(rippleAnim, { toValue: 1, duration: 1500, useNativeDriver: true }),
          Animated.timing(rippleAnim, { toValue: 0, duration: 1500, useNativeDriver: true }),
        ])
      ).start();
    } else {
      rippleAnim.setValue(0);
    }
  }, [isSpeaking]);

  // Slide animation for messages
  useEffect(() => {
    if (lastResponse) {
      slideAnim.setValue(height);
      Animated.timing(slideAnim, {
        toValue: 0,
        duration: 400,
        useNativeDriver: true,
      }).start();
    }
  }, [lastResponse]);

  // Handle recording start/stop
  const handleRecordingToggle = async () => {
    if (isRecording) {
      // Stop recording manually
      const uri = await realtimeVoiceService.stopRecording();
      if (uri) {
        processAudio(uri);
      }
    } else {
      // Start recording
      setLastResponse('');
      setTranscript('');
      await realtimeVoiceService.startRecording(
        (audioUri) => {
          // Auto-stop on silence
          processAudio(audioUri);
        },
        (error) => {
          console.error('Recording error:', error);
        }
      );
      setIsRecording(true);
    }
  };

  // Process audio through the pipeline
  const processAudio = async (audioUri: string) => {
    setIsRecording(false);
    setIsProcessing(true);

    const lang = selectedLanguage === 'hi' ? 'hi' : 'en';

    await realtimeVoiceService.processConversation(
      audioUri,
      lang,
      (text) => setTranscript(text), // onTranscript
      (response) => {
        setLastResponse(response);
        setMessages(prev => [...prev, {
          id: Date.now().toString(),
          role: 'assistant',
          content: response,
          isSpeaking: true,
        }]);
      }, // onResponse
      () => setIsSpeaking(true), // onSpeakingStart
      () => {
        setIsSpeaking(false);
        setIsProcessing(false);
        setMessages(prev => prev.map(m => ({ ...m, isSpeaking: false })));
      }, // onSpeakingEnd
      (error) => {
        setIsProcessing(false);
        setMessages(prev => [...prev, {
          id: Date.now().toString(),
          role: 'assistant',
          content: `⚠️ ${error}`,
        }]);
      } // onError
    );
  };

  // Interrupt current response
  const handleInterrupt = async () => {
    if (isSpeaking) {
      await realtimeVoiceService.interrupt();
      setIsSpeaking(false);
      setIsProcessing(false);
      setMessages(prev => prev.map(m => ({ ...m, isSpeaking: false })));
    }
  };

  // Cleanup
  useEffect(() => {
    return () => {
      isMounted.current = false;
      realtimeVoiceService.destroy();
    };
  }, []);

  const isHindi = selectedLanguage === 'hi';

  return (
    <SafeAreaView style={styles.container}>
      {/* Background Effects */}
      <View style={styles.background}>
        {/* Ripple effect when speaking */}
        {isSpeaking && (
          <>
            <Animated.View
              style={[
                styles.ripple,
                {
                  opacity: rippleAnim.interpolate({
                    inputRange: [0, 1],
                    outputRange: [0.5, 0],
                  }),
                  transform: [
                    {
                      scale: rippleAnim.interpolate({
                        inputRange: [0, 1],
                        outputRange: [1, 2],
                      }),
                    },
                  ],
                },
              ]}
            />
            <Animated.View
              style={[
                styles.ripple,
                styles.ripple2,
                {
                  opacity: rippleAnim.interpolate({
                    inputRange: [0, 0.5, 1],
                    outputRange: [0, 0.4, 0],
                  }),
                  transform: [
                    {
                      scale: rippleAnim.interpolate({
                        inputRange: [0, 1],
                        outputRange: [1, 1.5],
                      }),
                    },
                  ],
                },
              ]}
            />
          </>
        )}
      </View>

      {/* Header */}
      <View style={styles.header}>
        <View style={styles.headerLeft}>
          <View style={styles.iconContainer}>
            <Sparkles size={20} color={COLORS.primary} />
          </View>
          <Text style={styles.title}>
            {isHindi ? 'आवाज़ सहायक' : 'AI Assistant'}
          </Text>
        </View>
        <View style={styles.hdBadge}>
          <Waves size={12} color={COLORS.primary} />
          <Text style={styles.hdBadgeText}>HD Voice</Text>
        </View>
      </View>

      {/* Main Content */}
      <View style={styles.content}>
        {/* Status Text */}
        {isRecording && (
          <Animated.Text
            style={[
              styles.statusText,
              { opacity: pulseAnim },
            ]}
          >
            {isHindi ? 'सुन रहा हूं...' : 'Listening...'}
          </Animated.Text>
        )}

        {isProcessing && !isRecording && (
          <Text style={styles.statusText}>
            {isSpeaking
              ? (isHindi ? 'बोल रहा हूं...' : 'Speaking...')
              : (isHindi ? 'सोच रहा हूं...' : 'Thinking...')
            }
          </Text>
        )}

        {/* Transcript */}
        {transcript && !isRecording && (
          <Animated.View
            style={[
              styles.transcriptContainer,
              { transform: [{ translateY: slideAnim }] },
            ]}
          >
            <Text style={styles.transcriptLabel}>{isHindi ? 'आपने कहा:' : 'You said:'}</Text>
            <Text style={styles.transcriptText}>{transcript}</Text>
          </Animated.View>
        )}

        {/* Response Display */}
        {lastResponse && (
          <Animated.View
            style={[
              styles.responseContainer,
              isSpeaking && styles.responseSpeaking,
              { transform: [{ translateY: slideAnim }] },
            ]}
          >
            {/* Tap to interrupt hint */}
            {isSpeaking && (
              <TouchableOpacity onPress={handleInterrupt} style={styles.interruptHint}>
                <Square size={14} color={COLORS.primary} />
                <Text style={styles.interruptText}>
                  {isHindi ? 'टैप करें' : 'Tap to stop'}
                </Text>
              </TouchableOpacity>
            )}

            <Text style={styles.responseText}>{lastResponse}</Text>

            {/* Speaking indicator */}
            {isSpeaking && (
              <View style={styles.waveContainer}>
                {[0, 1, 2, 3, 4].map((i) => (
                  <Animated.View
                    key={i}
                    style={[
                      styles.waveBar,
                      {
                    opacity: rippleAnim.interpolate({
                      inputRange: [0, 0.5, 1],
                      outputRange: [0.3, 1, 0.3],
                    }),
                    transform: [
                      {
                        scaleY: rippleAnim.interpolate({
                          inputRange: [0, 0.5, 1],
                          outputRange: [0.5, 1.2, 0.5],
                        }),
                      },
                    ],
                    marginLeft: i > 0 ? 4 : 0,
                  },
                  ]}
                />
                ))}
              </View>
            )}
          </Animated.View>
        )}

        {/* Initial State */}
        {!transcript && !lastResponse && !isRecording && !isProcessing && (
          <View style={styles.emptyState}>
            <Animated.View style={{ transform: [{ scale: pulseAnim }] }}>
              <Mic size={64} color={COLORS.primary} />
            </Animated.View>
            <Text style={styles.emptyTitle}>
              {isHindi ? 'बात करें' : 'Start Talking'}
            </Text>
            <Text style={styles.emptySubtitle}>
              {isHindi
                ? 'नीचे बटन दबाएं और बोलें'
                : 'Hold button below to speak'}
            </Text>
          </View>
        )}
      </View>

      {/* Recording Button */}
      <View style={styles.buttonContainer}>
        <TouchableOpacity
          onPress={handleRecordingToggle}
          activeOpacity={0.8}
          style={[
            styles.recordButton,
            isRecording && styles.recordButtonActive,
            isProcessing && !isRecording && styles.recordButtonProcessing,
          ]}
        >
          {isRecording ? (
            <Square size={32} color={COLORS.background} />
          ) : isProcessing ? (
            <Waves size={32} color={COLORS.background} />
          ) : (
            <Mic size={32} color={COLORS.background} />
          )}
        </TouchableOpacity>

        <Text style={styles.buttonHint}>
          {isRecording
            ? (isHindi ? 'छोड़ने के लिए टैप करें' : 'Tap to stop')
            : (isHindi ? 'रिकॉर्ड करने के लिए टैप करें' : 'Tap to record')
          }
        </Text>
      </View>

      {/* Language Indicator */}
      <View style={styles.languageBar}>
        <View style={styles.languageDot} />
        <Text style={styles.languageText}>
          {isHindi ? 'हिंदी' : 'English'}
        </Text>
        <View style={styles.languageDot} />
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: COLORS.background,
  },
  background: {
    ...StyleSheet.absoluteFillObject,
    justifyContent: 'center',
    alignItems: 'center',
  },
  ripple: {
    position: 'absolute',
    width: 300,
    height: 300,
    borderRadius: 150,
    backgroundColor: COLORS.primary,
  },
  ripple2: {
    width: 200,
    height: 200,
    borderRadius: 100,
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: 20,
    paddingVertical: 16,
  },
  headerLeft: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
  },
  iconContainer: {
    width: 36,
    height: 36,
    borderRadius: 18,
    backgroundColor: `${COLORS.primary}20`,
    alignItems: 'center',
    justifyContent: 'center',
  },
  title: {
    fontSize: 20,
    fontWeight: '700',
    color: COLORS.text,
  },
  hdBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    backgroundColor: `${COLORS.primary}15`,
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 16,
    borderWidth: 1,
    borderColor: `${COLORS.primary}40`,
  },
  hdBadgeText: {
    fontSize: 12,
    fontWeight: '600',
    color: COLORS.primary,
  },
  content: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    paddingHorizontal: 24,
  },
  statusText: {
    fontSize: 18,
    fontWeight: '600',
    color: COLORS.primary,
    marginBottom: 24,
  },
  transcriptContainer: {
    width: '100%',
    backgroundColor: COLORS.card,
    borderRadius: 20,
    padding: 20,
    marginBottom: 16,
    borderWidth: 1,
    borderColor: `${COLORS.primary}30`,
  },
  transcriptLabel: {
    fontSize: 13,
    color: COLORS.textSecondary,
    marginBottom: 8,
    textTransform: 'uppercase',
    letterSpacing: 1,
  },
  transcriptText: {
    fontSize: 18,
    color: COLORS.text,
    fontWeight: '500',
  },
  responseContainer: {
    width: '100%',
    backgroundColor: COLORS.card,
    borderRadius: 24,
    padding: 24,
    borderWidth: 2,
    borderColor: COLORS.primary,
    position: 'relative',
  },
  responseSpeaking: {
    borderColor: COLORS.primary,
    shadowColor: COLORS.primary,
    shadowOffset: { width: 0, height: 0 },
    shadowOpacity: 0.3,
    shadowRadius: 20,
    elevation: 10,
  },
  interruptHint: {
    position: 'absolute',
    top: 12,
    right: 12,
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
    backgroundColor: `${COLORS.primary}20`,
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 12,
  },
  interruptText: {
    fontSize: 11,
    fontWeight: '600',
    color: COLORS.primary,
  },
  responseText: {
    fontSize: 18,
    color: COLORS.text,
    lineHeight: 28,
    fontWeight: '500',
  },
  waveContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    marginTop: 16,
    height: 24,
  },
  waveBar: {
    width: 4,
    height: 16,
    borderRadius: 2,
    backgroundColor: COLORS.primary,
  },
  emptyState: {
    alignItems: 'center',
    justifyContent: 'center',
  },
  emptyTitle: {
    fontSize: 24,
    fontWeight: '700',
    color: COLORS.text,
    marginTop: 20,
  },
  emptySubtitle: {
    fontSize: 15,
    color: COLORS.textSecondary,
    marginTop: 8,
  },
  buttonContainer: {
    alignItems: 'center',
    paddingBottom: 24,
  },
  recordButton: {
    width: 80,
    height: 80,
    borderRadius: 40,
    backgroundColor: COLORS.primary,
    alignItems: 'center',
    justifyContent: 'center',
    shadowColor: COLORS.primary,
    shadowOffset: { width: 0, height: 8 },
    shadowOpacity: 0.4,
    shadowRadius: 16,
    elevation: 12,
  },
  recordButtonActive: {
    backgroundColor: COLORS.error,
    shadowColor: COLORS.error,
  },
  recordButtonProcessing: {
    backgroundColor: `${COLORS.primary}60`,
  },
  buttonHint: {
    fontSize: 14,
    color: COLORS.textSecondary,
    marginTop: 12,
    fontWeight: '500',
  },
  languageBar: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 12,
    gap: 8,
  },
  languageDot: {
    width: 4,
    height: 4,
    borderRadius: 2,
    backgroundColor: COLORS.primary,
  },
  languageText: {
    fontSize: 12,
    color: COLORS.textSecondary,
    fontWeight: '500',
  },
});
