"use client"

import { useState } from "react"
import { Globe, Moon, Sun, Check, RotateCcw, Heart } from "lucide-react"
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
          className="fixed bottom-24 md:bottom-10 left-1/2 -translate-x-1/2 z-[100] flex items-center gap-2 bg-primary text-primary-foreground px-5 py-3 rounded-full shadow-xl text-sm font-medium"
        >
          <Check className="h-4 w-4" />
          {message}
        </motion.div>
      )}
    </AnimatePresence>
  )
}

export default function SettingsPage() {
  const { settings, updateSettings, resetSettings } = useSettings()
  const { t, locale } = useTranslation()
  const [toast, setToast] = useState<string | null>(null)

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

  const handleReset = () => {
    resetSettings()
    showToast(locale === "hi" ? "सेटिंग्स रीसेट हो गईं" : "Settings reset")
  }

  return (
    <div className="flex flex-col gap-6 p-4 md:p-8 pb-24 md:pb-8 max-w-2xl mx-auto">
      <Toast message={toast || ""} show={!!toast} />

      <header className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">{t("settings.title")}</h1>
          <p className="text-muted-foreground">{t("settings.subtitle")}</p>
        </div>
        <Button variant="ghost" size="sm" onClick={handleReset} title="Reset Settings">
          <RotateCcw className="h-4 w-4 mr-2" />
          {locale === "hi" ? "रीसेट" : "Reset"}
        </Button>
      </header>

      {/* Language Selector */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-lg">
            <Globe className="h-5 w-5 text-primary" />
            {t("settings.language")}
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 gap-4">
            <button
              onClick={() => handleLanguageChange("hi")}
              className={`flex flex-col items-center gap-2 p-4 rounded-xl border-2 transition-all ${
                locale === "hi"
                  ? "border-primary bg-primary/10 shadow-md"
                  : "border-muted hover:border-primary/50 hover:bg-muted/50"
              }`}
            >
              <span className="text-3xl">🇮🇳</span>
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
              <span className="text-3xl">🌐</span>
              <span className="font-semibold">English</span>
              <span className="text-xs text-muted-foreground">English</span>
              {locale === "en" && <Check className="h-4 w-4 text-primary" />}
            </button>
          </div>
        </CardContent>
      </Card>

      {/* Appearance */}
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

      {/* App Info */}
      <Card className="bg-muted/30">
        <CardContent className="pt-6">
          <div className="text-center space-y-3">
            <p className="font-bold text-xl text-primary">KisaanAI</p>
            <p className="text-sm text-muted-foreground">Version 1.0.0</p>
            <p className="text-xs text-muted-foreground max-w-md mx-auto">
              {locale === "hi"
                ? "भारतीय किसानों के लिए AI-संचालित कृषि खुफिया मंच"
                : "AI-Powered Agriculture Intelligence Platform for Indian Farmers"}
            </p>
            <div className="flex items-center justify-center gap-1 text-xs text-muted-foreground pt-2">
              Made with <Heart className="h-3 w-3 text-red-500 fill-red-500" /> for farmers
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
