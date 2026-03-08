"use client"

import React, { createContext, useContext, useState, useEffect, useCallback } from "react"

type Language = "en" | "hi" | "pa" | "ta" | "te" | "mr" | "bn" | "gu"

interface AppSettings {
  language: Language
  darkMode: boolean
  notifications: {
    priceAlerts: boolean
    weatherAlerts: boolean
    marketUpdates: boolean
    whatsapp: boolean
  }
  defaultCommodity: string | null
  defaultMandi: number | null
}

interface SettingsContextType {
  settings: AppSettings
  updateSettings: (updates: Partial<AppSettings>) => void
  updateNotificationSetting: (key: keyof AppSettings["notifications"], value: boolean) => void
  resetSettings: () => void
  isLoaded: boolean
}

const defaultSettings: AppSettings = {
  language: "hi",
  darkMode: true,
  notifications: {
    priceAlerts: true,
    weatherAlerts: true,
    marketUpdates: false,
    whatsapp: true,
  },
  defaultCommodity: null,
  defaultMandi: null,
}

const SettingsContext = createContext<SettingsContextType | undefined>(undefined)

export function SettingsProvider({ children }: { children: React.ReactNode }) {
  const [settings, setSettings] = useState<AppSettings>(defaultSettings)
  const [isLoaded, setIsLoaded] = useState(false)

  useEffect(() => {
    // Load settings from localStorage
    const storedSettings = localStorage.getItem("app_settings")
    if (storedSettings) {
      try {
        const parsed = JSON.parse(storedSettings)
        setSettings({ ...defaultSettings, ...parsed, notifications: { ...defaultSettings.notifications, ...parsed.notifications } })
      } catch (e) {
        console.error("Failed to parse stored settings:", e)
      }
    }
    setIsLoaded(true)
  }, [])

  // Apply dark mode to document
  useEffect(() => {
    if (typeof document !== "undefined") {
      if (settings.darkMode) {
        document.documentElement.classList.add("dark")
      } else {
        document.documentElement.classList.remove("dark")
      }
    }
  }, [settings.darkMode])

  // Apply language to <html lang> attribute
  useEffect(() => {
    if (typeof document !== "undefined") {
      document.documentElement.lang = settings.language === "hi" ? "hi" : "en"
    }
  }, [settings.language])

  const updateSettings = useCallback((updates: Partial<AppSettings>) => {
    setSettings(prev => {
      const newSettings = { ...prev, ...updates }
      localStorage.setItem("app_settings", JSON.stringify(newSettings))
      return newSettings
    })
  }, [])

  const updateNotificationSetting = useCallback((
    key: keyof AppSettings["notifications"],
    value: boolean
  ) => {
    setSettings(prev => {
      const newSettings = {
        ...prev,
        notifications: {
          ...prev.notifications,
          [key]: value,
        },
      }
      localStorage.setItem("app_settings", JSON.stringify(newSettings))
      return newSettings
    })
  }, [])

  const resetSettings = useCallback(() => {
    setSettings(defaultSettings)
    localStorage.removeItem("app_settings")
  }, [])

  const value: SettingsContextType = {
    settings,
    updateSettings,
    updateNotificationSetting,
    resetSettings,
    isLoaded,
  }

  return <SettingsContext.Provider value={value}>{children}</SettingsContext.Provider>
}

export function useSettings() {
  const context = useContext(SettingsContext)
  if (context === undefined) {
    throw new Error("useSettings must be used within a SettingsProvider")
  }
  return context
}
