import React, { useState } from 'react';
import { View, Text, StyleSheet, ScrollView, TouchableOpacity } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { TrendingUp, TrendingDown, Calendar, Download } from 'lucide-react-native';
import { COLORS } from '../constants';
import { useAppStore } from '../store/useAppStore';

export default function ChartsScreen() {
  const { selectedLanguage } = useAppStore();
  const [chartType, setChartType] = useState<'history' | 'forecast'>('history');
  const [timeRange, setTimeRange] = useState<'7D' | '30D'>('7D');

  const historyData = [
    { date: 'Jan 01', value: 1180 },
    { date: 'Jan 02', value: 1195 },
    { date: 'Jan 03', value: 1180 },
    { date: 'Jan 04', value: 1210 },
    { date: 'Jan 05', value: 1230 },
    { date: 'Jan 06', value: 1240 },
    { date: 'Jan 07', value: 1240 },
    { date: 'Jan 08', value: 1255 },
    { date: 'Jan 09', value: 1240 },
    { date: 'Jan 10', value: 1260 },
    { date: 'Jan 11', value: 1275 },
    { date: 'Jan 12', value: 1280 },
  ];

  const forecastData = [
    { date: 'Jan 12', value: 1280 },
    { date: 'Jan 13', value: 1290 },
    { date: 'Jan 14', value: 1295 },
    { date: 'Jan 15', value: 1285 },
    { date: 'Jan 16', value: 1270 },
    { date: 'Jan 17', value: 1260 },
    { date: 'Jan 18', value: 1255 },
  ];

  const currentPrice = historyData[historyData.length - 1].value;
  const priceChange = ((currentPrice - historyData[0].value) / historyData[0].value) * 100;

  // Simple bar chart component
  const SimpleBarChart = ({ data, color }: { data: typeof historyData; color: string }) => {
    const maxValue = Math.max(...data.map(d => d.value));
    const minValue = Math.min(...data.map(d => d.value));
    const range = maxValue - minValue;

    return (
      <View style={styles.chartContainer}>
        <View style={styles.chartBars}>
          {data.map((item, index) => {
            const height = 20 + ((item.value - minValue) / range) * 150;
            return (
              <View key={index} style={styles.chartBarWrapper}>
                <View style={[styles.chartBar, { height, backgroundColor: color }]} />
                <Text style={styles.chartLabel}>{item.date.slice(4)}</Text>
              </View>
            );
          })}
        </View>
      </View>
    );
  };

  return (
    <SafeAreaView style={styles.container} edges={['bottom']}>
      <ScrollView style={styles.scrollView} showsVerticalScrollIndicator={false}>
        {/* Header */}
        <View style={styles.header}>
          <Text style={styles.title}>
            {selectedLanguage === 'hi' ? 'मूल्य विश्लेषण' : 'Price Analytics'}
          </Text>
          <Text style={styles.subtitle}>
            {selectedLanguage === 'hi' ? 'आलू (ज्योति) के लिए ऐतिहासिक रुझान और पूर्वानुमान' : 'Historical trends and forecasts for Potato (Jyoti)'}
          </Text>
        </View>

        {/* Time Range Selector */}
        <View style={styles.timeRangeContainer}>
          {['7D', '30D'].map((range) => (
            <TouchableOpacity
              key={range}
              style={[styles.timeRangeButton, timeRange === range && styles.timeRangeButtonActive]}
              onPress={() => setTimeRange(range as '7D' | '30D')}
            >
              <Text
                style={[styles.timeRangeText, timeRange === range && styles.timeRangeTextActive]}
              >
                {range}
              </Text>
            </TouchableOpacity>
          ))}
        </View>

        {/* Stats Cards */}
        <View style={styles.statsGrid}>
          <View style={styles.statCard}>
            <Text style={styles.statLabel}>
              {selectedLanguage === 'hi' ? 'वर्तमान मूल्य' : 'Current'}
            </Text>
            <Text style={styles.statValue}>₹{currentPrice}</Text>
            <Text style={styles.statUnit}>/Q</Text>
          </View>

          <View style={styles.statCard}>
            <Text style={styles.statLabel}>
              {selectedLanguage === 'hi' ? 'परिवर्तन' : 'Change'}
            </Text>
            <View style={styles.statValueContainer}>
              {priceChange >= 0 ? <TrendingUp size={16} color={COLORS.success} /> : <TrendingDown size={16} color={COLORS.error} />}
              <Text style={[styles.statValue, priceChange >= 0 ? styles.statValueUp : styles.statValueDown]}>
                {priceChange > 0 ? '+' : ''}{priceChange.toFixed(1)}%
              </Text>
            </View>
            <Text style={styles.statUnit}>vs {timeRange}</Text>
          </View>

          <View style={styles.statCard}>
            <Text style={styles.statLabel}>
              {selectedLanguage === 'hi' ? 'बेचने का दिन' : 'Best Day'}
            </Text>
            <Text style={styles.statValue}>Wed-Thu</Text>
            <Text style={styles.statUnit}>
              {selectedLanguage === 'hi' ? 'ऐतिहासिक' : 'Historical'}
            </Text>
          </View>
        </View>

        {/* Chart Type Selector */}
        <View style={styles.chartTypeContainer}>
          <TouchableOpacity
            style={[styles.chartTypeButton, chartType === 'history' && styles.chartTypeButtonActive]}
            onPress={() => setChartType('history')}
          >
            <Text style={[styles.chartTypeText, chartType === 'history' && styles.chartTypeTextActive]}>
              {selectedLanguage === 'hi' ? 'मूल्य इतिहास' : 'Price History'}
            </Text>
          </TouchableOpacity>

          <TouchableOpacity
            style={[styles.chartTypeButton, chartType === 'forecast' && styles.chartTypeButtonActive]}
            onPress={() => setChartType('forecast')}
          >
            <Text style={[styles.chartTypeText, chartType === 'forecast' && styles.chartTypeTextActive]}>
              {selectedLanguage === 'hi' ? 'AI पूर्वानुमान' : 'AI Forecast'}
            </Text>
          </TouchableOpacity>
        </View>

        {/* Chart Card */}
        <View style={styles.chartCard}>
          <View style={styles.chartHeader}>
            <Text style={styles.chartTitle}>
              {chartType === 'history'
                ? (selectedLanguage === 'hi' ? 'मूल्य इतिहास' : 'Price History')
                : (selectedLanguage === 'hi' ? 'AI मूल्य पूर्वानुमान' : 'AI Price Forecast')}
            </Text>
            <TouchableOpacity>
              <Download size={20} color={COLORS.textSecondary} />
            </TouchableOpacity>
          </View>

          {chartType === 'history' ? (
            <SimpleBarChart data={historyData} color={COLORS.primary} />
          ) : (
            <SimpleBarChart data={forecastData} color={COLORS.success} />
          )}

          {/* AI Insights for forecast */}
          {chartType === 'forecast' && (
            <View style={styles.insightsCard}>
              <Text style={styles.insightsTitle}>
                {selectedLanguage === 'hi' ? 'AI अंतर्दृष्टि' : 'AI Insights'}
              </Text>
              <Text style={styles.insightText}>
                {'• ' + (selectedLanguage === 'hi' ? 'Jan 14 को ₹1,295 पर चरम' : 'Peak on Jan 14 (₹1,295)')}
              </Text>
              <Text style={styles.insightText}>
                {'• ' + (selectedLanguage === 'hi' ? 'मध्यम विश्वास स्तर' : 'Moderate confidence')}
              </Text>
              <Text style={styles.insightText}>
                {'• ' + (selectedLanguage === 'hi' ? 'Jan 16 से पहले बेचने पर विचार करें' : 'Consider selling before Jan 16')}
              </Text>
            </View>
          )}
        </View>

        {/* Statistics */}
        <View style={styles.statsSection}>
          <Text style={styles.statsSectionTitle}>
            {selectedLanguage === 'hi' ? 'मूल्य आँकड़े' : 'Price Statistics'}
          </Text>
          <View style={styles.statsRow}>
            <View style={styles.statItem}>
              <Text style={styles.statItemLabel}>
                {selectedLanguage === 'hi' ? 'उच्चतम (7 दिन)' : 'Highest (7D)'}
              </Text>
              <Text style={styles.statItemValue}>₹1,280</Text>
            </View>
            <View style={styles.statItem}>
              <Text style={styles.statItemLabel}>
                {selectedLanguage === 'hi' ? 'निम्नतम (7 दिन)' : 'Lowest (7D)'}
              </Text>
              <Text style={styles.statItemValue}>₹1,180</Text>
            </View>
          </View>
          <View style={styles.statsRow}>
            <View style={styles.statItem}>
              <Text style={styles.statItemLabel}>
                {selectedLanguage === 'hi' ? 'औसत' : 'Average'}
              </Text>
              <Text style={styles.statItemValue}>₹1,237</Text>
            </View>
            <View style={styles.statItem}>
              <Text style={styles.statItemLabel}>
                {selectedLanguage === 'hi' ? 'अस्थिरता' : 'Volatility'}
              </Text>
              <Text style={styles.statItemValue}>Low</Text>
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
    marginBottom: 20,
  },
  title: {
    fontSize: 28,
    fontWeight: 'bold',
    color: COLORS.text,
    marginBottom: 4,
  },
  subtitle: {
    fontSize: 14,
    color: COLORS.textSecondary,
  },
  timeRangeContainer: {
    flexDirection: 'row',
    gap: 8,
    marginBottom: 20,
  },
  timeRangeButton: {
    flex: 1,
    backgroundColor: COLORS.card,
    borderRadius: 10,
    paddingVertical: 12,
    alignItems: 'center',
    borderWidth: 1,
    borderColor: COLORS.border,
  },
  timeRangeButtonActive: {
    backgroundColor: COLORS.primary,
    borderColor: COLORS.primary,
  },
  timeRangeText: {
    fontSize: 14,
    fontWeight: '600',
    color: COLORS.text,
  },
  timeRangeTextActive: {
    color: COLORS.background,
  },
  statsGrid: {
    flexDirection: 'row',
    gap: 12,
    marginBottom: 20,
  },
  statCard: {
    flex: 1,
    backgroundColor: COLORS.card,
    borderRadius: 12,
    padding: 16,
    alignItems: 'center',
    borderWidth: 1,
    borderColor: COLORS.border,
  },
  statLabel: {
    fontSize: 12,
    color: COLORS.textSecondary,
    marginBottom: 8,
  },
  statValue: {
    fontSize: 20,
    fontWeight: 'bold',
    color: COLORS.text,
  },
  statValueUp: {
    color: COLORS.success,
  },
  statValueDown: {
    color: COLORS.error,
  },
  statValueContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
  },
  statUnit: {
    fontSize: 11,
    color: COLORS.textSecondary,
  },
  chartTypeContainer: {
    flexDirection: 'row',
    gap: 8,
    marginBottom: 16,
  },
  chartTypeButton: {
    flex: 1,
    backgroundColor: COLORS.card,
    borderRadius: 10,
    paddingVertical: 12,
    alignItems: 'center',
    borderWidth: 1,
    borderColor: COLORS.border,
  },
  chartTypeButtonActive: {
    backgroundColor: `${COLORS.primary}30`,
    borderColor: COLORS.primary,
  },
  chartTypeText: {
    fontSize: 14,
    color: COLORS.text,
  },
  chartTypeTextActive: {
    color: COLORS.primary,
    fontWeight: '600',
  },
  chartCard: {
    backgroundColor: COLORS.card,
    borderRadius: 16,
    padding: 16,
    marginBottom: 20,
    borderWidth: 1,
    borderColor: COLORS.border,
  },
  chartHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 16,
  },
  chartTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: COLORS.text,
  },
  chartContainer: {
    alignItems: 'center',
  },
  chartBars: {
    flexDirection: 'row',
    alignItems: 'flex-end',
    justifyContent: 'space-between',
    height: 200,
    width: '100%',
    paddingHorizontal: 4,
  },
  chartBarWrapper: {
    flex: 1,
    alignItems: 'center',
    height: '100%',
    justifyContent: 'flex-end',
  },
  chartBar: {
    width: 16,
    borderRadius: 8,
  },
  chartLabel: {
    fontSize: 8,
    color: COLORS.textSecondary,
    marginTop: 4,
  },
  insightsCard: {
    backgroundColor: `${COLORS.primary}10`,
    borderRadius: 12,
    padding: 16,
    marginTop: 16,
    borderWidth: 1,
    borderColor: `${COLORS.primary}30`,
  },
  insightsTitle: {
    fontSize: 14,
    fontWeight: '600',
    color: COLORS.text,
    marginBottom: 12,
  },
  insightText: {
    fontSize: 12,
    color: COLORS.textSecondary,
    marginBottom: 4,
  },
  statsSection: {
    backgroundColor: COLORS.card,
    borderRadius: 16,
    padding: 16,
    borderWidth: 1,
    borderColor: COLORS.border,
  },
  statsSectionTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: COLORS.text,
    marginBottom: 16,
  },
  statsRow: {
    flexDirection: 'row',
    marginBottom: 16,
  },
  statItem: {
    flex: 1,
  },
  statItemLabel: {
    fontSize: 12,
    color: COLORS.textSecondary,
    marginBottom: 4,
  },
  statItemValue: {
    fontSize: 18,
    fontWeight: 'bold',
    color: COLORS.text,
  },
});
