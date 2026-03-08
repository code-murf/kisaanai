"use client"

import { useState, useEffect } from "react"
import { User, MapPin, Bell, Globe, Shield, ChevronRight, Check, RotateCcw, Sun, Moon } from "lucide-react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { useSettings } from "@/contexts/SettingsContext"
import { useTranslation } from "@/hooks/useTranslation"
import { motion, AnimatePresence } from "framer-motion"

function Toast({ message, show }: { message: string; show: boolean }) {
  return (
    <AnimatePresence>
      {show && (
        <motion.div
          initial={{ opacity: 0, y: 50, scale: 0.9 }}
          animate={{ opacity: 1, y: 0, scale: 1 }}
          exit={{ opacity: 0, y: 20, scale: 0.95 }}
          className="fixed bottom-24 left-1/2 -translate-x-1/2 z-[100] flex items-center gap-2 bg-primary text-primary-foreground px-5 py-3 rounded-full shadow-xl text-sm font-medium"
        >
          <Check className="h-4 w-4" />
          {message}
        </motion.div>
      )}
    </AnimatePresence>
  )
}

interface UserProfile {
  name: string
  phone: string
  email: string
  state: string
  district: string
  defaultMandi: string
}

export default function SettingsPage() {
  const { settings, updateSettings, updateNotificationSetting, resetSettings } = useSettings()
  const { t, locale } = useTranslation()
  const [toast, setToast] = useState<string | null>(null)
  const [profile, setProfile] = useState<UserProfile>({
    name: "",
    phone: "",
    email: "",
    state: "",
    district: "",
    defaultMandi: "",
  })

  // Try fetching user profile from API
  useEffect(() => {
    async function fetchProfile() {
      try {
        const token = window.localStorage.getItem("access_token")
        if (!token) return

        const res = await fetch("/api/v1/auth/me", {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        })
        if (res.status === 401 || res.status === 403) return
        if (res.ok) {
          const data = await res.json()
          setProfile({
            name: data.name || data.full_name || "",
            phone: data.phone || data.phone_number || "",
            email: data.email || "",
            state: data.state || "",
            district: data.district || "",
            defaultMandi: data.default_mandi || "",
          })
        }
      } catch {
        // Not logged in — profile stays empty
      }
    }
    fetchProfile()
  }, [])

  // Fetch location info from mandis states
  useEffect(() => {
    async function fetchLocationInfo() {
      try {
        const statesRes = await fetch("/api/v1/mandis/states")
        if (statesRes.ok) {
          const states = await statesRes.json()
          if (Array.isArray(states) && states.length > 0 && !profile.state) {
            setProfile((prev) => ({ ...prev, state: states[0] }))
          }
        }
      } catch {
        // Optional
      }
    }
    fetchLocationInfo()
  }, [profile.state])

  const showToast = (msg: string) => {
    setToast(msg)
    setTimeout(() => setToast(null), 2000)
  }

  const handleLanguageChange = (lang: "hi" | "en") => {
    updateSettings({ language: lang })
    showToast(lang === "hi" ? "भाषा: हिन्दी" : "Language: English")
  }

  const handleDarkModeToggle = () => {
    const newVal = !settings.darkMode
    updateSettings({ darkMode: newVal })
    showToast(newVal ? (locale === "hi" ? "डार्क मोड चालू" : "Dark Mode On") : (locale === "hi" ? "लाइट मोड चालू" : "Light Mode On"))
  }

  const handleNotifToggle = (key: keyof typeof settings.notifications) => {
    const newVal = !settings.notifications[key]
    updateNotificationSetting(key, newVal)
    showToast(newVal ? (locale === "hi" ? "चालू" : "Enabled") : (locale === "hi" ? "बंद" : "Disabled"))
  }

  const handleReset = () => {
    resetSettings()
    showToast(locale === "hi" ? "सेटिंग्स रीसेट हो गईं" : "Settings reset")
  }

  const initials = profile.name
    ? profile.name.split(" ").map((w) => w[0]).join("").toUpperCase().slice(0, 2)
    : "?"

  return (
    <div className="flex flex-col gap-6 p-4 md:p-8 pb-24">
      <Toast message={toast || ""} show={!!toast} />

      <header className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">{t("settings.title")}</h1>
          <p className="text-muted-foreground">{t("settings.subtitle")}</p>
        </div>
        <Button variant="ghost" size="icon" onClick={handleReset} title="Reset Settings">
          <RotateCcw className="h-4 w-4" />
        </Button>
      </header>

      {/* Profile Card */}
      <Card className="overflow-hidden">
        <div className="h-16 bg-gradient-to-r from-emerald-600 to-emerald-400" />
        <CardContent className="-mt-8 pt-0">
          <div className="flex items-end gap-4">
            <div className="flex h-16 w-16 items-center justify-center rounded-full bg-primary text-primary-foreground text-2xl font-bold border-4 border-background shadow-lg">
              {initials}
            </div>
            <div className="pb-1">
              <h3 className="text-lg font-semibold">{profile.name || (locale === "hi" ? "किसान" : "Farmer")}</h3>
              <p className="text-sm text-muted-foreground">{profile.phone || (locale === "hi" ? "लॉगिन करें" : "Login to see profile")}</p>
              {profile.name && <p className="text-xs text-emerald-600 dark:text-emerald-400 font-medium">{t("settings.verifiedFarmer")} ✓</p>}
            </div>
          </div>
        </CardContent>
      </Card>

      {/* ─── Language Selector ─── */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-lg">
            <Globe className="h-5 w-5 text-primary" />
            {t("settings.language")}
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 gap-3">
            <button
              onClick={() => handleLanguageChange("hi")}
              className={`flex flex-col items-center gap-2 p-4 rounded-xl border-2 transition-all ${
                locale === "hi"
                  ? "border-primary bg-primary/10 shadow-md"
                  : "border-muted hover:border-primary/50 hover:bg-muted/50"
              }`}
            >
              <span className="text-2xl">🇮🇳</span>
              <span className="font-semibold">हिन्दी</span>
              <span className="text-xs text-muted-foreground">Hindi</span>
              {locale === "hi" && <Check className="h-4 w-4 text-primary" />}
            </button>
            <button
              onClick={() => handleLanguageChange("en")}
              className={`flex flex-col items-center gap-2 p-4 rounded-xl border-2 transition-all ${
                locale === "en"
                  ? "border-primary bg-primary/10 shadow-md"
                  : "border-muted hover:border-primary/50 hover:bg-muted/50"
              }`}
            >
              <span className="text-2xl">🌐</span>
              <span className="font-semibold">English</span>
              <span className="text-xs text-muted-foreground">English</span>
              {locale === "en" && <Check className="h-4 w-4 text-primary" />}
            </button>
          </div>
        </CardContent>
      </Card>

      {/* ─── Appearance ─── */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-lg">
            {settings.darkMode ? <Moon className="h-5 w-5 text-primary" /> : <Sun className="h-5 w-5 text-primary" />}
            {t("settings.darkMode")}
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-between">
            <div>
              <p className="font-medium">{settings.darkMode ? (locale === "hi" ? "डार्क थीम" : "Dark Theme") : (locale === "hi" ? "लाइट थीम" : "Light Theme")}</p>
              <p className="text-sm text-muted-foreground">
                {locale === "hi" ? "ऐप की दिखावट बदलें" : "Change app appearance"}
              </p>
            </div>
            <button
              onClick={handleDarkModeToggle}
              className={`relative h-7 w-12 rounded-full transition-colors duration-300 ${
                settings.darkMode ? "bg-primary" : "bg-muted"
              }`}
            >
              <motion.span
                layout
                className="absolute top-1 h-5 w-5 rounded-full bg-white shadow-md flex items-center justify-center"
                animate={{ x: settings.darkMode ? 24 : 4 }}
                transition={{ type: "spring", stiffness: 500, damping: 30 }}
              >
                {settings.darkMode ? <Moon className="h-3 w-3 text-slate-700" /> : <Sun className="h-3 w-3 text-amber-500" />}
              </motion.span>
            </button>
          </div>
        </CardContent>
      </Card>

      {/* ─── Account ─── */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-lg">
            <User className="h-5 w-5 text-primary" />
            {t("settings.account")}
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-0 p-0 px-6">
          {[
            { label: t("settings.phoneNumber"), value: profile.phone || "—", action: t("settings.edit") },
            { label: t("settings.name"), value: profile.name || "—", action: t("settings.edit") },
            { label: t("settings.email"), value: profile.email || "—", action: t("settings.edit") },
          ].map((item, i) => (
            <button key={i} className="flex items-center justify-between py-3.5 border-b last:border-0 w-full text-left hover:bg-accent/50 px-2 -mx-2 rounded transition-colors">
              <div>
                <p className="font-medium">{item.label}</p>
                <p className="text-sm text-muted-foreground">{item.value}</p>
              </div>
              <div className="flex items-center gap-1 text-muted-foreground">
                <span className="text-sm">{item.action}</span>
                <ChevronRight className="h-4 w-4" />
              </div>
            </button>
          ))}
        </CardContent>
      </Card>

      {/* ─── Location ─── */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-lg">
            <MapPin className="h-5 w-5 text-primary" />
            {t("settings.location")}
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-0 p-0 px-6">
          {[
            { label: t("settings.state"), value: profile.state || "—", action: t("settings.change") },
            { label: t("settings.district"), value: profile.district || "—", action: t("settings.change") },
            { label: t("settings.defaultMandi"), value: profile.defaultMandi || "—", action: t("settings.change") },
          ].map((item, i) => (
            <button key={i} className="flex items-center justify-between py-3.5 border-b last:border-0 w-full text-left hover:bg-accent/50 px-2 -mx-2 rounded transition-colors">
              <div>
                <p className="font-medium">{item.label}</p>
                <p className="text-sm text-muted-foreground">{item.value}</p>
              </div>
              <div className="flex items-center gap-1 text-muted-foreground">
                <span className="text-sm">{item.action}</span>
                <ChevronRight className="h-4 w-4" />
              </div>
            </button>
          ))}
        </CardContent>
      </Card>

      {/* ─── Notifications ─── */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-lg">
            <Bell className="h-5 w-5 text-primary" />
            {t("settings.notifications")}
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-0 p-0 px-6">
          {([
            { label: t("settings.priceAlerts"), key: "priceAlerts" as const, desc: locale === "hi" ? "भाव बदलने पर सूचना" : "Get notified when prices change" },
            { label: t("settings.weatherAlerts"), key: "weatherAlerts" as const, desc: locale === "hi" ? "मौसम अलर्ट प्राप्त करें" : "Receive weather alerts" },
            { label: t("settings.marketUpdates"), key: "marketUpdates" as const, desc: locale === "hi" ? "बाज़ार अपडेट समाचार" : "Market update news" },
            { label: t("settings.whatsappNotifications"), key: "whatsapp" as const, desc: locale === "hi" ? "व्हाट्सएप पर सूचनाएं" : "Get notifications on WhatsApp" },
          ] as const).map((item) => (
            <div key={item.key} className="flex items-center justify-between py-3.5 border-b last:border-0">
              <div>
                <p className="font-medium">{item.label}</p>
                <p className="text-xs text-muted-foreground">{item.desc}</p>
              </div>
              <button
                onClick={() => handleNotifToggle(item.key)}
                className={`relative h-7 w-12 rounded-full transition-colors duration-300 ${
                  settings.notifications[item.key] ? "bg-primary" : "bg-muted"
                }`}
              >
                <motion.span
                  layout
                  className="absolute top-1 h-5 w-5 rounded-full bg-white shadow-md"
                  animate={{ x: settings.notifications[item.key] ? 24 : 4 }}
                  transition={{ type: "spring", stiffness: 500, damping: 30 }}
                />
              </button>
            </div>
          ))}
        </CardContent>
      </Card>

      {/* ─── Security ─── */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-lg">
            <Shield className="h-5 w-5 text-primary" />
            {t("settings.security")}
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-0 p-0 px-6">
          {[
            { label: t("settings.changePin"), value: "", action: t("settings.update") },
            { label: t("settings.privacyPolicy"), value: "", action: t("settings.view") },
            { label: t("settings.termsOfService"), value: "", action: t("settings.view") },
          ].map((item, i) => (
            <button key={i} className="flex items-center justify-between py-3.5 border-b last:border-0 w-full text-left hover:bg-accent/50 px-2 -mx-2 rounded transition-colors">
              <div>
                <p className="font-medium">{item.label}</p>
                {item.value && <p className="text-sm text-muted-foreground">{item.value}</p>}
              </div>
              <div className="flex items-center gap-1 text-muted-foreground">
                <span className="text-sm">{item.action}</span>
                <ChevronRight className="h-4 w-4" />
              </div>
            </button>
          ))}
        </CardContent>
      </Card>

      {/* App Info */}
      <Card className="bg-muted/50">
        <CardContent className="pt-6">
          <div className="text-center space-y-2">
            <p className="font-medium text-lg">{t("settings.appTitle")}</p>
            <p className="text-sm text-muted-foreground">{t("settings.version")}</p>
            <p className="text-xs text-muted-foreground">{t("settings.madeWith")}</p>
          </div>
        </CardContent>
      </Card>

      {/* Logout Button */}
      <Button variant="destructive" className="w-full text-base py-6 rounded-xl">
        {t("settings.logout")}
      </Button>
    </div>
  )
}
