import React, { useState, useEffect, useMemo } from 'react';
import { View, Text, StyleSheet, ScrollView, TouchableOpacity, TextInput, ActivityIndicator } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { MapPin, Navigation, TrendingUp, Search, AlertCircle } from 'lucide-react-native';
import { COLORS, COMMODITIES } from '../constants';
import { useAppStore } from '../store/useAppStore';
import { api } from '../services/api';

type MandiCard = {
  id: number;
  name: string;
  district: string;
  state: string;
  price: number | null;
  distance: number | null;
  arrival: number | null;
};

export default function MandiScreen() {
  const { selectedLanguage, selectedCommodity } = useAppStore();
  const [searchQuery, setSearchQuery] = useState('');
  const [sortBy, setSortBy] = useState<'price' | 'distance'>('price');
  const [mandis, setMandis] = useState<MandiCard[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const selectedCommodityId = useMemo(() => {
    return COMMODITIES.find((c) => c.value === selectedCommodity)?.id ?? 1;
  }, [selectedCommodity]);

  useEffect(() => {
    let mounted = true;

    const loadMandis = async () => {
      setLoading(true);
      setError(null);

      try {
        const [nearby, prices] = await Promise.all([
          api.getNearbyMandis(28.6139, 77.209, 80),
          api.getCurrentPrice(selectedCommodityId),
        ]);

        const priceByMandi = new Map<number, any>();
        for (const row of prices) {
          priceByMandi.set(row.mandi_id, row);
        }

        const merged: MandiCard[] = nearby.map((m) => {
          const priceRow = priceByMandi.get(m.id);
          return {
            id: m.id,
            name: m.name,
            district: m.district,
            state: m.state,
            distance: typeof m.distance_km === 'number' ? Number(m.distance_km.toFixed(1)) : null,
            price: typeof priceRow?.modal_price === 'number' ? priceRow.modal_price : null,
            arrival: typeof priceRow?.arrival_qty === 'number' ? priceRow.arrival_qty : null,
          };
        });

        if (mounted) {
          setMandis(merged);
        }
      } catch (e) {
        if (mounted) {
          setError(e instanceof Error ? e.message : 'Failed to load mandi data');
          setMandis([]);
        }
      } finally {
        if (mounted) {
          setLoading(false);
        }
      }
    };

    loadMandis();

    return () => {
      mounted = false;
    };
  }, [selectedCommodityId]);

  const filteredMandis = mandis
    .filter((m) => m.name.toLowerCase().includes(searchQuery.toLowerCase()))
    .sort((a, b) => {
      if (sortBy === 'price') {
        return (b.price ?? -1) - (a.price ?? -1);
      }
      return (a.distance ?? Number.MAX_VALUE) - (b.distance ?? Number.MAX_VALUE);
    });

  return (
    <SafeAreaView style={styles.container} edges={['bottom']}>
      <ScrollView style={styles.scrollView} showsVerticalScrollIndicator={false}>
        <View style={styles.header}>
          <Text style={styles.title}>{selectedLanguage === 'hi' ? '??????? ???????' : 'Nearby Mandis'}</Text>
          <Text style={styles.subtitle}>
            {selectedLanguage === 'hi'
              ? '???? ??? ????? ?? ??? ???? ????? ???? ?????'
              : 'Find the best market to sell your produce'}
          </Text>
        </View>

        <View style={styles.searchContainer}>
          <Search size={20} color={COLORS.textSecondary} style={styles.searchIcon} />
          <TextInput
            style={styles.searchInput}
            placeholder={selectedLanguage === 'hi' ? '???? ?????...' : 'Search mandis...'}
            placeholderTextColor={COLORS.textSecondary}
            value={searchQuery}
            onChangeText={setSearchQuery}
          />
        </View>

        <View style={styles.sortContainer}>
          <TouchableOpacity style={[styles.sortButton, sortBy === 'price' && styles.sortButtonActive]} onPress={() => setSortBy('price')}>
            <TrendingUp size={16} color={sortBy === 'price' ? COLORS.background : COLORS.text} />
            <Text style={[styles.sortButtonText, sortBy === 'price' && styles.sortButtonTextActive]}>
              {selectedLanguage === 'hi' ? '????????? ?????' : 'Best Price'}
            </Text>
          </TouchableOpacity>

          <TouchableOpacity style={[styles.sortButton, sortBy === 'distance' && styles.sortButtonActive]} onPress={() => setSortBy('distance')}>
            <Navigation size={16} color={sortBy === 'distance' ? COLORS.background : COLORS.text} />
            <Text style={[styles.sortButtonText, sortBy === 'distance' && styles.sortButtonTextActive]}>
              {selectedLanguage === 'hi' ? '???????' : 'Nearest'}
            </Text>
          </TouchableOpacity>
        </View>

        <View style={styles.section}>
          <Text style={styles.sectionTitle}>
            {selectedLanguage === 'hi' ? `${filteredMandis.length} ???? ????` : `${filteredMandis.length} Mandis found`}
          </Text>

          {loading ? (
            <View style={styles.stateContainer}>
              <ActivityIndicator size="large" color={COLORS.primary} />
              <Text style={styles.stateText}>{selectedLanguage === 'hi' ? '???? ??? ?? ??? ??...' : 'Loading mandi data...'}</Text>
            </View>
          ) : error ? (
            <View style={styles.errorContainer}>
              <AlertCircle size={20} color={COLORS.error} />
              <Text style={styles.errorText}>{error}</Text>
            </View>
          ) : (
            filteredMandis.map((mandi, index) => {
              const isBestPrice = sortBy === 'price' && index === 0 && mandi.price !== null;
              const transportCost = mandi.distance !== null ? Math.round(mandi.distance * 2) : null;
              const netPrice = mandi.price !== null && transportCost !== null ? mandi.price - transportCost : null;

              return (
                <TouchableOpacity key={mandi.id} style={[styles.mandiCard, isBestPrice && styles.mandiCardBest]}>
                  {isBestPrice && (
                    <View style={styles.bestBadge}>
                      <Text style={styles.bestBadgeText}>{selectedLanguage === 'hi' ? '????????? ?????' : 'Best Price'}</Text>
                    </View>
                  )}

                  <View style={styles.mandiHeader}>
                    <View style={styles.mandiIcon}>
                      <MapPin size={20} color={COLORS.primary} />
                    </View>
                    <View style={styles.mandiInfo}>
                      <Text style={styles.mandiName}>{mandi.name}</Text>
                      <Text style={styles.mandiLocation}>{mandi.district}, {mandi.state}</Text>
                    </View>
                  </View>

                  <View style={styles.priceGrid}>
                    <View style={styles.priceItem}>
                      <Text style={styles.priceLabel}>{selectedLanguage === 'hi' ? '?????' : 'Price'}</Text>
                      <Text style={styles.priceValue}>{mandi.price !== null ? `?${mandi.price}` : '--'}</Text>
                    </View>

                    <View style={styles.priceItem}>
                      <Text style={styles.priceLabel}>{selectedLanguage === 'hi' ? '????' : 'Distance'}</Text>
                      <Text style={styles.priceValue}>{mandi.distance !== null ? `${mandi.distance} km` : '--'}</Text>
                      <Text style={styles.priceSubtext}>
                        {transportCost !== null
                          ? `${selectedLanguage === 'hi' ? '?' : '?'}${transportCost} ${selectedLanguage === 'hi' ? '??????' : 'transport'}`
                          : '--'}
                      </Text>
                    </View>

                    <View style={styles.priceItem}>
                      <Text style={styles.priceLabel}>{selectedLanguage === 'hi' ? '????? ????' : 'Net'}</Text>
                      <Text style={[styles.priceValue, styles.netPriceValue]}>{netPrice !== null ? `?${netPrice}` : '--'}</Text>
                      <Text style={styles.priceSubtext}>{selectedLanguage === 'hi' ? '?????? ?? ???' : 'after transport'}</Text>
                    </View>
                  </View>

                  <View style={styles.arrivalContainer}>
                    <View style={styles.arrivalInfo}>
                      <Text style={styles.arrivalLabel}>{selectedLanguage === 'hi' ? '?? ?? ???:' : "Today's arrival:"}</Text>
                      <Text style={styles.arrivalValue}>{mandi.arrival !== null ? `${mandi.arrival.toLocaleString()} Q` : '--'}</Text>
                    </View>
                    <View style={styles.arrivalBar}>
                      <View
                        style={[
                          styles.arrivalFill,
                          { width: `${mandi.arrival !== null ? Math.min((mandi.arrival / 5000) * 100, 100) : 0}%` },
                        ]}
                      />
                    </View>
                  </View>
                </TouchableOpacity>
              );
            })
          )}
        </View>
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: COLORS.background,
  },
  scrollView: {
    flex: 1,
    padding: 16,
  },
  header: {
    marginBottom: 20,
  },
  title: {
    fontSize: 28,
    fontWeight: 'bold',
    color: COLORS.text,
    marginBottom: 4,
  },
  subtitle: {
    fontSize: 16,
    color: COLORS.textSecondary,
  },
  searchContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: COLORS.card,
    borderRadius: 12,
    paddingHorizontal: 16,
    marginBottom: 16,
    borderWidth: 1,
    borderColor: COLORS.border,
  },
  searchIcon: {
    marginRight: 12,
  },
  searchInput: {
    flex: 1,
    paddingVertical: 14,
    fontSize: 16,
    color: COLORS.text,
  },
  sortContainer: {
    flexDirection: 'row',
    gap: 8,
    marginBottom: 20,
  },
  sortButton: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
    backgroundColor: COLORS.card,
    borderRadius: 10,
    paddingVertical: 12,
    borderWidth: 1,
    borderColor: COLORS.border,
  },
  sortButtonActive: {
    backgroundColor: COLORS.primary,
    borderColor: COLORS.primary,
  },
  sortButtonText: {
    fontSize: 14,
    color: COLORS.text,
    fontWeight: '500',
  },
  sortButtonTextActive: {
    color: COLORS.background,
  },
  section: {
    marginBottom: 24,
  },
  sectionTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: COLORS.text,
    marginBottom: 12,
  },
  mandiCard: {
    backgroundColor: COLORS.card,
    borderRadius: 16,
    padding: 16,
    marginBottom: 12,
    borderWidth: 1,
    borderColor: COLORS.border,
  },
  mandiCardBest: {
    borderColor: COLORS.primary,
    borderWidth: 2,
  },
  bestBadge: {
    position: 'absolute',
    top: -1,
    right: 16,
    backgroundColor: COLORS.primary,
    paddingHorizontal: 12,
    paddingVertical: 4,
    borderRadius: 12,
  },
  bestBadgeText: {
    fontSize: 12,
    fontWeight: '600',
    color: COLORS.background,
  },
  mandiHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 16,
  },
  mandiIcon: {
    width: 44,
    height: 44,
    borderRadius: 22,
    backgroundColor: `${COLORS.primary}20`,
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: 12,
  },
  mandiInfo: {
    flex: 1,
  },
  mandiName: {
    fontSize: 16,
    fontWeight: '600',
    color: COLORS.text,
    marginBottom: 2,
  },
  mandiLocation: {
    fontSize: 14,
    color: COLORS.textSecondary,
  },
  priceGrid: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 16,
  },
  priceItem: {
    flex: 1,
    alignItems: 'center',
  },
  priceLabel: {
    fontSize: 12,
    color: COLORS.textSecondary,
    marginBottom: 4,
  },
  priceValue: {
    fontSize: 18,
    fontWeight: 'bold',
    color: COLORS.text,
    marginBottom: 4,
  },
  netPriceValue: {
    color: COLORS.primary,
  },
  priceSubtext: {
    fontSize: 11,
    color: COLORS.textSecondary,
  },
  arrivalContainer: {
    paddingTop: 12,
    borderTopWidth: 1,
    borderTopColor: COLORS.border,
  },
  arrivalInfo: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 8,
  },
  arrivalLabel: {
    fontSize: 12,
    color: COLORS.textSecondary,
  },
  arrivalValue: {
    fontSize: 12,
    fontWeight: '600',
    color: COLORS.text,
  },
  arrivalBar: {
    height: 4,
    backgroundColor: `${COLORS.primary}30`,
    borderRadius: 2,
    overflow: 'hidden',
  },
  arrivalFill: {
    height: '100%',
    backgroundColor: COLORS.primary,
  },
  stateContainer: {
    alignItems: 'center',
    gap: 8,
    paddingVertical: 24,
  },
  stateText: {
    color: COLORS.textSecondary,
  },
  errorContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    backgroundColor: `${COLORS.error}1A`,
    borderRadius: 10,
    borderWidth: 1,
    borderColor: `${COLORS.error}55`,
    padding: 12,
  },
  errorText: {
    color: COLORS.error,
    flex: 1,
  },
});

