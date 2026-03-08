import React, { useState, useEffect, useCallback, useRef } from 'react';
import {
  View, Text, StyleSheet, ScrollView, TouchableOpacity,
  Dimensions, ActivityIndicator, RefreshControl, StatusBar,
  Animated, Easing,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { LinearGradient } from 'expo-linear-gradient';
import {
  ChevronRight, MapPin, BarChart3, Mic, CloudSun,
  Newspaper, Users, Thermometer, Droplets,
  Sun, Cloud, CloudRain, Stethoscope,
} from 'lucide-react-native';
import { useAppStore } from '../store/useAppStore';
import { api } from '../services/api';

const { width: W } = Dimensions.get('window');

// ── Web colors (dark mode: neutral-950 base) ──
const BG = '#0a0a0a';          // neutral-950
const CARD = '#171717';         // neutral-900
const BORDER = '#262626';       // neutral-800
const MUTED = '#a3a3a3';        // neutral-400
const GREEN = '#34d399';        // emerald-400
const INDIGO = '#818cf8';       // indigo-400
const ROSE = '#fb7185';         // rose-400

function WeatherIcon({ condition, sz = 20 }: { condition: string; sz?: number }) {
  const c = (condition || '').toLowerCase();
  if (c.includes('sun') || c.includes('clear')) return <Sun size={sz} color="#f59e0b" />;
  if (c.includes('rain')) return <CloudRain size={sz} color="#3b82f6" />;
  return <Cloud size={sz} color="#9ca3af" />;
}

export default function HomeScreen({ navigation }: any) {
  const { selectedLanguage } = useAppStore();
  const hi = selectedLanguage === 'hi';

  const tickerAnim = useRef(new Animated.Value(0)).current;

  const [stats, setStats] = useState<any>(null);
  const [gainers, setGainers] = useState<any[] | null>(null);
  const [losers, setLosers] = useState<any[] | null>(null);
  const [weather, setWeather] = useState<any[] | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState('');

  // Match web's MagicDashboard data fetching exactly
  const load = useCallback(async (isRefresh = false) => {
    if (isRefresh) setRefreshing(true); else setLoading(true);
    setError('');
    try {
      const [statsR, gainersR, losersR, weatherR] = await Promise.allSettled([
        api.getStats(),
        api.getGainers(4),
        api.getLosers(4),
        api.getWeather(),
      ]);
      if (statsR.status === 'fulfilled') setStats(statsR.value);
      if (gainersR.status === 'fulfilled') setGainers(gainersR.value);
      if (losersR.status === 'fulfilled') setLosers(losersR.value);
      if (weatherR.status === 'fulfilled') setWeather(weatherR.value);

      const none = [statsR, gainersR, losersR, weatherR].every(r => r.status === 'rejected');
      if (none) setError(hi ? 'सर्वर से कनेक्ट नहीं हो पाया' : 'Could not connect to server');
    } catch {
      setError(hi ? 'नेटवर्क त्रुटि' : 'Network Error');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, [hi]);

  useEffect(() => { load(); }, [load]);

  // Ticker animation
  useEffect(() => {
    if (!gainers?.length && !losers?.length) return;
    const loop = Animated.loop(
      Animated.timing(tickerAnim, { toValue: 1, duration: 25000, easing: Easing.linear, useNativeDriver: true }),
    );
    loop.start();
    return () => loop.stop();
  }, [tickerAnim, gainers, losers]);

  const ticks = [
    ...(gainers || []).map(g => ({
      name: g.commodity_name || g.name || 'Crop',
      price: `₹${Math.round(g.current_price || g.avg_price || 0).toLocaleString()}/q`,
      change: `+${(g.change_pct || 0).toFixed(1)}%`,
      up: true,
    })),
    ...(losers || []).map(l => ({
      name: l.commodity_name || l.name || 'Crop',
      price: `₹${Math.round(l.current_price || l.avg_price || 0).toLocaleString()}/q`,
      change: `${(l.change_pct || 0).toFixed(1)}%`,
      up: false,
    })),
  ];
  const tw = ticks.length * 140;
  const tickerX = tickerAnim.interpolate({ inputRange: [0, 1], outputRange: [W, -tw] });

  // BentoCard features — matches web's exact feature list
  const features = [
    { icon: <MapPin size={20} color={GREEN} />,       label: hi ? 'मंडी खोजें' : 'Find Mandi',       screen: 'Mandi',     desc: hi ? 'नजदीकी मंडी के भाव' : 'Nearby mandi prices' },
    { icon: <BarChart3 size={20} color={INDIGO} />,   label: hi ? 'भाव चार्ट' : 'Price Forecast',     screen: 'Charts',    desc: hi ? 'AI भविष्यवाणी' : 'AI Predictions' },
    { icon: <Mic size={20} color={ROSE} />,           label: hi ? 'वॉइस AI' : 'Voice Assistant',      screen: 'Voice',     desc: hi ? 'बोलकर पूछें' : 'Ask by speaking' },
    { icon: <Stethoscope size={20} color="#fbbf24" />, label: hi ? 'फसल डॉक्टर' : 'Crop Doctor',      screen: 'Doctor',    desc: hi ? 'बीमारी का पता' : 'Disease diagnosis' },
    { icon: <Newspaper size={20} color="#38bdf8" />,  label: hi ? 'समाचार' : 'News Alerts',            screen: 'News',      desc: hi ? 'कृषि अपडेट' : 'Agriculture updates' },
    { icon: <Users size={20} color="#c084fc" />,      label: hi ? 'समुदाय' : 'Community',              screen: 'Community', desc: hi ? 'किसानों से जुड़ें' : 'Connect with farmers' },
  ];

  return (
    <View style={st.root}>
      <StatusBar barStyle="light-content" backgroundColor={BG} translucent={false} />
      <SafeAreaView style={st.safe} edges={['top']}>
        <ScrollView
          showsVerticalScrollIndicator={false}
          contentContainerStyle={st.scroll}
          refreshControl={<RefreshControl refreshing={refreshing} onRefresh={() => load(true)} tintColor={GREEN} colors={[GREEN]} />}
        >
          {/* ═══ Hero — matches web's hero section ═══ */}
          <View style={st.hero}>
            <View style={st.badge}>
              <Text style={st.badgeText}>{hi ? '🌾 भारतीय किसानों का AI प्लेटफ़ॉर्म' : '🌾 AI Platform for Indian Farmers'}</Text>
            </View>
            <Text style={st.heroTitle}>
              KisaanAI <Text style={st.heroGreen}>{hi ? 'भविष्य की खेती' : 'Future of Farming'}</Text>
            </Text>
            <Text style={st.heroSub}>
              {hi ? 'लाइव मंडी भाव · AI भविष्यवाणी · वॉइस सहायक' : 'Live Mandi Prices · AI Predictions · Voice Assistant'}
            </Text>
          </View>

          {/* ═══ Error ═══ */}
          {error ? (
            <TouchableOpacity style={st.errorBox} onPress={() => load(true)} activeOpacity={0.7}>
              <Text style={st.errorText}>⚠️ {error} — {hi ? 'टैप करें' : 'Tap to retry'}</Text>
            </TouchableOpacity>
          ) : null}

          {/* ═══ Stats — matches web's 3-column grid ═══ */}
          {loading && !stats ? (
            <View style={st.statsRow}>
              {[1, 2, 3].map(i => <View key={i} style={st.statCard}><ActivityIndicator color={GREEN} /></View>)}
            </View>
          ) : stats && (stats.totalMandis > 0 || stats.totalCommodities > 0 || stats.totalStates > 0) ? (
            <View style={st.statsRow}>
              <View style={[st.statCard, { borderColor: '#064e3b50' }]}>
                <Text style={[st.statVal, { color: GREEN }]}>{stats.totalMandis}</Text>
                <Text style={st.statLbl}>{hi ? 'मंडियाँ' : 'Mandis Tracked'}</Text>
              </View>
              <View style={[st.statCard, { borderColor: '#312e8150' }]}>
                <Text style={[st.statVal, { color: INDIGO }]}>{stats.totalCommodities}</Text>
                <Text style={st.statLbl}>{hi ? 'फसलें' : 'Commodities'}</Text>
              </View>
              <View style={[st.statCard, { borderColor: '#4c051950' }]}>
                <Text style={[st.statVal, { color: ROSE }]}>{stats.totalStates}</Text>
                <Text style={st.statLbl}>{hi ? 'राज्य' : 'States Covered'}</Text>
              </View>
            </View>
          ) : null}

          {/* ═══ Weather — matches web's ShineBorder weather widget ═══ */}
          {loading && !weather ? (
            <View style={st.weatherBox}>
              <ActivityIndicator color="#38bdf8" />
              <Text style={st.loadText}>{hi ? 'मौसम लोड हो रहा...' : 'Loading weather...'}</Text>
            </View>
          ) : weather && weather.length > 0 ? (
            <View style={st.weatherBox}>
              <View style={st.weatherHead}>
                <View style={st.weatherIconBox}><CloudSun size={16} color="#38bdf8" /></View>
                <Text style={st.sectionLabel}>{hi ? 'मौसम पूर्वानुमान' : 'Weather Forecast'}</Text>
              </View>
              <View style={st.weatherGrid}>
                {weather.map((d: any, i: number) => (
                  <View key={i} style={st.weatherDay}>
                    <Text style={st.wDate}>
                      {new Date(d.date).toLocaleDateString(hi ? 'hi-IN' : 'en-US', { weekday: 'short', day: 'numeric' })}
                    </Text>
                    <WeatherIcon condition={d.condition} sz={22} />
                    <View style={st.wRow}>
                      <Thermometer size={12} color="#ef4444" />
                      <Text style={st.wHigh}>{Math.round(d.temp_max)}°</Text>
                      <Text style={st.wLow}>/{Math.round(d.temp_min)}°</Text>
                    </View>
                    <View style={st.wRow}>
                      <Droplets size={12} color="#3b82f6" />
                      <Text style={st.wHum}>{d.humidity_pct}%</Text>
                    </View>
                  </View>
                ))}
              </View>
            </View>
          ) : null}

          {/* ═══ BentoGrid — matches web's feature cards ═══ */}
          <View style={st.bentoGrid}>
            {features.map((f, i) => (
              <TouchableOpacity
                key={i}
                style={st.bentoCard}
                onPress={() => navigation.navigate(f.screen)}
                activeOpacity={0.7}
              >
                <View style={st.bentoIconBox}>{f.icon}</View>
                <Text style={st.bentoName}>{f.label}</Text>
                <Text style={st.bentoDesc}>{f.desc}</Text>
                <ChevronRight size={14} color={MUTED} style={{ position: 'absolute', right: 14, top: 14 }} />
              </TouchableOpacity>
            ))}
          </View>

          {/* ═══ Marquee Ticker — matches web's price marquee ═══ */}
          {ticks.length > 0 && (
            <View style={st.marqueeBox}>
              <Animated.View style={[st.marqueeTrack, { transform: [{ translateX: tickerX }] }]}>
                {[...ticks, ...ticks].map((t, i) => (
                  <View key={i} style={st.marqueeItem}>
                    <Text style={st.mqName}>{t.name}</Text>
                    <Text style={st.mqPrice}>{t.price}</Text>
                    <View style={[st.mqBadge, { backgroundColor: t.up ? '#052e1680' : '#4c051980' }]}>
                      <Text style={[st.mqChange, { color: t.up ? GREEN : ROSE }]}>{t.change}</Text>
                    </View>
                  </View>
                ))}
              </Animated.View>
            </View>
          )}

          {/* ═══ Global Loading ═══ */}
          {loading && !stats && !gainers && !weather && (
            <View style={st.globalLoad}>
              <ActivityIndicator size="large" color={GREEN} />
              <Text style={st.globalText}>{hi ? 'सर्वर से कनेक्ट हो रहा...' : 'Connecting to server...'}</Text>
              <Text style={st.globalSub}>{hi ? 'पहली बार 15-30 सेकंड लग सकते हैं' : 'First request may take 15-30s'}</Text>
            </View>
          )}

          <View style={{ height: 90 }} />
        </ScrollView>
      </SafeAreaView>
    </View>
  );
}

const st = StyleSheet.create({
  root: { flex: 1, backgroundColor: BG },
  safe: { flex: 1 },
  scroll: { padding: 20 },

  // Hero
  hero: { alignItems: 'center', paddingVertical: 28, paddingHorizontal: 8, marginBottom: 16, borderRadius: 16, borderWidth: 1, borderColor: BORDER, backgroundColor: CARD },
  badge: { paddingHorizontal: 16, paddingVertical: 6, borderRadius: 20, borderWidth: 1, borderColor: '#065f4650', backgroundColor: '#0a0a0a', marginBottom: 14 },
  badgeText: { fontSize: 12, color: MUTED, fontWeight: '500' },
  heroTitle: { fontSize: 32, fontWeight: '900', color: '#fff', textAlign: 'center', letterSpacing: -0.5 },
  heroGreen: { color: GREEN },
  heroSub: { fontSize: 14, color: MUTED, textAlign: 'center', marginTop: 8, lineHeight: 20 },

  // Error
  errorBox: { borderRadius: 12, padding: 14, borderWidth: 1, borderColor: '#7f1d1d', backgroundColor: '#1c1917', marginBottom: 16 },
  errorText: { color: ROSE, fontSize: 13, fontWeight: '600', textAlign: 'center' },

  // Stats — 3-column matching web
  statsRow: { flexDirection: 'row', gap: 8, marginBottom: 16 },
  statCard: { flex: 1, borderRadius: 14, padding: 16, alignItems: 'center', borderWidth: 1, backgroundColor: CARD, minHeight: 80, justifyContent: 'center' },
  statVal: { fontSize: 28, fontWeight: '800' },
  statLbl: { fontSize: 11, color: MUTED, fontWeight: '500', marginTop: 4, textAlign: 'center' },

  // Weather
  weatherBox: { borderRadius: 16, padding: 16, borderWidth: 1, borderColor: BORDER, backgroundColor: CARD, marginBottom: 16, alignItems: 'center', minHeight: 60 },
  weatherHead: { flexDirection: 'row', alignItems: 'center', gap: 8, marginBottom: 14, alignSelf: 'flex-start' },
  weatherIconBox: { width: 32, height: 32, borderRadius: 8, backgroundColor: '#0c4a6e40', alignItems: 'center', justifyContent: 'center' },
  sectionLabel: { fontSize: 15, fontWeight: '700', color: '#fff' },
  weatherGrid: { flexDirection: 'row', gap: 8, width: '100%' },
  weatherDay: { flex: 1, alignItems: 'center', gap: 5, padding: 12, borderRadius: 12, backgroundColor: '#0a0a0a80', borderWidth: 1, borderColor: BORDER },
  wDate: { fontSize: 10, color: MUTED, fontWeight: '600' },
  wRow: { flexDirection: 'row', alignItems: 'center', gap: 3 },
  wHigh: { fontSize: 14, fontWeight: '800', color: '#fff' },
  wLow: { fontSize: 11, color: MUTED },
  wHum: { fontSize: 11, color: MUTED },
  loadText: { fontSize: 12, color: MUTED, marginTop: 6 },

  // BentoGrid
  bentoGrid: { flexDirection: 'row', flexWrap: 'wrap', gap: 10, marginBottom: 16 },
  bentoCard: { width: (W - 50) / 2, borderRadius: 14, padding: 16, borderWidth: 1, borderColor: BORDER, backgroundColor: CARD, minHeight: 100 },
  bentoIconBox: { width: 38, height: 38, borderRadius: 10, backgroundColor: '#26262680', alignItems: 'center', justifyContent: 'center', marginBottom: 10 },
  bentoName: { fontSize: 14, fontWeight: '700', color: '#fff', marginBottom: 2 },
  bentoDesc: { fontSize: 11, color: MUTED },

  // Marquee
  marqueeBox: { borderRadius: 16, overflow: 'hidden', height: 80, borderWidth: 1, borderColor: BORDER, backgroundColor: CARD, marginBottom: 16 },
  marqueeTrack: { flexDirection: 'row', alignItems: 'center', height: 80 },
  marqueeItem: { alignItems: 'center', width: 130, paddingHorizontal: 8 },
  mqName: { fontSize: 11, color: MUTED, fontWeight: '600' },
  mqPrice: { fontSize: 16, fontWeight: '800', color: '#fff', marginVertical: 2 },
  mqBadge: { paddingHorizontal: 8, paddingVertical: 2, borderRadius: 10 },
  mqChange: { fontSize: 11, fontWeight: '700' },

  // Loading
  globalLoad: { alignItems: 'center', paddingVertical: 50, gap: 10 },
  globalText: { color: '#fff', fontSize: 15, fontWeight: '600' },
  globalSub: { color: MUTED, fontSize: 12 },
});
