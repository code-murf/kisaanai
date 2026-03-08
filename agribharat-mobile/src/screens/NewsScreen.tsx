import React, { useState, useEffect, useCallback } from 'react';
import {
  View, Text, StyleSheet, ScrollView, TouchableOpacity,
  Image, ActivityIndicator, RefreshControl, Dimensions, Linking, SafeAreaView
} from 'react-native';
import { ChevronRight, ExternalLink, Newspaper, TrendingUp, AlertCircle, CloudRain, ShieldAlert } from 'lucide-react-native';
import { useAppStore } from '../store/useAppStore';
import { api } from '../services/api';

const { width } = Dimensions.get('window');
const G = '#34c759';

export default function NewsScreen({ navigation }: any) {
  const { selectedLanguage } = useAppStore();
  const hi = selectedLanguage === 'hi';

  const [news, setNews] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState('');

  const load = useCallback(async (isRefresh = false) => {
    if (isRefresh) setRefreshing(true); else setLoading(true);
    setError('');
    try {
      const data = await api.getAxios().get('/news');
      setNews(data.data || []);
    } catch (e: any) {
      setError(hi ? 'समाचार लोड करने में विफल' : 'Failed to load news');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, [hi]);

  useEffect(() => { load(); }, []);

  const getCategoryIcon = (category: string) => {
    switch (category) {
      case 'Market Trend': return <TrendingUp color="#34c759" size={16} />;
      case 'Weather Alert': return <CloudRain color="#0a84ff" size={16} />;
      case 'Policy': return <ShieldAlert color="#ff9f0a" size={16} />;
      default: return <Newspaper color="#bf5af2" size={16} />;
    }
  };

  return (
    <SafeAreaView style={st.container}>
      <View style={st.header}>
        <Text style={st.brand}>{hi ? 'KisaanAI समाचार' : 'Agri News'}</Text>
        <Text style={st.tagline}>
          {hi ? 'बाज़ार, मौसम और नीतियाँ' : 'Market, Weather & Policies'}
        </Text>
      </View>

      <ScrollView 
        contentContainerStyle={st.scroll} 
        showsVerticalScrollIndicator={false}
        refreshControl={<RefreshControl refreshing={refreshing} onRefresh={() => load(true)} tintColor={G} />}
      >
        {error ? (
          <TouchableOpacity style={st.errorBox} onPress={() => load(true)}>
            <AlertCircle color="#ff3b30" size={32} style={{ marginBottom: 12 }} />
            <Text style={st.errorText}>{error}</Text>
            <Text style={st.errorRetry}>{hi ? 'रिफ्रेश करने के लिए टैप करें' : 'Tap to retry'}</Text>
          </TouchableOpacity>
        ) : loading && !refreshing ? (
          <View style={{ paddingVertical: 40, alignItems: 'center' }}>
            <ActivityIndicator color={G} size="large" />
          </View>
        ) : news.length === 0 ? (
          <View style={{ paddingVertical: 40, alignItems: 'center' }}>
            <Text style={{ color: '#8e8e93' }}>
              {hi ? 'अभी कोई ताज़ा खबर नहीं है।' : 'No recent news available.'}
            </Text>
          </View>
        ) : (
          <View style={st.grid}>
            {news.map((item, i) => (
              <TouchableOpacity key={i} style={st.card} activeOpacity={0.8}>
                <Image source={{ uri: item.image_url }} style={st.image} borderTopLeftRadius={16} borderTopRightRadius={16} />
                <View style={st.overlay} />
                <View style={st.categoryBadge}>
                  {getCategoryIcon(item.category)}
                  <Text style={st.categoryText}>{item.category}</Text>
                </View>
                
                <View style={st.content}>
                  <Text style={st.title} numberOfLines={2}>{item.title}</Text>
                  <Text style={st.excerpt} numberOfLines={3}>{item.excerpt}</Text>
                  
                  <View style={st.metaRow}>
                    <Text style={st.source}>{item.source}</Text>
                    <Text style={st.date}>{item.date.split('T')[0]}</Text>
                  </View>
                </View>
              </TouchableOpacity>
            ))}
          </View>
        )}
        <View style={{ height: 100 }} />
      </ScrollView>
    </SafeAreaView>
  );
}

const st = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#000' },
  header: { paddingHorizontal: 20, paddingTop: 12, paddingBottom: 16 },
  brand: { fontSize: 28, fontWeight: '800', color: '#fff', letterSpacing: -0.5 },
  tagline: { fontSize: 13, color: '#8e8e93', marginTop: 4 },
  scroll: { paddingHorizontal: 16, paddingTop: 8 },

  grid: { flexDirection: 'column', gap: 16 },
  card: { backgroundColor: '#111', borderRadius: 16, borderWidth: 0.5, borderColor: '#1c1c1e' },
  image: { width: '100%', height: 180 },
  overlay: { position: 'absolute', top: 0, left: 0, right: 0, height: 180, backgroundColor: 'rgba(0,0,0,0.3)', borderTopLeftRadius: 16, borderTopRightRadius: 16 },
  
  categoryBadge: { position: 'absolute', top: 12, left: 12, flexDirection: 'row', alignItems: 'center', gap: 6, backgroundColor: 'rgba(0,0,0,0.6)', paddingHorizontal: 10, paddingVertical: 6, borderRadius: 20 },
  categoryText: { color: '#fff', fontSize: 11, fontWeight: '600', textTransform: 'uppercase', letterSpacing: 0.5 },

  content: { padding: 16 },
  title: { fontSize: 17, fontWeight: '700', color: '#fff', marginBottom: 8, lineHeight: 22 },
  excerpt: { fontSize: 13, color: '#a1a1aa', lineHeight: 20, marginBottom: 16 },

  metaRow: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', paddingTop: 12, borderTopWidth: 0.5, borderTopColor: '#1c1c1e' },
  source: { fontSize: 11, color: '#34c759', fontWeight: '600' },
  date: { fontSize: 11, color: '#636366' },

  errorBox: { alignItems: 'center', justifyContent: 'center', padding: 30, backgroundColor: '#111', borderRadius: 16, borderWidth: 1, borderColor: '#3a1c1c', marginTop: 20 },
  errorText: { color: '#ff3b30', fontSize: 16, fontWeight: '600', textAlign: 'center', marginBottom: 4 },
  errorRetry: { color: '#8e8e93', fontSize: 13 },
});
