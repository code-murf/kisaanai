"use client"

import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import { useState } from "react"
import { AuthProvider } from "@/contexts/AuthContext"
import { LocationProvider } from "@/contexts/LocationContext"
import { SettingsProvider } from "@/contexts/SettingsContext"

function createQueryClient() {
  return new QueryClient({
    defaultOptions: {
      queries: {
        staleTime: 60 * 1000,
        refetchOnWindowFocus: false,
        retry: 1,
      },
      mutations: {
        retry: 1,
      },
    },
  })
}

export default function Providers({ children }: { children: React.ReactNode }) {
  const [queryClient] = useState(createQueryClient)

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
