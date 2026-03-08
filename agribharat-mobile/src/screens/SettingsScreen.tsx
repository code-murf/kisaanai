import React, { useState } from 'react';
import {
  View, Text, StyleSheet, ScrollView, TouchableOpacity, Switch,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Globe, Bell, Shield, ChevronRight, Moon, Check } from 'lucide-react-native';
import { COLORS } from '../constants';
import { useAppStore } from '../store/useAppStore';

const C = { bg: '#000', card: '#111', border: '#1c1c1e', muted: '#8e8e93', green: '#34c759', white: '#fff' };

export default function SettingsScreen() {
  const { selectedLanguage, setSelectedLanguage } = useAppStore();
  const hi = selectedLanguage === 'hi';
  const [notifs, setNotifs] = useState({ price: true, weather: true, market: false });

  return (
    <SafeAreaView style={s.container} edges={['top']}>
      <ScrollView showsVerticalScrollIndicator={false} contentContainerStyle={s.content}>
        <Text style={s.title}>{hi ? 'सेटिंग्स' : 'Settings'}</Text>

        {/* Profile */}
        <View style={s.card}>
          <View style={s.profileRow}>
            <View style={s.avatar}><Text style={s.avatarText}>K</Text></View>
            <View style={{ flex: 1 }}>
              <Text style={s.profileName}>{hi ? 'किसान' : 'Farmer'}</Text>
              <Text style={s.profileSub}>{hi ? 'प्रोफ़ाइल सेट करें' : 'Set up your profile'}</Text>
            </View>
            <ChevronRight size={16} color={C.muted} />
          </View>
        </View>

        {/* Language */}
        <View style={s.card}>
          <View style={s.cardHead}><Globe size={16} color={C.muted} /><Text style={s.cardTitle}>{hi ? 'भाषा' : 'Language'}</Text></View>
          <View style={s.langRow}>
            {[
              { code: 'hi', name: 'हिन्दी', sub: 'Hindi' },
              { code: 'en', name: 'English', sub: 'English' },
            ].map((l) => (
              <TouchableOpacity key={l.code} style={[s.langCard, selectedLanguage === l.code && s.langCardActive]} onPress={() => setSelectedLanguage(l.code)}>
                <Text style={s.langName}>{l.name}</Text>
                <Text style={s.langSub}>{l.sub}</Text>
                {selectedLanguage === l.code && <Check size={14} color={C.green} style={{ marginTop: 4 }} />}
              </TouchableOpacity>
            ))}
          </View>
        </View>

        {/* Notifications */}
        <View style={s.card}>
          <View style={s.cardHead}><Bell size={16} color={C.muted} /><Text style={s.cardTitle}>{hi ? 'सूचनाएं' : 'Notifications'}</Text></View>
          {[
            { k: 'price' as const, l: hi ? 'भाव अलर्ट' : 'Price Alerts' },
            { k: 'weather' as const, l: hi ? 'मौसम अलर्ट' : 'Weather Alerts' },
            { k: 'market' as const, l: hi ? 'बाज़ार अपडेट' : 'Market Updates' },
          ].map((n) => (
            <View key={n.k} style={s.settingRow}>
              <Text style={s.settingLabel}>{n.l}</Text>
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
          <View style={s.cardHead}><Shield size={16} color={C.muted} /><Text style={s.cardTitle}>{hi ? 'सुरक्षा' : 'More'}</Text></View>
          {[hi ? 'गोपनीयता नीति' : 'Privacy Policy', hi ? 'सेवा की शर्तें' : 'Terms of Service', hi ? 'सहायता' : 'Help & Support'].map((l, i) => (
            <TouchableOpacity key={i} style={s.settingRow}>
              <Text style={s.settingLabel}>{l}</Text>
              <ChevronRight size={14} color={C.muted} />
            </TouchableOpacity>
          ))}
        </View>

        {/* App Info */}
        <View style={s.appInfo}>
          <Text style={s.appName}>KisaanAI v1.0.0</Text>
          <Text style={s.appMade}>{hi ? '❤️ भारत में बनाया' : 'Made with ❤️ in India'}</Text>
        </View>

        {/* Logout */}
        <TouchableOpacity style={s.logoutBtn}>
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
  title: { fontSize: 26, fontWeight: '700', color: C.white, marginBottom: 20 },

  card: { backgroundColor: C.card, borderRadius: 12, padding: 16, marginBottom: 12, borderWidth: 0.5, borderColor: C.border },
  cardHead: { flexDirection: 'row', alignItems: 'center', gap: 8, marginBottom: 14 },
  cardTitle: { fontSize: 15, fontWeight: '600', color: C.white },

  profileRow: { flexDirection: 'row', alignItems: 'center', gap: 14 },
  avatar: { width: 44, height: 44, borderRadius: 22, backgroundColor: C.green, alignItems: 'center', justifyContent: 'center' },
  avatarText: { color: C.bg, fontSize: 18, fontWeight: '700' },
  profileName: { fontSize: 16, fontWeight: '600', color: C.white },
  profileSub: { fontSize: 13, color: C.muted, marginTop: 1 },

  langRow: { flexDirection: 'row', gap: 10 },
  langCard: { flex: 1, alignItems: 'center', paddingVertical: 16, borderRadius: 10, borderWidth: 1, borderColor: C.border },
  langCardActive: { borderColor: C.green, backgroundColor: 'rgba(52,199,89,0.08)' },
  langName: { fontSize: 16, fontWeight: '600', color: C.white },
  langSub: { fontSize: 12, color: C.muted, marginTop: 2 },

  settingRow: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', paddingVertical: 14, borderBottomWidth: 0.5, borderBottomColor: C.border },
  settingLabel: { fontSize: 15, color: C.white },

  appInfo: { alignItems: 'center', paddingVertical: 20, gap: 4 },
  appName: { fontSize: 14, color: C.muted },
  appMade: { fontSize: 12, color: '#555' },

  logoutBtn: { backgroundColor: '#1c1c1e', borderRadius: 12, paddingVertical: 16, alignItems: 'center', borderWidth: 0.5, borderColor: '#3a3a3c' },
  logoutText: { color: '#ff3b30', fontSize: 16, fontWeight: '500' },
});
