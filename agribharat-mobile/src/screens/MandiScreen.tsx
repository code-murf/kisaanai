import React, { useState, useEffect } from 'react';
import { View, Text, StyleSheet, ScrollView, TouchableOpacity, TextInput } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { MapPin, Navigation, TrendingUp, TrendingDown, Search, SlidersHorizontal } from 'lucide-react-native';
import { COLORS, SAMPLE_MANDIS } from '../constants';
import { useAppStore } from '../store/useAppStore';
import { mockApi } from '../services/api';

export default function MandiScreen() {
  const { selectedLanguage } = useAppStore();
  const [searchQuery, setSearchQuery] = useState('');
  const [sortBy, setSortBy] = useState<'price' | 'distance'>('price');
  const [mandis, setMandis] = useState(SAMPLE_MANDIS);

  const filteredMandis = mandis
    .filter(m => m.name.toLowerCase().includes(searchQuery.toLowerCase()))
    .sort((a, b) => (sortBy === 'price' ? b.price - a.price : a.distance - b.distance));

  return (
    <SafeAreaView style={styles.container} edges={['bottom']}>
      <ScrollView style={styles.scrollView} showsVerticalScrollIndicator={false}>
        {/* Header */}
        <View style={styles.header}>
          <Text style={styles.title}>
            {selectedLanguage === 'hi' ? 'नज़दीकी मंडियां' : 'Nearby Mandis'}
          </Text>
          <Text style={styles.subtitle}>
            {selectedLanguage === 'hi'
              ? 'अपनी फसल बेचने के लिए सबसे अच्छा मंडी खोजें'
              : 'Find the best market to sell your produce'}
          </Text>
        </View>

        {/* Search Bar */}
        <View style={styles.searchContainer}>
          <Search size={20} color={COLORS.textSecondary} style={styles.searchIcon} />
          <TextInput
            style={styles.searchInput}
            placeholder={selectedLanguage === 'hi' ? 'मंडी खोजें...' : 'Search mandis...'}
            placeholderTextColor={COLORS.textSecondary}
            value={searchQuery}
            onChangeText={setSearchQuery}
          />
        </View>

        {/* Sort Buttons */}
        <View style={styles.sortContainer}>
          <TouchableOpacity
            style={[styles.sortButton, sortBy === 'price' && styles.sortButtonActive]}
            onPress={() => setSortBy('price')}
          >
            <TrendingUp
              size={16}
              color={sortBy === 'price' ? COLORS.background : COLORS.text}
            />
            <Text
              style={[
                styles.sortButtonText,
                sortBy === 'price' && styles.sortButtonTextActive,
              ]}
            >
              {selectedLanguage === 'hi' ? 'सर्वोत्तम मूल्य' : 'Best Price'}
            </Text>
          </TouchableOpacity>

          <TouchableOpacity
            style={[styles.sortButton, sortBy === 'distance' && styles.sortButtonActive]}
            onPress={() => setSortBy('distance')}
          >
            <Navigation
              size={16}
              color={sortBy === 'distance' ? COLORS.background : COLORS.text}
            />
            <Text
              style={[
                styles.sortButtonText,
                sortBy === 'distance' && styles.sortButtonTextActive,
              ]}
            >
              {selectedLanguage === 'hi' ? 'नज़दीकी' : 'Nearest'}
            </Text>
          </TouchableOpacity>
        </View>

        {/* Mandi List */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>
            {selectedLanguage === 'hi' ? `${filteredMandis.length} मंडी मिली` : `${filteredMandis.length} Mandis found`}
          </Text>

          {filteredMandis.map((mandi, index) => {
            const isBestPrice = sortBy === 'price' && index === 0;
            const transportCost = mandi.distance * 2;
            const netPrice = mandi.price - transportCost;

            return (
              <TouchableOpacity
                key={mandi.id}
                style={[styles.mandiCard, isBestPrice && styles.mandiCardBest]}
              >
                {isBestPrice && (
                  <View style={styles.bestBadge}>
                    <Text style={styles.bestBadgeText}>
                      {selectedLanguage === 'hi' ? 'सर्वोत्तम मूल्य' : 'Best Price'}
                    </Text>
                  </View>
                )}

                <View style={styles.mandiHeader}>
                  <View style={styles.mandiIcon}>
                    <MapPin size={20} color={COLORS.primary} />
                  </View>
                  <View style={styles.mandiInfo}>
                    <Text style={styles.mandiName}>{mandi.name}</Text>
                    <Text style={styles.mandiLocation}>
                      {mandi.district}, {mandi.state}
                    </Text>
                  </View>
                </View>

                <View style={styles.priceGrid}>
                  <View style={styles.priceItem}>
                    <Text style={styles.priceLabel}>
                      {selectedLanguage === 'hi' ? 'मूल्य' : 'Price'}
                    </Text>
                    <Text style={styles.priceValue}>₹{mandi.price}</Text>
                    <View style={styles.trendContainer}>
                      {index % 2 === 0 ? (
                        <TrendingUp size={12} color={COLORS.success} />
                      ) : (
                        <TrendingDown size={12} color={COLORS.error} />
                      )}
                      <Text
                        style={[
                          styles.trendText,
                          index % 2 === 0 ? styles.trendTextUp : styles.trendTextDown,
                        ]}
                      >
                        {index % 2 === 0 ? '+' : '-'}{Math.abs(Math.random() * 3).toFixed(1)}%
                      </Text>
                    </View>
                  </View>

                  <View style={styles.priceItem}>
                    <Text style={styles.priceLabel}>
                      {selectedLanguage === 'hi' ? 'दूरी' : 'Distance'}
                    </Text>
                    <Text style={styles.priceValue}>{mandi.distance} km</Text>
                    <Text style={styles.priceSubtext}>
                      {selectedLanguage === 'hi' ? '₹' : '₹'}
                      {transportCost} {selectedLanguage === 'hi' ? 'परिवहन' : 'transport'}
                    </Text>
                  </View>

                  <View style={styles.priceItem}>
                    <Text style={styles.priceLabel}>
                      {selectedLanguage === 'hi' ? 'शुद्ध कमाई' : 'Net'}
                    </Text>
                    <Text style={[styles.priceValue, styles.netPriceValue]}>₹{netPrice}</Text>
                    <Text style={styles.priceSubtext}>
                      {selectedLanguage === 'hi' ? 'परिवहन के बाद' : 'after transport'}
                    </Text>
                  </View>
                </View>

                <View style={styles.arrivalContainer}>
                  <View style={styles.arrivalInfo}>
                    <Text style={styles.arrivalLabel}>
                      {selectedLanguage === 'hi' ? 'आज की आवक:' : "Today's arrival:"}
                    </Text>
                    <Text style={styles.arrivalValue}>{mandi.arrival.toLocaleString()} Q</Text>
                  </View>
                  <View style={styles.arrivalBar}>
                    <View
                      style={[
                        styles.arrivalFill,
                        { width: `${Math.min((mandi.arrival / 5000) * 100, 100)}%` },
                      ]}
                    />
                  </View>
                </View>
              </TouchableOpacity>
            );
          })}
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
  trendContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
  },
  trendText: {
    fontSize: 12,
    fontWeight: '500',
  },
  trendTextUp: {
    color: COLORS.success,
  },
  trendTextDown: {
    color: COLORS.error,
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
});
