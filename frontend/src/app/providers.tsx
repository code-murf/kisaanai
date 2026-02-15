"use client"

import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import { getQueryClient } from "@/app/get-query-client"
import { AuthProvider } from "@/contexts/AuthContext"
import { LocationProvider } from "@/contexts/LocationContext"
import { SettingsProvider } from "@/contexts/SettingsContext"

export default function Providers({ children }: { children: React.ReactNode }) {
  const queryClient = getQueryClient()

  return (
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <LocationProvider>
          <SettingsProvider>
            {children}
          </SettingsProvider>
        </LocationProvider>
      </AuthProvider>
    </QueryClientProvider>
  )
}
