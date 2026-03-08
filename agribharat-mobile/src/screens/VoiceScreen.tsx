import React, { useState, useRef, useEffect } from 'react';
import {
  View, Text, StyleSheet, ScrollView, TouchableOpacity,
  TextInput, KeyboardAvoidingView, Platform, ActivityIndicator,
  Animated, Easing, Dimensions,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Audio } from 'expo-av';
import { Send, Mic, Bot, Square, Volume2, ChevronLeft, MessageSquare } from 'lucide-react-native';
import { useAppStore } from '../store/useAppStore';
import { api } from '../services/api';

const { width: W, height: H } = Dimensions.get('window');
const G = '#34c759';
const CYAN = '#1CC0D1';
const C = { bg: '#05070A', card: '#0d1117', border: '#1c1c1e', muted: '#8e8e93', white: '#fff' };

type VoiceState = 'idle' | 'listening' | 'processing' | 'speaking';
interface Msg { id: string; role: 'user' | 'bot'; text: string; hasAudio?: boolean; }

const quick = {
  hi: ['आज आलू का भाव?', 'सबसे अच्छी मंडी?', 'गेहूं की कीमत?', 'मौसम कैसा रहेगा?'],
  en: ['Potato price today?', 'Best mandi?', 'Wheat price trend?', 'Weather forecast?'],
};

