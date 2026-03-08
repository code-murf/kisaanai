import React, { useState, useEffect } from 'react';
import {
  View, Text, StyleSheet, ScrollView, TouchableOpacity, Switch, Alert,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { LinearGradient } from 'expo-linear-gradient';
import {
  Globe, Bell, Shield, ChevronRight, Check, User,
  MapPin, Phone, Mail, RotateCcw, Info, LogOut, Heart,
} from 'lucide-react-native';
import { useAppStore } from '../store/useAppStore';
import { api } from '../services/api';

const C = { bg: '#0a0a0a', card: '#171717', border: '#262626', muted: '#a3a3a3', green: '#34d399', white: '#fff' };

export default function SettingsScreen() {
  const { selectedLanguage, setSelectedLanguage } = useAppStore();
  const hi = selectedLanguage === 'hi';
  const [notifs, setNotifs] = useState({ price: true, weather: true, market: false, whatsapp: false });
  const [profile, setProfile] = useState<any>(null);
  const [states, setStates] = useState<string[]>([]);

  useEffect(() => {
    // Try to load profile and states
    (async () => {
      try {
        const [p, st] = await Promise.all([api.getProfile(), api.getMandiStates()]);
        if (p) setProfile(p);
        if (st) setStates(st);
      } catch {}
    })();
  }, []);

  const initials = profile?.name
    ? profile.name.split(' ').map((w: string) => w[0]).join('').toUpperCase().slice(0, 2)
    : 'K';

  const handleReset = () => {
    Alert.alert(
      hi ? 'रीसेट करें?' : 'Reset Settings?',
      hi ? 'सभी सेटिंग्स डिफ़ॉल्ट पर वापस आ जाएंगी' : 'All settings will be restored to defaults',
      [
        { text: hi ? 'रद्द करें' : 'Cancel', style: 'cancel' },
        { text: hi ? 'रीसेट' : 'Reset', style: 'destructive', onPress: () => {
          setNotifs({ price: true, weather: true, market: false, whatsapp: false });
          setSelectedLanguage('hi');
        }},
      ]
    );
  };

  return (
    <SafeAreaView style={s.container} edges={['top']}>
      <ScrollView showsVerticalScrollIndicator={false} contentContainerStyle={s.content}>
        {/* Header */}
        <View style={s.headerRow}>
          <View>
            <Text style={s.title}>{hi ? '⚙️ सेटिंग्स' : '⚙️ Settings'}</Text>
            <Text style={s.subtitle}>{hi ? 'ऐप कस्टमाइज़ करें' : 'Customize your experience'}</Text>
          </View>
          <TouchableOpacity style={s.resetBtn} onPress={handleReset}>
            <RotateCcw size={16} color={C.muted} />
          </TouchableOpacity>
        </View>

        {/* Profile Card */}
        <View style={s.profileCard}>
          <LinearGradient colors={['#059669', '#10b981']} style={s.profileBanner} start={{ x: 0, y: 0 }} end={{ x: 1, y: 0 }} />
          <View style={s.profileBody}>
            <View style={s.avatarRow}>
              <View style={s.avatar}>
                <Text style={s.avatarText}>{initials}</Text>
              </View>
              <View style={{ flex: 1 }}>
                <Text style={s.profileName}>{profile?.name || profile?.full_name || (hi ? 'किसान' : 'Farmer')}</Text>
                <Text style={s.profilePhone}>{profile?.phone || profile?.phone_number || (hi ? 'लॉगिन करें' : 'Login to see profile')}</Text>
                {profile?.name && <Text style={s.verifiedBadge}>{hi ? 'सत्यापित किसान' : 'Verified Farmer'} ✓</Text>}
              </View>
              <ChevronRight size={16} color={C.muted} />
            </View>
          </View>
        </View>

        {/* Language */}
        <View style={s.card}>
          <View style={s.cardHead}>
            <Globe size={16} color="#6366f1" />
            <Text style={s.cardTitle}>{hi ? 'भाषा' : 'Language'}</Text>
          </View>
          <View style={s.langRow}>
            {[
              { code: 'hi', flag: '🇮🇳', name: 'हिन्दी', sub: 'Hindi' },
              { code: 'en', flag: '🌐', name: 'English', sub: 'English' },
            ].map((l) => (
              <TouchableOpacity
                key={l.code}
                style={[s.langCard, selectedLanguage === l.code && s.langCardActive]}
                onPress={() => setSelectedLanguage(l.code as any)}
                activeOpacity={0.7}
              >
                <Text style={s.langFlag}>{l.flag}</Text>
                <Text style={s.langName}>{l.name}</Text>
                <Text style={s.langSub}>{l.sub}</Text>
                {selectedLanguage === l.code && <Check size={14} color={C.green} style={{ marginTop: 4 }} />}
              </TouchableOpacity>
            ))}
          </View>
        </View>

        {/* Account Info */}
        <View style={s.card}>
          <View style={s.cardHead}>
            <User size={16} color="#f59e0b" />
            <Text style={s.cardTitle}>{hi ? 'खाता' : 'Account'}</Text>
          </View>
          {[
            { icon: <Phone size={14} color={C.muted} />, l: hi ? 'फ़ोन नंबर' : 'Phone Number', v: profile?.phone || profile?.phone_number || '—' },
            { icon: <Mail size={14} color={C.muted} />, l: hi ? 'ईमेल' : 'Email', v: profile?.email || '—' },
            { icon: <User size={14} color={C.muted} />, l: hi ? 'नाम' : 'Name', v: profile?.name || profile?.full_name || '—' },
          ].map((item, i) => (
            <TouchableOpacity key={i} style={s.settingRow}>
              <View style={{ flexDirection: 'row', alignItems: 'center', gap: 10, flex: 1 }}>
                {item.icon}
                <View>
                  <Text style={s.settingLabel}>{item.l}</Text>
                  <Text style={s.settingValue}>{item.v}</Text>
                </View>
              </View>
              <ChevronRight size={14} color={C.muted} />
            </TouchableOpacity>
          ))}
        </View>

        {/* Location */}
        <View style={s.card}>
          <View style={s.cardHead}>
            <MapPin size={16} color="#10b981" />
            <Text style={s.cardTitle}>{hi ? 'स्थान' : 'Location'}</Text>
          </View>
          {[
            { l: hi ? 'राज्य' : 'State', v: profile?.state || (states.length > 0 ? states[0] : '—') },
            { l: hi ? 'ज़िला' : 'District', v: profile?.district || '—' },
            { l: hi ? 'डिफ़ॉल्ट मंडी' : 'Default Mandi', v: profile?.default_mandi || '—' },
          ].map((item, i) => (
            <TouchableOpacity key={i} style={s.settingRow}>
              <View>
                <Text style={s.settingLabel}>{item.l}</Text>
                <Text style={s.settingValue}>{item.v}</Text>
              </View>
              <ChevronRight size={14} color={C.muted} />
            </TouchableOpacity>
          ))}
        </View>

        {/* Notifications */}
        <View style={s.card}>
          <View style={s.cardHead}>
            <Bell size={16} color="#f43f5e" />
            <Text style={s.cardTitle}>{hi ? 'सूचनाएं' : 'Notifications'}</Text>
          </View>
          {[
            { k: 'price' as const, l: hi ? 'भाव अलर्ट' : 'Price Alerts', d: hi ? 'भाव बदलने पर सूचना' : 'Get notified when prices change' },
            { k: 'weather' as const, l: hi ? 'मौसम अलर्ट' : 'Weather Alerts', d: hi ? 'मौसम अलर्ट प्राप्त करें' : 'Receive weather alerts' },
            { k: 'market' as const, l: hi ? 'बाज़ार अपडेट' : 'Market Updates', d: hi ? 'बाज़ार अपडेट समाचार' : 'Market update news' },
            { k: 'whatsapp' as const, l: hi ? 'व्हाट्सएप सूचनाएं' : 'WhatsApp Notifications', d: hi ? 'व्हाट्सएप पर सूचनाएं' : 'Get notifications on WhatsApp' },
          ].map((n) => (
            <View key={n.k} style={s.settingRow}>
              <View style={{ flex: 1 }}>
                <Text style={s.settingLabel}>{n.l}</Text>
                <Text style={s.settingDesc}>{n.d}</Text>
              </View>
              <Switch
                value={notifs[n.k]}
                onValueChange={() => setNotifs((p) => ({ ...p, [n.k]: !p[n.k] }))}
                trackColor={{ false: '#39393d', true: C.green }}
                thumbColor={C.white}
              />
            </View>
          ))}
        </View>

        {/* Security */}
        <View style={s.card}>
          <View style={s.cardHead}>
            <Shield size={16} color="#8b5cf6" />
            <Text style={s.cardTitle}>{hi ? 'सुरक्षा और गोपनीयता' : 'Security & Privacy'}</Text>
          </View>
          {[
            { l: hi ? 'PIN बदलें' : 'Change PIN', v: hi ? 'अपडेट' : 'Update' },
            { l: hi ? 'गोपनीयता नीति' : 'Privacy Policy', v: hi ? 'देखें' : 'View' },
            { l: hi ? 'सेवा की शर्तें' : 'Terms of Service', v: hi ? 'देखें' : 'View' },
            { l: hi ? 'सहायता' : 'Help & Support', v: hi ? 'संपर्क करें' : 'Contact' },
          ].map((l, i) => (
            <TouchableOpacity key={i} style={s.settingRow}>
              <Text style={s.settingLabel}>{l.l}</Text>
              <View style={{ flexDirection: 'row', alignItems: 'center', gap: 4 }}>
                <Text style={s.settingAction}>{l.v}</Text>
                <ChevronRight size={14} color={C.muted} />
              </View>
            </TouchableOpacity>
          ))}
        </View>

        {/* App Info */}
        <View style={s.appInfo}>
          <Text style={s.appName}>KisaanAI v1.0.0</Text>
          <Text style={s.appMade}>
            {hi ? '❤️ भारत में बनाया' : 'Made with ❤️ in India'}
          </Text>
        </View>

        {/* Logout */}
        <TouchableOpacity style={s.logoutBtn} activeOpacity={0.7}>
          <LogOut size={16} color="#ff3b30" />
          <Text style={s.logoutText}>{hi ? 'लॉगआउट' : 'Log Out'}</Text>
        </TouchableOpacity>

        <View style={{ height: 90 }} />
      </ScrollView>
    </SafeAreaView>
  );
}

const s = StyleSheet.create({
  container: { flex: 1, backgroundColor: C.bg },
  content: { padding: 20 },

  headerRow: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 20 },
  title: { fontSize: 26, fontWeight: '700', color: C.white },
  subtitle: { fontSize: 13, color: C.muted, marginTop: 2 },
  resetBtn: { width: 40, height: 40, borderRadius: 12, backgroundColor: 'rgba(255,255,255,0.06)', alignItems: 'center', justifyContent: 'center', borderWidth: 0.5, borderColor: 'rgba(255,255,255,0.08)' },

  // Profile
  profileCard: { borderRadius: 16, overflow: 'hidden', marginBottom: 16, borderWidth: 0.5, borderColor: 'rgba(255,255,255,0.06)' },
  profileBanner: { height: 60 },
  profileBody: { padding: 16, paddingTop: 0, marginTop: -20 },
  avatarRow: { flexDirection: 'row', alignItems: 'center', gap: 14 },
  avatar: { width: 52, height: 52, borderRadius: 26, backgroundColor: '#059669', alignItems: 'center', justifyContent: 'center', borderWidth: 3, borderColor: '#000' },
  avatarText: { color: '#fff', fontSize: 18, fontWeight: '800' },
  profileName: { fontSize: 17, fontWeight: '700', color: C.white, marginTop: 8 },
  profilePhone: { fontSize: 13, color: C.muted, marginTop: 2 },
  verifiedBadge: { fontSize: 11, color: '#34d399', fontWeight: '600', marginTop: 2 },

  // Cards
  card: { borderRadius: 16, padding: 16, marginBottom: 12, borderWidth: 0.5, borderColor: 'rgba(255,255,255,0.06)', backgroundColor: 'rgba(255,255,255,0.03)' },
  cardHead: { flexDirection: 'row', alignItems: 'center', gap: 8, marginBottom: 14 },
  cardTitle: { fontSize: 15, fontWeight: '700', color: C.white },

  // Language
  langRow: { flexDirection: 'row', gap: 10 },
  langCard: { flex: 1, alignItems: 'center', paddingVertical: 16, borderRadius: 12, borderWidth: 1, borderColor: 'rgba(255,255,255,0.08)', backgroundColor: 'rgba(255,255,255,0.03)' },
  langCardActive: { borderColor: C.green, backgroundColor: 'rgba(16,185,129,0.1)' },
  langFlag: { fontSize: 28, marginBottom: 6 },
  langName: { fontSize: 16, fontWeight: '600', color: C.white },
  langSub: { fontSize: 12, color: C.muted, marginTop: 2 },

  // Setting Rows
  settingRow: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', paddingVertical: 14, borderBottomWidth: 0.5, borderBottomColor: 'rgba(255,255,255,0.04)' },
  settingLabel: { fontSize: 15, color: C.white, fontWeight: '500' },
  settingValue: { fontSize: 12, color: C.muted, marginTop: 1 },
  settingDesc: { fontSize: 11, color: C.muted, marginTop: 1 },
  settingAction: { fontSize: 12, color: C.muted },

  // App Info
  appInfo: { alignItems: 'center', paddingVertical: 24, gap: 4 },
  appName: { fontSize: 14, color: C.muted, fontWeight: '600' },
  appMade: { fontSize: 12, color: 'rgba(255,255,255,0.3)' },

  // Logout
  logoutBtn: { flexDirection: 'row', alignItems: 'center', justifyContent: 'center', gap: 8, backgroundColor: 'rgba(255,59,48,0.08)', borderRadius: 14, paddingVertical: 16, borderWidth: 0.5, borderColor: 'rgba(255,59,48,0.2)' },
  logoutText: { color: '#ff3b30', fontSize: 16, fontWeight: '600' },
});
