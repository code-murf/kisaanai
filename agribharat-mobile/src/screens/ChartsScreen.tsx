import React, { useState, useEffect } from 'react';
import {
  View, Text, StyleSheet, ScrollView, TouchableOpacity,
  ActivityIndicator, Dimensions,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { LinearGradient } from 'expo-linear-gradient';
import { TrendingUp, TrendingDown, ArrowUpRight, ArrowDownRight, Calendar } from 'lucide-react-native';
import { COLORS, COMMODITIES } from '../constants';
import { useAppStore } from '../store/useAppStore';
import { api } from '../services/api';

const { width } = Dimensions.get('window');
const C = { bg: '#0a0a0a', card: '#171717', border: '#262626', muted: '#a3a3a3', green: '#34d399', red: '#fb7185', white: '#fff' };

export default function ChartsScreen() {
  const { selectedLanguage, selectedCommodity, setSelectedCommodity } = useAppStore();
  const hi = selectedLanguage === 'hi';
  const [trend, setTrend] = useState<any[]>([]);
  const [current, setCurrent] = useState<any[]>([]);
  const [forecast, setForecast] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [tab, setTab] = useState<'trend' | 'forecast' | 'compare'>('trend');
  const [days, setDays] = useState(30);

  const cd = COMMODITIES.find((c) => c.value === selectedCommodity);
  const cid = cd?.id ?? 1;

  useEffect(() => { load(); }, [cid, days]);

  const load = async () => {
    setLoading(true);
    try {
      const [t, p, f] = await Promise.all([
        api.getPriceTrend(cid, days), api.getCurrentPrices(cid), api.getForecast(cid),
      ]);
      setTrend(t); setCurrent(p); setForecast(f);
    } catch {} finally { setLoading(false); }
  };

  const maxP = Math.max(...trend.map((d) => d.price || d.modal_price || 0), 1);
  const minP = Math.min(...trend.map((d) => d.price || d.modal_price || 999999));
  const latestP = trend.length > 0 ? (trend[trend.length - 1].price || trend[trend.length - 1].modal_price || 0) : 0;
  const firstP = trend.length > 0 ? (trend[0].price || trend[0].modal_price || 0) : 0;
  const changePct = firstP > 0 ? (((latestP - firstP) / firstP) * 100).toFixed(1) : '0';
  const isUp = Number(changePct) >= 0;

  return (
    <SafeAreaView style={s.container} edges={['top']}>
      <ScrollView showsVerticalScrollIndicator={false} contentContainerStyle={s.content}>
        <Text style={s.title}>{hi ? '📊 चार्ट्स' : '📊 Price Charts'}</Text>
        <Text style={s.subtitle}>{hi ? 'लाइव भाव विश्लेषण और AI अनुमान' : 'Live price analysis & AI predictions'}</Text>

        {/* Commodity chips */}
        <ScrollView horizontal showsHorizontalScrollIndicator={false} style={{ marginBottom: 16 }}>
          {COMMODITIES.map((c) => (
            <TouchableOpacity key={c.id} style={[s.chip, selectedCommodity === c.value && s.chipActive]} onPress={() => setSelectedCommodity(c.value)}>
              <Text style={[s.chipText, selectedCommodity === c.value && s.chipTextActive]}>{hi ? c.name_hi : c.name}</Text>
            </TouchableOpacity>
          ))}
        </ScrollView>

        {/* Tabs */}
        <View style={s.tabBar}>
          {(['trend', 'forecast', 'compare'] as const).map((t) => (
            <TouchableOpacity key={t} style={[s.tab, tab === t && s.tabActive]} onPress={() => setTab(t)}>
              <Text style={[s.tabText, tab === t && s.tabTextActive]}>
                {t === 'trend' ? (hi ? '📈 भाव' : '📈 Price') : t === 'forecast' ? (hi ? '🤖 AI' : '🤖 AI') : (hi ? '⚖️ तुलना' : '⚖️ Compare')}
              </Text>
            </TouchableOpacity>
          ))}
        </View>

        {/* Time Range Pills */}
        <View style={s.daysRow}>
          <Calendar size={14} color={C.muted} />
          {[{ l: '7D', d: 7 }, { l: '14D', d: 14 }, { l: '30D', d: 30 }, { l: '90D', d: 90 }, { l: '1Y', d: 365 }].map((item) => (
            <TouchableOpacity key={item.d} style={[s.dayChip, days === item.d && s.dayChipActive]} onPress={() => setDays(item.d)}>
              <Text style={[s.dayText, days === item.d && s.dayTextActive]}>{item.l}</Text>
            </TouchableOpacity>
          ))}
        </View>

        {loading ? <ActivityIndicator size="small" color={C.green} style={{ marginTop: 40 }} /> : (
          <>
            {/* Price Summary */}
            {tab === 'trend' && trend.length > 0 && (
              <View style={s.summaryRow}>
                <View style={s.summaryCard}>
                  <LinearGradient colors={['rgba(16,185,129,0.08)', 'rgba(0,0,0,0)']} style={StyleSheet.absoluteFill} start={{ x: 0, y: 0 }} end={{ x: 1, y: 1 }} />
                  <Text style={s.summaryLabel}>{hi ? 'वर्तमान' : 'Latest'}</Text>
                  <Text style={[s.summaryVal, { color: '#34d399' }]}>₹{latestP.toLocaleString()}</Text>
                </View>
                <View style={s.summaryCard}>
                  <Text style={s.summaryLabel}>{days}D {hi ? 'बदलाव' : 'Change'}</Text>
                  <View style={{ flexDirection: 'row', alignItems: 'center', gap: 4 }}>
                    {isUp ? <ArrowUpRight size={14} color={C.green} /> : <ArrowDownRight size={14} color={C.red} />}
                    <Text style={[s.summaryVal, { color: isUp ? C.green : C.red }]}>{changePct}%</Text>
                  </View>
                </View>
                <View style={s.summaryCard}>
                  <Text style={s.summaryLabel}>{hi ? 'रेंज' : 'Range'}</Text>
                  <Text style={s.summaryVal}>₹{minP}-{maxP}</Text>
                </View>
              </View>
            )}

            {/* Price Trend Chart */}
            {tab === 'trend' && (
              <View style={s.card}>
                <LinearGradient colors={['rgba(99,102,241,0.06)', 'rgba(0,0,0,0)']} style={StyleSheet.absoluteFill} start={{ x: 0, y: 0 }} end={{ x: 1, y: 1 }} />
                <Text style={s.cardTitle}>{hi ? 'मूल्य इतिहास' : 'Price History'} — {cd?.name || ''}</Text>
                <View style={s.chart}>
                  {trend.slice(-30).map((d, i) => {
                    const p = d.price || d.modal_price || 0;
                    const h = (p / maxP) * 120;
                    const prev = i > 0 ? (trend.slice(-30)[i-1]?.price || trend.slice(-30)[i-1]?.modal_price || 0) : p;
                    const barColor = p >= prev ? C.green : C.red;
                    return (
                      <View key={i} style={s.barCol}>
                        <View style={[s.bar, { height: Math.max(h, 3), backgroundColor: barColor }]} />
                      </View>
                    );
                  })}
                </View>
                {trend.length > 0 && (
                  <View style={s.chartDates}>
                    <Text style={s.chartDate}>{trend[0]?.date?.split('T')[0] || ''}</Text>
                    <Text style={s.chartDate}>{trend[trend.length - 1]?.date?.split('T')[0] || ''}</Text>
                  </View>
                )}
              </View>
            )}

            {/* AI Forecast */}
            {tab === 'forecast' && (
              <View style={s.card}>
                <LinearGradient colors={['rgba(168,85,247,0.08)', 'rgba(0,0,0,0)']} style={StyleSheet.absoluteFill} start={{ x: 0, y: 0 }} end={{ x: 1, y: 1 }} />
                <Text style={s.cardTitle}>{hi ? '🤖 AI भविष्यवाणी' : '🤖 AI Forecast'}</Text>
                {forecast ? (
                  <>
                    <View style={s.forecastRow}>
                      <View style={s.forecastItem}>
                        <Text style={s.fLabel}>{hi ? 'वर्तमान' : 'Current'}</Text>
                        <Text style={s.fValue}>₹{forecast.current_price || '--'}</Text>
                      </View>
                      <View style={s.forecastArrow}>
                        <TrendingUp size={24} color={C.green} />
                      </View>
                      <View style={s.forecastItem}>
                        <Text style={s.fLabel}>{hi ? 'अनुमानित' : 'Predicted'}</Text>
                        <Text style={[s.fValue, { color: '#34d399' }]}>₹{forecast.predicted_price || '--'}</Text>
                      </View>
                    </View>
                    {/* Confidence Bar */}
                    <View style={s.confBox}>
                      <Text style={s.confLabel}>{hi ? 'विश्वसनीयता' : 'Confidence'}</Text>
                      <View style={s.confTrack}>
                        <View style={[s.confBar, { width: `${forecast.confidence || 0}%` }]} />
                      </View>
                      <Text style={s.confValue}>{forecast.confidence || '--'}%</Text>
                    </View>
                    {forecast.predictions && forecast.predictions.length > 0 && (
                      <View style={s.predList}>
                        <Text style={s.predTitle}>{hi ? '7-दिन अनुमान' : '7-Day Forecast'}</Text>
                        {forecast.predictions.slice(0, 7).map((p: any, i: number) => (
                          <View key={i} style={s.predRow}>
                            <Text style={s.predDate}>{p.date?.split('T')[0] || `Day ${i + 1}`}</Text>
                            <Text style={s.predPrice}>₹{p.price?.toLocaleString() || '--'}</Text>
                          </View>
                        ))}
                      </View>
                    )}
                  </>
                ) : <Text style={s.noData}>{hi ? 'डेटा उपलब्ध नहीं' : 'No forecast data'}</Text>}
              </View>
            )}

            {/* Compare */}
            {tab === 'compare' && (
              <View style={s.card}>
                <LinearGradient colors={['rgba(245,158,11,0.06)', 'rgba(0,0,0,0)']} style={StyleSheet.absoluteFill} start={{ x: 0, y: 0 }} end={{ x: 1, y: 1 }} />
                <Text style={s.cardTitle}>{hi ? '⚖️ मंडी तुलना' : '⚖️ Mandi Comparison'}</Text>
                {current.length > 0 ? current.slice(0, 10).map((p, i) => (
                  <View key={i} style={s.compareRow}>
                    <View style={{ flex: 1 }}>
                      <Text style={s.compareName} numberOfLines={1}>{p.mandi_name || `Mandi ${i + 1}`}</Text>
                      {p.state && <Text style={s.compareState}>{p.state}</Text>}
                    </View>
                    <Text style={s.comparePrice}>₹{p.modal_price?.toLocaleString() || '--'}</Text>
                  </View>
                )) : <Text style={s.noData}>{hi ? 'डेटा नहीं' : 'No comparison data'}</Text>}
              </View>
            )}
          </>
        )}

        <View style={{ height: 90 }} />
      </ScrollView>
    </SafeAreaView>
  );
}

const s = StyleSheet.create({
  container: { flex: 1, backgroundColor: C.bg },
  content: { padding: 20 },
  title: { fontSize: 26, fontWeight: '700', color: C.white, marginBottom: 4 },
  subtitle: { fontSize: 13, color: C.muted, marginBottom: 16 },

  chip: { paddingHorizontal: 16, paddingVertical: 8, borderRadius: 20, backgroundColor: 'rgba(255,255,255,0.06)', marginRight: 6, borderWidth: 0.5, borderColor: 'rgba(255,255,255,0.08)' },
  chipActive: { backgroundColor: '#6366f1', borderColor: '#6366f1' },
  chipText: { color: C.muted, fontSize: 13, fontWeight: '500' },
  chipTextActive: { color: '#fff', fontWeight: '600' },

  tabBar: { flexDirection: 'row', backgroundColor: 'rgba(255,255,255,0.04)', borderRadius: 12, padding: 3, marginBottom: 12, borderWidth: 0.5, borderColor: 'rgba(255,255,255,0.06)' },
  tab: { flex: 1, paddingVertical: 10, borderRadius: 10, alignItems: 'center' },
  tabActive: { backgroundColor: 'rgba(255,255,255,0.08)' },
  tabText: { color: C.muted, fontSize: 13, fontWeight: '500' },
  tabTextActive: { color: C.white, fontWeight: '600' },

  daysRow: { flexDirection: 'row', gap: 6, marginBottom: 16, alignItems: 'center' },
  dayChip: { paddingHorizontal: 14, paddingVertical: 7, borderRadius: 8, backgroundColor: 'rgba(255,255,255,0.06)', borderWidth: 0.5, borderColor: 'rgba(255,255,255,0.06)' },
  dayChipActive: { backgroundColor: '#818cf8', borderColor: '#818cf8' },
  dayText: { color: C.muted, fontSize: 12, fontWeight: '700' },
  dayTextActive: { color: '#fff' },

  summaryRow: { flexDirection: 'row', gap: 8, marginBottom: 12 },
  summaryCard: { flex: 1, borderRadius: 14, padding: 14, borderWidth: 0.5, borderColor: 'rgba(255,255,255,0.06)', overflow: 'hidden' },
  summaryLabel: { fontSize: 10, color: C.muted, textTransform: 'uppercase', letterSpacing: 0.5, marginBottom: 4 },
  summaryVal: { fontSize: 16, fontWeight: '800', color: C.white },

  card: { borderRadius: 16, padding: 16, borderWidth: 0.5, borderColor: 'rgba(255,255,255,0.06)', marginBottom: 12, overflow: 'hidden' },
  cardTitle: { fontSize: 15, fontWeight: '700', color: C.white, marginBottom: 16 },

  chart: { flexDirection: 'row', alignItems: 'flex-end', height: 140, gap: 2, paddingBottom: 4 },
  barCol: { flex: 1, alignItems: 'center' },
  bar: { width: '80%', borderRadius: 2 },
  chartDates: { flexDirection: 'row', justifyContent: 'space-between', marginTop: 8, paddingTop: 8, borderTopWidth: 0.5, borderTopColor: 'rgba(255,255,255,0.06)' },
  chartDate: { fontSize: 10, color: C.muted },

  forecastRow: { flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 16, marginVertical: 20 },
  forecastItem: { alignItems: 'center', flex: 1 },
  forecastArrow: { width: 48, height: 48, borderRadius: 24, backgroundColor: 'rgba(16,185,129,0.12)', justifyContent: 'center', alignItems: 'center' },
  fLabel: { fontSize: 12, color: C.muted, marginBottom: 6 },
  fValue: { fontSize: 24, fontWeight: '800', color: C.white },

  confBox: { flexDirection: 'row', alignItems: 'center', gap: 10, paddingVertical: 12, borderTopWidth: 0.5, borderTopColor: 'rgba(255,255,255,0.06)' },
  confLabel: { fontSize: 12, color: C.muted, width: 80 },
  confTrack: { flex: 1, height: 6, borderRadius: 3, backgroundColor: 'rgba(255,255,255,0.06)' },
  confBar: { height: 6, borderRadius: 3, backgroundColor: '#34d399' },
  confValue: { fontSize: 13, fontWeight: '700', color: '#34d399', width: 40, textAlign: 'right' },

  predList: { marginTop: 12 },
  predTitle: { fontSize: 13, fontWeight: '600', color: C.white, marginBottom: 8 },
  predRow: { flexDirection: 'row', justifyContent: 'space-between', paddingVertical: 8, borderBottomWidth: 0.5, borderBottomColor: 'rgba(255,255,255,0.06)' },
  predDate: { fontSize: 13, color: C.muted },
  predPrice: { fontSize: 14, fontWeight: '700', color: '#34d399' },

  compareRow: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', paddingVertical: 12, borderBottomWidth: 0.5, borderBottomColor: 'rgba(255,255,255,0.06)' },
  compareName: { color: C.white, fontSize: 14, fontWeight: '600' },
  compareState: { color: C.muted, fontSize: 11, marginTop: 2 },
  comparePrice: { color: '#34d399', fontSize: 16, fontWeight: '700' },
  noData: { color: C.muted, textAlign: 'center', paddingVertical: 30, fontSize: 14 },
});
