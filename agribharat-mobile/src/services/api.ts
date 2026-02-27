import Constants from 'expo-constants';
import axios, { AxiosInstance, AxiosError } from 'axios';
import * as SecureStore from 'expo-secure-store';
import { Mandi, Commodity, Price, Forecast, Alert } from '../types';

const API_URL = Constants.expoConfig?.extra?.API_URL || 'http://localhost:8000/api/v1';

type PaginatedResponse<T> = {
  items: T[];
};

class ApiClient {
  private client: AxiosInstance;

  constructor() {
    this.client = axios.create({
      baseURL: API_URL,
      timeout: 15000,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    this.client.interceptors.request.use(async (config) => {
      const token = await SecureStore.getItemAsync('access_token');
      if (token) {
        config.headers.Authorization = `Bearer ${token}`;
      }
      return config;
    });

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
    return this.client.post('/auth/otp/request', { phone_number: phone, purpose: 'login' });
  }

  async verifyOTP(phone: string, otp: string) {
    const response = await this.client.post('/auth/otp/verify', { phone_number: phone, otp_code: otp });
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
    const response = await this.client.get<PaginatedResponse<Commodity>>('/commodities');
    return response.data.items || [];
  }

  // Mandi APIs
  async getMandis(params?: { state?: string; district?: string; page?: number; page_size?: number }): Promise<Mandi[]> {
    const response = await this.client.get<PaginatedResponse<Mandi>>('/mandis', { params });
    return response.data.items || [];
  }

  async getNearbyMandis(lat: number, lon: number, radius = 50): Promise<(Mandi & { distance_km: number })[]> {
    const response = await this.client.post('/mandis/nearby', {
      latitude: lat,
      longitude: lon,
      radius_km: radius,
      limit: 20,
    });
    return response.data;
  }

  async getOptimalMandi(lat: number, lon: number, commodityId: number) {
    return this.client.post('/routing/recommend', {
      latitude: lat,
      longitude: lon,
      commodity_id: commodityId,
    });
  }

  // Price APIs
  async getPriceHistory(params: {
    commodity_id: number;
    mandi_id?: number;
    start_date?: string;
    end_date?: string;
    days?: number;
  }): Promise<Price[]> {
    const response = await this.client.get<PaginatedResponse<Price>>('/prices', { params });
    return response.data.items || [];
  }

  async getCurrentPrice(commodityId: number, mandiId?: number): Promise<any[]> {
    if (mandiId) {
      const response = await this.client.get<any[]>(`/prices/current/mandi/${mandiId}`);
      return response.data.filter((p) => p.commodity_id === commodityId);
    }

    const response = await this.client.get<any[]>(`/prices/current/commodity/${commodityId}`);
    return response.data;
  }

  // Forecast APIs
  async getForecast(commodityId: number, mandiId: number, days = 7): Promise<Forecast[]> {
    const response = await this.client.get(`/forecasts/${commodityId}/${mandiId}`, {
      params: { horizon_days: days },
    });

    const payload = response.data;
    return [
      {
        date: payload.target_date,
        predicted_price: payload.predicted_price,
        lower_bound: payload.confidence_lower,
        upper_bound: payload.confidence_upper,
        confidence: payload.confidence,
      },
    ];
  }

  // Alert APIs (not available in current backend build)
  async getAlerts(): Promise<Alert[]> {
    throw new Error('Alerts endpoint is not available in current backend build');
  }

  async createAlert(_data: Omit<Alert, 'id' | 'is_active'>): Promise<Alert> {
    throw new Error('Alerts endpoint is not available in current backend build');
  }

  async deleteAlert(_id: number): Promise<void> {
    throw new Error('Alerts endpoint is not available in current backend build');
  }
}

export const api = new ApiClient();

