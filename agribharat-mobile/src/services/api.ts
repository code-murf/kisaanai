import axios, { AxiosInstance, AxiosError } from 'axios';
import * as SecureStore from 'expo-secure-store';

// Same live API as web frontend — backend prefix is /api/v1
const API_URL = 'https://kisaanai.duckdns.org/api/v1';

class ApiClient {
  private client: AxiosInstance;

  constructor() {
    this.client = axios.create({
      baseURL: API_URL,
      timeout: 30000,
      headers: { 'Content-Type': 'application/json' },
    });

    // Auth interceptor
    this.client.interceptors.request.use(async (config) => {
      try {
        const token = await SecureStore.getItemAsync('access_token');
        if (token) config.headers.Authorization = `Bearer ${token}`;
      } catch {}
      return config;
    });

    this.client.interceptors.response.use(
      (r) => r,
      async (err: AxiosError) => {
        if (err.response?.status === 401) {
          try { await SecureStore.deleteItemAsync('access_token'); } catch {}
        }
        return Promise.reject(err);
      }
    );
  }

  // ─── Stats (matches web: MagicDashboard fetchStats) ───
  async getStats() {
    const [mandisRes, commoditiesRes, statesRes] = await Promise.allSettled([
      this.client.get('/mandis', { params: { page_size: 1 } }),
      this.client.get('/commodities', { params: { page_size: 1 } }),
      this.client.get('/mandis/states'),
    ]);
    return {
      totalMandis: mandisRes.status === 'fulfilled' ? (mandisRes.value.data?.total || 0) : 0,
      totalCommodities: commoditiesRes.status === 'fulfilled' ? (commoditiesRes.value.data?.total || (Array.isArray(commoditiesRes.value.data) ? commoditiesRes.value.data.length : 0)) : 0,
      totalStates: statesRes.status === 'fulfilled' ? (Array.isArray(statesRes.value.data) ? statesRes.value.data.length : 0) : 0,
    };
  }

  // ─── Gainers & Losers (matches web: separate /prices/gainers and /prices/losers) ───
  async getGainers(limit = 4) {
    const r = await this.client.get('/prices/gainers', { params: { period: 7, limit } });
    return r.data || [];
  }
  async getLosers(limit = 4) {
    const r = await this.client.get('/prices/losers', { params: { period: 7, limit } });
    return r.data || [];
  }

  // ─── Weather (matches web: /weather/forecast) ───
  async getWeather(lat = 22.7196, lon = 75.8577, days = 3) {
    const r = await this.client.get('/weather/forecast', { params: { lat, lon, days } });
    return r.data || [];
  }

  // ─── Live Prices ───
  async getLivePrices(params?: { state?: string; commodity?: string; limit?: number }) {
    const r = await this.client.get('/prices/live', { params: { limit: 30, ...params } });
    return r.data;
  }

  // ─── Commodities ───
  async getCommodities() {
    const r = await this.client.get('/commodities');
    return r.data?.items || r.data || [];
  }

  // ─── Mandis ───
  async getMandis(params?: any) {
    const r = await this.client.get('/mandis', { params: { page_size: 50, ...params } });
    return r.data?.items || r.data || [];
  }
  async getMandiStates() {
    const r = await this.client.get('/mandis/states');
    return r.data || [];
  }

  // ─── Prices ───
  async getPrices(params: any) {
    const r = await this.client.get('/prices', { params: { page_size: 200, ...params } });
    return r.data?.items || r.data || [];
  }
  async getPriceTrend(commodityId: number, days = 30) {
    const r = await this.client.get(`/prices/trend/${commodityId}`, { params: { days } });
    return r.data || [];
  }
  async getCurrentPrices(commodityId: number) {
    const r = await this.client.get(`/prices/current/commodity/${commodityId}`, { params: { limit: 10 } });
    return r.data || [];
  }

  // Expose axios instance for screens that need direct access
  getAxios(): AxiosInstance {
    return this.client;
  }

  // ─── Forecasts ───
  async getForecast(commodityId: number) {
    const r = await this.client.get(`/forecasts/${commodityId}/1`, { params: { horizon_days: 7 } });
    return r.data;
  }

  // ─── Voice ───
  async sendVoiceText(text: string, language = 'hi-IN') {
    const r = await this.client.post('/voice/text', { text, language });
    return r.data;
  }
  async sendVoiceAudio(fileUri: string, language = 'hi-IN') {
    const formData = new FormData();
    const filename = fileUri.split('/').pop() || 'recording.m4a';
    const match = /\.(\w+)$/.exec(filename);
    const type = match ? `audio/${match[1]}` : 'audio/m4a';
    formData.append('file', { uri: fileUri, type, name: filename } as any);
    formData.append('language', language);
    const r = await this.client.post('/voice/query', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      timeout: 30000,
    });
    return r.data;
  }

  // ─── News ───
  async getNews() {
    const r = await this.client.get('/news');
    return r.data || [];
  }

  // ─── Community ───
  async getCommunityNotes() {
    const r = await this.client.get('/community/notes');
    return r.data || [];
  }
  async postCommunityNote(formData: FormData) {
    return this.client.post('/community/notes', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      timeout: 30000,
    });
  }
  async likeCommunityNote(noteId: string) {
    return this.client.post(`/community/notes/${noteId}/like`);
  }

  // ─── Diseases ───
  async diagnosePlant(formData: FormData) {
    const r = await this.client.post('/diseases/diagnose', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      timeout: 30000,
    });
    return r.data;
  }

  // ─── Auth ───
  async sendOTP(phone: string) {
    return this.client.post('/auth/otp/request', { phone_number: phone, purpose: 'login' });
  }
  async verifyOTP(phone: string, otp: string) {
    const r = await this.client.post('/auth/otp/verify', { phone_number: phone, otp_code: otp });
    if (r.data.access_token) await SecureStore.setItemAsync('access_token', r.data.access_token);
    if (r.data.refresh_token) await SecureStore.setItemAsync('refresh_token', r.data.refresh_token);
    return r.data;
  }
  async getProfile() {
    const r = await this.client.get('/auth/me');
    return r.data;
  }
}

export const api = new ApiClient();
