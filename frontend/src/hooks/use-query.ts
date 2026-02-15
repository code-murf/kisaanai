/**
 * React Query Hooks for Agri-Analytics
 * Provides hooks for data fetching with caching and error handling
 */

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import {
  commodityApi,
  mandiApi,
  priceApi,
  forecastApi,
  alertApi,
  authApi,
  ApiError,
} from "@/lib/api-client"

// Query keys factory
export const queryKeys = {
  commodities: ["commodities"] as const,
  commodity: (id: number) => ["commodities", id] as const,
  mandis: ["mandis"] as const,
  mandi: (id: number) => ["mandis", id] as const,
  nearbyMandis: (lat: number, lon: number) => ["mandis", "nearby", lat, lon] as const,
  prices: (filters: any) => ["prices", filters] as const,
  forecast: (commodityId: number, mandiId: number) => ["forecast", commodityId, mandiId] as const,
  alerts: ["alerts"] as const,
  user: ["user"] as const,
}

// Commodity hooks
export function useCommodities(params?: { page?: number; limit?: number; search?: string }) {
  return useQuery({
    queryKey: queryKeys.commodities,
    queryFn: () => commodityApi.list(params),
    staleTime: 5 * 60 * 1000, // 5 minutes
  })
}

export function useCommodity(id: number) {
  return useQuery({
    queryKey: queryKeys.commodity(id),
    queryFn: () => commodityApi.get(id),
    enabled: !!id,
  })
}

// Mandi hooks
export function useMandis(params?: { page?: number; limit?: number; state?: string; district?: string }) {
  return useQuery({
    queryKey: [...queryKeys.mandis, params],
    queryFn: () => mandiApi.list(params),
    staleTime: 5 * 60 * 1000,
  })
}

export function useMandi(id: number) {
  return useQuery({
    queryKey: queryKeys.mandi(id),
    queryFn: () => mandiApi.get(id),
    enabled: !!id,
  })
}

export function useNearbyMandis(lat: number, lon: number, radius = 50) {
  return useQuery({
    queryKey: queryKeys.nearbyMandis(lat, lon),
    queryFn: () => mandiApi.nearby(lat, lon, radius),
    enabled: !!lat && !!lon,
    staleTime: 2 * 60 * 1000, // 2 minutes
  })
}

export function useOptimalMandi() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ lat, lon, commodityId }: { lat: number; lon: number; commodityId: number }) =>
      mandiApi.getBestPrice(lat, lon, commodityId),
    onSuccess: (data) => {
      // Invalidate related queries
      queryClient.invalidateQueries({ queryKey: ["mandis", "nearby"] })
    },
  })
}

// Price hooks
export function usePriceHistory(params: {
  commodity_id: number
  mandi_id?: number
  start_date?: string
  end_date?: string
}) {
  return useQuery({
    queryKey: queryKeys.prices(params),
    queryFn: () => priceApi.getHistory(params),
    enabled: !!params.commodity_id,
    staleTime: 10 * 60 * 1000, // 10 minutes
  })
}

export function useCurrentPrice(commodityId: number, mandiId?: number) {
  return useQuery({
    queryKey: ["prices", "current", commodityId, mandiId],
    queryFn: () => priceApi.getCurrent(commodityId, mandiId),
    enabled: !!commodityId,
    staleTime: 5 * 60 * 1000,
    refetchInterval: 5 * 60 * 1000, // Refetch every 5 minutes
  })
}

// Forecast hooks
export function useForecast(commodityId: number, mandiId: number, days = 7) {
  return useQuery({
    queryKey: [...queryKeys.forecast(commodityId, mandiId), days],
    queryFn: () => forecastApi.predict(commodityId, mandiId, days),
    enabled: !!commodityId && !!mandiId,
    staleTime: 30 * 60 * 1000, // 30 minutes
  })
}

export function useForecastExplainability(commodityId: number, mandiId: number) {
  return useQuery({
    queryKey: ["forecast", "explain", commodityId, mandiId],
    queryFn: () => forecastApi.explainability(commodityId, mandiId),
    enabled: !!commodityId && !!mandiId,
    staleTime: 60 * 60 * 1000, // 1 hour
  })
}

// Alert hooks
export function useAlerts() {
  return useQuery({
    queryKey: queryKeys.alerts,
    queryFn: () => alertApi.list(),
    staleTime: 2 * 60 * 1000,
  })
}

export function useCreateAlert() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: alertApi.create,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.alerts })
    },
  })
}

export function useDeleteAlert() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (id: number) => alertApi.delete(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.alerts })
    },
  })
}

export function useUpdateAlert() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ id, data }: { id: number; data: any }) => alertApi.update(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.alerts })
    },
  })
}

// Auth hooks
export function useSendOTP() {
  return useMutation({
    mutationFn: (phone: string) => authApi.sendOTP(phone),
  })
}

export function useVerifyOTP() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ phone, otp }: { phone: string; otp: string }) =>
      authApi.verifyOTP(phone, otp),
    onSuccess: (data) => {
      // Store tokens
      if (data.access_token) {
        localStorage.setItem("access_token", data.access_token)
      }
      if (data.refresh_token) {
        localStorage.setItem("refresh_token", data.refresh_token)
      }
      // Invalidate and refetch user queries
      queryClient.invalidateQueries({ queryKey: queryKeys.user })
    },
  })
}

export function useLogout() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: authApi.logout,
    onSuccess: () => {
      // Clear tokens
      localStorage.removeItem("access_token")
      localStorage.removeItem("refresh_token")
      // Clear all queries
      queryClient.clear()
    },
  })
}

export { ApiError }