// ═══════════════════════════════════════════════
//  GLOWING ORB COMPONENT (GPT / Siri style)
// ═══════════════════════════════════════════════
function VoiceOrb({ state, onTap, onStop }: { state: VoiceState; onTap: () => void; onStop: () => void }) {
  const pulseAnim = useRef(new Animated.Value(1)).current;
  const glowAnim = useRef(new Animated.Value(0.3)).current;
  const ring1 = useRef(new Animated.Value(1)).current;
  const ring2 = useRef(new Animated.Value(1)).current;
  const ring3 = useRef(new Animated.Value(1)).current;
  const breathe = useRef(new Animated.Value(1)).current;

  useEffect(() => {
    // Stop all previous animations
    pulseAnim.stopAnimation();
    glowAnim.stopAnimation();
    ring1.stopAnimation();
    ring2.stopAnimation();
    ring3.stopAnimation();
    breathe.stopAnimation();

    if (state === 'idle') {
      // Gentle breathing
      Animated.loop(Animated.sequence([
        Animated.timing(breathe, { toValue: 1.05, duration: 2000, easing: Easing.inOut(Easing.sin), useNativeDriver: true }),
        Animated.timing(breathe, { toValue: 1, duration: 2000, easing: Easing.inOut(Easing.sin), useNativeDriver: true }),
      ])).start();
      Animated.timing(glowAnim, { toValue: 0.3, duration: 500, useNativeDriver: true }).start();
    }

    if (state === 'listening') {
      // Pulsing rings expanding outward
      Animated.loop(Animated.stagger(200, [
        Animated.sequence([
          Animated.timing(ring1, { toValue: 1.6, duration: 1000, easing: Easing.out(Easing.ease), useNativeDriver: true }),
          Animated.timing(ring1, { toValue: 1, duration: 0, useNativeDriver: true }),
        ]),
        Animated.sequence([
          Animated.timing(ring2, { toValue: 1.8, duration: 1200, easing: Easing.out(Easing.ease), useNativeDriver: true }),
          Animated.timing(ring2, { toValue: 1, duration: 0, useNativeDriver: true }),
        ]),
        Animated.sequence([
          Animated.timing(ring3, { toValue: 2.0, duration: 1400, easing: Easing.out(Easing.ease), useNativeDriver: true }),
          Animated.timing(ring3, { toValue: 1, duration: 0, useNativeDriver: true }),
        ]),
      ])).start();
      Animated.timing(glowAnim, { toValue: 0.8, duration: 400, useNativeDriver: true }).start();
      Animated.loop(Animated.sequence([
        Animated.timing(pulseAnim, { toValue: 1.08, duration: 500, useNativeDriver: true }),
        Animated.timing(pulseAnim, { toValue: 1, duration: 500, useNativeDriver: true }),
      ])).start();
    }

    if (state === 'processing') {
      // Spinning / contracting
      Animated.timing(glowAnim, { toValue: 0.5, duration: 300, useNativeDriver: true }).start();
      Animated.loop(Animated.sequence([
        Animated.timing(pulseAnim, { toValue: 0.92, duration: 600, easing: Easing.inOut(Easing.sin), useNativeDriver: true }),
        Animated.timing(pulseAnim, { toValue: 1.02, duration: 600, easing: Easing.inOut(Easing.sin), useNativeDriver: true }),
      ])).start();
    }

    if (state === 'speaking') {
      // Energetic pulsing
      Animated.timing(glowAnim, { toValue: 1, duration: 200, useNativeDriver: true }).start();
      Animated.loop(Animated.sequence([
        Animated.timing(pulseAnim, { toValue: 1.15, duration: 300, easing: Easing.out(Easing.ease), useNativeDriver: true }),
        Animated.timing(pulseAnim, { toValue: 0.95, duration: 300, easing: Easing.in(Easing.ease), useNativeDriver: true }),
        Animated.timing(pulseAnim, { toValue: 1.1, duration: 250, useNativeDriver: true }),
        Animated.timing(pulseAnim, { toValue: 1, duration: 250, useNativeDriver: true }),
      ])).start();
    }
  }, [state]);

  const orbSize = 180;
  const stateLabels: Record<VoiceState, { hi: string; en: string }> = {
    idle: { hi: 'टैप करें बोलने के लिए', en: 'Tap to speak' },
    listening: { hi: '🎤 सुन रहा हूँ...', en: '🎤 Listening...' },
    processing: { hi: '🧠 सोच रहा हूँ...', en: '🧠 Processing...' },
    speaking: { hi: '🔊 बोल रहा हूँ...', en: '🔊 Speaking...' },
  };

  const ringOpacity = ring1.interpolate({ inputRange: [1, 2], outputRange: [0.4, 0], extrapolate: 'clamp' });
  const ring2Opacity = ring2.interpolate({ inputRange: [1, 2], outputRange: [0.3, 0], extrapolate: 'clamp' });
  const ring3Opacity = ring3.interpolate({ inputRange: [1, 2], outputRange: [0.2, 0], extrapolate: 'clamp' });

  return (
    <View style={orb.container}>
      {/* Expanding rings (listening state) */}
      {state === 'listening' && (
        <>
          <Animated.View style={[orb.ring, { width: orbSize, height: orbSize, borderRadius: orbSize / 2, opacity: ringOpacity, transform: [{ scale: ring1 }] }]} />
          <Animated.View style={[orb.ring, { width: orbSize, height: orbSize, borderRadius: orbSize / 2, opacity: ring2Opacity, transform: [{ scale: ring2 }] }]} />
          <Animated.View style={[orb.ring, { width: orbSize, height: orbSize, borderRadius: orbSize / 2, opacity: ring3Opacity, transform: [{ scale: ring3 }] }]} />
        </>
      )}

      {/* Main orb */}
      <TouchableOpacity
        activeOpacity={0.8}
        onPress={state === 'listening' ? onStop : state === 'idle' ? onTap : undefined}
        disabled={state === 'processing' || state === 'speaking'}
      >
        <Animated.View style={[orb.orbOuter, {
          opacity: glowAnim,
          transform: [{ scale: state === 'idle' ? breathe : pulseAnim }],
        }]}>
          <View style={orb.orbInner}>
            {state === 'idle' && <Mic size={48} color={CYAN} />}
            {state === 'listening' && <View style={orb.listeningDot} />}
            {state === 'processing' && <ActivityIndicator size="large" color={CYAN} />}
            {state === 'speaking' && <Volume2 size={44} color={CYAN} />}
          </View>
        </Animated.View>
      </TouchableOpacity>

      {/* Status label */}
      <Text style={orb.stateText}>{stateLabels[state].en}</Text>

      {/* Stop button for listening */}
      {state === 'listening' && (
        <TouchableOpacity style={orb.stopBtn} onPress={onStop}>
          <Square size={16} color="#fff" fill="#fff" />
          <Text style={orb.stopText}>Stop</Text>
        </TouchableOpacity>
      )}
    </View>
  );
}

