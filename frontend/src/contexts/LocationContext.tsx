"use client"

import React, { createContext, useContext, useState, useEffect, useCallback } from "react"

interface Coordinates {
  lat: number
  lon: number
}

interface LocationContextType {
  location: Coordinates | null
  isLoading: boolean
  error: string | null
  permission: "granted" | "denied" | "prompt" | "unknown"
  requestLocation: () => Promise<void>
  setLocation: (location: Coordinates | null) => void
}

const LocationContext = createContext<LocationContextType | undefined>(undefined)

export function LocationProvider({ children }: { children: React.ReactNode }) {
  const [location, setLocation] = useState<Coordinates | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [permission, setPermission] = useState<"granted" | "denied" | "prompt" | "unknown">("unknown")

  useEffect(() => {
    if (typeof window === "undefined" || !navigator.geolocation) {
      setError("Geolocation is not supported by your browser")
      return
    }

    // Check permission status
    if ("permissions" in navigator) {
      navigator.permissions.query({ name: "geolocation" as PermissionName }).then((result) => {
        setPermission(result.state as "granted" | "denied" | "prompt")

        result.addEventListener("change", () => {
          setPermission(result.state as "granted" | "denied" | "prompt")
        })
      })
    }

    // Load cached location
    const cachedLocation = localStorage.getItem("cached_location")
    if (cachedLocation) {
      try {
        setLocation(JSON.parse(cachedLocation))
      } catch (e) {
        console.error("Failed to parse cached location:", e)
      }
    }
  }, [])

  const requestLocation = useCallback(async () => {
    if (!navigator.geolocation) {
      setError("Geolocation is not supported by your browser")
      return
    }

    setIsLoading(true)
    setError(null)

    try {
      const position = await new Promise<GeolocationPosition>((resolve, reject) => {
        navigator.geolocation.getCurrentPosition(
          resolve,
          reject,
          {
            enableHighAccuracy: true,
            timeout: 10000,
            maximumAge: 5 * 60 * 1000, // 5 minutes
          }
        )
      })

      const coords: Coordinates = {
        lat: position.coords.latitude,
        lon: position.coords.longitude,
      }

      setLocation(coords)
      setPermission("granted")
      localStorage.setItem("cached_location", JSON.stringify(coords))
    } catch (err: any) {
      if (err.code === 1) {
        // PERMISSION_DENIED
        setPermission("denied")
        setError("Location access was denied. Please enable location in your browser settings.")
      } else if (err.code === 2) {
        // POSITION_UNAVAILABLE
        setError("Unable to determine your location. Please try again.")
      } else if (err.code === 3) {
        // TIMEOUT
        setError("Location request timed out. Please try again.")
      } else {
        setError("Failed to get your location. Please try again.")
      }
    } finally {
      setIsLoading(false)
    }
  }, [])

  const value: LocationContextType = {
    location,
    isLoading,
    error,
    permission,
    requestLocation,
    setLocation: (loc) => {
      setLocation(loc)
      if (loc) {
        localStorage.setItem("cached_location", JSON.stringify(loc))
      } else {
        localStorage.removeItem("cached_location")
      }
    },
  }

  return <LocationContext.Provider value={value}>{children}</LocationContext.Provider>
}

export function useLocation() {
  const context = useContext(LocationContext)
  if (context === undefined) {
    throw new Error("useLocation must be used within a LocationProvider")
  }
  return context
}
