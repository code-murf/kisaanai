import React, { useState, useEffect, useMemo } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  Dimensions,
  ActivityIndicator,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { TrendingUp, TrendingDown, MapPin, Bell, ChevronRight } from 'lucide-react-native';
import { COLORS, COMMODITIES } from '../constants';
import { useAppStore } from '../store/useAppStore';
import { api } from '../services/api';

const { width } = Dimensions.get('window');

type BestMandi = {
  id: number;
  name: string;
  district: string;
  state: string;
  price: number;
};

export default function HomeScreen({ navigation }: any) {
  const { user, selectedCommodity, setSelectedCommodity, selectedLanguage } = useAppStore();
  const [currentPrice, setCurrentPrice] = useState<number | null>(null);
  const [priceChangePct, setPriceChangePct] = useState<number | null>(null);
  const [bestMandi, setBestMandi] = useState<BestMandi | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const selectedCommodityData = COMMODITIES.find((c) => c.value === selectedCommodity);

  const selectedCommodityId = useMemo(() => {
    return selectedCommodityData?.id ?? 1;
  }, [selectedCommodityData]);

  useEffect(() => {
    let mounted = true;

    const loadDashboard = async () => {
      setLoading(true);
      setError(null);

      try {
        const [nearbyMandis, currentPrices] = await Promise.all([
          api.getNearbyMandis(28.6139, 77.209, 80),
          api.getCurrentPrice(selectedCommodityId),
        ]);

        const priceByMandi = new Map<number, any>();
        for (const row of currentPrices) {
          priceByMandi.set(row.mandi_id, row);
        }

        const ranked = nearbyMandis
          .map((m) => {
            const priceRow = priceByMandi.get(m.id);
            return {
              id: m.id,
              name: m.name,
              district: m.district,
              state: m.state,
              price: typeof priceRow?.modal_price === 'number' ? priceRow.modal_price : null,
              arrival: typeof priceRow?.arrival_qty === 'number' ? priceRow.arrival_qty : null,
            };
          })
          .filter((m) => m.price !== null)
          .sort((a, b) => (b.price as number) - (a.price as number));

        const best = ranked[0] as BestMandi | undefined;

        let changePct: number | null = null;
        if (best?.id) {
          const history = await api.getPriceHistory({
            commodity_id: selectedCommodityId,
            mandi_id: best.id,
            days: 2,
          });

          if (history.length >= 2 && history[0].modal_price && history[1].modal_price) {
            const latest = Number(history[0].modal_price);
            const prev = Number(history[1].modal_price);
            if (prev > 0) {
              changePct = ((latest - prev) / prev) * 100;
            }
          }
        }

        if (mounted) {
          setBestMandi(best ?? null);
          setCurrentPrice(best?.price ?? null);
          setPriceChangePct(changePct);
        }
      } catch (e) {
        if (mounted) {
          setError(e instanceof Error ? e.message : 'Failed to load live data');
          setBestMandi(null);
          setCurrentPrice(null);
          setPriceChangePct(null);
        }
      } finally {
        if (mounted) {
          setLoading(false);
        }
      }
    };

    loadDashboard();

    return () => {
      mounted = false;
    };
  }, [selectedCommodityId]);

  return (
    <SafeAreaView style={styles.container} edges={['bottom']}>
      <ScrollView style={styles.scrollView} showsVerticalScrollIndicator={false}>
        <View style={styles.header}>
          <View>
            <Text style={styles.greeting}>{selectedLanguage === 'hi' ? 'नमस्ते,' : 'Hello,'}</Text>
            <Text style={styles.userName}>{user?.full_name || 'Farmer'}</Text>
          </View>
          <TouchableOpacity style={styles.bellButton}>
            <Bell size={24} color={COLORS.text} />
            <View style={styles.badge} />
          </TouchableOpacity>
        </View>

        <View style={styles.section}>
          <Text style={styles.sectionTitle}>{selectedLanguage === 'hi' ? 'फसल चुनें' : 'Select Crop'}</Text>
          <ScrollView horizontal showsHorizontalScrollIndicator={false} style={styles.commodityScroll}>
            {COMMODITIES.map((commodity) => (
              <TouchableOpacity
                key={commodity.id}
                style={[
                  styles.commodityChip,
                  selectedCommodity === commodity.value && styles.commodityChipActive,
                ]}
                onPress={() => setSelectedCommodity(commodity.value)}
              >
                <Text
                  style={[
                    styles.commodityChipText,
                    selectedCommodity === commodity.value && styles.commodityChipTextActive,
                  ]}
                >
                  {selectedLanguage === 'hi' ? commodity.name_hi : commodity.name}
                </Text>
              </TouchableOpacity>
            ))}
          </ScrollView>
        </View>

        <View style={styles.priceCard}>
          <View style={styles.priceHeader}>
            <Text style={styles.priceTitle}>{selectedLanguage === 'hi' ? 'वर्तमान मूल्य' : 'Current Price'}</Text>
            {priceChangePct !== null && priceChangePct >= 0 ? (
              <TrendingUp size={24} color={COLORS.success} />
            ) : (
              <TrendingDown size={24} color={COLORS.error} />
            )}
          </View>

          {loading ? (
            <View style={styles.loadingRow}>
              <ActivityIndicator size="small" color={COLORS.primary} />
              <Text style={styles.loadingText}>{selectedLanguage === 'hi' ? 'लाइव डेटा लोड हो रहा है...' : 'Loading live data...'}</Text>
            </View>
          ) : error ? (
            <Text style={styles.errorText}>{error}</Text>
          ) : (
            <>
              <View style={styles.priceBody}>
                <Text style={styles.priceValue}>{currentPrice !== null ? `₹${currentPrice}` : '--'}</Text>
                <Text style={styles.priceUnit}>{selectedLanguage === 'hi' ? '/क्विंटल' : '/Quintal'}</Text>
              </View>
              <View style={styles.priceTrend}>
                {priceChangePct !== null ? (
                  <>
                    <View style={styles.trendUp}>
                      {priceChangePct >= 0 ? (
                        <TrendingUp size={16} color={COLORS.success} />
                      ) : (
                        <TrendingDown size={16} color={COLORS.error} />
                      )}
                      <Text style={[styles.trendText, { color: priceChangePct >= 0 ? COLORS.success : COLORS.error }]}>
                        {priceChangePct >= 0 ? '+' : ''}{priceChangePct.toFixed(1)}%
                      </Text>
                    </View>
                    <Text style={styles.trendLabel}>{selectedLanguage === 'hi' ? 'पिछले दिन से' : 'from previous day'}</Text>
                  </>
                ) : (
                  <Text style={styles.trendLabel}>{selectedLanguage === 'hi' ? 'परिवर्तन डेटा उपलब्ध नहीं' : 'Change data unavailable'}</Text>
                )}
              </View>
            </>
          )}
        </View>

        <View style={styles.section}>
          <Text style={styles.sectionTitle}>{selectedLanguage === 'hi' ? 'त्वरित कार्य' : 'Quick Actions'}</Text>
          <View style={styles.actionsGrid}>
            <TouchableOpacity style={styles.actionCard} onPress={() => navigation.navigate('Voice')}>
              <View style={styles.actionIcon}>
                <Text style={styles.emoji}>🎤</Text>
              </View>
              <Text style={styles.actionLabel}>{selectedLanguage === 'hi' ? 'आवाज़ खोज' : 'Voice Search'}</Text>
            </TouchableOpacity>

            <TouchableOpacity style={styles.actionCard} onPress={() => navigation.navigate('Mandi')}>
              <View style={styles.actionIcon}>
                <Text style={styles.emoji}>📍</Text>
              </View>
              <Text style={styles.actionLabel}>{selectedLanguage === 'hi' ? 'मंडी खोजें' : 'Find Mandis'}</Text>
            </TouchableOpacity>

            <TouchableOpacity style={styles.actionCard} onPress={() => navigation.navigate('Charts')}>
              <View style={styles.actionIcon}>
                <Text style={styles.emoji}>📊</Text>
              </View>
              <Text style={styles.actionLabel}>{selectedLanguage === 'hi' ? 'मूल्य चार्ट' : 'Price Charts'}</Text>
            </TouchableOpacity>

            <TouchableOpacity style={styles.actionCard} onPress={() => navigation.navigate('Settings')}>
              <View style={styles.actionIcon}>
                <Text style={styles.emoji}>⚙️</Text>
              </View>
              <Text style={styles.actionLabel}>{selectedLanguage === 'hi' ? 'सेटिंग्स' : 'Settings'}</Text>
            </TouchableOpacity>
          </View>
        </View>

        <TouchableOpacity style={styles.mandiCard} onPress={() => navigation.navigate('Mandi')}>
          <View style={styles.mandiHeader}>
            <View style={styles.mandiIcon}>
              <MapPin size={20} color={COLORS.primary} />
            </View>
            <View style={styles.mandiInfo}>
              <Text style={styles.mandiName}>{bestMandi?.name || (selectedLanguage === 'hi' ? 'डेटा उपलब्ध नहीं' : 'No mandi data')}</Text>
              <Text style={styles.mandiLocation}>
                {bestMandi ? `${bestMandi.district}, ${bestMandi.state}` : '--'}
              </Text>
            </View>
            <ChevronRight size={20} color={COLORS.textSecondary} />
          </View>
          <View style={styles.mandiPrice}>
            <Text style={styles.mandiPriceValue}>{bestMandi?.price ? `₹${bestMandi.price}` : '--'}</Text>
            <Text style={styles.mandiPriceLabel}>{selectedLanguage === 'hi' ? 'सर्वोत्तम मूल्य' : 'Best Price'}</Text>
          </View>
        </TouchableOpacity>

        <View style={styles.section}>
          <View style={styles.sectionHeader}>
            <Text style={styles.sectionTitle}>{selectedLanguage === 'hi' ? 'अलर्ट' : 'Alerts'}</Text>
          </View>
          <View style={styles.alertCard}>
            <View style={styles.alertIndicator} />
            <View style={styles.alertContent}>
              <Text style={styles.alertTitle}>{selectedLanguage === 'hi' ? 'लाइव अलर्ट इंटीग्रेशन प्रगति पर' : 'Live alerts integration in progress'}</Text>
              <Text style={styles.alertMessage}>
                {selectedLanguage === 'hi'
                  ? 'वर्तमान बैकएंड बिल्ड में अलर्ट एपीआई सक्षम नहीं है।'
                  : 'Alerts API is not enabled in the current backend build.'}
              </Text>
            </View>
          </View>
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
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 24,
  },
  greeting: {
    fontSize: 14,
    color: COLORS.textSecondary,
  },
  userName: {
    fontSize: 24,
    fontWeight: 'bold',
    color: COLORS.text,
    marginTop: 4,
  },
  bellButton: {
    position: 'relative',
    padding: 8,
  },
  badge: {
    position: 'absolute',
    top: 8,
    right: 8,
    width: 8,
    height: 8,
    borderRadius: 4,
    backgroundColor: COLORS.error,
  },
  section: {
    marginBottom: 24,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: COLORS.text,
    marginBottom: 12,
  },
  sectionHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 12,
  },
  commodityScroll: {
    flexDirection: 'row',
  },
  commodityChip: {
    paddingHorizontal: 16,
    paddingVertical: 10,
    borderRadius: 20,
    backgroundColor: COLORS.card,
    marginRight: 8,
    borderWidth: 1,
    borderColor: COLORS.border,
  },
  commodityChipActive: {
    backgroundColor: COLORS.primary,
    borderColor: COLORS.primary,
  },
  commodityChipText: {
    fontSize: 14,
    color: COLORS.text,
  },
  commodityChipTextActive: {
    color: COLORS.background,
    fontWeight: '600',
  },
  priceCard: {
    backgroundColor: COLORS.card,
    borderRadius: 16,
    padding: 20,
    marginBottom: 24,
    borderWidth: 1,
    borderColor: COLORS.border,
  },
  priceHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 16,
  },
  priceTitle: {
    fontSize: 16,
    color: COLORS.textSecondary,
  },
  loadingRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    marginVertical: 12,
  },
  loadingText: {
    color: COLORS.textSecondary,
  },
  errorText: {
    color: COLORS.error,
  },
  priceBody: {
    flexDirection: 'row',
    alignItems: 'baseline',
    marginBottom: 12,
  },
  priceValue: {
    fontSize: 48,
    fontWeight: 'bold',
    color: COLORS.text,
  },
  priceUnit: {
    fontSize: 18,
    color: COLORS.textSecondary,
    marginLeft: 4,
  },
  priceTrend: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  trendUp: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
  },
  trendText: {
    fontSize: 16,
    fontWeight: '600',
  },
  trendLabel: {
    fontSize: 14,
    color: COLORS.textSecondary,
  },
  actionsGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 12,
  },
  actionCard: {
    width: (width - 48) / 2 - 6,
    backgroundColor: COLORS.card,
    borderRadius: 16,
    padding: 16,
    alignItems: 'center',
    borderWidth: 1,
    borderColor: COLORS.border,
  },
  actionIcon: {
    width: 48,
    height: 48,
    borderRadius: 24,
    backgroundColor: `${COLORS.primary}20`,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 8,
  },
  emoji: {
    fontSize: 24,
  },
  actionLabel: {
    fontSize: 12,
    color: COLORS.text,
    textAlign: 'center',
  },
  mandiCard: {
    backgroundColor: COLORS.card,
    borderRadius: 16,
    padding: 16,
    borderWidth: 1,
    borderColor: COLORS.border,
    marginBottom: 24,
  },
  mandiHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 12,
  },
  mandiIcon: {
    width: 40,
    height: 40,
    borderRadius: 20,
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
  },
  mandiLocation: {
    fontSize: 14,
    color: COLORS.textSecondary,
    marginTop: 2,
  },
  mandiPrice: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  mandiPriceValue: {
    fontSize: 24,
    fontWeight: 'bold',
    color: COLORS.primary,
  },
  mandiPriceLabel: {
    fontSize: 12,
    color: COLORS.textSecondary,
  },
  alertCard: {
    flexDirection: 'row',
    backgroundColor: COLORS.card,
    borderRadius: 12,
    padding: 16,
    borderWidth: 1,
    borderColor: COLORS.border,
  },
  alertIndicator: {
    width: 4,
    borderRadius: 2,
    backgroundColor: COLORS.warning,
    marginRight: 12,
  },
  alertContent: {
    flex: 1,
  },
  alertTitle: {
    fontSize: 14,
    fontWeight: '600',
    color: COLORS.text,
    marginBottom: 4,
  },
  alertMessage: {
    fontSize: 12,
    color: COLORS.textSecondary,
  },
});