const orb = StyleSheet.create({
  container: { alignItems: 'center', justifyContent: 'center', height: H * 0.45, position: 'relative' },
  ring: { position: 'absolute', borderWidth: 1.5, borderColor: CYAN },
  orbOuter: {
    width: 180, height: 180, borderRadius: 90,
    backgroundColor: 'transparent',
    borderWidth: 2, borderColor: CYAN,
    alignItems: 'center', justifyContent: 'center',
    shadowColor: CYAN, shadowOffset: { width: 0, height: 0 }, shadowOpacity: 0.6, shadowRadius: 30,
    elevation: 15,
  },
  orbInner: {
    width: 150, height: 150, borderRadius: 75,
    backgroundColor: 'rgba(28, 192, 209, 0.06)',
    alignItems: 'center', justifyContent: 'center',
    borderWidth: 0.5, borderColor: 'rgba(28, 192, 209, 0.2)',
  },
  listeningDot: { width: 24, height: 24, borderRadius: 12, backgroundColor: '#ff3b30' },
  stateText: { marginTop: 20, fontSize: 15, color: 'rgba(255,255,255,0.5)', fontWeight: '500', letterSpacing: 0.5 },
  stopBtn: {
    flexDirection: 'row', alignItems: 'center', gap: 8,
    marginTop: 16, paddingVertical: 10, paddingHorizontal: 20,
    backgroundColor: 'rgba(255,59,48,0.15)', borderRadius: 20,
    borderWidth: 0.5, borderColor: 'rgba(255,59,48,0.3)',
  },
  stopText: { color: '#ff6b6b', fontSize: 14, fontWeight: '600' },
});


