import React, { useState, useEffect, useCallback, useRef } from 'react';
import {
  View, Text, StyleSheet, ScrollView, TouchableOpacity,
  Dimensions, ActivityIndicator, RefreshControl, StatusBar,
  Animated, Easing,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Video, ResizeMode } from 'expo-av';
import { LinearGradient } from 'expo-linear-gradient';
import {
  ChevronRight, ArrowUpRight, ArrowDownRight, ExternalLink,
} from 'lucide-react-native';
import { useAppStore } from '../store/useAppStore';
import { api } from '../services/api';

const { width } = Dimensions.get('window');
const G = '#34c759';
const R = '#ff3b30';
const CYAN = '#1CC0D1';

export default function HomeScreen({ navigation }: any) {
  const { selectedLanguage } = useAppStore();
  const hi = selectedLanguage === 'hi';

  const videoRef = useRef<any>(null);
  const floatAnim = useRef(new Animated.Value(0)).current;
  const pulseAnim = useRef(new Animated.Value(0)).current;
  const shimmerAnim = useRef(new Animated.Value(0)).current;

  const [stats, setStats] = useState<any>({});
  const [liveData, setLiveData] = useState<any[]>([]);
  const [liveTotal, setLiveTotal] = useState(0);
  const [gainers, setGainers] = useState<any[]>([]);
  const [losers, setLosers] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState('');

  const load = useCallback(async (isRefresh = false) => {
    if (isRefresh) setRefreshing(true); else setLoading(true);
    setError('');
    try {
      const [s, live, gl] = await Promise.all([
        api.getDashboardStats(),
        api.getLivePrices({ limit: 20 }),
        api.getGainersLosers(),
      ]);
      setStats(s);
      setLiveData(live?.records || []);
      setLiveTotal(live?.total || 0);
      setGainers(gl?.gainers?.slice(0, 4) || []);
      setLosers(gl?.losers?.slice(0, 4) || []);
    } catch (e: any) {
      setError(hi ? 'नेटवर्क त्रुटि' : 'Network Error');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, [hi]);

  useEffect(() => {
    load();
  }, [load]);

  useEffect(() => {
    const floatLoop = Animated.loop(
      Animated.sequence([
        Animated.timing(floatAnim, {
          toValue: 1,
          duration: 8000,
          easing: Easing.inOut(Easing.sin),
          useNativeDriver: true,
        }),
        Animated.timing(floatAnim, {
          toValue: 0,
          duration: 8000,
          easing: Easing.inOut(Easing.sin),
          useNativeDriver: true,
        }),
      ]),
    );

    const pulseLoop = Animated.loop(
      Animated.sequence([
        Animated.timing(pulseAnim, {
          toValue: 1,
          duration: 5000,
          easing: Easing.inOut(Easing.quad),
          useNativeDriver: true,
        }),
        Animated.timing(pulseAnim, {
          toValue: 0,
          duration: 5000,
          easing: Easing.inOut(Easing.quad),
          useNativeDriver: true,
        }),
      ]),
    );

    const shimmerLoop = Animated.loop(
      Animated.sequence([
        Animated.timing(shimmerAnim, {
          toValue: 1,
          duration: 6500,
          easing: Easing.inOut(Easing.cubic),
          useNativeDriver: true,
        }),
        Animated.timing(shimmerAnim, {
          toValue: 0,
          duration: 6500,
          easing: Easing.inOut(Easing.cubic),
          useNativeDriver: true,
        }),
      ]),
    );

    floatLoop.start();
    pulseLoop.start();
    shimmerLoop.start();

    return () => {
      floatLoop.stop();
      pulseLoop.stop();
      shimmerLoop.stop();
    };
  }, [floatAnim, pulseAnim, shimmerAnim]);

  const orbOneX = floatAnim.interpolate({
    inputRange: [0, 1],
    outputRange: [-30, 24],
  });
  const orbOneY = floatAnim.interpolate({
    inputRange: [0, 1],
    outputRange: [-20, 36],
  });
  const orbTwoX = floatAnim.interpolate({
    inputRange: [0, 1],
    outputRange: [24, -22],
  });
  const orbTwoY = floatAnim.interpolate({
    inputRange: [0, 1],
    outputRange: [18, -28],
  });
  const orbScale = pulseAnim.interpolate({
    inputRange: [0, 1],
    outputRange: [0.92, 1.08],
  });
  const orbPrimaryOpacity = pulseAnim.interpolate({
    inputRange: [0, 1],
    outputRange: [0.2, 0.34],
  });
  const orbSecondaryOpacity = pulseAnim.interpolate({
    inputRange: [0, 1],
    outputRange: [0.12, 0.22],
  });
  const shimmerTranslateY = shimmerAnim.interpolate({
    inputRange: [0, 1],
    outputRange: [-80, 90],
  });
  const shimmerOpacity = shimmerAnim.interpolate({
    inputRange: [0, 1],
    outputRange: [0.08, 0.16],
  });

  return (
    <SafeAreaView style={st.container} edges={['top']}>
      <StatusBar barStyle="light-content" backgroundColor="transparent" translucent />

      <Video
        ref={videoRef}
        source={require('../../assets/GIF_Loop_Without_Camera_Movement.mp4')}
        shouldPlay
        isLooping
        isMuted
        resizeMode={ResizeMode.COVER}
        style={StyleSheet.absoluteFill}
      />

      <LinearGradient
        colors={['rgba(2, 14, 12, 0.22)', 'rgba(1, 7, 10, 0.62)', 'rgba(0, 0, 0, 0.82)']}
        locations={[0, 0.42, 1]}
        style={StyleSheet.absoluteFill}
      />

      <View pointerEvents="none" style={st.motionLayer}>
        <Animated.View
          style={[
            st.orb,
            st.orbPrimary,
            {
              opacity: orbPrimaryOpacity,
              transform: [{ translateX: orbOneX }, { translateY: orbOneY }, { scale: orbScale }],
            },
          ]}
        />
        <Animated.View
          style={[
            st.orb,
            st.orbSecondary,
            {
              opacity: orbSecondaryOpacity,
              transform: [{ translateX: orbTwoX }, { translateY: orbTwoY }, { scale: orbScale }],
            },
          ]}
        />
        <Animated.View
          style={[
            st.shimmerBand,
            {
              opacity: shimmerOpacity,
              transform: [{ rotate: '-14deg' }, { translateY: shimmerTranslateY }],
            },
          ]}
        />
      </View>

      <ScrollView
        showsVerticalScrollIndicator={false}
        contentContainerStyle={st.scroll}
        refreshControl={<RefreshControl refreshing={refreshing} onRefresh={() => load(true)} tintColor={G} colors={[G]} />}
      >
        <View style={st.header}>
          <Text style={st.brand}>🌾 KisaanAI</Text>
          <Text style={st.tagline}>{hi ? 'भारतीय किसानों का AI प्लेटफ़ॉर्म' : 'AI Platform for Indian Farmers'}</Text>
        </View>

        <View style={st.sourceBadge}>
          <View style={st.sourceGreen} />
          <Text style={st.sourceText}>
            {hi ? '🔴 लाइव — data.gov.in (Agmarknet)' : '🔴 LIVE — data.gov.in (Agmarknet)'}
          </Text>
          {liveTotal > 0 && (
            <Text style={st.sourceCount}>{liveTotal.toLocaleString()} {hi ? 'रिकॉर्ड' : 'records'}</Text>
          )}
        </View>

        {error ? (
          <TouchableOpacity style={st.errorBanner} onPress={() => load(true)}>
            <Text style={st.errorText}>⚠️ {error} — {hi ? 'रिफ्रेश करें' : 'Tap to retry'}</Text>
          </TouchableOpacity>
        ) : null}

        <View style={st.statsRow}>
          {[
            { v: stats.total_mandis || '--', l: hi ? 'मंडियाँ' : 'Mandis', icon: '🏪' },
            { v: stats.total_commodities || '--', l: hi ? 'फसलें' : 'Crops', icon: '🌾' },
            { v: stats.total_states || '--', l: hi ? 'राज्य' : 'States', icon: '🗺️' },
          ].map((item, i) => (
            <View key={i} style={st.statCard}>
              <Text style={st.statIcon}>{item.icon}</Text>
              <Text style={st.statVal}>{item.v}</Text>
              <Text style={st.statLbl}>{item.l}</Text>
            </View>
          ))}
        </View>

        <View style={st.section}>
          <Text style={st.secTitle}>{hi ? '⚡ सुविधाएँ' : '⚡ Quick Actions'}</Text>
          <View style={st.actGrid}>
            {[
              { icon: '📍', l: hi ? 'मंडी खोजें' : 'Find Mandi', s: 'Mandi' },
              { icon: '📊', l: hi ? 'भाव चार्ट' : 'Price Charts', s: 'Charts' },
              { icon: '🎤', l: hi ? 'AI सहायक' : 'Voice AI', s: 'Voice' },
              { icon: '🩺', l: hi ? 'फसल डॉक्टर' : 'Crop Doctor', s: 'Doctor' },
              { icon: '📰', l: hi ? 'समाचार' : 'News', s: 'News' },
              { icon: '👥', l: hi ? 'समुदाय' : 'Community', s: 'Community' },
              { icon: '⚙️', l: hi ? 'सेटिंग्स' : 'Settings', s: 'Settings' },
            ].map((a, i) => (
              <TouchableOpacity key={i} style={st.actCard} onPress={() => navigation.navigate(a.s)} activeOpacity={0.7}>
                <Text style={st.actIcon}>{a.icon}</Text>
                <Text style={st.actLabel}>{a.l}</Text>
                <ChevronRight size={12} color="#7bd6e0" style={{ position: 'absolute', right: 12, top: 16 }} />
              </TouchableOpacity>
            ))}
          </View>
        </View>

        {(gainers.length > 0 || losers.length > 0) && (
          <View style={st.section}>
            <Text style={st.secTitle}>{hi ? '📈 बाज़ार' : '📈 Market Movers'}</Text>
            <View style={st.moversRow}>
              <View style={st.moverCol}>
                <Text style={[st.moverHead, { color: G }]}>▲ {hi ? 'बढ़े' : 'Gainers'}</Text>
                {gainers.map((g, i) => (
                  <View key={i} style={st.moverItem}>
                    <View style={{ flex: 1 }}>
                      <Text style={st.moverName} numberOfLines={1}>{g.commodity_name}</Text>
                      <Text style={st.moverMarket} numberOfLines={1}>{g.market || g.state}</Text>
                    </View>
                    <View style={{ alignItems: 'flex-end' }}>
                      <Text style={[st.moverPrice, { color: G }]}>₹{g.modal_price}</Text>
                      <View style={st.moverBadge}>
                        <ArrowUpRight size={10} color={G} />
                        <Text style={[st.moverPct, { color: G }]}>{g.change_pct}%</Text>
                      </View>
                    </View>
                  </View>
                ))}
              </View>
              {losers.length > 0 && (
                <View style={st.moverCol}>
                  <Text style={[st.moverHead, { color: R }]}>▼ {hi ? 'गिरे' : 'Losers'}</Text>
                  {losers.map((l, i) => (
                    <View key={i} style={st.moverItem}>
                      <View style={{ flex: 1 }}>
                        <Text style={st.moverName} numberOfLines={1}>{l.commodity_name}</Text>
                        <Text style={st.moverMarket} numberOfLines={1}>{l.market || l.state}</Text>
                      </View>
                      <View style={{ alignItems: 'flex-end' }}>
                        <Text style={[st.moverPrice, { color: R }]}>₹{l.modal_price}</Text>
                        <View style={st.moverBadge}>
                          <ArrowDownRight size={10} color={R} />
                          <Text style={[st.moverPct, { color: R }]}>{Math.abs(l.change_pct)}%</Text>
                        </View>
                      </View>
                    </View>
                  ))}
                </View>
              )}
            </View>
          </View>
        )}

        {liveData.length > 0 && (
          <View style={st.section}>
            <View style={st.secHead}>
              <Text style={st.secTitle}>{hi ? '💰 आज के भाव' : "💰 Today's Prices"}</Text>
              <TouchableOpacity onPress={() => navigation.navigate('Mandi')}>
                <Text style={st.viewAll}>{hi ? 'सभी >' : 'View All >'}</Text>
              </TouchableOpacity>
            </View>

            {liveData.map((p: any, i: number) => (
              <View key={i} style={st.priceRow}>
                <View style={{ flex: 1 }}>
                  <Text style={st.pComm}>{p.commodity}</Text>
                  <Text style={st.pMarket}>{p.market}</Text>
                  <Text style={st.pState}>{p.district}, {p.state}</Text>
                </View>
                <View style={st.pRight}>
                  <Text style={st.pVal}>₹{p.modal_price?.toLocaleString()}</Text>
                  <Text style={st.pRange}>₹{p.min_price} — ₹{p.max_price}</Text>
                  <Text style={st.pUnit}>/quintal</Text>
                </View>
              </View>
            ))}

            <View style={st.dataSource}>
              <ExternalLink size={12} color={CYAN} />
              <Text style={st.dataSourceText}>Source: data.gov.in · Agmarknet · {liveData[0]?.arrival_date}</Text>
            </View>
          </View>
        )}

        {loading && !refreshing && (
          <View style={st.loader}>
            <ActivityIndicator size="small" color={G} />
            <Text style={st.loaderText}>{hi ? 'data.gov.in से डेटा लोड हो रहा है...' : 'Loading live data from data.gov.in...'}</Text>
          </View>
        )}

        <View style={{ height: 90 }} />
      </ScrollView>
    </SafeAreaView>
  );
}

const st = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#000' },
  scroll: { padding: 20 },
  motionLayer: {
    ...StyleSheet.absoluteFillObject,
    overflow: 'hidden',
  },
  orb: {
    position: 'absolute',
    borderRadius: 999,
  },
  orbPrimary: {
    width: 220,
    height: 220,
    top: 72,
    right: -48,
    backgroundColor: 'rgba(52, 199, 89, 0.9)',
  },
  orbSecondary: {
    width: 180,
    height: 180,
    bottom: 160,
    left: -44,
    backgroundColor: 'rgba(28, 192, 209, 0.95)',
  },
  shimmerBand: {
    position: 'absolute',
    top: -120,
    left: width * 0.25,
    width: width * 0.9,
    height: 260,
    borderRadius: 40,
    backgroundColor: 'rgba(255, 255, 255, 0.18)',
  },

  header: { marginBottom: 12 },
  brand: { fontSize: 28, fontWeight: '800', color: '#fff', letterSpacing: -0.5 },
  tagline: { fontSize: 13, color: '#c7c9d1', marginTop: 4 },

  sourceBadge: { flexDirection: 'row', alignItems: 'center', gap: 6, backgroundColor: 'rgba(8, 15, 20, 0.78)', borderRadius: 10, padding: 10, marginBottom: 16, borderWidth: 0.8, borderColor: 'rgba(28, 192, 209, 0.24)' },
  sourceGreen: { width: 6, height: 6, borderRadius: 3, backgroundColor: '#ff3b30' },
  sourceText: { fontSize: 12, color: '#d1d1d6', fontWeight: '600', flex: 1 },
  sourceCount: { fontSize: 11, color: CYAN, fontWeight: '700' },

  errorBanner: { backgroundColor: 'rgba(58, 28, 28, 0.84)', borderRadius: 10, padding: 12, marginBottom: 16, borderWidth: 0.5, borderColor: '#5c2020' },
  errorText: { color: '#ff6b6b', fontSize: 13, textAlign: 'center' },

  statsRow: { flexDirection: 'row', gap: 8, marginBottom: 20 },
  statCard: { flex: 1, backgroundColor: 'rgba(6, 12, 16, 0.76)', borderRadius: 14, padding: 14, alignItems: 'center', borderWidth: 0.8, borderColor: 'rgba(255,255,255,0.08)' },
  statIcon: { fontSize: 20, marginBottom: 4 },
  statVal: { fontSize: 22, fontWeight: '800', color: '#fff' },
  statLbl: { fontSize: 10, color: '#8e8e93', marginTop: 2, textTransform: 'uppercase', letterSpacing: 0.5 },

  section: { marginBottom: 20 },
  secHead: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: 10 },
  secTitle: { fontSize: 16, fontWeight: '700', color: '#fff', marginBottom: 10 },
  viewAll: { fontSize: 13, color: G, fontWeight: '500', marginBottom: 10 },

  actGrid: { flexDirection: 'row', flexWrap: 'wrap', gap: 8 },
  actCard: { width: (width - 48) / 2, backgroundColor: 'rgba(6, 12, 16, 0.74)', borderRadius: 14, padding: 16, borderWidth: 0.8, borderColor: 'rgba(255,255,255,0.08)' },
  actIcon: { fontSize: 24, marginBottom: 8 },
  actLabel: { fontSize: 14, fontWeight: '600', color: '#fff' },

  moversRow: { flexDirection: 'row', gap: 8 },
  moverCol: { flex: 1, backgroundColor: 'rgba(6, 12, 16, 0.74)', borderRadius: 14, padding: 12, borderWidth: 0.8, borderColor: 'rgba(255,255,255,0.08)' },
  moverHead: { fontSize: 13, fontWeight: '700', marginBottom: 8 },
  moverItem: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', paddingVertical: 6, borderBottomWidth: 0.5, borderBottomColor: 'rgba(255,255,255,0.06)' },
  moverName: { fontSize: 13, color: '#fff', fontWeight: '600' },
  moverMarket: { fontSize: 10, color: '#8e8e93', marginTop: 1 },
  moverPrice: { fontSize: 14, fontWeight: '800' },
  moverBadge: { flexDirection: 'row', alignItems: 'center', gap: 2 },
  moverPct: { fontSize: 11, fontWeight: '700' },

  priceRow: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', backgroundColor: 'rgba(6, 12, 16, 0.74)', borderRadius: 12, padding: 14, marginBottom: 6, borderWidth: 0.8, borderColor: 'rgba(255,255,255,0.08)' },
  pComm: { fontSize: 15, fontWeight: '700', color: '#fff' },
  pMarket: { fontSize: 12, color: CYAN, marginTop: 2 },
  pState: { fontSize: 11, color: '#8e8e93', marginTop: 1 },
  pRight: { alignItems: 'flex-end' },
  pVal: { fontSize: 18, fontWeight: '800', color: G },
  pRange: { fontSize: 10, color: '#8e8e93', marginTop: 2 },
  pUnit: { fontSize: 9, color: '#6b7280', marginTop: 1 },

  dataSource: { flexDirection: 'row', alignItems: 'center', gap: 6, paddingTop: 10 },
  dataSourceText: { fontSize: 11, color: CYAN, fontWeight: '500' },

  loader: { alignItems: 'center', paddingVertical: 30, gap: 8 },
  loaderText: { fontSize: 13, color: '#d1d1d6' },
});
