import Constants from 'expo-constants';
import axios, { AxiosInstance, AxiosError } from 'axios';
import * as SecureStore from 'expo-secure-store';

// Try ADB reverse (localhost) first, then WiFi IP as fallback
// For native builds: adb reverse tcp:8000 tcp:8000 makes localhost:8000 go to laptop
const PRIMARY_URL = 'http://localhost:8000/api/v1';
const FALLBACK_URL = 'http://192.168.29.111:8000/api/v1';

class ApiClient {
  private client: AxiosInstance;
  private activeUrl: string;

  constructor() {
    this.activeUrl = PRIMARY_URL;
    this.client = this.createClient(this.activeUrl);
    // Try primary, fallback silently
    this.detectWorkingUrl();
  }

  private createClient(baseURL: string): AxiosInstance {
    const c = axios.create({
      baseURL,
      timeout: 12000,
      headers: { 'Content-Type': 'application/json' },
    });

    c.interceptors.request.use(async (config) => {
      try {
        const token = await SecureStore.getItemAsync('access_token');
        if (token) config.headers.Authorization = `Bearer ${token}`;
      } catch {}
      return config;
    });

    c.interceptors.response.use(
      (r) => r,
      async (err: AxiosError) => {
        if (err.response?.status === 401) {
          try { await SecureStore.deleteItemAsync('access_token'); } catch {}
        }
        return Promise.reject(err);
      }
    );
    return c;
  }

  public getAxios(): AxiosInstance {
    return this.client;
  }

  private async detectWorkingUrl() {
    // Try localhost first (ADB reverse)
    try {
      await axios.get(`${PRIMARY_URL}/commodities`, { timeout: 3000 });
      this.activeUrl = PRIMARY_URL;
      this.client = this.createClient(PRIMARY_URL);
      console.log('[API] ✅ Using localhost (ADB reverse)');
      return;
    } catch {}

    // Try WiFi IP
    try {
      await axios.get(`${FALLBACK_URL}/commodities`, { timeout: 3000 });
      this.activeUrl = FALLBACK_URL;
      this.client = this.createClient(FALLBACK_URL);
      console.log('[API] ✅ Using WiFi IP');
      return;
    } catch {}

    console.log('[API] ⚠️ No backend reachable, using localhost');
    this.activeUrl = PRIMARY_URL;
    this.client = this.createClient(PRIMARY_URL);
  }

  // ─── Dashboard ───
  async getDashboardStats() {
    try { return (await this.client.get('/prices/dashboard-stats')).data; }
    catch { return { total_mandis: 20, total_commodities: 8, total_states: 11 }; }
  }

  // ─── Commodities ───
  async getCommodities(): Promise<any[]> {
    try { return (await this.client.get('/commodities')).data?.items || []; }
    catch { return []; }
  }

  // ─── Mandis ───
  async getMandis(params?: any): Promise<any[]> {
    try { return (await this.client.get('/mandis', { params: { page_size: 50, ...params } })).data?.items || []; }
    catch { return []; }
  }
  async getMandiStates(): Promise<string[]> {
    try { return (await this.client.get('/mandis/states')).data || []; }
    catch { return []; }
  }

  // ─── Prices ───
  async getPrices(params: any): Promise<any[]> {
    try { return (await this.client.get('/prices', { params: { page_size: 200, ...params } })).data?.items || []; }
    catch { return []; }
  }
  async getPriceTrend(commodityId: number, days = 30): Promise<any[]> {
    try { return (await this.client.get(`/prices/trend/${commodityId}`, { params: { days } })).data || []; }
    catch { return []; }
  }
  async getCurrentPrices(commodityId: number): Promise<any[]> {
    try { return (await this.client.get(`/prices/current/commodity/${commodityId}`, { params: { limit: 10 } })).data || []; }
    catch { return []; }
  }
  async getGainersLosers(): Promise<any> {
    try { return (await this.client.get('/prices/gainers-losers')).data; }
    catch { return { gainers: [], losers: [] }; }
  }

  // ─── Forecasts ───
  async getForecast(commodityId: number): Promise<any> {
    try { return (await this.client.get(`/forecasts/${commodityId}/1`, { params: { horizon_days: 7 } })).data; }
    catch { return null; }
  }

  // ─── Weather ───
  async getWeather(lat = 22.7196, lon = 75.8577): Promise<any[]> {
    try { return (await this.client.get('/weather/forecast', { params: { lat, lon, days: 3 } })).data || []; }
    catch { return []; }
  }

  // ─── Live Prices (data.gov.in) ───
  async getLivePrices(params?: { state?: string; commodity?: string; limit?: number }): Promise<any> {
    try {
      const r = await this.client.get('/prices/live', { params: { limit: 30, ...params } });
      return r.data;
    } catch { return { records: [], total: 0 }; }
  }

  // ─── Voice (text → LLM → TTS) ───
  async sendVoiceText(text: string, language = 'hi-IN'): Promise<any> {
    const r = await this.client.post('/voice/text', { text, language });
    return r.data;
  }

  // ─── Voice (audio → Sarvam STT → Groq AI → Sarvam TTS) ───
  async sendVoiceAudio(fileUri: string, language = 'hi-IN'): Promise<any> {
    const formData = new FormData();
    // Expo audio on Android/iOS uses .m4a format typically when using HIGH_QUALITY
    const filename = fileUri.split('/').pop() || 'recording.m4a';
    const match = /\.(\w+)$/.exec(filename);
    const type = match ? `audio/${match[1]}` : 'audio/m4a';

    formData.append('file', {
      uri: fileUri,
      type: type,
      name: filename,
    } as any);
    formData.append('language', language);

    const r = await this.client.post('/voice/query', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      timeout: 30000,
    });
    return r.data;
  }

  // ─── News ───
  async getNews(): Promise<any[]> {
    try { return (await this.client.get('/news/news')).data || []; }
    catch { return []; }
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
    try { return (await this.client.get('/auth/me')).data; }
    catch { return null; }
  }
}

export const api = new ApiClient();
