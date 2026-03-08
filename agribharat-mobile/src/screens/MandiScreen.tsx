import React, { useState, useEffect } from 'react';
import {
  View, Text, StyleSheet, ScrollView, TouchableOpacity,
  TextInput, ActivityIndicator, RefreshControl,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { LinearGradient } from 'expo-linear-gradient';
import { MapPin, Search, ChevronRight, TrendingUp, TrendingDown } from 'lucide-react-native';
import { COLORS } from '../constants';
import { useAppStore } from '../store/useAppStore';
import { api } from '../services/api';

const C = { bg: '#0a0a0a', card: '#171717', border: '#262626', muted: '#a3a3a3', green: '#34d399', white: '#fff' };

export default function MandiScreen() {
  const { selectedLanguage } = useAppStore();
  const hi = selectedLanguage === 'hi';
  const [mandis, setMandis] = useState<any[]>([]);
  const [prices, setPrices] = useState<Map<number, any>>(new Map());
  const [search, setSearch] = useState('');
  const [selectedState, setSelectedState] = useState<string | null>(null);
  const [states, setStates] = useState<string[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState('');

  const load = async (refresh = false) => {
    if (refresh) setRefreshing(true); else setLoading(true);
    setError('');
    try {
      const [m, st, p] = await Promise.allSettled([
        api.getMandis({ page_size: 50 }), api.getMandiStates(), api.getPrices({ commodity_id: 1, page_size: 200 }),
      ]);
      if (m.status === 'fulfilled') setMandis(m.value);
      if (st.status === 'fulfilled') setStates(st.value);
      if (p.status === 'fulfilled') {
        const pm = new Map<number, any>();
        for (const pr of p.value) pm.set(pr.mandi_id, pr);
        setPrices(pm);
      }
      if (m.status === 'rejected' && st.status === 'rejected') setError(hi ? 'सर्वर से कनेक्ट नहीं हो पाया' : 'Could not connect to server');
    } catch { setError(hi ? 'नेटवर्क त्रुटि' : 'Network error'); } finally { setLoading(false); setRefreshing(false); }
  };

  useEffect(() => { load(); }, []);

  const filtered = mandis.filter((m) => {
    const ms = !search || m.name?.toLowerCase().includes(search.toLowerCase()) || m.district?.toLowerCase().includes(search.toLowerCase());
    const mst = !selectedState || m.state === selectedState;
    return ms && mst;
  });

  return (
    <SafeAreaView style={s.container} edges={['top']}>
      {/* Header */}
      <View style={s.header}>
        <View>
          <Text style={s.headerTitle}>{hi ? '📍 मंडी' : '📍 Mandis'}</Text>
          <Text style={s.headerSub}>{hi ? 'लाइव भाव देखें' : 'Live market prices'}</Text>
        </View>
        <View style={s.countBadge}>
          <Text style={s.countText}>{filtered.length}</Text>
        </View>
      </View>

      {/* Search */}
      <View style={s.searchBox}>
        <Search size={16} color={C.muted} />
        <TextInput style={s.searchInput} placeholder={hi ? 'मंडी खोजें...' : 'Search mandis...'} placeholderTextColor="#555" value={search} onChangeText={setSearch} />
      </View>

      {/* State Filters */}
      <ScrollView horizontal showsHorizontalScrollIndicator={false} style={s.filterRow} contentContainerStyle={{ paddingHorizontal: 20 }}>
        <TouchableOpacity style={[s.chip, !selectedState && s.chipActive]} onPress={() => setSelectedState(null)}>
          <Text style={[s.chipText, !selectedState && s.chipTextActive]}>{hi ? 'सभी' : 'All'}</Text>
        </TouchableOpacity>
        {states.slice(0, 10).map((st) => (
          <TouchableOpacity key={st} style={[s.chip, selectedState === st && s.chipActive]} onPress={() => setSelectedState(st === selectedState ? null : st)}>
            <Text style={[s.chipText, selectedState === st && s.chipTextActive]}>{st}</Text>
          </TouchableOpacity>
        ))}
      </ScrollView>

      {/* List */}
      <ScrollView showsVerticalScrollIndicator={false} style={s.list} refreshControl={<RefreshControl refreshing={refreshing} onRefresh={() => load(true)} tintColor={C.green} />}>
        {loading ? (
          <ActivityIndicator size="small" color={C.green} style={{ marginTop: 40 }} />
        ) : filtered.length === 0 ? (
          <Text style={s.empty}>{hi ? 'कोई मंडी नहीं मिली' : 'No mandis found'}</Text>
        ) : (
          filtered.map((m) => {
            const p = prices.get(m.id);
            return (
              <View key={m.id} style={s.card}>
                <LinearGradient colors={['rgba(16,185,129,0.06)', 'rgba(0,0,0,0)']} style={StyleSheet.absoluteFill} start={{ x: 0, y: 0 }} end={{ x: 1, y: 1 }} />
                <View style={s.cardAccent} />
                <View style={s.cardTop}>
                  <View style={s.iconBox}><MapPin size={16} color={C.green} /></View>
                  <View style={{ flex: 1 }}>
                    <Text style={s.cardName}>{m.name}</Text>
                    <Text style={s.cardLoc}>{m.district}, {m.state}</Text>
                  </View>
                  <ChevronRight size={16} color={C.muted} />
                </View>
                {p && (
                  <View style={s.cardBottom}>
                    <View>
                      <Text style={s.priceLabel}>{hi ? 'भाव' : 'Price'}</Text>
                      <Text style={s.priceVal}>₹{p.modal_price?.toLocaleString() || '--'}</Text>
                    </View>
                    <View>
                      <Text style={s.priceLabel}>{hi ? 'न्यूनतम' : 'Min'}</Text>
                      <Text style={[s.priceVal, { color: '#f59e0b' }]}>₹{p.min_price || '--'}</Text>
                    </View>
                    <View>
                      <Text style={s.priceLabel}>{hi ? 'आवक' : 'Arrival'}</Text>
                      <Text style={s.priceVal}>{p.arrival_qty || '--'} T</Text>
                    </View>
                  </View>
                )}
              </View>
            );
          })
        )}
        <View style={{ height: 90 }} />
      </ScrollView>
    </SafeAreaView>
  );
}

const s = StyleSheet.create({
  container: { flex: 1, backgroundColor: C.bg },
  header: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', paddingHorizontal: 20, paddingTop: 16, paddingBottom: 8 },
  headerTitle: { fontSize: 26, fontWeight: '700', color: C.white },
  headerSub: { fontSize: 12, color: C.muted, marginTop: 2 },
  countBadge: { backgroundColor: 'rgba(16,185,129,0.15)', paddingHorizontal: 14, paddingVertical: 6, borderRadius: 20 },
  countText: { fontSize: 14, fontWeight: '700', color: '#34d399' },

  searchBox: { flexDirection: 'row', alignItems: 'center', marginHorizontal: 20, marginBottom: 12, backgroundColor: 'rgba(255,255,255,0.06)', borderRadius: 12, paddingHorizontal: 14, gap: 10, borderWidth: 0.5, borderColor: 'rgba(255,255,255,0.08)' },
  searchInput: { flex: 1, color: C.white, fontSize: 15, paddingVertical: 12 },

  filterRow: { maxHeight: 40, marginBottom: 12 },
  chip: { paddingHorizontal: 16, paddingVertical: 8, borderRadius: 20, backgroundColor: 'rgba(255,255,255,0.06)', marginRight: 6, borderWidth: 0.5, borderColor: 'rgba(255,255,255,0.08)' },
  chipActive: { backgroundColor: '#059669', borderColor: '#059669' },
  chipText: { color: C.muted, fontSize: 13, fontWeight: '500' },
  chipTextActive: { color: '#fff', fontWeight: '600' },

  list: { flex: 1, paddingHorizontal: 20 },
  empty: { color: C.muted, textAlign: 'center', marginTop: 40, fontSize: 14 },

  card: { borderRadius: 14, padding: 16, marginBottom: 10, borderWidth: 0.5, borderColor: 'rgba(255,255,255,0.06)', overflow: 'hidden' },
  cardAccent: { position: 'absolute', left: 0, top: 8, bottom: 8, width: 3, backgroundColor: '#10b981', borderRadius: 2 },
  cardTop: { flexDirection: 'row', alignItems: 'center', gap: 12 },
  iconBox: { width: 36, height: 36, borderRadius: 10, backgroundColor: 'rgba(16,185,129,0.12)', alignItems: 'center', justifyContent: 'center' },
  cardName: { fontSize: 15, fontWeight: '600', color: C.white },
  cardLoc: { fontSize: 13, color: C.muted, marginTop: 1 },
  cardBottom: { flexDirection: 'row', gap: 32, marginTop: 12, paddingTop: 12, borderTopWidth: 0.5, borderTopColor: 'rgba(255,255,255,0.06)' },
  priceLabel: { fontSize: 11, color: C.muted, marginBottom: 2, textTransform: 'uppercase', letterSpacing: 0.3 },
  priceVal: { fontSize: 16, fontWeight: '700', color: '#34d399' },
});
