import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  Dimensions,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Search, TrendingUp, MapPin, Bell, ChevronRight } from 'lucide-react-native';
import { COLORS, COMMODITIES, SAMPLE_MANDIS } from '../constants';
import { useAppStore } from '../store/useAppStore';

const { width } = Dimensions.get('window');

export default function HomeScreen({ navigation }: any) {
  const { selectedCommodity, setSelectedCommodity, selectedLanguage } = useAppStore();
  const [currentPrice, setCurrentPrice] = useState(1240);

  const selectedCommodityData = COMMODITIES.find(c => c.value === selectedCommodity);

  return (
    <SafeAreaView style={styles.container} edges={['bottom']}>
      <ScrollView style={styles.scrollView} showsVerticalScrollIndicator={false}>
        {/* Header */}
        <View style={styles.header}>
          <View>
            <Text style={styles.greeting}>
              {selectedLanguage === 'hi' ? 'नमस्ते,' : 'Hello,'}
            </Text>
            <Text style={styles.userName}>Ram Lal</Text>
          </View>
          <TouchableOpacity style={styles.bellButton}>
            <Bell size={24} color={COLORS.text} />
            <View style={styles.badge} />
          </TouchableOpacity>
        </View>

        {/* Commodity Selector */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>
            {selectedLanguage === 'hi' ? 'फसल चुनें' : 'Select Crop'}
          </Text>
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

        {/* Price Card */}
        <View style={styles.priceCard}>
          <View style={styles.priceHeader}>
            <Text style={styles.priceTitle}>
              {selectedLanguage === 'hi' ? 'वर्तमान मूल्य' : 'Current Price'}
            </Text>
            <TrendingUp size={24} color={COLORS.success} />
          </View>
          <View style={styles.priceBody}>
            <Text style={styles.priceValue}>₹{currentPrice}</Text>
            <Text style={styles.priceUnit}>
              {selectedLanguage === 'hi' ? '/क्विंटल' : '/Quintal'}
            </Text>
          </View>
          <View style={styles.priceTrend}>
            <View style={styles.trendUp}>
              <TrendingUp size={16} color={COLORS.success} />
              <Text style={styles.trendText}>+2.5%</Text>
            </View>
            <Text style={styles.trendLabel}>
              {selectedLanguage === 'hi' ? 'कल से' : 'from yesterday'}
            </Text>
          </View>
        </View>

        {/* Quick Actions */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>
            {selectedLanguage === 'hi' ? 'त्वरित कार्य' : 'Quick Actions'}
          </Text>
          <View style={styles.actionsGrid}>
            <TouchableOpacity
              style={styles.actionCard}
              onPress={() => navigation.navigate('Voice')}
            >
              <View style={styles.actionIcon}>
                <Text style={styles.emoji}>🎤</Text>
              </View>
              <Text style={styles.actionLabel}>
                {selectedLanguage === 'hi' ? 'आवाज़ खोज' : 'Voice Search'}
              </Text>
            </TouchableOpacity>

            <TouchableOpacity
              style={styles.actionCard}
              onPress={() => navigation.navigate('Mandi')}
            >
              <View style={styles.actionIcon}>
                <Text style={styles.emoji}>📍</Text>
              </View>
              <Text style={styles.actionLabel}>
                {selectedLanguage === 'hi' ? 'मंडी खोजें' : 'Find Mandis'}
              </Text>
            </TouchableOpacity>

            <TouchableOpacity
              style={styles.actionCard}
              onPress={() => navigation.navigate('Charts')}
            >
              <View style={styles.actionIcon}>
                <Text style={styles.emoji}>📊</Text>
              </View>
              <Text style={styles.actionLabel}>
                {selectedLanguage === 'hi' ? 'मूल्य चार्ट' : 'Price Charts'}
              </Text>
            </TouchableOpacity>

            <TouchableOpacity
              style={styles.actionCard}
              onPress={() => navigation.navigate('Settings')}
            >
              <View style={styles.actionIcon}>
                <Text style={styles.emoji}>⚙️</Text>
              </View>
              <Text style={styles.actionLabel}>
                {selectedLanguage === 'hi' ? 'सेटिंग्स' : 'Settings'}
              </Text>
            </TouchableOpacity>
          </View>
        </View>

        {/* Best Mandi Card */}
        <TouchableOpacity
          style={styles.mandiCard}
          onPress={() => navigation.navigate('Mandi')}
        >
          <View style={styles.mandiHeader}>
            <View style={styles.mandiIcon}>
              <MapPin size={20} color={COLORS.primary} />
            </View>
            <View style={styles.mandiInfo}>
              <Text style={styles.mandiName}>Azadpur Mandi</Text>
              <Text style={styles.mandiLocation}>
                {selectedLanguage === 'hi' ? 'दिल्ली • 12 किमी' : 'Delhi • 12 km'}
              </Text>
            </View>
            <ChevronRight size={20} color={COLORS.textSecondary} />
          </View>
          <View style={styles.mandiPrice}>
            <Text style={styles.mandiPriceValue}>₹1,260</Text>
            <Text style={styles.mandiPriceLabel}>
              {selectedLanguage === 'hi' ? 'सर्वोत्तम मूल्य' : 'Best Price'}
            </Text>
          </View>
        </TouchableOpacity>

        {/* Alerts Section */}
        <View style={styles.section}>
          <View style={styles.sectionHeader}>
            <Text style={styles.sectionTitle}>
              {selectedLanguage === 'hi' ? 'हालिया अलर्ट' : 'Recent Alerts'}
            </Text>
            <TouchableOpacity>
              <Text style={styles.seeAll}>View All</Text>
            </TouchableOpacity>
          </View>

          <View style={styles.alertCard}>
            <View style={styles.alertIndicator} />
            <View style={styles.alertContent}>
              <Text style={styles.alertTitle}>
                {selectedLanguage === 'hi' ? 'भारी बारिश चेतावनी' : 'Heavy Rain Alert'}
              </Text>
              <Text style={styles.alertMessage}>
                {selectedLanguage === 'hi' ? '2 दिनों में अपेक्षित। जल्दी कटाई करें।' : 'Expected in 2 days. Harvest soon.'}
              </Text>
            </View>
          </View>

          <View style={styles.alertCard}>
            <View style={[styles.alertIndicator, styles.alertIndicatorSuccess]} />
            <View style={styles.alertContent}>
              <Text style={styles.alertTitle}>
                {selectedLanguage === 'hi' ? 'बाजार ऊपर की ओर' : 'Market Up-trend'}
              </Text>
              <Text style={styles.alertMessage}>
                {selectedLanguage === 'hi' ? 'प्याज की कीमतें बढ़ रही हैं।' : 'Onion prices rising nearby.'}
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
  seeAll: {
    fontSize: 14,
    color: COLORS.primary,
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
    color: COLORS.success,
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
    marginBottom: 8,
    borderWidth: 1,
    borderColor: COLORS.border,
  },
  alertIndicator: {
    width: 4,
    borderRadius: 2,
    backgroundColor: COLORS.error,
    marginRight: 12,
  },
  alertIndicatorSuccess: {
    backgroundColor: COLORS.success,
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
