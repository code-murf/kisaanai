import React from 'react';
import { View, Text, StyleSheet, ScrollView, TouchableOpacity, Switch } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { User, MapPin, Globe, Bell, Shield, ChevronRight, Moon, Sun } from 'lucide-react-native';
import { COLORS, LANGUAGES } from '../constants';
import { useAppStore } from '../store/useAppStore';

export default function SettingsScreen() {
  const { user, selectedLanguage, setSelectedLanguage, logout } = useAppStore();
  const [darkMode, setDarkMode] = React.useState(true);
  const [notifications, setNotifications] = React.useState({
    priceAlerts: true,
    weatherAlerts: true,
    marketUpdates: false,
    whatsapp: true,
  });

  const SettingSection = ({ title, icon: Icon, children }: any) => (
    <View style={styles.section}>
      <View style={styles.sectionHeader}>
        <Icon size={20} color={COLORS.primary} />
        <Text style={styles.sectionTitle}>{title}</Text>
      </View>
      <View style={styles.sectionContent}>{children}</View>
    </View>
  );

  const SettingItem = ({ label, value, action, onPress, isToggle, toggleValue }: any) => (
    <TouchableOpacity
      style={styles.settingItem}
      onPress={onPress}
      disabled={!onPress && !isToggle}
    >
      <View style={styles.settingLeft}>
        <Text style={styles.settingLabel}>{label}</Text>
        {value && <Text style={styles.settingValue}>{value}</Text>}
      </View>
      {isToggle ? (
        <Switch
          value={toggleValue}
          onValueChange={onPress}
          trackColor={{ false: COLORS.border, true: COLORS.primary }}
          thumbColor={toggleValue ? COLORS.background : COLORS.textSecondary}
        />
      ) : (
        <ChevronRight size={20} color={COLORS.textSecondary} />
      )}
    </TouchableOpacity>
  );

  return (
    <SafeAreaView style={styles.container} edges={['bottom']}>
      <ScrollView style={styles.scrollView} showsVerticalScrollIndicator={false}>
        {/* Profile Card */}
        <View style={styles.profileCard}>
          <View style={styles.avatar}>
            <Text style={styles.avatarText}>RL</Text>
          </View>
          <View style={styles.profileInfo}>
            <Text style={styles.profileName}>Ram Lal</Text>
            <Text style={styles.profilePhone}>+91 98765 43210</Text>
            <Text style={styles.verified}>Verified Farmer</Text>
          </View>
        </View>

        {/* Account Section */}
        <SettingSection title="Account" icon={User}>
          <SettingItem label="Phone Number" value="+91 98765 43210" action="Edit" />
          <SettingItem label="Name" value="Ram Lal" action="Edit" />
          <SettingItem label="Email" value="ram@example.com" action="Edit" />
        </SettingSection>

        {/* Location Section */}
        <SettingSection title="Location" icon={MapPin}>
          <SettingItem label="State" value="Uttar Pradesh" action="Change" />
          <SettingItem label="District" value="Meerut" action="Change" />
          <SettingItem label="Default Mandi" value="Meerut Mandi" action="Change" />
        </SettingSection>

        {/* Preferences Section */}
        <SettingSection title="Preferences" icon={Globe}>
          <View style={styles.languageSelector}>
            {LANGUAGES.map((lang) => (
              <TouchableOpacity
                key={lang.code}
                style={[
                  styles.languageButton,
                  selectedLanguage === lang.code && styles.languageButtonActive,
                ]}
                onPress={() => setSelectedLanguage(lang.code as 'hi' | 'en')}
              >
                <Text
                  style={[
                    styles.languageButtonText,
                    selectedLanguage === lang.code && styles.languageButtonTextActive,
                  ]}
                >
                  {lang.name}
                </Text>
              </TouchableOpacity>
            ))}
          </View>
          <SettingItem
            label="Dark Mode"
            value={darkMode ? 'Enabled' : 'Disabled'}
            isToggle
            toggleValue={darkMode}
            onPress={() => setDarkMode(!darkMode)}
          />
          <SettingItem label="Default Commodity" value="Potato (Jyoti)" action="Change" />
        </SettingSection>

        {/* Notifications Section */}
        <SettingSection title="Notifications" icon={Bell}>
          <SettingItem
            label="Price Alerts"
            isToggle
            toggleValue={notifications.priceAlerts}
            onPress={() => setNotifications({ ...notifications, priceAlerts: !notifications.priceAlerts })}
          />
          <SettingItem
            label="Weather Alerts"
            isToggle
            toggleValue={notifications.weatherAlerts}
            onPress={() => setNotifications({ ...notifications, weatherAlerts: !notifications.weatherAlerts })}
          />
          <SettingItem
            label="Market Updates"
            isToggle
            toggleValue={notifications.marketUpdates}
            onPress={() => setNotifications({ ...notifications, marketUpdates: !notifications.marketUpdates })}
          />
          <SettingItem label="WhatsApp Notifications" value="Enabled" action="Manage" />
        </SettingSection>

        {/* Security Section */}
        <SettingSection title="Security" icon={Shield}>
          <SettingItem label="Change PIN" action="Update" />
          <SettingItem
            label="Biometric Login"
            value="Enabled"
            isToggle
            toggleValue={true}
          />
          <SettingItem label="Privacy Policy" action="View" />
          <SettingItem label="Terms of Service" action="View" />
        </SettingSection>

        {/* App Info */}
        <View style={styles.appInfo}>
          <Text style={styles.appName}>Agri-Analytics Platform</Text>
          <Text style={styles.appVersion}>Version 1.0.0</Text>
          <Text style={styles.appTagline}>Made with ❤️ for Indian Farmers</Text>
        </View>

        {/* Logout Button */}
        <TouchableOpacity style={styles.logoutButton} onPress={logout}>
          <Text style={styles.logoutText}>Logout</Text>
        </TouchableOpacity>
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
  profileCard: {
    flexDirection: 'row',
    backgroundColor: COLORS.card,
    borderRadius: 16,
    padding: 16,
    marginBottom: 24,
    alignItems: 'center',
    borderWidth: 1,
    borderColor: COLORS.border,
  },
  avatar: {
    width: 60,
    height: 60,
    borderRadius: 30,
    backgroundColor: COLORS.primary,
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: 16,
  },
  avatarText: {
    fontSize: 24,
    fontWeight: 'bold',
    color: COLORS.background,
  },
  profileInfo: {
    flex: 1,
  },
  profileName: {
    fontSize: 18,
    fontWeight: 'bold',
    color: COLORS.text,
    marginBottom: 4,
  },
  profilePhone: {
    fontSize: 14,
    color: COLORS.textSecondary,
    marginBottom: 4,
  },
  verified: {
    fontSize: 12,
    color: COLORS.primary,
  },
  section: {
    backgroundColor: COLORS.card,
    borderRadius: 16,
    marginBottom: 16,
    borderWidth: 1,
    borderColor: COLORS.border,
  },
  sectionHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    padding: 16,
    paddingBottom: 8,
  },
  sectionTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: COLORS.text,
  },
  sectionContent: {
    paddingHorizontal: 16,
    paddingBottom: 8,
  },
  settingItem: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingVertical: 12,
    borderBottomWidth: 1,
    borderBottomColor: COLORS.border,
  },
  settingLeft: {
    flex: 1,
  },
  settingLabel: {
    fontSize: 14,
    color: COLORS.text,
    marginBottom: 2,
  },
  settingValue: {
    fontSize: 12,
    color: COLORS.textSecondary,
  },
  languageSelector: {
    flexDirection: 'row',
    gap: 8,
    paddingVertical: 8,
    marginBottom: 8,
  },
  languageButton: {
    flex: 1,
    backgroundColor: COLORS.background,
    borderRadius: 8,
    paddingVertical: 10,
    alignItems: 'center',
    borderWidth: 1,
    borderColor: COLORS.border,
  },
  languageButtonActive: {
    backgroundColor: COLORS.primary,
    borderColor: COLORS.primary,
  },
  languageButtonText: {
    fontSize: 14,
    color: COLORS.text,
  },
  languageButtonTextActive: {
    color: COLORS.background,
    fontWeight: '600',
  },
  appInfo: {
    backgroundColor: `${COLORS.primary}10`,
    borderRadius: 16,
    padding: 20,
    alignItems: 'center',
    marginBottom: 16,
    borderWidth: 1,
    borderColor: `${COLORS.primary}30`,
  },
  appName: {
    fontSize: 16,
    fontWeight: '600',
    color: COLORS.text,
    marginBottom: 4,
  },
  appVersion: {
    fontSize: 14,
    color: COLORS.textSecondary,
    marginBottom: 4,
  },
  appTagline: {
    fontSize: 12,
    color: COLORS.textSecondary,
  },
  logoutButton: {
    backgroundColor: `${COLORS.error}20`,
    borderRadius: 12,
    padding: 16,
    alignItems: 'center',
    marginBottom: 24,
    borderWidth: 1,
    borderColor: COLORS.error,
  },
  logoutText: {
    fontSize: 16,
    fontWeight: '600',
    color: COLORS.error,
  },
});
