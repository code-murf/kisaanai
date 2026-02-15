import Constants from 'expo-constants';
import axios, { AxiosInstance, AxiosError } from 'axios';
import * as SecureStore from 'expo-secure-store';
import { Mandi, Commodity, Price, Forecast, Alert, User } from '../types';

const API_URL = Constants.expoConfig?.extra?.API_URL || 'http://localhost:8000/api/v1';

class ApiClient {
  private client: AxiosInstance;

  constructor() {
    this.client = axios.create({
      baseURL: API_URL,
      timeout: 10000,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // Add auth interceptor
    this.client.interceptors.request.use(async (config) => {
      const token = await SecureStore.getItemAsync('access_token');
      if (token) {
        config.headers.Authorization = `Bearer ${token}`;
      }
      return config;
    });

    // Handle token refresh
    this.client.interceptors.response.use(
      (response) => response,
      async (error: AxiosError) => {
        if (error.response?.status === 401) {
          await SecureStore.deleteItemAsync('access_token');
          await SecureStore.deleteItemAsync('refresh_token');
        }
        return Promise.reject(error);
      }
    );
  }

  // Auth APIs
  async sendOTP(phone: string) {
    return this.client.post('/auth/send-otp', { phone_number: phone });
  }

  async verifyOTP(phone: string, otp: string) {
    const response = await this.client.post('/auth/verify-otp', { phone_number: phone, otp_code: otp });
    if (response.data.access_token) {
      await SecureStore.setItemAsync('access_token', response.data.access_token);
    }
    if (response.data.refresh_token) {
      await SecureStore.setItemAsync('refresh_token', response.data.refresh_token);
    }
    return response.data;
  }

  // Commodity APIs
  async getCommodities(): Promise<Commodity[]> {
    const response = await this.client.get('/commodities');
    return response.data;
  }

  // Mandi APIs
  async getMandis(params?: { state?: string; district?: string }): Promise<Mandi[]> {
    const response = await this.client.get('/mandis', { params });
    return response.data;
  }

  async getNearbyMandis(lat: number, lon: number, radius = 50): Promise<Mandi[]> {
    const response = await this.client.get(`/mandis/nearby?lat=${lat}&lon=${lon}&radius=${radius}`);
    return response.data;
  }

  async getOptimalMandi(lat: number, lon: number, commodityId: number) {
    return this.client.post('/mandi/optimal', {
      latitude: lat,
      longitude: lon,
      commodity_id: commodityId,
    });
  }

  // Price APIs
  async getPriceHistory(params: { commodity_id: number; mandi_id?: number; start_date?: string; end_date?: string }): Promise<Price[]> {
    const response = await this.client.get('/prices/history', { params });
    return response.data;
  }

  async getCurrentPrice(commodityId: number, mandiId?: number) {
    const response = await this.client.get(`/prices/current?commodity_id=${commodityId}${mandiId ? `&mandi_id=${mandiId}` : ''}`);
    return response.data;
  }

  // Forecast APIs
  async getForecast(commodityId: number, mandiId: number, days = 7): Promise<Forecast[]> {
    const response = await this.client.post('/forecast/predict', {
      commodity_id: commodityId,
      mandi_id: mandiId,
      forecast_days: days,
    });
    return response.data;
  }

  // Alert APIs
  async getAlerts(): Promise<Alert[]> {
    const response = await this.client.get('/alerts');
    return response.data;
  }

  async createAlert(data: Omit<Alert, 'id' | 'is_active'>): Promise<Alert> {
    const response = await this.client.post('/alerts', data);
    return response.data;
  }

  async deleteAlert(id: number): Promise<void> {
    await this.client.delete(`/alerts/${id}`);
  }
}

export const api = new ApiClient();

// For demo without backend
export const mockApi = {
  async getNearbyMandis(lat: number, lon: number): Promise<Mandi[]> {
    // Simulate API delay
    await new Promise(resolve => setTimeout(resolve, 500));
    return [
      { id: 1, name: 'Azadpur Mandi', state: 'Delhi', district: 'Delhi', latitude: 28.7131, longitude: 77.1678, price: 1240, distance: 12 },
      { id: 2, name: 'Okhla Mandi', state: 'Delhi', district: 'Delhi', latitude: 28.5398, longitude: 77.2721, price: 1210, distance: 15 },
      { id: 3, name: 'Ghazipur Mandi', state: 'Delhi', district: 'Delhi', latitude: 28.6289, longitude: 77.3328, price: 1260, distance: 18 },
    ];
  },

  async getForecast(): Promise<Forecast[]> {
    await new Promise(resolve => setTimeout(resolve, 500));
    const today = new Date();
    return Array.from({ length: 7 }, (_, i) => {
      const date = new Date(today);
      date.setDate(date.getDate() + i);
      const basePrice = 1240;
      const variance = Math.random() * 100 - 50;
      return {
        date: date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
        predicted_price: Math.round(basePrice + variance),
        lower_bound: Math.round(basePrice + variance - 40),
        upper_bound: Math.round(basePrice + variance + 40),
      };
    });
  },
};
