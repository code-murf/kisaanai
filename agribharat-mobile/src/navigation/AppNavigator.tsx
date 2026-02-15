import React from 'react';
import { View } from 'react-native';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { NavigationContainer } from '@react-navigation/native';
import { Home, Map, Mic, BarChart3, Settings } from 'lucide-react-native';
import { COLORS } from '../constants';

import HomeScreen from '../screens/HomeScreen';
import MandiScreen from '../screens/MandiScreen';
import VoiceScreen from '../screens/VoiceScreen';
import ChartsScreen from '../screens/ChartsScreen';
import SettingsScreen from '../screens/SettingsScreen';

const Tab = createBottomTabNavigator();

function TabIcon({ name, focused, color }: { name: string; focused: boolean; color: string }) {
  const size = focused ? 24 : 20;

  switch (name) {
    case 'Home':
      return <Home size={size} color={color} strokeWidth={focused ? 2.5 : 2} />;
    case 'Mandi':
      return <Map size={size} color={color} strokeWidth={focused ? 2.5 : 2} />;
    case 'Voice':
      return (
        <View style={{
          width: focused ? 48 : 40,
          height: focused ? 48 : 40,
          borderRadius: focused ? 24 : 20,
          backgroundColor: COLORS.primary,
          alignItems: 'center',
          justifyContent: 'center',
          marginTop: focused ? -20 : -10,
        }}>
          <Mic size={focused ? 24 : 18} color={COLORS.background} strokeWidth={2.5} />
        </View>
      );
    case 'Charts':
      return <BarChart3 size={size} color={color} strokeWidth={focused ? 2.5 : 2} />;
    case 'Settings':
      return <Settings size={size} color={color} strokeWidth={focused ? 2.5 : 2} />;
    default:
      return null;
  }
}

export default function AppNavigator() {
  return (
    <NavigationContainer>
      <Tab.Navigator
        screenOptions={({ route }) => ({
          headerShown: false,
          tabBarIcon: ({ focused, color }) => (
            <TabIcon name={route.name} focused={focused} color={color} />
          ),
          tabBarActiveTintColor: COLORS.primary,
          tabBarInactiveTintColor: COLORS.textSecondary,
          tabBarStyle: {
            backgroundColor: COLORS.card,
            borderTopColor: COLORS.border,
            borderTopWidth: 1,
            height: 70,
            paddingBottom: 10,
            paddingTop: 10,
          },
          tabBarLabelStyle: {
            fontSize: 11,
            fontWeight: '500',
          },
        })}
      >
        <Tab.Screen
          name="Home"
          component={HomeScreen}
          options={{ tabBarLabel: 'Home' }}
        />
        <Tab.Screen
          name="Mandi"
          component={MandiScreen}
          options={{ tabBarLabel: 'Mandi' }}
        />
        <Tab.Screen
          name="Voice"
          component={VoiceScreen}
          options={{ tabBarLabel: 'Voice' }}
        />
        <Tab.Screen
          name="Charts"
          component={ChartsScreen}
          options={{ tabBarLabel: 'Charts' }}
        />
        <Tab.Screen
          name="Settings"
          component={SettingsScreen}
          options={{ tabBarLabel: 'Settings' }}
        />
      </Tab.Navigator>
    </NavigationContainer>
  );
}
