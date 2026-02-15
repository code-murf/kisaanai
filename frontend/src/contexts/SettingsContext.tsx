"use client"

import React, { createContext, useContext, useState, useEffect } from "react"

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

  useEffect(() => {
    // Load settings from localStorage
    const storedSettings = localStorage.getItem("app_settings")
    if (storedSettings) {
      try {
        const parsed = JSON.parse(storedSettings)
        setSettings({ ...defaultSettings, ...parsed })
      } catch (e) {
        console.error("Failed to parse stored settings:", e)
      }
    }
  }, [])

  useEffect(() => {
    // Apply dark mode to document
    if (typeof document !== "undefined") {
      if (settings.darkMode) {
        document.documentElement.classList.add("dark")
      } else {
        document.documentElement.classList.remove("dark")
      }
    }
  }, [settings.darkMode])

  const updateSettings = (updates: Partial<AppSettings>) => {
    const newSettings = { ...settings, ...updates }
    setSettings(newSettings)
    localStorage.setItem("app_settings", JSON.stringify(newSettings))
  }

  const updateNotificationSetting = (
    key: keyof AppSettings["notifications"],
    value: boolean
  ) => {
    const newSettings = {
      ...settings,
      notifications: {
        ...settings.notifications,
        [key]: value,
      },
    }
    setSettings(newSettings)
    localStorage.setItem("app_settings", JSON.stringify(newSettings))
  }

  const resetSettings = () => {
    setSettings(defaultSettings)
    localStorage.removeItem("app_settings")
  }

  const value: SettingsContextType = {
    settings,
    updateSettings,
    updateNotificationSetting,
    resetSettings,
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