// ═══════════════════════════════════════════════
//  MAIN VOICE SCREEN
// ═══════════════════════════════════════════════
export default function VoiceScreen() {
  const { selectedLanguage } = useAppStore();
  const hi = selectedLanguage === 'hi';
  const lang = hi ? 'hi-IN' : 'en-IN';

  const [mode, setMode] = useState<'chat' | 'voice'>('voice'); // Start with voice orb
  const [voiceState, setVoiceState] = useState<VoiceState>('idle');
  const [msgs, setMsgs] = useState<Msg[]>([]);
  const [input, setInput] = useState('');
  const [sending, setSending] = useState(false);
  const scrollRef = useRef<ScrollView>(null);
  const recordingRef = useRef<Audio.Recording | null>(null);
  const soundRef = useRef<Audio.Sound | null>(null);

  useEffect(() => {
    setTimeout(() => scrollRef.current?.scrollToEnd({ animated: true }), 150);
  }, [msgs]);

  // ─── Text Message ───
  const sendText = async (text: string) => {
    if (!text.trim() || sending) return;
    setMsgs(p => [...p, { id: Date.now().toString(), role: 'user', text: text.trim() }]);
    setInput('');
    setSending(true);
    try {
      const r = await api.sendVoiceText(text.trim(), lang);
      const botText = r.response || r.response_text || (hi ? 'कोई जवाब नहीं' : 'No response');
      const botId = (Date.now() + 1).toString();
      setMsgs(p => [...p, { id: botId, role: 'bot', text: botText, hasAudio: !!r.audio }]);
      if (r.audio) await playBase64Audio(r.audio);
    } catch {
      setMsgs(p => [...p, { id: (Date.now() + 1).toString(), role: 'bot', text: hi ? '⚠️ त्रुटि हुई।' : '⚠️ Error occurred.' }]);
    } finally { setSending(false); }
  };

  // ─── Voice Recording ───
  const startRecording = async () => {
    try {
      if (soundRef.current) { await soundRef.current.stopAsync(); soundRef.current = null; }
      const perm = await Audio.requestPermissionsAsync();
      if (!perm.granted) return;
      await Audio.setAudioModeAsync({ allowsRecordingIOS: true, playsInSilentModeIOS: true });
      const { recording } = await Audio.Recording.createAsync(Audio.RecordingOptionsPresets.HIGH_QUALITY);
      recordingRef.current = recording;
      setVoiceState('listening');
    } catch (e) {
      console.error('[Voice] Start error:', e);
    }
  };

  const stopRecording = async () => {
    if (!recordingRef.current) return;
    setVoiceState('processing');

    try {
      await recordingRef.current.stopAndUnloadAsync();
      await Audio.setAudioModeAsync({ allowsRecordingIOS: false });
      const uri = recordingRef.current.getURI();
      recordingRef.current = null;
      if (!uri) { setVoiceState('idle'); return; }

      // Show user message
      const uid = Date.now().toString();
      setMsgs(p => [...p, { id: uid, role: 'user', text: hi ? '🎤 वॉइस...' : '🎤 Voice...' }]);

      // Send to backend → Sarvam STT → Groq → Sarvam TTS
      const r = await api.sendVoiceAudio(uri, lang);

      // Update user message with transcript
      if (r.query) {
        setMsgs(prev => {
          const copy = [...prev];
          const idx = copy.findIndex(m => m.id === uid);
          if (idx >= 0) copy[idx] = { ...copy[idx], text: `🎤 "${r.query}"` };
          return copy;
        });
      }

      // Bot response
      const botText = r.response || (hi ? 'कोई जवाब नहीं' : 'No response');
      setMsgs(p => [...p, { id: (Date.now() + 1).toString(), role: 'bot', text: botText, hasAudio: !!r.audio }]);

      // Play TTS
      if (r.audio) {
        setVoiceState('speaking');
        await playBase64Audio(r.audio);
      }
    } catch (e) {
      console.error('[Voice] Error:', e);
      setMsgs(p => [...p, { id: (Date.now() + 1).toString(), role: 'bot', text: hi ? '⚠️ वॉइस प्रोसेस नहीं हुआ।' : '⚠️ Voice processing failed.' }]);
    } finally {
      setTimeout(() => setVoiceState('idle'), 500);
    }
  };

  // ─── Audio Playback ───
  const playBase64Audio = async (base64Data: string) => {
    try {
      const clean = base64Data.replace(/^data:audio\/[^;]+;base64,/, '');
      const uri = `data:audio/mp3;base64,${clean}`;
      if (soundRef.current) { await soundRef.current.unloadAsync(); soundRef.current = null; }
      const { sound } = await Audio.Sound.createAsync({ uri }, { shouldPlay: true });
      soundRef.current = sound;
      sound.setOnPlaybackStatusUpdate((s: any) => {
        if (s.didJustFinish) {
          setVoiceState('idle');
          sound.unloadAsync();
          soundRef.current = null;
        }
      });
    } catch (e) {
      console.error('[Voice] Playback error:', e);
      setVoiceState('idle');
    }
  };

  // ═══════════════════════
  //  RENDER
  // ═══════════════════════
  return (
    <SafeAreaView style={s.container} edges={['top']}>
      {/* Header */}
      <View style={s.header}>
        <View style={s.avatar}><Bot size={18} color={CYAN} /></View>
        <View style={{ flex: 1 }}>
          <Text style={s.headerTitle}>{hi ? 'AI कृषि सहायक' : 'AI Farm Assistant'}</Text>
          <Text style={s.headerSub}>Sarvam AI + Groq</Text>
        </View>
        {/* Toggle mode */}
        <TouchableOpacity
          style={s.modeToggle}
          onPress={() => setMode(mode === 'voice' ? 'chat' : 'voice')}
        >
          {mode === 'voice'
            ? <MessageSquare size={18} color={C.muted} />
            : <Mic size={18} color={CYAN} />
          }
        </TouchableOpacity>
      </View>

      {mode === 'voice' ? (
        /* ═══ VOICE ORB MODE ═══ */
        <View style={s.voiceMode}>
          <VoiceOrb
            state={voiceState}
            onTap={startRecording}
            onStop={stopRecording}
          />

          {/* Last response preview */}
          {msgs.length > 0 && (
            <ScrollView style={s.transcript} contentContainerStyle={{ padding: 16 }}>
              {msgs.slice(-2).map(m => (
                <View key={m.id} style={[s.miniMsg, m.role === 'user' && s.miniUser]}>
                  <Text style={[s.miniText, m.role === 'user' && { color: '#000' }]} numberOfLines={3}>
                    {m.text}
                  </Text>
                </View>
              ))}
            </ScrollView>
          )}

          {/* Quick suggestions */}
          {msgs.length === 0 && voiceState === 'idle' && (
            <View style={s.quickWrap}>
              {(hi ? quick.hi : quick.en).map((q, i) => (
                <TouchableOpacity key={i} style={s.quickChip} onPress={() => { setMode('chat'); sendText(q); }}>
                  <Text style={s.quickText}>{q}</Text>
                </TouchableOpacity>
              ))}
            </View>
          )}
        </View>
      ) : (
        /* ═══ CHAT MODE ═══ */
        <>
          <ScrollView ref={scrollRef} style={s.chat} contentContainerStyle={s.chatContent}>
            {msgs.length === 0 && (
              <View style={s.emptyChat}>
                <Bot size={40} color="rgba(28,192,209,0.3)" />
                <Text style={s.emptyChatText}>{hi ? 'कुछ भी पूछें!' : 'Ask me anything!'}</Text>
              </View>
            )}
            {msgs.map(m => (
              <View key={m.id} style={[s.bubble, m.role === 'user' ? s.userBubble : s.botBubble]}>
                <Text style={[s.bubbleText, m.role === 'user' && { color: '#000' }]}>{m.text}</Text>
                {m.hasAudio && m.role === 'bot' && (
                  <View style={s.audioTag}>
                    <Volume2 size={12} color={CYAN} />
                    <Text style={s.audioTagText}>{hi ? 'ऑडियो' : 'Audio played'}</Text>
                  </View>
                )}
              </View>
            ))}
            {sending && (
              <View style={[s.bubble, s.botBubble, { flexDirection: 'row', gap: 8, alignItems: 'center' }]}>
                <ActivityIndicator size="small" color={CYAN} />
                <Text style={{ color: C.muted, fontSize: 14 }}>{hi ? 'प्रोसेस हो रहा...' : 'Processing...'}</Text>
              </View>
            )}
          </ScrollView>

          <KeyboardAvoidingView behavior={Platform.OS === 'ios' ? 'padding' : undefined}>
            <View style={s.inputBar}>
              <TextInput
                style={s.input}
                placeholder={hi ? 'टाइप करें...' : 'Type a message...'}
                placeholderTextColor="#555"
                value={input}
                onChangeText={setInput}
                onSubmitEditing={() => sendText(input)}
                returnKeyType="send"
                multiline
              />
              <TouchableOpacity
                style={[s.sendBtn, !input.trim() && s.sendBtnOff]}
                onPress={() => sendText(input)}
                disabled={sending || !input.trim()}
              >
                <Send size={16} color={input.trim() ? '#000' : '#555'} />
              </TouchableOpacity>
            </View>
          </KeyboardAvoidingView>
        </>
      )}
    </SafeAreaView>
  );
}

