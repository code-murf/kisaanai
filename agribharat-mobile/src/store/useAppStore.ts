import { create } from 'zustand';
import * as SecureStore from 'expo-secure-store';
import { persist, createJSONStorage } from 'zustand/middleware';

interface User {
  id: number;
  phone_number: string;
  full_name?: string;
  preferred_language: string;
}

interface AppStore {
  user: User | null;
  selectedCommodity: string;
  selectedLanguage: 'hi' | 'en';
  isLoading: boolean;

  setUser: (user: User | null) => void;
  setSelectedCommodity: (commodity: string) => void;
  setSelectedLanguage: (language: 'hi' | 'en') => void;
  setLoading: (loading: boolean) => void;
  logout: () => void;
}

// Custom storage adapter for SecureStore
const secureStorage = {
  getItem: async (key: string) => {
    return await SecureStore.getItemAsync(key);
  },
  setItem: async (key: string, value: string) => {
    await SecureStore.setItemAsync(key, value);
  },
  removeItem: async (key: string) => {
    await SecureStore.deleteItemAsync(key);
  },
};

export const useAppStore = create<AppStore>()(
  persist(
    (set) => ({
      user: null,
      selectedCommodity: 'potato',
      selectedLanguage: 'hi',
      isLoading: false,

      setUser: (user) => set({ user }),

      setSelectedCommodity: (commodity) => set({ selectedCommodity: commodity }),

      setSelectedLanguage: (language) => set({ selectedLanguage: language }),

      setLoading: (loading) => set({ isLoading: loading }),

      logout: () => {
        set({ user: null, selectedCommodity: 'potato' });
        SecureStore.deleteItemAsync('access_token');
        SecureStore.deleteItemAsync('refresh_token');
      },
    }),
    {
      name: 'agribharat-storage',
      storage: createJSONStorage(() => secureStorage),
    }
  )
);
