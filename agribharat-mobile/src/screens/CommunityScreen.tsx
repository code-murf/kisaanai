import React, { useState, useEffect, useCallback, useRef } from 'react';
import {
  View, Text, StyleSheet, ScrollView, TouchableOpacity,
  ActivityIndicator, RefreshControl, Dimensions, Alert
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Audio } from 'expo-av';
import { Users, Mic, Square, Play, Pause, Send, Heart, MapPin, ChevronLeft } from 'lucide-react-native';
import { useAppStore } from '../store/useAppStore';
import { api } from '../services/api';

const { width } = Dimensions.get('window');
const BLUE = '#0a84ff';
const PURPLE = '#bf5af2';

export default function CommunityScreen({ navigation }: any) {
  const { selectedLanguage } = useAppStore();
  const hi = selectedLanguage === 'hi';

  const [notes, setNotes] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [recording, setRecording] = useState<Audio.Recording | null>(null);
  const [audioUri, setAudioUri] = useState<string | null>(null);
  const [uploading, setUploading] = useState(false);
  
  const [playingId, setPlayingId] = useState<string | null>(null);
  const soundRef = useRef<Audio.Sound | null>(null);

  const load = useCallback(async (isRefresh = false) => {
    if (isRefresh) setRefreshing(true); else setLoading(true);
    try {
      const data = await api.getCommunityNotes();
      setNotes(data || []);
    } catch (e) {
      console.warn("Error loading community notes", e);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  useEffect(() => {
    load();
    return () => {
      if (soundRef.current) soundRef.current.unloadAsync();
    };
  }, []);

  const startRecording = async () => {
    try {
      await Audio.requestPermissionsAsync();
      await Audio.setAudioModeAsync({ allowsRecordingIOS: true, playsInSilentModeIOS: true });
      const { recording } = await Audio.Recording.createAsync(Audio.RecordingOptionsPresets.HIGH_QUALITY);
      setRecording(recording);
      setAudioUri(null);
    } catch (err) {
      console.error('Failed to start recording', err);
    }
  };

  const stopRecording = async () => {
    setLoading(true);
    try {
      if (!recording) return;
      await recording.stopAndUnloadAsync();
      const uri = recording.getURI();
      setAudioUri(uri);
      setRecording(null);
    } catch (error) {
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  const handlePublish = async () => {
    if (!audioUri) return;
    setUploading(true);
    
    try {
      const formData = new FormData();
      formData.append('audio', { uri: audioUri, type: 'audio/m4a', name: 'voice_note.m4a' } as any);
      formData.append('user_id', 'mobile-user-123');
      formData.append('user_name', 'Mobile Farmer');
      formData.append('location_lat', '22.7196');
      formData.append('location_lng', '75.8577');
      formData.append('tags', JSON.stringify(['Mobile App']));

      await api.postCommunityNote(formData);

      setAudioUri(null);
      await load(true);
      Alert.alert(hi ? 'सफल' : 'Success', hi ? 'आपका वॉयस नोट पोस्ट हो गया।' : 'Your voice note was published.');
    } catch (error) {
      Alert.alert('Error', 'Could not publish note.');
    } finally {
      setUploading(false);
    }
  };

  const togglePlay = async (id: string, url: string, isPreview = false) => {
    if (playingId === id) {
      await soundRef.current?.pauseAsync();
      setPlayingId(null);
      return;
    }

    try {
      if (soundRef.current) await soundRef.current.unloadAsync();
      const { sound } = await Audio.Sound.createAsync(
        isPreview ? { uri: url } : { uri: `https://kisaanai-backend.onrender.com${url}` }
      );
      soundRef.current = sound;
      
      sound.setOnPlaybackStatusUpdate((status) => {
        if (status.isLoaded && status.didJustFinish) setPlayingId(null);
      });

      await sound.playAsync();
      setPlayingId(id);
    } catch (e) {
      console.error("Playback failed", e);
    }
  };

  return (
    <SafeAreaView style={st.container} edges={['top']}>
      <View style={st.header}>
        <TouchableOpacity style={st.backBtn} onPress={() => navigation.goBack()}>
          <ChevronLeft color="#fff" size={24} />
        </TouchableOpacity>
        <View style={st.headerTextContainer}>
          <Text style={st.brand}>{hi ? 'KisaanAI समुदाय' : 'Community'}</Text>
          <Text style={st.tagline}>{hi ? 'किसानों की आवाज़' : 'Farmer Voice Forum'}</Text>
        </View>
        <View style={{ width: 40 }} />
      </View>

      <ScrollView 
        contentContainerStyle={st.scroll} 
        showsVerticalScrollIndicator={false}
        refreshControl={<RefreshControl refreshing={refreshing} onRefresh={() => load(true)} tintColor={PURPLE} />}
      >
        {/* Record Section */}
        <View style={st.recordCard}>
          <Text style={st.recordTitle}>{audioUri ? (hi ? 'वॉयस नोट भेजें' : 'Review Note') : (hi ? 'अपनी बात कहें' : 'Record a Note')}</Text>
          
          {!audioUri ? (
            <View style={st.recordControls}>
              <TouchableOpacity 
                style={[st.micBtn, recording && st.micBtnActive]} 
                onPress={recording ? stopRecording : startRecording}
              >
                {recording ? <Square color="#fff" size={32} fill="#fff" /> : <Mic color="#fff" size={32} />}
              </TouchableOpacity>
              <Text style={[st.recordHint, recording && { color: '#ff3b30' }]}>
                {recording ? (hi ? 'रिकॉर्ड हो रहा है... रोकने के लिए टैप करें' : 'Recording... Tap to stop') : (hi ? 'रिकॉर्डिंग शुरू करने के लिए टैप करें' : 'Tap mic to start recording')}
              </Text>
            </View>
          ) : (
            <View style={st.previewControls}>
              <View style={st.playerBox}>
                <TouchableOpacity onPress={() => togglePlay('preview', audioUri, true)} style={st.playBtn}>
                  {playingId === 'preview' ? <Pause color="#fff" size={16} /> : <Play color="#fff" size={16} fill="#fff" />}
                </TouchableOpacity>
                <View style={st.waveform}>
                  {Array.from({length: 20}).map((_, i) => (
                    <View key={i} style={[st.waveBar, { height: Math.max(8, Math.random() * 24) }]} />
                  ))}
                </View>
              </View>

              <View style={st.actionRow}>
                <TouchableOpacity style={st.btnSecondary} onPress={() => setAudioUri(null)} disabled={uploading}>
                  <Text style={st.btnText}>{hi ? 'हटाएं' : 'Delete'}</Text>
                </TouchableOpacity>
                <TouchableOpacity style={st.btnPrimary} onPress={handlePublish} disabled={uploading}>
                  {uploading ? <ActivityIndicator size="small" color="#fff" /> : <Send color="#fff" size={16} />}
                  <Text style={st.btnPrimaryText}>{hi ? 'पोस्ट करें' : 'Publish'}</Text>
                </TouchableOpacity>
              </View>
            </View>
          )}
        </View>

        {/* Feed */}
        <Text style={st.feedTitle}>{hi ? 'आस-पास के किसानों से सुनें' : 'Recent Notes from Farmers'}</Text>
        
        {loading && !refreshing ? (
          <ActivityIndicator color={PURPLE} size="large" style={{ marginTop: 40 }} />
        ) : notes.length === 0 ? (
          <Text style={st.emptyFeedback}>{hi ? 'अभी कोई वॉयस नोट नहीं है।' : 'No voice notes yet. Be the first!'}</Text>
        ) : (
          <View style={st.feed}>
            {notes.map((note) => (
              <View key={note.id} style={st.noteCard}>
                <View style={st.noteHeader}>
                  <View style={st.avatar}>
                    <Text style={st.avatarText}>{note.user_name.charAt(0)}</Text>
                  </View>
                  <View style={st.noteMeta}>
                    <Text style={st.noteUser}>{note.user_name}</Text>
                    <View style={st.metaRow}>
                      <MapPin color="#8e8e93" size={10} />
                      <Text style={st.metaText}>{note.location_lat.toFixed(1)}, {note.location_lng.toFixed(1)}</Text>
                      <Text style={st.metaText}> • </Text>
                      <Text style={st.metaText}>{new Date(note.created_at).toLocaleDateString()}</Text>
                    </View>
                  </View>
                </View>
                
                {note.tags && note.tags.length > 0 && (
                  <View style={st.tagsRow}>
                    {note.tags.map((t: string) => (
                      <View key={t} style={st.tag}>
                        <Text style={st.tagText}>{t}</Text>
                      </View>
                    ))}
                  </View>
                )}

                <View style={st.playerBox}>
                  <TouchableOpacity onPress={() => togglePlay(note.id, note.audio_url)} style={st.playBtn}>
                    {playingId === note.id ? <Pause color="#fff" size={16} /> : <Play color="#fff" size={16} fill="#fff" />}
                  </TouchableOpacity>
                  <View style={st.waveform}>
                    {Array.from({length: 30}).map((_, i) => (
                      <View key={i} style={[st.waveBar, { height: Math.max(4, Math.random() * 20), backgroundColor: playingId === note.id ? BLUE : '#333' }]} />
                    ))}
                  </View>
                </View>

                <View style={st.actions}>
                  <TouchableOpacity style={st.likeBtn}>
                    <Heart color={note.likes > 0 ? '#ff3b30' : '#8e8e93'} size={16} fill={note.likes > 0 ? '#ff3b30' : 'transparent'} />
                    <Text style={[st.likeText, note.likes > 0 && { color: '#ff3b30' }]}>{note.likes || 'Like'}</Text>
                  </TouchableOpacity>
                </View>
              </View>
            ))}
          </View>
        )}
        <View style={{ height: 100 }} />
      </ScrollView>
    </SafeAreaView>
  );
}

const st = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#0a0a0a' },
  header: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', paddingHorizontal: 16, paddingVertical: 12, borderBottomWidth: 0.5, borderBottomColor: '#1c1c1e' },
  backBtn: { padding: 8, marginLeft: -8, width: 40 },
  headerTextContainer: { alignItems: 'center' },
  brand: { fontSize: 20, fontWeight: '800', color: '#fff' },
  tagline: { fontSize: 11, color: '#8e8e93', marginTop: 2 },
  scroll: { paddingHorizontal: 16, paddingTop: 16 },

  recordCard: { backgroundColor: '#111', borderRadius: 20, padding: 20, borderWidth: 1, borderColor: '#1c1c1e', alignItems: 'center', marginBottom: 24 },
  recordTitle: { color: '#fff', fontSize: 16, fontWeight: '700', marginBottom: 20 },
  recordControls: { alignItems: 'center' },
  micBtn: { width: 80, height: 80, borderRadius: 40, backgroundColor: BLUE, justifyContent: 'center', alignItems: 'center', shadowColor: BLUE, shadowOffset: { width: 0, height: 4 }, shadowOpacity: 0.3, shadowRadius: 8 },
  micBtnActive: { backgroundColor: '#ff3b30', shadowColor: '#ff3b30' },
  recordHint: { color: '#8e8e93', fontSize: 13, marginTop: 16, fontWeight: '500' },

  previewControls: { width: '100%', gap: 16 },
  playerBox: { flexDirection: 'row', alignItems: 'center', backgroundColor: '#1a1a1c', padding: 12, borderRadius: 12, gap: 12, borderWidth: 0.5, borderColor: '#2c2c2e' },
  playBtn: { width: 40, height: 40, borderRadius: 20, backgroundColor: '#333', justifyContent: 'center', alignItems: 'center' },
  waveform: { flex: 1, flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between', height: 24 },
  waveBar: { width: 3, backgroundColor: '#555', borderRadius: 2 },
  
  actionRow: { flexDirection: 'row', gap: 12 },
  btnSecondary: { flex: 1, paddingVertical: 14, backgroundColor: '#1c1c1e', borderRadius: 12, alignItems: 'center' },
  btnText: { color: '#fff', fontSize: 15, fontWeight: '600' },
  btnPrimary: { flex: 1, flexDirection: 'row', paddingVertical: 14, backgroundColor: BLUE, borderRadius: 12, alignItems: 'center', justifyContent: 'center', gap: 8 },
  btnPrimaryText: { color: '#fff', fontSize: 15, fontWeight: '600' },

  feedTitle: { color: '#fff', fontSize: 18, fontWeight: '800', marginBottom: 16 },
  emptyFeedback: { color: '#8e8e93', textAlign: 'center', marginTop: 40, fontSize: 14 },
  feed: { gap: 16 },
  noteCard: { backgroundColor: '#111', borderRadius: 16, padding: 16, borderWidth: 0.5, borderColor: '#1c1c1e' },
  noteHeader: { flexDirection: 'row', alignItems: 'center', gap: 12, marginBottom: 12 },
  avatar: { width: 40, height: 40, borderRadius: 20, backgroundColor: PURPLE, justifyContent: 'center', alignItems: 'center' },
  avatarText: { color: '#fff', fontWeight: '800', fontSize: 18 },
  noteMeta: { flex: 1 },
  noteUser: { color: '#fff', fontSize: 15, fontWeight: '700', marginBottom: 2 },
  metaRow: { flexDirection: 'row', alignItems: 'center', gap: 4 },
  metaText: { color: '#8e8e93', fontSize: 11 },

  tagsRow: { flexDirection: 'row', gap: 8, marginBottom: 12 },
  tag: { backgroundColor: 'rgba(10,132,255,0.15)', paddingHorizontal: 10, paddingVertical: 4, borderRadius: 8 },
  tagText: { color: BLUE, fontSize: 11, fontWeight: '600' },

  actions: { flexDirection: 'row', marginTop: 16, paddingTop: 16, borderTopWidth: 0.5, borderTopColor: '#1c1c1e' },
  likeBtn: { flexDirection: 'row', alignItems: 'center', gap: 6 },
  likeText: { color: '#8e8e93', fontSize: 13, fontWeight: '600' }
});
