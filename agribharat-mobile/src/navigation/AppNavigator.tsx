import React from 'react';
import { View, StyleSheet, Platform } from 'react-native';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { NavigationContainer } from '@react-navigation/native';
import { createStackNavigator } from '@react-navigation/stack';
import { Home, MapPin, Mic, BarChart, Settings } from 'lucide-react-native';

import HomeScreen from '../screens/HomeScreen';
import MandiScreen from '../screens/MandiScreen';
import VoiceScreen from '../screens/VoiceScreen';
import ChartsScreen from '../screens/ChartsScreen';
import SettingsScreen from '../screens/SettingsScreen';

import DoctorScreen from '../screens/DoctorScreen';
import NewsScreen from '../screens/NewsScreen';
import CommunityScreen from '../screens/CommunityScreen';

const Tab = createBottomTabNavigator();
const Stack = createStackNavigator();

const C = { bg: '#0a0a0a', card: '#0a0a0a', border: '#262626', muted: '#a3a3a3', green: '#34d399' };

function TabIcon({ name, focused, color }: { name: string; focused: boolean; color: string }) {
  const size = 22;
  const w = focused ? 2 : 1.5;
  switch (name) {
    case 'Home': return <Home size={size} color={color} strokeWidth={w} />;
    case 'Mandi': return <MapPin size={size} color={color} strokeWidth={w} />;
    case 'Voice': return (
      <View style={[styles.micBtn, focused && styles.micBtnActive]}>
        <Mic size={20} color="#000" strokeWidth={2.5} />
      </View>
    );
    case 'Charts': return <BarChart size={size} color={color} strokeWidth={w} />;
    case 'Settings': return <Settings size={size} color={color} strokeWidth={w} />;
    default: return null;
  }
}

function TabNavigator() {
  return (
    <Tab.Navigator
      screenOptions={({ route }) => ({
        headerShown: false,
        tabBarIcon: ({ focused, color }) => <TabIcon name={route.name} focused={focused} color={color} />,
        tabBarActiveTintColor: C.green,
        tabBarInactiveTintColor: C.muted,
        tabBarStyle: {
          backgroundColor: C.card,
          borderTopColor: C.border,
          borderTopWidth: 0.5,
          height: Platform.OS === 'ios' ? 84 : 64,
          paddingBottom: Platform.OS === 'ios' ? 24 : 8,
          paddingTop: 6,
          elevation: 0,
        },
        tabBarLabelStyle: { fontSize: 10, fontWeight: '500' },
      })}
    >
      <Tab.Screen name="Home" component={HomeScreen} />
      <Tab.Screen name="Mandi" component={MandiScreen} />
      <Tab.Screen name="Voice" component={VoiceScreen} options={{ tabBarLabel: '' }} />
      <Tab.Screen name="Charts" component={ChartsScreen} />
      <Tab.Screen name="Settings" component={SettingsScreen} />
    </Tab.Navigator>
  );
}

export default function AppNavigator() {
  return (
    <NavigationContainer>
      <Stack.Navigator screenOptions={{ headerShown: false }}>
        <Stack.Screen name="MainTabs" component={TabNavigator} />
        <Stack.Screen name="Doctor" component={DoctorScreen} />
        <Stack.Screen name="News" component={NewsScreen} />
        <Stack.Screen name="Community" component={CommunityScreen} />
      </Stack.Navigator>
    </NavigationContainer>
  );
}

const styles = StyleSheet.create({
  micBtn: {
    width: 46, height: 46, borderRadius: 23,
    backgroundColor: '#34c759',
    alignItems: 'center', justifyContent: 'center',
    marginTop: -16,
  },
  micBtnActive: { backgroundColor: '#30b350' },
});
