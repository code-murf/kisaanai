/**
 * API Client for KisaanAI Backend
 * Handles all HTTP requests with proper error handling and token management
 */

const API_BASE_URL = `/api/v1`

type HttpMethod = "GET" | "POST" | "PUT" | "PATCH" | "DELETE"

interface RequestConfig {
  method: HttpMethod
  body?: Record<string, unknown> | null;
  headers?: Record<string, string>;
  requiresAuth?: boolean
}

class ApiError extends Error {
  constructor(
    public message: string,
    public status: number,
    public data?: any
  ) {
    super(message)
    this.name = "ApiError"
  }
}

class ApiClient {
  private baseUrl: string
  private defaultHeaders: Record<string, string>

  constructor(baseUrl: string = API_BASE_URL) {
    this.baseUrl = baseUrl
    this.defaultHeaders = {
      "Content-Type": "application/json",
    }
  }

  private getAuthHeader(): Record<string, string> | undefined {
    if (typeof window === "undefined") return undefined

    const token = localStorage.getItem("access_token")
    if (token) {
      return { Authorization: `Bearer ${token}` }
    }
    return undefined
  }

  private async request<T>(
    endpoint: string,
    config: RequestConfig
  ): Promise<T> {
    const { method, body, headers = {}, requiresAuth = true } = config

    const requestHeaders: Record<string, string> = {
      ...this.defaultHeaders,
      ...headers,
    }

    if (requiresAuth) {
      const authHeader = this.getAuthHeader()
      if (authHeader) {
        Object.assign(requestHeaders, authHeader)
      } else if (typeof window !== "undefined") {
        // Redirect to login if no token and auth is required
        window.location.href = "/login"
        throw new ApiError("Authentication required", 401)
      }
    }

    const url = `${this.baseUrl}${endpoint}`

    try {
      const response = await fetch(url, {
        method,
        headers: requestHeaders,
        body: body ? JSON.stringify(body) : undefined,
      })

      const data = await response.json()

      if (!response.ok) {
        throw new ApiError(
          data.message || data.detail || "An error occurred",
          response.status,
          data
        )
      }

      return data
    } catch (error: unknown) {
      if (error instanceof ApiError) {
        throw error
      }

      // Network error or other issues
      throw new ApiError(
        "Network error. Please check your connection.",
        0,
        error
      )
    }
  }

  async get<T>(endpoint: string, requiresAuth = true): Promise<T> {
    return this.request<T>(endpoint, { method: "GET", requiresAuth })
  }

  async post<T>(endpoint: string, body: any, requiresAuth = true): Promise<T> {
    return this.request<T>(endpoint, { method: "POST", body, requiresAuth })
  }

  async put<T>(endpoint: string, body: any, requiresAuth = true): Promise<T> {
    return this.request<T>(endpoint, { method: "PUT", body, requiresAuth })
  }

  async patch<T>(endpoint: string, body: any, requiresAuth = true): Promise<T> {
    return this.request<T>(endpoint, { method: "PATCH", body, requiresAuth })
  }

  async delete<T>(endpoint: string, requiresAuth = true): Promise<T> {
    return this.request<T>(endpoint, { method: "DELETE", requiresAuth })
  }
}

// API instance
export const api = new ApiClient()

interface AuthResponse {
  access_token: string
  refresh_token: string
}

// Auth API
export const authApi = {
  sendOTP: (phone: string) =>
    api.post("/auth/otp/request", { phone_number: phone, purpose: "login" }, false),

  verifyOTP: (phone: string, otp: string) =>
    api.post<AuthResponse>("/auth/otp/verify", { phone_number: phone, otp_code: otp }, false),

  refreshToken: (refreshToken: string) =>
    api.post<AuthResponse>("/auth/refresh", { refresh_token: refreshToken }, false),

  logout: () => api.post("/auth/logout", {}),
}

// Commodities API
export const commodityApi = {
  list: (params?: { page?: number; limit?: number; search?: string }) =>
    api.get<{ items: any[] }>("/commodities" + (params ? `?${new URLSearchParams(params as any)}` : "")).then((r) => r.items),

  get: (id: number) => api.get(`/commodities/${id}`),
}

// Mandis API
export const mandiApi = {
  list: (params?: { page?: number; limit?: number; state?: string; district?: string }) =>
    api.get<{ items: any[] }>("/mandis" + (params ? `?${new URLSearchParams(params as any)}` : "")).then((r) => r.items),

  get: (id: number) => api.get(`/mandis/${id}`),

  nearby: (lat: number, lon: number, radius: number = 50) =>
    api.post("/mandis/nearby", { latitude: lat, longitude: lon, radius_km: radius, limit: 10 }),

  getBestPrice: (lat: number, lon: number, commodityId: number) =>
    api.post(`/routing/recommend`, { latitude: lat, longitude: lon, commodity_id: commodityId }),
}

// Prices API
export const priceApi = {
  getHistory: (params: {
    commodity_id: number
    mandi_id?: number
    start_date?: string
    end_date?: string
  }) => api.get<{ items: any[] }>("/prices" + `?${new URLSearchParams(params as any)}`).then((r) => r.items),

  getCurrent: (commodityId: number, mandiId?: number) =>
    mandiId
      ? api.get(`/prices/current/mandi/${mandiId}`)
      : api.get(`/prices/current/commodity/${commodityId}`),
}

// Forecast API
export const forecastApi = {
  predict: (commodityId: number, mandiId: number, days: number = 7) =>
    api.get(`/forecasts/${commodityId}/${mandiId}?horizon_days=${days}`),

  explainability: (commodityId: number, mandiId: number) =>
    api.get(`/forecasts/${commodityId}/${mandiId}?horizon_days=7&include_explanation=true`),
}

// Alerts API
export const alertApi = {
  list: async () => [],
  create: (data: {
    commodity_id: number
    mandi_id?: number
    target_price: number
    condition: "above" | "below"
  }) => {
    void data
    return Promise.reject(new ApiError("Alerts endpoint is not available in this backend build", 501))
  },
  delete: (id: number) => {
    void id
    return Promise.reject(new ApiError("Alerts endpoint is not available in this backend build", 501))
  },
  update: (id: number, data: any) => {
    void id
    void data
    return Promise.reject(new ApiError("Alerts endpoint is not available in this backend build", 501))
  },
}

export { ApiError }