const s = StyleSheet.create({
  container: { flex: 1, backgroundColor: C.bg },

  header: { flexDirection: 'row', alignItems: 'center', gap: 12, paddingHorizontal: 20, paddingVertical: 12, borderBottomWidth: 0.5, borderBottomColor: C.border },
  avatar: { width: 36, height: 36, borderRadius: 18, backgroundColor: 'rgba(28,192,209,0.1)', alignItems: 'center', justifyContent: 'center' },
  headerTitle: { fontSize: 16, fontWeight: '600', color: C.white },
  headerSub: { fontSize: 10, color: C.muted, marginTop: 1, fontFamily: Platform.OS === 'ios' ? 'Menlo' : 'monospace' },
  modeToggle: { width: 36, height: 36, borderRadius: 18, backgroundColor: 'rgba(255,255,255,0.06)', alignItems: 'center', justifyContent: 'center' },

  // Voice mode
  voiceMode: { flex: 1, justifyContent: 'center' },
  transcript: { maxHeight: 120, marginHorizontal: 20, borderRadius: 16, backgroundColor: 'rgba(255,255,255,0.03)' },
  miniMsg: { padding: 10, borderRadius: 12, marginBottom: 6, backgroundColor: C.card },
  miniUser: { backgroundColor: G, alignSelf: 'flex-end' },
  miniText: { fontSize: 13, lineHeight: 18, color: '#d1d1d6' },

  quickWrap: { paddingHorizontal: 20, paddingBottom: 20, gap: 6 },
  quickChip: { backgroundColor: C.card, borderRadius: 12, padding: 14, borderWidth: 0.5, borderColor: C.border },
  quickText: { color: '#d1d1d6', fontSize: 14 },

  // Chat mode
  chat: { flex: 1, paddingHorizontal: 16 },
  chatContent: { paddingVertical: 16 },
  emptyChat: { alignItems: 'center', justifyContent: 'center', paddingTop: 80, gap: 12 },
  emptyChatText: { color: 'rgba(255,255,255,0.3)', fontSize: 16 },

  bubble: { maxWidth: '82%', borderRadius: 18, padding: 12, paddingHorizontal: 16, marginBottom: 8 },
  userBubble: { alignSelf: 'flex-end', backgroundColor: G, borderBottomRightRadius: 4 },
  botBubble: { alignSelf: 'flex-start', backgroundColor: C.card, borderBottomLeftRadius: 4, borderWidth: 0.5, borderColor: C.border },
  bubbleText: { fontSize: 15, lineHeight: 22, color: '#d1d1d6' },
  audioTag: { flexDirection: 'row', alignItems: 'center', gap: 4, marginTop: 6, paddingTop: 6, borderTopWidth: 0.5, borderTopColor: C.border },
  audioTagText: { fontSize: 11, color: CYAN },

  inputBar: { flexDirection: 'row', alignItems: 'flex-end', padding: 10, gap: 8, borderTopWidth: 0.5, borderTopColor: C.border },
  input: { flex: 1, backgroundColor: C.card, borderRadius: 22, paddingHorizontal: 16, paddingVertical: 10, color: C.white, fontSize: 15, maxHeight: 100, borderWidth: 0.5, borderColor: C.border },
  sendBtn: { width: 36, height: 36, borderRadius: 18, backgroundColor: G, alignItems: 'center', justifyContent: 'center' },
  sendBtnOff: { backgroundColor: '#1c1c1e' },
});
