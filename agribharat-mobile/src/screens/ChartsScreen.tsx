import React, { useState, useEffect } from 'react';
import {
  View, Text, StyleSheet, ScrollView, TouchableOpacity,
  ActivityIndicator, Dimensions,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { TrendingUp } from 'lucide-react-native';
import { COLORS, COMMODITIES } from '../constants';
import { useAppStore } from '../store/useAppStore';
import { api } from '../services/api';

const { width } = Dimensions.get('window');
const C = { bg: '#000', card: '#111', border: '#1c1c1e', muted: '#8e8e93', green: '#34c759', red: '#ff3b30', white: '#fff' };

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

  return (
    <SafeAreaView style={s.container} edges={['top']}>
      <ScrollView showsVerticalScrollIndicator={false} contentContainerStyle={s.content}>
        <Text style={s.title}>{hi ? 'चार्ट्स' : 'Charts'}</Text>

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
                {t === 'trend' ? (hi ? 'भाव' : 'Price') : t === 'forecast' ? (hi ? 'AI' : 'AI') : (hi ? 'तुलना' : 'Compare')}
              </Text>
            </TouchableOpacity>
          ))}
        </View>

        {/* Days */}
        <View style={s.daysRow}>
          {[7, 14, 30, 90].map((d) => (
            <TouchableOpacity key={d} style={[s.dayChip, days === d && s.dayChipActive]} onPress={() => setDays(d)}>
              <Text style={[s.dayText, days === d && s.dayTextActive]}>{d}D</Text>
            </TouchableOpacity>
          ))}
        </View>

        {loading ? <ActivityIndicator size="small" color={C.green} style={{ marginTop: 40 }} /> : (
          <>
            {/* Price Trend */}
            {tab === 'trend' && (
              <View style={s.card}>
                <Text style={s.cardTitle}>{hi ? 'मूल्य इतिहास' : 'Price History'}</Text>
                <View style={s.chart}>
                  {trend.slice(-25).map((d, i) => {
                    const p = d.price || d.modal_price || 0;
                    const h = (p / maxP) * 100;
                    return (
                      <View key={i} style={s.barCol}>
                        <View style={[s.bar, { height: Math.max(h, 3) }]} />
                      </View>
                    );
                  })}
                </View>
                {trend.length > 0 && (
                  <View style={s.chartStats}>
                    <Text style={s.chartStat}>{hi ? 'न्यूनतम' : 'Low'}: ₹{Math.min(...trend.map(t => t.price || t.modal_price || 0))}</Text>
                    <Text style={s.chartStat}>{hi ? 'अधिकतम' : 'High'}: ₹{Math.max(...trend.map(t => t.price || t.modal_price || 0))}</Text>
                  </View>
                )}
              </View>
            )}

            {/* AI Forecast */}
            {tab === 'forecast' && (
              <View style={s.card}>
                <Text style={s.cardTitle}>{hi ? 'AI भविष्यवाणी' : 'AI Forecast'}</Text>
                {forecast ? (
                  <>
                    <View style={s.forecastRow}>
                      <View style={s.forecastItem}>
                        <Text style={s.fLabel}>{hi ? 'वर्तमान' : 'Current'}</Text>
                        <Text style={s.fValue}>₹{forecast.current_price || '--'}</Text>
                      </View>
                      <TrendingUp size={20} color={C.green} />
                      <View style={s.forecastItem}>
                        <Text style={s.fLabel}>{hi ? 'अनुमानित' : 'Predicted'}</Text>
                        <Text style={[s.fValue, { color: C.green }]}>₹{forecast.predicted_price || '--'}</Text>
                      </View>
                    </View>
                    <Text style={s.confidence}>{hi ? 'विश्वसनीयता' : 'Confidence'}: {forecast.confidence || '--'}%</Text>
                  </>
                ) : <Text style={s.noData}>{hi ? 'डेटा उपलब्ध नहीं' : 'No forecast data'}</Text>}
              </View>
            )}

            {/* Compare */}
            {tab === 'compare' && (
              <View style={s.card}>
                <Text style={s.cardTitle}>{hi ? 'मंडी तुलना' : 'Mandi Comparison'}</Text>
                {current.length > 0 ? current.slice(0, 8).map((p, i) => (
                  <View key={i} style={s.compareRow}>
                    <Text style={s.compareName} numberOfLines={1}>{p.mandi_name || `Mandi ${i + 1}`}</Text>
                    <Text style={s.comparePrice}>₹{p.modal_price || '--'}</Text>
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
  title: { fontSize: 26, fontWeight: '700', color: C.white, marginBottom: 16 },

  chip: { paddingHorizontal: 14, paddingVertical: 7, borderRadius: 18, backgroundColor: C.card, marginRight: 6, borderWidth: 0.5, borderColor: C.border },
  chipActive: { backgroundColor: C.green },
  chipText: { color: C.muted, fontSize: 13, fontWeight: '500' },
  chipTextActive: { color: C.bg, fontWeight: '600' },

  tabBar: { flexDirection: 'row', backgroundColor: C.card, borderRadius: 10, padding: 3, marginBottom: 12, borderWidth: 0.5, borderColor: C.border },
  tab: { flex: 1, paddingVertical: 10, borderRadius: 8, alignItems: 'center' },
  tabActive: { backgroundColor: '#1c1c1e' },
  tabText: { color: C.muted, fontSize: 13, fontWeight: '500' },
  tabTextActive: { color: C.white, fontWeight: '600' },

  daysRow: { flexDirection: 'row', gap: 6, marginBottom: 16 },
  dayChip: { paddingHorizontal: 14, paddingVertical: 6, borderRadius: 8, backgroundColor: C.card, borderWidth: 0.5, borderColor: C.border },
  dayChipActive: { backgroundColor: C.green },
  dayText: { color: C.muted, fontSize: 12, fontWeight: '600' },
  dayTextActive: { color: C.bg },

  card: { backgroundColor: C.card, borderRadius: 12, padding: 16, borderWidth: 0.5, borderColor: C.border, marginBottom: 12 },
  cardTitle: { fontSize: 15, fontWeight: '600', color: C.white, marginBottom: 16 },

  chart: { flexDirection: 'row', alignItems: 'flex-end', height: 120, gap: 2 },
  barCol: { flex: 1, alignItems: 'center' },
  bar: { width: '70%', borderRadius: 3, backgroundColor: C.green },
  chartStats: { flexDirection: 'row', justifyContent: 'space-between', marginTop: 12, paddingTop: 12, borderTopWidth: 0.5, borderTopColor: C.border },
  chartStat: { fontSize: 13, color: C.muted },

  forecastRow: { flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 20, marginVertical: 16 },
  forecastItem: { alignItems: 'center' },
  fLabel: { fontSize: 13, color: C.muted, marginBottom: 4 },
  fValue: { fontSize: 22, fontWeight: '700', color: C.white },
  confidence: { textAlign: 'center', color: C.muted, fontSize: 13, marginTop: 8 },

  compareRow: { flexDirection: 'row', justifyContent: 'space-between', paddingVertical: 12, borderBottomWidth: 0.5, borderBottomColor: C.border },
  compareName: { color: C.white, fontSize: 14, flex: 1 },
  comparePrice: { color: C.green, fontSize: 15, fontWeight: '700' },
  noData: { color: C.muted, textAlign: 'center', paddingVertical: 30, fontSize: 14 },
});
